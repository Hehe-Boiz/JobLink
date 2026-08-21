from __future__ import annotations

import hashlib
import re
from functools import partial

from .concurrency import (
    DEFAULT_MAX_IN_FLIGHT,
    DEFAULT_REFILL_SIZE,
    RefillWindowConfig,
    run_refill_window,
)
from .judges import JudgeClient
from .schema import CareerTopic, CorpusJob, Nugget, RelevanceJudgment
from .semantics import topic_description

NUGGET_PROMPT_VERSION = "career-rag-silver-nuggets-v3"
DEFAULT_VITAL_PREVALENCE = 0.35
DEFAULT_NUGGET_BATCH_SIZE = 8
DEFAULT_SUPPORT_JOB_BATCH_SIZE = 8


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold()).strip(" .,:;-/")


def _token_set(text: str) -> set[str]:
    return set(re.findall(r"\w+", _normalize(text), flags=re.UNICODE))


def _dedup_candidates(items: list[dict]) -> list[dict]:
    kept: list[dict] = []
    for item in items:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        tokens = _token_set(text)
        if not tokens:
            continue
        duplicate = False
        for previous in kept:
            other = _token_set(previous["text"])
            union = tokens | other
            score = len(tokens & other) / len(union) if union else 1.0
            if _normalize(text) == _normalize(previous["text"]) or score >= 0.85:
                previous_ids = set(previous.get("support_job_keys", []))
                previous["support_job_keys"] = sorted(previous_ids | set(item.get("support_job_keys", [])))
                duplicate = True
                break
        if not duplicate:
            kept.append({"text": text, "support_job_keys": sorted(set(item.get("support_job_keys", [])))})
    return kept


