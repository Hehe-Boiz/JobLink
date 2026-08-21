from __future__ import annotations

import hashlib
import math
import re
from functools import partial
from collections import defaultdict

from .concurrency import (
    DEFAULT_MAX_IN_FLIGHT,
    DEFAULT_REFILL_SIZE,
    RefillWindowConfig,
    run_refill_window,
)
from .judges import JudgeClient
from .schema import CareerTopic, CorpusJob, Nugget, RelevanceJudgment
from .semantics import topic_description

NUGGET_PROMPT_VERSION = "career-rag-silver-nuggets-v2"
DEFAULT_VITAL_PREVALENCE = 0.35


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
        raw = data.get("support", {})
        for jid, job in mapping.items():
            if bool(raw.get(jid, False)):
                supported.append(job.job_key)
    return supported


def build_nuggets_for_topic(
    client: JudgeClient,
    topic: CareerTopic,
    qrels: list[RelevanceJudgment],
    corpus_by_key: dict[str, CorpusJob],
    *,
    min_support_jobs: int = 2,
    vital_prevalence: float = DEFAULT_VITAL_PREVALENCE,
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

    if len(strong_jobs)  < min_support_jobs:
        return []

    extracted = _extract_candidates(client, topic, strong_jobs, max_in_flight=max_in_flight, refill_size=refill_size)

    by_key = {
        job.job_key: job
        for job in strong_jobs
    }

    verification_inputs = []

    for item in extracted:
        claimed_keys = [
            key
            for key
            in item.get("support_job_keys", [])
            if key in by_key
        ]

        candidate_jobs = [
            by_key[key]
            for key in claimed_keys
        ]

        if len(candidate_jobs) < min_support_jobs:
            continue

        verification_inputs.append((item, candidate_jobs))

    config = RefillWindowConfig(max_in_flight=max_in_flight, refill_size=refill_size,)
    def verify_item(item: dict, candidate_jobs: list[CorpusJob]):
        verified_keys = sorted(set(_verify_support(client, item["text"], candidate_jobs)))

        return (item, verified_keys,)

    verified_results = (
        run_refill_window(
            [
                partial(verify_item, item, candidate_jobs,)
                for (item, candidate_jobs) in verification_inputs
            ],
            config=config,
            label=f"nugget-verify:{topic.topic_id}",
        )
    )

    nuggets: list[Nugget] = []
    for (item, verified_keys) in verified_results:
        if len(verified_keys) < min_support_jobs:
            continue

        prevalence = len(verified_keys) / len(strong_jobs)
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
                support_count=len(verified_keys),
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
