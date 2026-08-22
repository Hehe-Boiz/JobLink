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
from .semantics import canonical_information_need
from .evidence import pack_job_evidence

NUGGET_PROMPT_VERSION = "career-rag-silver-nuggets-v4"
NUGGET_IMPORTANCE_POLICY_VERSION = "career-rag-nugget-importance-v1"
NUGGET_WEIGHT_POLICY = {"VITAL": 1.0, "OKAY": 0.5}
PREVALENCE_UNAVAILABLE = -1.0
PREVALENCE_POLICY_VERSION = "career-rag-nugget-prevalence-adaptive-v1"
NUGGET_SUPPORT_SEMANTICS_VERSION = "career-rag-nugget-support-observed-before-adaptive-stop-v1"
DEFAULT_NUGGET_BATCH_SIZE = 8
DEFAULT_SUPPORT_JOB_BATCH_SIZE = 8
DEFAULT_IMPORTANCE_BATCH_SIZE = 8
IMPORTANCE_EVIDENCE_PREVIEW_JOBS = 3
IMPORTANCE_VALUES = frozenset({"VITAL", "OKAY"})


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
                f"{pack_job_evidence(job, char_budget=evidence_chars)}"
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
                f"{canonical_information_need(topic)}\n\n"
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
        f"{job_id}\n{pack_job_evidence(job, char_budget=evidence_chars)}"
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
                f"\n\nSCHEMA_RETRY_ATTEMPT={attempt}\n"
                "IMPORTANT CORRECTION: The previous response failed strict "
                "schema validation. Return JSON only with exactly one top-level "
                "key named 'support'. The support object must contain all and "
                f"only these nugget IDs: {expected_nuggets}. Every nugget row "
                "must contain all and only these job IDs: "
                f"{expected_jobs}. Every cell value must be a literal JSON "
                "true or false, never a string, number, or null. Do not omit "
                "or add any row or cell."
            )

        data = client.json_call(
            system=system_prompt,
            user=user_prompt,
            retries=0,
        )

        try:
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


def _validate_importance(
    data: object,
    *,
    nugget_ids: tuple[str, ...],
) -> dict[str, str]:
    if not isinstance(data, dict) or set(data) != {"importance"}:
        raise ValueError("Nugget importance judge returned invalid top-level JSON")

    raw_importance = data["importance"]
    if not isinstance(raw_importance, dict) or set(raw_importance) != set(nugget_ids):
        raise ValueError(
            "Nugget importance judge returned an incomplete or unexpected nugget mapping"
        )

    importance: dict[str, str] = {}
    for nugget_id in nugget_ids:
        value = raw_importance[nugget_id]
        if type(value) is not str or value not in IMPORTANCE_VALUES:
            raise ValueError(
                f"Nugget importance value for {nugget_id} must be exactly "
                "'VITAL' or 'OKAY'"
            )
        importance[nugget_id] = value
    return importance


def _importance_evidence(
    item: dict,
    corpus_by_key: dict[str, CorpusJob],
    *,
    evidence_chars: int,
    max_evidence_jobs: int = IMPORTANCE_EVIDENCE_PREVIEW_JOBS,
) -> str:
    if max_evidence_jobs <= 0:
        raise ValueError("max_evidence_jobs must be positive")

    # Importance is need-conditioned. The judge receives only a fixed preview
    # of grounded evidence; it must not see support keys, support counts, or an
    # omitted-evidence count that could act as a prevalence signal.
    evidence_keys = tuple(
        sorted(set(item.get("importance_evidence_keys", item.get("support_job_keys", ()))))
    )[:max_evidence_jobs]
    lines: list[str] = []
    for index, job_key in enumerate(evidence_keys, start=1):
        job = corpus_by_key.get(job_key)
        if job is None:
            continue
        lines.append(
            f"SUPPORTING_EVIDENCE_{index}\n"
            f"{pack_job_evidence(job, char_budget=evidence_chars)}"
        )
    if not lines:
        return "SUPPORTING_EVIDENCE_PREVIEW\n(no evidence preview available)"
    return "\n\n".join(lines)


