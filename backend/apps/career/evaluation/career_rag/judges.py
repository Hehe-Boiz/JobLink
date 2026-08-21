from __future__ import annotations

import json
import hashlib
import threading
from pathlib import Path
import os
import random
import time
import re
from functools import partial
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from django.conf import settings
from openai import OpenAI

from apps.career.normalization import normalize_key

from .schema import CareerTopic, CorpusJob, PooledCandidate, RelevanceJudgment
from .semantics import topic_description

from .concurrency import DEFAULT_MAX_IN_FLIGHT, DEFAULT_REFILL_SIZE, RefillWindowConfig, run_refill_window

JUDGE_PROMPT_VERSION = "career-rag-silver-qrels-v2"
JUDGE_VIEWS = (
    "query-centric: Does this JD directly help answer the user's career information need?",
    "evidence-centric: Does this JD contain requirements, skills, or responsibilities useful for this information need?",
    "conservative: Give grade 2-3 only when the connection and useful evidence are clearly supported by the raw JD text.",
)


@dataclass(frozen=True, slots=True)
class ControlResult:
    control_id: str
    control_type: str
    topic_id: str
    job_key: str
    expected: str
    grade: int
    judge_grades: tuple[int, int, int]
    passed: bool

    def to_dict(self) -> dict:
        return {
            "control_id": self.control_id,
            "control_type": self.control_type,
            "topic_id": self.topic_id,
            "job_key": self.job_key,
            "expected": self.expected,
            "grade": self.grade,
            "judge_grades": list(self.judge_grades),
            "passed": self.passed,
        }