def _extract_candidates(
    client: JudgeClient,
    topic: CareerTopic,
    strong_jobs: list[CorpusJob],
    *,
    batch_jobs: int = 10,
    evidence_chars: int = 5000,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[dict]:
    config = RefillWindowConfig(
        max_in_flight=max_in_flight,
        refill_size=refill_size,
    )

    batches = [
        strong_jobs[start: start + batch_jobs]
        for start in range(0, len(strong_jobs), batch_jobs)
    ]

    def extract_batch(batch: list[CorpusJob]) -> list[dict]:
        blocks = [
            (
                f"JOB_KEY={job.job_key}\n"
                f"{job.raw_evidence[:evidence_chars]}"
            )
            for job in batch
        ]

        data = client.json_call(
            system=(
                "Extract atomic career-information "
                "nuggets from raw job descriptions. "
                "A nugget must be a concise skill, "
                "technology, qualification, "
                "responsibility, or capability that "
                "directly helps answer the topic. "
                "Do not invent anything. "
                "Return only nuggets clearly supported "
                "by the supplied raw evidence, and "
                "include the JOB_KEY values that "
                "support each nugget. "
                "Prefer reusable canonical phrases, "
                "not full sentences. Return JSON only: "
                '{"nuggets":[{"text":"...",'
                '"support_job_keys":["source::id"]}]}.'
            ),
            user=(
                f"Information need: "
                f"{topic_description(topic)}\n\n"
                + "\n\n---\n\n".join(
                    blocks
                )
            ),
        )

        raw = data.get("nuggets", [])

        if not isinstance(raw, list,):
            raise ValueError("Nugget extractor returned non-list nuggets")

        return [
            item
            for item in raw
            if isinstance(item, dict)
        ]

    groups = run_refill_window(
        [
            partial(extract_batch, batch)
            for batch in batches
        ],
        config=config,
        label=f"nugget-extract:{topic.topic_id}",
    )

    items = [
        item
        for group in groups
        for item in group
    ]

    return _dedup_candidates(items)

def _verify_support(
    client: JudgeClient,
    nugget_text: str,
    jobs: list[CorpusJob],
    *,
    batch_size: int = 8,
    evidence_chars: int = 5000,
) -> list[str]:
    supported: list[str] = []
    for start in range(0, len(jobs), batch_size):
        batch = jobs[start : start + batch_size]
        mapping = {f"J{index}": job for index, job in enumerate(batch, start=1)}
        blocks = [f"{jid}\n{job.raw_evidence[:evidence_chars]}" for jid, job in mapping.items()]
        data = client.json_call(
            system=(
                "Verify whether each raw JD explicitly or clearly semantically supports the candidate career nugget. "
                "Be conservative. Return JSON only as {\"support\": {\"J1\": true, ...}}."
            ),
            user=f"Candidate nugget: {nugget_text}\n\n" + "\n\n---\n\n".join(blocks),
        )
        if not isinstance(data, dict) or set(data) != {"support"}:
            raise ValueError("Nugget verifier returned invalid top-level JSON")

        raw = data["support"]
        if not isinstance(raw, dict) or set(raw) != set(mapping):
            raise ValueError(
                "Nugget verifier returned an incomplete or unexpected support mapping"
            )

        for jid, job in mapping.items():
            value = raw[jid]
            if type(value) is not bool:
                raise ValueError(
                    f"Nugget verifier support value for {jid} must be a JSON boolean"
                )
            if value:
                supported.append(job.job_key)
    return supported


def _validate_support_matrix(
    data: object,
    *,
    nugget_ids: tuple[str, ...],
    job_ids: tuple[str, ...],
) -> dict[str, dict[str, bool]]:
    if not isinstance(data, dict) or set(data) != {"support"}:
        raise ValueError("Nugget matrix verifier returned invalid top-level JSON")

    raw_support = data["support"]
    if not isinstance(raw_support, dict) or set(raw_support) != set(nugget_ids):
        raise ValueError(
            "Nugget matrix verifier returned an incomplete or unexpected nugget mapping"
        )

    matrix: dict[str, dict[str, bool]] = {}
    for nugget_id in nugget_ids:
        raw_row = raw_support[nugget_id]
        if not isinstance(raw_row, dict) or set(raw_row) != set(job_ids):
            raise ValueError(
                f"Nugget matrix verifier returned an incomplete or unexpected row for {nugget_id}"
            )

        row: dict[str, bool] = {}
        for job_id in job_ids:
            value = raw_row[job_id]
            if type(value) is not bool:
                raise ValueError(
                    f"Nugget matrix verifier support value for {nugget_id}/{job_id} "
                    "must be a JSON boolean"
                )
            row[job_id] = value
        matrix[nugget_id] = row

    return matrix


def _verify_support_matrix_batch(
    client: JudgeClient,
    candidates: list[dict],
    jobs: list[CorpusJob],
    *,
    evidence_chars: int,
    schema_retries: int = 2,
) -> list[list[str]]:
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")

    nugget_ids = tuple(f"N{index}" for index in range(1, len(candidates) + 1))
    job_ids = tuple(f"J{index}" for index in range(1, len(jobs) + 1))
    candidate_blocks = [
        f"{nugget_id}\nCandidate nugget: {item['text']}"
        for nugget_id, item in zip(nugget_ids, candidates, strict=True)
    ]
    job_blocks = [
        f"{job_id}\n{job.raw_evidence[:evidence_chars]}"
        for job_id, job in zip(job_ids, jobs, strict=True)
    ]

    system_prompt = (
        "Verify whether each candidate career nugget is explicitly or clearly "
        "semantically supported by each supplied raw JD. Be conservative. "
        "Return JSON only as a complete support matrix: "
        '{"support":{"N1":{"J1":true,"J2":false}}}. '
        "Use exactly the supplied N IDs and exactly the supplied J IDs in every row. "
        "Every cell must be a JSON boolean; do not omit or add rows or cells."
    )
    base_user_prompt = (
        "Candidate nuggets and their local IDs:\n\n"
        + "\n\n---\n\n".join(candidate_blocks)
        + "\n\nJobs and their local IDs:\n\n"
        + "\n\n---\n\n".join(job_blocks)
    )
    expected_nuggets = ", ".join(nugget_ids)
    expected_jobs = ", ".join(job_ids)

    matrix: dict[str, dict[str, bool]] | None = None
    last_error: Exception | None = None
    for attempt in range(schema_retries + 1):
        user_prompt = base_user_prompt
        if attempt:
            user_prompt += (
                "\n\nIMPORTANT CORRECTION: The previous response failed strict "
                "schema validation. Return JSON only with exactly one top-level "
                "key named 'support'. The support object must contain all and "
                f"only these nugget IDs: {expected_nuggets}. Every nugget row "
                "must contain all and only these job IDs: "
                f"{expected_jobs}. Every cell value must be a literal JSON "
                "true or false, never a string, number, or null. Do not omit "
                "or add any row or cell."
            )

        try:
            data = client.json_call(
                system=system_prompt,
                user=user_prompt,
                retries=0,
            )
            matrix = _validate_support_matrix(
                data,
                nugget_ids=nugget_ids,
                job_ids=job_ids,
            )
            break
        except Exception as exc:
            last_error = exc

    if matrix is None:
        raise RuntimeError(
            "Nugget matrix verifier failed strict schema validation after "
            f"{schema_retries} retries; nugget_ids={list(nugget_ids)!r}; "
            f"job_ids={list(job_ids)!r}; error={last_error}"
        ) from last_error

    jobs_by_id = dict(zip(job_ids, jobs, strict=True))
    return [
        [
            jobs_by_id[job_id].job_key
            for job_id in job_ids
            if matrix[nugget_id][job_id]
        ]
        for nugget_id in nugget_ids
    ]


def _verify_support_matrix(
    client: JudgeClient,
    candidates: list[dict],
    jobs: list[CorpusJob],
    *,
    nugget_batch_size: int = DEFAULT_NUGGET_BATCH_SIZE,
    job_batch_size: int = DEFAULT_SUPPORT_JOB_BATCH_SIZE,
    evidence_chars: int = 5000,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[list[str]]:
    if nugget_batch_size <= 0:
        raise ValueError("nugget_batch_size must be positive")
    if job_batch_size <= 0:
        raise ValueError("job_batch_size must be positive")
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")

    verified: list[set[str]] = [set() for _ in candidates]
    if not candidates or not jobs:
        return [sorted(keys) for keys in verified]

    candidate_batches = [
        (start, candidates[start : start + nugget_batch_size])
        for start in range(0, len(candidates), nugget_batch_size)
    ]
    job_batches = [
        jobs[start : start + job_batch_size]
        for start in range(0, len(jobs), job_batch_size)
    ]
    specifications = [
        (candidate_start, candidate_batch, job_batch)
        for candidate_start, candidate_batch in candidate_batches
        for job_batch in job_batches
    ]
    results = run_refill_window(
        [
            partial(
                _verify_support_matrix_batch,
                client,
                candidate_batch,
                job_batch,
                evidence_chars=evidence_chars,
                schema_retries=schema_retries,
            )
            for _, candidate_batch, job_batch in specifications
        ],
        config=RefillWindowConfig(
            max_in_flight=max_in_flight,
            refill_size=refill_size,
        ),
        label="nugget-support-matrix",
    )

    for (candidate_start, candidate_batch, _), batch_results in zip(
        specifications,
        results,
        strict=True,
    ):
        if len(batch_results) != len(candidate_batch):
            raise RuntimeError("Nugget matrix verifier returned an unexpected result shape")
        for offset, support_keys in enumerate(batch_results):
            verified[candidate_start + offset].update(support_keys)

    return [sorted(keys) for keys in verified]


def build_nuggets_for_topic(
    client: JudgeClient,
    topic: CareerTopic,
    qrels: list[RelevanceJudgment],
    corpus_by_key: dict[str, CorpusJob],
    *,
    min_support_jobs: int = 2,
    vital_prevalence: float = DEFAULT_VITAL_PREVALENCE,
    nugget_batch_size: int = DEFAULT_NUGGET_BATCH_SIZE,
    job_batch_size: int = DEFAULT_SUPPORT_JOB_BATCH_SIZE,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[Nugget]:
    strong_keys = sorted(
        {
            qrel.job_key
            for qrel in qrels
            if not qrel.uncertain and qrel.grade >= 2
        }
    )

    strong_jobs = [
        corpus_by_key[key]
        for key in strong_keys
        if key in corpus_by_key
    ]

    if not strong_jobs:
        return []

    extracted = _extract_candidates(client, topic, strong_jobs, max_in_flight=max_in_flight, refill_size=refill_size)

    # Extractor support_job_keys are hints/provenance only.  Authoritative
    # prevalence is measured against every strong job for this topic.
    verified_keys_by_item = _verify_support_matrix(
        client,
        extracted,
        strong_jobs,
        nugget_batch_size=nugget_batch_size,
        job_batch_size=job_batch_size,
        schema_retries=schema_retries,
        max_in_flight=max_in_flight,
        refill_size=refill_size,
    )

    nuggets: list[Nugget] = []
    strong_job_key_set = {job.job_key for job in strong_jobs}
    for item, verified_keys in zip(extracted, verified_keys_by_item, strict=True):
        if not set(verified_keys).issubset(strong_job_key_set):
            raise ValueError("Nugget verifier returned a job outside the strong-job universe")

        support_count = len(set(verified_keys))
        if support_count < min_support_jobs:
            continue

        prevalence = support_count / len(strong_jobs)
        if not 0 <= prevalence <= 1:
            raise RuntimeError("Nugget prevalence must be between 0 and 1")
        normalized = _normalize(item["text"])
        nugget_id = (
            "nug-"
            + hashlib.sha256(
                (
                    f"{topic.topic_id}:"
                    f"{normalized}"
                ).encode(
                    "utf-8"
                )
            ).hexdigest()[:12]
        )

        nuggets.append(
            Nugget(
                topic_id=topic.topic_id,
                nugget_id=nugget_id,
                text=item["text"],
                normalized_text=normalized,
                support_job_keys=tuple(verified_keys),
                support_count=support_count,
                prevalence=prevalence,
                weight=prevalence,
                importance=(
                    "VITAL"
                    if prevalence
                    >= vital_prevalence
                    else "OKAY"
                ),
            )
        )

    return sorted(
        nuggets,
        key=lambda nugget: (
            -nugget.weight,
            nugget.normalized_text,
        ),
    )
