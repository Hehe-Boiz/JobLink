from __future__ import annotations

import hashlib
import json
import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from apps.career.models import CareerJobChunk

from .schema import CareerTopic, CorpusJob, Nugget, RelevanceJudgment

FORBIDDEN_DERIVED_KEYS = {"technical_skills", "soft_skills", "gold_nuggets", "judge_labels", "derived_role_labels"}
QUALIFICATION_SECTION_TERMS = (
    "required",
    "requirement",
    "qualification",
    "preferred",
    "nice to have",
    "must have",
    "yêu cầu",
    "bằng cấp",
    "ưu tiên",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_tree(paths: Iterable[Path]) -> str:
    resolved_paths = [Path(path).resolve() for path in paths]
    if not resolved_paths:
        return hashlib.sha256().hexdigest()

    # The logical root is the common parent directory.  Using the files
    # themselves makes a singleton tree's relative path become ".", which
    # loses the filename from the digest.
    try:
        root = Path(os.path.commonpath([str(path.parent) for path in resolved_paths]))
    except ValueError as exc:
        raise ValueError("sha256_tree paths must share a common root") from exc

    digest = hashlib.sha256()
    digest.update(b"career-rag-tree-v2\0")
    entries = sorted(
        ((path.relative_to(root).as_posix(), path) for path in resolved_paths),
        key=lambda item: item[0],
    )
    for relative_path, path in entries:
        path_bytes = relative_path.encode("utf-8")
        content_digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                content_digest.update(chunk)

        digest.update(len(path_bytes).to_bytes(8, "big"))
        digest.update(path_bytes)
        digest.update(content_digest.digest())
    return digest.hexdigest()


def _percentile(values: list[int], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def audit_evidence_truncation(
    jobs: Iterable[CorpusJob],
    *,
    cutoff: int = 5000,
) -> dict:
    """Report deterministic evidence-length and late-section statistics."""

    if cutoff <= 0:
        raise ValueError("cutoff must be positive")

    lengths: list[int] = []
    over_cutoff = 0
    late_qualification_jobs = 0
    late_section_counts: Counter[str] = Counter()
    qualification_pattern = re.compile(
        "|".join(re.escape(term) for term in QUALIFICATION_SECTION_TERMS),
        flags=re.IGNORECASE,
    )

    for job in jobs:
        evidence = job.raw_evidence
        lengths.append(len(evidence))
        if len(evidence) > cutoff:
            over_cutoff += 1

        late_sections: set[str] = set()
        for match in re.finditer(r"(?im)^\[([^\]]+)\]", evidence):
            section = " ".join(match.group(1).split())
            if match.start() >= cutoff and qualification_pattern.search(section):
                late_sections.add(section)
        if late_sections:
            late_qualification_jobs += 1
            late_section_counts.update(late_sections)

    count = len(lengths)
    return {
        "cutoff_chars": cutoff,
        "job_count": count,
        "raw_evidence_chars": {
            "p50": _percentile(lengths, 0.50),
            "p90": _percentile(lengths, 0.90),
            "p95": _percentile(lengths, 0.95),
            "p99": _percentile(lengths, 0.99),
            "max": max(lengths, default=0),
        },
        "over_cutoff_count": over_cutoff,
        "over_cutoff_percentage": (100.0 * over_cutoff / count) if count else 0.0,
        "late_qualification_section_job_count": late_qualification_jobs,
        "late_qualification_section_percentage": (
            100.0 * late_qualification_jobs / count
            if count
            else 0.0
        ),
        "late_qualification_sections": dict(sorted(late_section_counts.items())),
        "interpretation": (
            "A qualification section is counted as late when its bracketed "
            "section header begins at or after the raw-evidence cutoff."
        ),
    }


def embedding_provenance_contract(
    *,
    backend_root: Path,
    corpus_membership_sha256: str,
    corpus_chunks_sha256: str,
    forbidden_derived_metadata_present: bool,
) -> dict:
    """Create the V3 embedding provenance contract without inspecting/mutating DB vectors."""

    chunking_path = backend_root / "apps" / "career" / "chunking.py"
    embedding_path = backend_root / "apps" / "career" / "embedding.py"
    return {
        "status": "UNVERIFIED",
        "embedding_model": "intfloat/multilingual-e5-small",
        "embedding_dimension": 384,
        "chunking_source_sha256": sha256_file(chunking_path),
        "embedding_source_sha256": sha256_file(embedding_path),
        "input_field_policy": (
            "UNVERIFIED: the historical input fields used to create the frozen "
            "numeric vectors cannot be reconstructed from the surviving artifacts. "
            "The current chunking implementation is capable of including derived "
            "technical_skills metadata in embedding prefixes, so a clean historical "
            "contract cannot be inferred from source code alone."
        ),
        "forbidden_derived_metadata_present": bool(forbidden_derived_metadata_present),
        "corpus_membership_sha256": corpus_membership_sha256,
        "corpus_chunks_sha256": corpus_chunks_sha256,
        "requires_verified_clean_for_freeze": True,
    }


def audit_derived_label_leakage() -> dict:
    offenders: list[dict] = []
    rows = CareerJobChunk.objects.filter(active=True).values("chunk_id", "metadata")
    for row in rows.iterator(chunk_size=5000):
        metadata = row.get("metadata") or {}
        leaked = sorted(FORBIDDEN_DERIVED_KEYS.intersection(metadata))
        if leaked:
            offenders.append({"chunk_id": row["chunk_id"], "keys": leaked})
            if len(offenders) >= 20:
                break
    return {"passed": not offenders, "sample_offenders": offenders}


def audit_split(topics: list[CareerTopic]) -> dict:
    dev = {topic.family_id for topic in topics if topic.split == "dev"}
    test = {topic.family_id for topic in topics if topic.split == "test"}
    overlap = sorted(dev & test)
    return {"passed": not overlap, "dev_families": sorted(dev), "test_families": sorted(test), "overlap": overlap}


def audit_qrels(topics: list[CareerTopic], qrels: list[RelevanceJudgment], *, min_strong_per_topic: int = 5, max_uncertain_rate: float = 0.15) -> dict:
    by_topic: dict[str, list[RelevanceJudgment]] = defaultdict(list)
    for qrel in qrels:
        by_topic[qrel.topic_id].append(qrel)
    details = {}
    passed = True
    for topic in topics:
        rows = by_topic.get(topic.topic_id, [])
        uncertain = sum(1 for row in rows if row.uncertain)
        certain = [row for row in rows if not row.uncertain]
        strong = sum(1 for row in certain if row.grade >= 2)
        rate = uncertain / len(rows) if rows else 1.0
        topic_passed = strong >= min_strong_per_topic and rate <= max_uncertain_rate
        passed = passed and topic_passed
        details[topic.topic_id] = {
            "pool_size": len(rows),
            "uncertain_count": uncertain,
            "uncertain_rate": rate,
            "strong_relevant_count": strong,
            "passed": topic_passed,
        }
    return {"passed": passed, "topics": details}


def audit_controls(
    control_rows: list[dict],
    *,
    min_positive_accuracy: float = 0.90,
    min_negative_accuracy: float = 0.95,
    min_invariance_rate: float = 0.90,
) -> dict:
    by_type: dict[str, list[bool]] = defaultdict(list)
    for row in control_rows:
        by_type[row["control_type"]].append(bool(row["passed"]))

    def accuracy(kind: str) -> float:
        values = by_type.get(kind, [])
        return sum(values) / len(values) if values else 0.0

    positive_accuracy = accuracy("positive")
    negative_accuracy = accuracy("negative")
    order_rate = accuracy("order_invariance")
    paraphrase_rate = accuracy("paraphrase_consistency")
    passed = (
        positive_accuracy >= min_positive_accuracy
        and negative_accuracy >= min_negative_accuracy
        and order_rate >= min_invariance_rate
        and paraphrase_rate >= min_invariance_rate
    )
    return {
        "passed": passed,
        "positive_accuracy": positive_accuracy,
        "negative_accuracy": negative_accuracy,
        "order_invariance_rate": order_rate,
        "paraphrase_consistency_rate": paraphrase_rate,
        "positive_threshold": min_positive_accuracy,
        "negative_threshold": min_negative_accuracy,
        "invariance_threshold": min_invariance_rate,
    }


def audit_nuggets(topics: list[CareerTopic], nuggets: list[Nugget], *, min_nuggets_per_topic: int = 3) -> dict:
    counts = Counter(nugget.topic_id for nugget in nuggets)
    details = {topic.topic_id: counts.get(topic.topic_id, 0) for topic in topics}
    return {"passed": all(count >= min_nuggets_per_topic for count in details.values()), "counts": details}


def run_audit(
    *,
    topics: list[CareerTopic],
    qrels: list[RelevanceJudgment],
    nuggets: list[Nugget],
    controls: list[dict],
) -> dict:
    report = {
        "derived_label_leakage": audit_derived_label_leakage(),
        "split": audit_split(topics),
        "qrels": audit_qrels(topics, qrels),
        "controls": audit_controls(controls),
        "nuggets": audit_nuggets(topics, nuggets),
    }
    report["passed"] = all(section.get("passed", False) for section in report.values() if isinstance(section, dict) and section is not report)
    return report


def assert_audit_passes(report: dict) -> None:
    if not report.get("passed", False):
        raise RuntimeError("CareerRAGBench-Auto-V3 quality gates failed. See reports/build_audit.json; benchmark was NOT frozen.")