class JudgeClient:
    """
    Robust LLM transport for benchmark construction.

    Properties:
    - bounded global request-start rate
    - shared cooldown on 429
    - adaptive request spacing
    - independent 429 / transport / JSON retries
    - persistent prompt-response cache
    - atomic cache writes

    The transport layer does NOT change benchmark
    prompts or relevance/nugget semantics.
    """

    _gate_lock = threading.Lock()

    _next_request_at = 0.0
    _cooldown_until = 0.0

    _current_interval = 0.0
    _rate_limit_streak = 0

    def __init__(self, model_name: str, client: OpenAI | None = None) -> None:
        self.model_name = model_name
        self.client = client or self._make_client()


    @staticmethod
    def _make_client() -> OpenAI:
        api_key = getattr(settings, "CKEY_API_KEY", "",)
        base_url = getattr(settings, "CKEY_BASE_URL", "")
        if not api_key:
            raise RuntimeError("CKEY_API_KEY is required to build silver qrels/nuggets.")

        if not api_key.isascii():
            raise RuntimeError("CKEY_API_KEY contains non-ASCII characters. Check that a placeholder was not exported accidentally.")

        timeout = float(os.environ.get("CAREER_RAG_HTTP_TIMEOUT_SECONDS", "240"))
        return OpenAI(api_key=api_key, base_url=base_url or None, max_retries=0, timeout=timeout,)

    def _cache_key(self, *, system: str, user: str) -> str:
        base_url = getattr(settings, "CKEY_BASE_URL", "")
        payload = json.dumps(
            {
                "model": self.model_name,
                "base_url": base_url,
                "temperature": 0,
                "system": system,
                "user": user,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _cache_path(self, *, system: str, user: str) -> Path | None:
        if os.environ.get("CAREER_RAG_DISABLE_LLM_CACHE", "0") == "1":
            return None

        root = Path(
            os.environ.get(
                "CAREER_RAG_LLM_CACHE_DIR",
                (
                    "data/career_eval/"
                    "career_rag_bench_auto_v2/"
                    "checkpoints/llm_calls"
                ),
            )
        )

        key = self._cache_key(system=system, user=user)

        return root / key[:2] / f"{key}.json"

    def _load_cache(self, *, system: str, user: str) -> dict | None:
        path = self._cache_path(system=system, user=user,)
        if path is None or not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            payload = data.get("payload")
            if not isinstance(payload, dict,):
                raise ValueError("cached payload is not dict")

            return payload

        except Exception:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass

            return None

    def _save_cache(self, *, system: str, user: str, payload: dict) -> None:
        path = self._cache_path(system=system, user=user)
        if path is None:
            return

        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(
            (
                f".{path.name}."
                f"{os.getpid()}."
                f"{threading.get_ident()}.tmp"
            )
        )

        tmp.write_text(
            json.dumps(
                {
                    "model": self.model_name,
                    "payload": payload,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        os.replace(tmp, path)

    @classmethod
    def _base_interval(cls) -> float:
        return float(os.environ.get("CAREER_RAG_MIN_REQUEST_INTERVAL_SECONDS", "1.5"))

    @classmethod
    def _max_interval(cls) -> float:
        return float(os.environ.get("CAREER_RAG_MAX_REQUEST_INTERVAL_SECONDS", "6"))

    @classmethod
    def _wait_for_request_slot(cls) -> None:
        """
        Space REQUEST STARTS globally.

        Threads may still overlap while waiting for
        responses, but they cannot all hit the gateway
        at the same instant.
        """

        while True:
            with cls._gate_lock:
                now = time.monotonic()
                base = cls._base_interval()

                if cls._current_interval < base:
                    cls._current_interval = base

                target = max(cls._next_request_at, cls._cooldown_until)

                if now >= target:
                    cls._next_request_at = now + cls._current_interval

                    return

                delay = target - now

            time.sleep(min(delay, 1.0))

    @classmethod
    def _register_success(cls) -> None:
        """
        Slowly recover throughput after successful calls.
        """

        with cls._gate_lock:
            base = cls._base_interval()
            cls._current_interval = max(base, cls._current_interval* 0.90)
            cls._rate_limit_streak = max(0, cls._rate_limit_streak - 1)

    @classmethod
    def _register_rate_limit(cls, *, retry_after: float | None) -> tuple[float, float]:
        """
        Global congestion response.

        Every worker sees the same cooldown and the
        request-start interval increases adaptively.
        """

        with cls._gate_lock:
            cls._rate_limit_streak += 1

            base_cooldown = float(os.environ.get("CAREER_RAG_RATE_LIMIT_COOLDOWN_SECONDS", "10"))
            max_cooldown = float(os.environ.get("CAREER_RAG_RATE_LIMIT_MAX_COOLDOWN_SECONDS", "60"))
            exponent = min(cls._rate_limit_streak - 1, 4)
            cooldown = min(max_cooldown, base_cooldown * (2 ** exponent))

            if retry_after is not None:
                cooldown = max(cooldown, retry_after)

            now = time.monotonic()
            cls._cooldown_until = max(cls._cooldown_until,now + cooldown)
            base_interval = cls._base_interval()
            current = max(cls._current_interval, base_interval,)
            cls._current_interval = min(
                cls._max_interval(),
                max(base_interval, current * 1.5),
            )

            return (cooldown, cls._current_interval)

    @staticmethod
    def _retry_after_seconds(exc: Exception) -> float | None:
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", None)

        if not headers:
            return None

        value = headers.get("retry-after") or headers.get("Retry-After")

        if value is None:
            return None

        try:
            result = float(value)

            if result >= 0:
                return result

        except (TypeError, ValueError):
            pass

        return None

    def json_call(self, system: str,user: str, *, retries: int = 2) -> dict:
        cached = self._load_cache(system=system, user=user)

        if cached is not None:
            return cached

        rate_limit_budget = int(os.environ.get("CAREER_RAG_RATE_LIMIT_RETRIES", "50"))
        transport_budget = int(os.environ.get("CAREER_RAG_TRANSPORT_RETRIES", "10"))
        transport_base = float(os.environ.get( "CAREER_RAG_RETRY_BASE_SECONDS", "3"))
        transport_max = float(os.environ.get("CAREER_RAG_RETRY_MAX_SECONDS", "30"))
        jitter = float(os.environ.get("CAREER_RAG_RETRY_JITTER_SECONDS", "1"))

        rate_limit_used = 0
        transport_used = 0
        generic_used = 0

        transient_statuses = {
            408,
            409,
            500,
            502,
            503,
            504,
        }

        transient_names = {
            "APIConnectionError",
            "APITimeoutError",
            "InternalServerError",
        }

        while True:
            self._wait_for_request_slot()

            try:
                response = (
                    self.client
                    .chat
                    .completions
                    .create(
                        model=self.model_name,
                        temperature=0,
                        messages=[
                            {
                                "role": "system",
                                "content": system,
                            },
                            {
                                "role": "user",
                                "content": user,
                            },
                        ],
                    )
                )

                content = response.choices[0].message.content or ""
                payload = self._parse_json(content)
                self._register_success()
                self._save_cache(system=system, user=user, payload=payload)

                return payload

            except Exception as exc:
                status = getattr(exc, "status_code", None)
                error_name = exc.__class__.__name__
                if status == 429 or error_name == "RateLimitError":
                    if rate_limit_used >= rate_limit_budget:
                        raise RuntimeError(
                            "Judge rate limit persisted "
                            "after "
                            f"{rate_limit_budget} "
                            "retries: "
                            f"{exc}"
                        ) from exc

                    rate_limit_used += 1
                    retry_after = self._retry_after_seconds(exc)
                    (cooldown, interval) = self._register_rate_limit(retry_after=retry_after)
                    print(
                        "[rate-limit] "
                        f"429; "
                        f"attempt="
                        f"{rate_limit_used}/"
                        f"{rate_limit_budget}; "
                        f"global_cooldown="
                        f"{cooldown:.1f}s; "
                        f"request_interval="
                        f"{interval:.2f}s"
                    )

                    continue

                is_transport = status in transient_statuses or error_name in transient_names
                if is_transport:
                    if transport_used >= transport_budget:
                        raise RuntimeError(
                            "Judge transport failure "
                            "persisted after "
                            f"{transport_budget} "
                            "retries. "
                            f"error={error_name}; "
                            f"status={status}; "
                            f"detail={exc}"
                        ) from exc

                    delay = min(transport_max, transport_base* (2 ** transport_used))
                    delay += random.uniform(0.0, jitter)
                    transport_used += 1

                    print(
                        "[transport-retry] "
                        f"error={error_name}; "
                        f"status={status}; "
                        f"attempt="
                        f"{transport_used}/"
                        f"{transport_budget}; "
                        f"sleep={delay:.1f}s"
                    )

                    time.sleep(delay)

                    continue


                if status is not None and 400 <= status < 500:
                    raise RuntimeError(f"Non-retryable judge HTTP error {status}: {exc}") from exc

                if isinstance(exc, (UnicodeEncodeError, TypeError)):
                    raise RuntimeError(
                        "Non-retryable local judge "
                        f"error: {exc}"
                    ) from exc

                if generic_used >= retries:
                    raise RuntimeError(f"Judge call failed after semantic/JSON retries: {error_name}: {exc}") from exc

                generic_used += 1
                delay = min(2.0, 0.25 * (2 ** (generic_used - 1)))
                print(
                    "[json-retry] "
                    f"error={error_name}; "
                    f"attempt="
                    f"{generic_used}/{retries}; "
                    f"sleep={delay:.2f}s"
                )

                time.sleep(delay)

    @staticmethod
    def _parse_json(text: str) -> dict:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(
                (
                    r"^```(?:json)?\s*"
                    r"|\s*```$"
                ),
                "",
                stripped,
                flags=(re.IGNORECASE | re.DOTALL),
            )

        try:
            value = json.loads(stripped)
            if isinstance(value, dict):
                return value

        except json.JSONDecodeError:
            pass

        match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)

        if not match:
            raise ValueError(f"Model did not return JSON: {text[:300]!r}")

        value = json.loads(match.group(0))

        if not isinstance(value, dict):
            raise ValueError("Expected a JSON object")

        return value


def judge_candidates(
    client: JudgeClient,
    topic: CareerTopic,
    candidates: list[PooledCandidate],
    corpus_by_key: dict[str, CorpusJob],
    *,
    batch_size: int = 8,
    evidence_chars: int = 5000,
    information_need: str | None = None,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[RelevanceJudgment]:
    """
    Judge candidate batches concurrently.

    batch_size:
        number of JDs inside ONE API request.

    max_in_flight:
        maximum simultaneous API requests.

    refill_size:
        after this many logical requests finish,
        submit another refill group.

    Strict-schema validation is still atomic:
    no candidate grades are committed unless
    every request completes successfully.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")

    config = RefillWindowConfig(max_in_flight=max_in_flight, refill_size=refill_size,)
    config.validate()
    grades_by_key: dict[str, list[int | None]] = {
        candidate.job_key: [
            None
            for _ in JUDGE_VIEWS
        ]
        for candidate in candidates
    }

    def run_batch(view_index: int, view: str, batch_index: int, batch: list[PooledCandidate]):
        blocks: list[str] = []
        id_to_key: dict[str,str] = {}

        for index, candidate in enumerate(batch, start=1):
            cid = f"C{index}"

            id_to_key[cid] = candidate.job_key
            job = corpus_by_key[candidate.job_key]

            blocks.append(
                f"{cid}\n"
                f"{job.raw_evidence[:evidence_chars]}"
            )

        expected_ids = tuple(id_to_key)
        expected_set = set(expected_ids)
        expected_text = ", ".join(expected_ids)
        example_grades = ", ".join(
            f'"{cid}": 0'
            for cid in expected_ids
        )

        system_prompt = (
            "You create silver TREC-style relevance "
            "judgments for a career RAG benchmark. "
            "Judge only from the user's information "
            "need and raw JD evidence. "
            "Never use hidden retrieval scores. "
            "Grades: "
            "3=directly answers scope with strong useful "
            "skills/requirements evidence; "
            "2=clearly useful/relevant evidence; "
            "1=related/adjacent but insufficient; "
            "0=off-scope/not useful. "
            "Return JSON only. "
            "The top-level object must contain exactly "
            "one key named 'grades'. "
            "The grades object must contain every "
            "requested candidate ID exactly once and "
            "no other candidate IDs. "
            "Every grade must be an integer in "
            "{0,1,2,3}."
        )

        base_user_prompt = (
            f"Topic ID: {topic.topic_id}\n"
            f"Information need: "
            f"{information_need or topic_description(topic)}\n"
            f"Judge view: {view}\n"
            f"Candidate count: {len(expected_ids)}\n"
            f"Required candidate IDs: "
            f"{expected_text}\n"
            f'Required shape: '
            f'{{"grades": {{{example_grades}}}}}\n\n'
            + "\n\n---\n\n".join(
                blocks
            )
        )

        validated: dict[str, int] | None = None

        last_error: Exception | None = None

        for attempt in range(schema_retries + 1):
            user_prompt = base_user_prompt
            if attempt:
                user_prompt += (
                    "\n\nIMPORTANT: "
                    "The previous response failed "
                    "schema validation. "
                    "Return ALL and ONLY these "
                    "candidate grade keys: "
                    f"{expected_text}. "
                    "Do not omit any candidate. "
                    "Do not include explanation."
                )

            try:
                payload = client.json_call(system=system_prompt, user=user_prompt, retries=0)

                if set(payload) != {
                    "grades"
                }:
                    raise ValueError(
                        "Judge response must contain "
                        "exactly one top-level key "
                        "'grades'; got "
                        f"{sorted(payload)}"
                    )

                raw = payload["grades"]

                if not isinstance(raw, dict):
                    raise ValueError("'grades' must be a JSON object")

                returned_ids = set(raw)
                missing = sorted(expected_set - returned_ids)
                extra = sorted(returned_ids - expected_set)

                if missing or extra:
                    raise ValueError(
                        "Judge candidate-ID mismatch; "
                        f"missing={missing}, "
                        f"extra={extra}"
                    )

                current: dict[str, int] = {}
                for cid in expected_ids:
                    value = raw[cid]

                    if isinstance(value, bool):
                        raise ValueError(f"Boolean is not a valid relevance grade for {cid}")

                    try:
                        grade = int(value)

                    except (TypeError, ValueError) as exc:
                        raise ValueError(f"Non-integer relevance grade {value!r} for {cid}") from exc

                    if isinstance(value, float) and not value.is_integer():
                        raise ValueError(f"Non-integral relevance grade {value!r} for {cid}")

                    if isinstance(value, str) and value.strip() != str(grade):
                        raise ValueError(f"Malformed relevance grade {value!r} for {cid}")

                    if grade not in (0, 1, 2, 3):
                        raise ValueError(f"Invalid relevance grade {grade} for {cid}")

                    current[cid] = grade
                validated = current
                break

            except Exception as exc:
                last_error = exc

        if validated is None:
            raise RuntimeError(
                "Judge batch failed strict schema "
                "validation after retries. "
                f"topic={topic.topic_id!r}, "
                f"view={view!r}, "
                f"batch_index={batch_index}, "
                f"candidate_ids="
                f"{list(expected_ids)!r}, "
                f"error={last_error}"
            ) from last_error

        return (view_index, id_to_key, validated)

    tasks = []
    for (view_index, view) in enumerate(JUDGE_VIEWS):
        for (batch_index, start) in enumerate(range(0, len(candidates), batch_size)):
            batch = candidates[start: start + batch_size]

            tasks.append(partial(run_batch, view_index, view, batch_index, batch))

    batch_results = run_refill_window(tasks, config=config, label=(f"judge:{topic.topic_id}"))
    for (view_index, id_to_key, validated) in batch_results:
        for (cid, key) in id_to_key.items():
            grades_by_key[key][view_index] = validated[cid]

    output: list[RelevanceJudgment] = []
    by_candidate = {
        candidate.job_key: candidate
        for candidate in candidates
    }

    for (key, raw_grades) in grades_by_key.items():
        if any(grade is None for grade in raw_grades):
            raise RuntimeError(f"Missing judge view grade for {key}: {raw_grades}")

        grades = [
            int(grade)
            for grade in raw_grades
            if grade is not None
        ]

        if len(grades)  != len(JUDGE_VIEWS):
            raise RuntimeError(f"Expected {len(JUDGE_VIEWS)} judge grades for {key}; got {grades}")

        final_grade = int(median(grades))
        uncertain = (max(grades) - min(grades) >= 2)
        candidate = by_candidate[key]
        output.append(
            RelevanceJudgment(
                topic_id=topic.topic_id,
                source=candidate.source,
                source_job_id=candidate.source_job_id,
                grade=final_grade,
                judge_grades=(grades[0], grades[1], grades[2]),
                uncertain=uncertain,
            )
        )

    return output

def build_and_judge_controls(
    client: JudgeClient,
    topics: Iterable[CareerTopic],
    corpus_jobs: list[CorpusJob],
    queries_by_topic: dict[str, list] | None = None,
) -> list[ControlResult]:
    jobs_by_category: dict[str, list[CorpusJob]] = {}
    for job in corpus_jobs:
        if job.category_key:
            jobs_by_category.setdefault(job.category_key, []).append(job)
    sorted_jobs = sorted(corpus_jobs, key=lambda job: job.job_key)
    results: list[ControlResult] = []
    queries_by_topic = queries_by_topic or {}

    for topic in topics:
        positives = jobs_by_category.get(topic.category_key, [])
        if topic.scope == "specific" and topic.title_key:
            exact = [
                job
                for job in positives
                if (normalize_key(job.job_title)== topic.title_key)
            ]
            positive = (exact or positives)[0] if positives else None
        else:
            positive = positives[0] if positives else None

        topic_tokens = set(re.findall(r"\w+", topic.label.casefold(), flags=re.UNICODE))
        negative = next(
            (
                job for job in sorted_jobs
                if job.category_key
                and job.category_key != topic.category_key
                and not topic_tokens.intersection(re.findall(r"\w+", job.job_title.casefold(), flags=re.UNICODE))
            ),
            None,
        )

        if positive is not None:
            positive_candidate = PooledCandidate(
                topic_id=topic.topic_id,
                source=positive.source,
                source_job_id=positive.source_job_id,
                job_title=positive.job_title,
                category_key=positive.category_key,
                location_key=positive.location_key,
            )
            judged = judge_candidates(client, topic, [positive_candidate], {positive.job_key: positive})[0]
            results.append(
                ControlResult(
                    control_id=f"{topic.topic_id}:positive",
                    control_type="positive",
                    topic_id=topic.topic_id,
                    job_key=positive.job_key,
                    expected=">=2",
                    grade=judged.grade,
                    judge_grades=judged.judge_grades,
                    passed=judged.grade >= 2,
                )
            )

            reversed_job = CorpusJob(
                source=positive.source,
                source_job_id=positive.source_job_id,
                job_title=positive.job_title,
                category_key=positive.category_key,
                location_key=positive.location_key,
                experience_level=positive.experience_level,
                employment_type=positive.employment_type,
                chunks=tuple(reversed(positive.chunks)),
            )
            reversed_judged = judge_candidates(
                client,
                topic,
                [positive_candidate],
                {positive.job_key: reversed_job},
            )[0]
            order_passed = abs(judged.grade - reversed_judged.grade) <= 1
            results.append(
                ControlResult(
                    control_id=f"{topic.topic_id}:order",
                    control_type="order_invariance",
                    topic_id=topic.topic_id,
                    job_key=positive.job_key,
                    expected="abs(delta)<=1",
                    grade=reversed_judged.grade,
                    judge_grades=reversed_judged.judge_grades,
                    passed=order_passed,
                )
            )

            query_rows = queries_by_topic.get(topic.topic_id, [])
            direct = next((q for q in query_rows if getattr(q, "variant", "") == "direct"), None)
            noisy = next((q for q in query_rows if getattr(q, "variant", "") == "noisy"), None)
            if direct is not None and noisy is not None:
                direct_j = judge_candidates(
                    client,
                    topic,
                    [positive_candidate],
                    {positive.job_key: positive},
                    information_need=direct.text,
                )[0]
                noisy_j = judge_candidates(
                    client,
                    topic,
                    [positive_candidate],
                    {positive.job_key: positive},
                    information_need=noisy.text,
                )[0]
                results.append(
                    ControlResult(
                        control_id=f"{topic.topic_id}:paraphrase",
                        control_type="paraphrase_consistency",
                        topic_id=topic.topic_id,
                        job_key=positive.job_key,
                        expected="abs(delta)<=1",
                        grade=noisy_j.grade,
                        judge_grades=noisy_j.judge_grades,
                        passed=abs(direct_j.grade - noisy_j.grade) <= 1,
                    )
                )

        if negative is not None:
            negative_candidate = PooledCandidate(
                topic_id=topic.topic_id,
                source=negative.source,
                source_job_id=negative.source_job_id,
                job_title=negative.job_title,
                category_key=negative.category_key,
                location_key=negative.location_key,
            )
            judged = judge_candidates(client, topic, [negative_candidate], {negative.job_key: negative})[0]
            results.append(
                ControlResult(
                    control_id=f"{topic.topic_id}:negative",
                    control_type="negative",
                    topic_id=topic.topic_id,
                    job_key=negative.job_key,
                    expected="<=1",
                    grade=judged.grade,
                    judge_grades=judged.judge_grades,
                    passed=judged.grade <= 1,
                )
            )
    return results
