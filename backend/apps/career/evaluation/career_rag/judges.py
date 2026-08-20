from __future__ import annotations

import json
import re
from dataclasses import dataclass
from statistics import median
from typing import Iterable

from django.conf import settings
from openai import OpenAI

from .schema import CareerTopic, CorpusJob, PooledCandidate, RelevanceJudgment

JUDGE_PROMPT_VERSION = "career-rag-silver-qrels-v1"
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
    def __init__(self, model_name: str, client: OpenAI | None = None) -> None:
        self.model_name = model_name
        self.client = client or self._make_client()

    @staticmethod
    def _make_client() -> OpenAI:
        api_key = getattr(settings, "CKEY_API_KEY", "")
        base_url = getattr(settings, "CKEY_BASE_URL", "")
        if not api_key:
            raise RuntimeError("CKEY_API_KEY is required to build silver qrels/nuggets.")
        return OpenAI(api_key=api_key, base_url=base_url or None)

    def json_call(self, system: str, user: str, *, retries: int = 2) -> dict:
        last_error: Exception | None = None
        for _ in range(retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    temperature=0,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                )
                content = response.choices[0].message.content or ""
                return self._parse_json(content)
            except Exception as exc:  # noqa: BLE001 - surface provider errors after retries
                last_error = exc
        raise RuntimeError(f"Judge call failed after retries: {last_error}") from last_error

    @staticmethod
    def _parse_json(text: str) -> dict:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?\s*|\s*```$", "", stripped, flags=re.IGNORECASE | re.DOTALL)
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


def _topic_description(topic: CareerTopic) -> str:
    if topic.scope == "specific":
        return f"specific occupation/specialization: {topic.label}"
    return f"broad career field/domain: {topic.label}"


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
) -> list[RelevanceJudgment]:
    """
    Judge pooled candidates with strict schema validation.

    Important invariant:
    no relevance grade is committed until EVERY candidate
    in the current batch has a valid grade.

    If the LLM omits C7, invents C9, returns malformed
    grades, etc., retry only that batch instead of silently
    assigning a fallback grade.
    """

    if batch_size <= 0:
        raise ValueError(
            "batch_size must be positive"
        )

    if schema_retries < 0:
        raise ValueError(
            "schema_retries must be >= 0"
        )

    grades_by_key: dict[
        str,
        list[int],
    ] = {
        candidate.job_key: []
        for candidate in candidates
    }

    for view in JUDGE_VIEWS:
        for start in range(
            0,
            len(candidates),
            batch_size,
        ):
            batch = candidates[
                start : start + batch_size
            ]

            blocks: list[str] = []

            id_to_key: dict[
                str,
                str,
            ] = {}

            for index, candidate in enumerate(
                batch,
                start=1,
            ):
                cid = f"C{index}"

                id_to_key[
                    cid
                ] = candidate.job_key

                job = corpus_by_key[
                    candidate.job_key
                ]

                blocks.append(
                    f"{cid}\n"
                    f"{job.raw_evidence[:evidence_chars]}"
                )

            expected_ids = tuple(
                id_to_key
            )

            expected_set = set(
                expected_ids
            )

            expected_text = ", ".join(
                expected_ids
            )

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
                f"{information_need or _topic_description(topic)}\n"
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

            validated: (
                dict[str, int]
                | None
            ) = None

            last_error: (
                Exception
                | None
            ) = None

            # -----------------------------------------
            # Semantic/schema retry.
            #
            # JudgeClient.json_call gets retries=0
            # here so we do not accidentally multiply
            # nested retry counts.
            # -----------------------------------------

            for attempt in range(
                schema_retries + 1
            ):
                user_prompt = (
                    base_user_prompt
                )

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
                    payload = client.json_call(
                        system=system_prompt,
                        user=user_prompt,
                        retries=0,
                    )

                    if set(payload) != {
                        "grades"
                    }:
                        raise ValueError(
                            "Judge response must contain "
                            "exactly one top-level key "
                            "'grades'; got "
                            f"{sorted(payload)}"
                        )

                    raw = payload[
                        "grades"
                    ]

                    if not isinstance(
                        raw,
                        dict,
                    ):
                        raise ValueError(
                            "'grades' must be "
                            "a JSON object"
                        )

                    returned_ids = set(
                        raw
                    )

                    missing = sorted(
                        expected_set
                        - returned_ids
                    )

                    extra = sorted(
                        returned_ids
                        - expected_set
                    )

                    if missing or extra:
                        raise ValueError(
                            "Judge candidate-ID mismatch; "
                            f"missing={missing}, "
                            f"extra={extra}"
                        )

                    current: dict[
                        str,
                        int,
                    ] = {}

                    for cid in expected_ids:
                        value = raw[cid]

                        if isinstance(
                            value,
                            bool,
                        ):
                            raise ValueError(
                                "Boolean is not a valid "
                                "relevance grade for "
                                f"{cid}"
                            )

                        try:
                            grade = int(
                                value
                            )
                        except (
                            TypeError,
                            ValueError,
                        ) as exc:
                            raise ValueError(
                                "Non-integer relevance "
                                f"grade {value!r} "
                                f"for {cid}"
                            ) from exc

                        if (
                            isinstance(
                                value,
                                float,
                            )
                            and not value.is_integer()
                        ):
                            raise ValueError(
                                "Non-integral relevance "
                                f"grade {value!r} "
                                f"for {cid}"
                            )

                        if (
                            isinstance(
                                value,
                                str,
                            )
                            and value.strip()
                            != str(grade)
                        ):
                            raise ValueError(
                                "Malformed relevance "
                                f"grade {value!r} "
                                f"for {cid}"
                            )

                        if grade not in (
                            0,
                            1,
                            2,
                            3,
                        ):
                            raise ValueError(
                                "Invalid relevance grade "
                                f"{grade} for {cid}"
                            )

                        current[
                            cid
                        ] = grade

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
                    f"candidate_ids="
                    f"{list(expected_ids)!r}, "
                    f"error={last_error}"
                ) from last_error

            # -----------------------------------------
            # Atomic batch commit.
            #
            # Nothing was appended before every C-ID
            # passed validation.
            # -----------------------------------------

            for cid, key in (
                id_to_key.items()
            ):
                grades_by_key[
                    key
                ].append(
                    validated[cid]
                )

    output: list[
        RelevanceJudgment
    ] = []

    by_candidate = {
        candidate.job_key: (
            candidate
        )
        for candidate in candidates
    }

    for (
        key,
        grades,
    ) in grades_by_key.items():

        if (
            len(grades)
            != len(JUDGE_VIEWS)
        ):
            raise RuntimeError(
                "Expected "
                f"{len(JUDGE_VIEWS)} "
                "judge grades for "
                f"{key}; got {grades}"
            )

        final_grade = int(
            median(grades)
        )

        uncertain = (
            max(grades)
            - min(grades)
            >= 2
        )

        candidate = (
            by_candidate[key]
        )

        output.append(
            RelevanceJudgment(
                topic_id=(
                    topic.topic_id
                ),
                source=(
                    candidate.source
                ),
                source_job_id=(
                    candidate.source_job_id
                ),
                grade=(
                    final_grade
                ),
                judge_grades=(
                    grades[0],
                    grades[1],
                    grades[2],
                ),
                uncertain=(
                    uncertain
                ),
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
            exact = [job for job in positives if job.job_title.casefold().strip() == topic.label.casefold().strip()]
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