def _judge_importance_batch(
    client: JudgeClient,
    topic: CareerTopic,
    items: list[dict],
    corpus_by_key: dict[str, CorpusJob],
    *,
    evidence_chars: int,
    schema_retries: int = 2,
) -> list[str]:
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")

    nugget_ids = tuple(f"N{index}" for index in range(1, len(items) + 1))
    blocks = [
        (
            f"{nugget_id}\n"
            f"Nugget text: {item['text']}\n"
            f"{_importance_evidence(item, corpus_by_key, evidence_chars=evidence_chars)}"
        )
        for nugget_id, item in zip(nugget_ids, items, strict=True)
    ]
    system_prompt = (
        "Judge the importance of each atomic nugget for the supplied canonical "
        "career information need. VITAL means essential or highly necessary for "
        "a good answer to that need. OKAY means useful but non-essential. Do not "
        "infer importance from how frequently information appears across documents. Use only the "
        "nugget text and grounded supporting evidence. Return JSON only as "
        '{"importance":{"N1":"VITAL"}}. Use exactly the supplied nugget IDs, '
        "with one value per ID and no other IDs. Values must be exactly VITAL or OKAY."
    )
    base_user_prompt = (
        f"Canonical information need: {canonical_information_need(topic)}\n\n"
        "Candidate nuggets and verified supporting evidence:\n\n"
        + "\n\n---\n\n".join(blocks)
    )
    expected_text = ", ".join(nugget_ids)
    validated: dict[str, str] | None = None
    last_error: Exception | None = None

    for attempt in range(schema_retries + 1):
        user_prompt = base_user_prompt
        if attempt:
            user_prompt += (
                f"\n\nSCHEMA_RETRY_ATTEMPT={attempt}\n"
                "IMPORTANT CORRECTION: The previous response failed strict schema "
                "validation. Return JSON only with exactly one top-level key named "
                "'importance'. The importance object must contain all and only "
                f"these nugget IDs: {expected_text}. Every value must be exactly "
                "the JSON string \"VITAL\" or \"OKAY\"; do not omit, add, or "
                "rename any ID."
            )
        payload = client.json_call(
            system=system_prompt,
            user=user_prompt,
            retries=0,
        )

        try:
            validated = _validate_importance(payload, nugget_ids=nugget_ids)
            break
        except Exception as exc:
            last_error = exc

    if validated is None:
        raise RuntimeError(
            "Nugget importance judge failed strict schema validation after "
            f"{schema_retries} retries; nugget_ids={list(nugget_ids)!r}; "
            f"error={last_error}"
        ) from last_error

    return [validated[nugget_id] for nugget_id in nugget_ids]


def _judge_importance(
    client: JudgeClient,
    topic: CareerTopic,
    items: list[dict],
    corpus_by_key: dict[str, CorpusJob],
    *,
    batch_size: int = DEFAULT_IMPORTANCE_BATCH_SIZE,
    evidence_chars: int = 5000,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[str]:
    if batch_size <= 0:
        raise ValueError("importance batch_size must be positive")
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")
    if not items:
        return []

    specifications = [
        (start, items[start : start + batch_size])
        for start in range(0, len(items), batch_size)
    ]
    results = run_refill_window(
        [
            partial(
                _judge_importance_batch,
                client,
                topic,
                batch,
                corpus_by_key,
                evidence_chars=evidence_chars,
                schema_retries=schema_retries,
            )
            for _, batch in specifications
        ],
        config=RefillWindowConfig(
            max_in_flight=max_in_flight,
            refill_size=refill_size,
        ),
        label=f"nugget-importance:{topic.topic_id}",
    )
    importance: list[str | None] = [None] * len(items)
    for (start, batch), batch_result in zip(specifications, results, strict=True):
        if len(batch_result) != len(batch):
            raise RuntimeError("Nugget importance judge returned an unexpected result shape")
        importance[start : start + len(batch)] = batch_result
    if any(value is None for value in importance):
        raise RuntimeError("Nugget importance reconstruction left an unassigned nugget")
    return [value for value in importance if value is not None]


def _verify_support_group_adaptive(
    client: JudgeClient,
    indexed_candidates: list[tuple[int, dict]],
    strong_jobs: list[CorpusJob],
    *,
    min_support_jobs: int,
    job_batch_size: int,
    evidence_chars: int,
    schema_retries: int,
) -> dict[int, list[str]]:
    """Verify a deterministic hint-equivalence group with matrix requests.

    Extractor support keys only determine which strong jobs are checked first;
    they never establish support and never remove jobs from the verification
    universe. Candidates leave the active matrix as soon as their verified
    support reaches the threshold.
    """

    if not indexed_candidates:
        return {}

    candidate_by_index = dict(indexed_candidates)
    hinted_key_set = set(indexed_candidates[0][1].get("support_job_keys", ()))
    ordered_jobs = [
        job
        for job in strong_jobs
        if job.job_key in hinted_key_set
    ] + [
        job
        for job in strong_jobs
        if job.job_key not in hinted_key_set
    ]

    verified: dict[int, set[str]] = {
        index: set()
        for index, _ in indexed_candidates
    }
    active = list(indexed_candidates)
    for start in range(0, len(ordered_jobs), job_batch_size):
        if not active:
            break
        job_batch = ordered_jobs[start : start + job_batch_size]
        batch_result = _verify_support_matrix_batch(
            client,
            [candidate for _, candidate in active],
            job_batch,
            evidence_chars=evidence_chars,
            schema_retries=schema_retries,
        )
        if len(batch_result) != len(active):
            raise RuntimeError("Adaptive nugget verifier returned an unexpected result shape")
        remaining: list[tuple[int, dict]] = []
        for (index, _), support_keys in zip(active, batch_result, strict=True):
            # A matrix request may contain jobs beyond this candidate's logical
            # adaptive stopping point.  Consume cells in the deterministic job
            # order and ignore later positives once the threshold is reached,
            # so transport batch size cannot change stored support semantics.
            supported_in_batch = set(support_keys)
            for job in job_batch:
                if (
                    len(verified[index]) < min_support_jobs
                    and job.job_key in supported_in_batch
                ):
                    verified[index].add(job.job_key)
            if len(verified[index]) < min_support_jobs:
                remaining.append((index, candidate_by_index[index]))
        active = remaining

    return {index: sorted(keys) for index, keys in verified.items()}


def _verify_support_adaptive(
    client: JudgeClient,
    candidates: list[dict],
    strong_jobs: list[CorpusJob],
    *,
    min_support_jobs: int,
    nugget_batch_size: int = DEFAULT_NUGGET_BATCH_SIZE,
    job_batch_size: int = DEFAULT_SUPPORT_JOB_BATCH_SIZE,
    evidence_chars: int = 5000,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[list[str]]:
    """Return only support keys established by adaptive verification."""

    if min_support_jobs <= 0:
        raise ValueError("min_support_jobs must be positive")
    if nugget_batch_size <= 0:
        raise ValueError("nugget_batch_size must be positive")
    if job_batch_size <= 0:
        raise ValueError("job_batch_size must be positive")
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")
    if not candidates:
        return []

    strong_by_key = {job.job_key for job in strong_jobs}
    groups: dict[tuple[str, ...], list[tuple[int, dict]]] = {}
    for index, candidate in enumerate(candidates):
        hinted = tuple(
            job.job_key
            for job in strong_jobs
            if job.job_key in {
                key
                for key in candidate.get("support_job_keys", ())
                if isinstance(key, str) and key in strong_by_key
            }
        )
        groups.setdefault(hinted, []).append((index, candidate))

    specifications: list[list[tuple[int, dict]]] = []
    for hinted in sorted(groups):
        members = groups[hinted]
        specifications.extend(
            members[start : start + nugget_batch_size]
            for start in range(0, len(members), nugget_batch_size)
        )

    results = run_refill_window(
        [
            partial(
                _verify_support_group_adaptive,
                client,
                specification,
                strong_jobs,
                min_support_jobs=min_support_jobs,
                job_batch_size=job_batch_size,
                evidence_chars=evidence_chars,
                schema_retries=schema_retries,
            )
            for specification in specifications
        ],
        config=RefillWindowConfig(
            max_in_flight=max_in_flight,
            refill_size=refill_size,
        ),
        label="nugget-support-adaptive",
    )
    if len(results) != len(specifications):
        raise RuntimeError("Adaptive nugget verifier returned an unexpected group count")
    verified_by_index: list[list[str] | None] = [None] * len(candidates)
    for group_result in results:
        for index, support_keys in group_result.items():
            verified_by_index[index] = support_keys
    if any(value is None for value in verified_by_index):
        raise RuntimeError("Adaptive nugget verifier left an unassigned candidate")
    return [value for value in verified_by_index if value is not None]


def build_nuggets_for_topic(
    client: JudgeClient,
    topic: CareerTopic,
    qrels: list[RelevanceJudgment],
    corpus_by_key: dict[str, CorpusJob],
    *,
    min_support_jobs: int = 2,
    nugget_batch_size: int = DEFAULT_NUGGET_BATCH_SIZE,
    job_batch_size: int = DEFAULT_SUPPORT_JOB_BATCH_SIZE,
    importance_batch_size: int = DEFAULT_IMPORTANCE_BATCH_SIZE,
    importance_evidence_chars: int = 5000,
    schema_retries: int = 2,
    max_in_flight: int = DEFAULT_MAX_IN_FLIGHT,
    refill_size: int = DEFAULT_REFILL_SIZE,
) -> list[Nugget]:
    if min_support_jobs <= 0:
        raise ValueError("min_support_jobs must be positive")
    if nugget_batch_size <= 0:
        raise ValueError("nugget_batch_size must be positive")
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

    # Extractor support_job_keys are hints only. Verify hinted strong jobs
    # first, then deterministic remaining strong jobs until the grounding
    # threshold is met or the strong-job universe is exhausted.
    verification_results = _verify_support_adaptive(
        client,
        extracted,
        strong_jobs,
        min_support_jobs=min_support_jobs,
        nugget_batch_size=nugget_batch_size,
        job_batch_size=job_batch_size,
        schema_retries=schema_retries,
        max_in_flight=max_in_flight,
        refill_size=refill_size,
    )

    strong_job_key_set = {job.job_key for job in strong_jobs}
    surviving_items: list[dict] = []
    for item, verified_keys in zip(extracted, verification_results, strict=True):
        unique_verified_keys = tuple(sorted(set(verified_keys)))
        if not set(unique_verified_keys).issubset(strong_job_key_set):
            raise ValueError("Nugget verifier returned a job outside the strong-job universe")

        support_count = len(unique_verified_keys)
        if support_count < min_support_jobs:
            continue

        surviving_items.append(
            {
                "text": item["text"],
                "support_job_keys": unique_verified_keys,
                "importance_evidence_keys": unique_verified_keys[:3],
            }
        )

    importance_values = _judge_importance(
        client,
        topic,
        surviving_items,
        corpus_by_key,
        batch_size=importance_batch_size,
        evidence_chars=importance_evidence_chars,
        schema_retries=schema_retries,
        max_in_flight=max_in_flight,
        refill_size=refill_size,
    )

    nuggets: list[Nugget] = []
    for item, importance in zip(surviving_items, importance_values, strict=True):
        verified_keys = tuple(item["support_job_keys"])
        support_count = len(verified_keys)

        # Adaptive verification intentionally does not compute prevalence.
        # Keeping the sentinel constant makes nugget objects invariant to job
        # batch boundaries and prevents partial checks from looking exact.
        prevalence = PREVALENCE_UNAVAILABLE
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
                # Adaptive verification deliberately does not report exact
                # prevalence. This field is a documented unavailable sentinel
                # and never controls importance/weight.
                weight=NUGGET_WEIGHT_POLICY[importance],
                importance=importance,
            )
        )

    return sorted(
        nuggets,
        key=lambda nugget: (
            -nugget.weight,
            nugget.normalized_text,
        ),
    )
