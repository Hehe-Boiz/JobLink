from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from apps.career.models import CareerJobChunk

from .schema import CareerTopic, Nugget, RelevanceJudgment

FORBIDDEN_DERIVED_KEYS = {"technical_skills", "soft_skills", "gold_nuggets", "judge_labels", "derived_role_labels"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_tree(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


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
        raise RuntimeError("CareerRAGBench-Auto-V1 quality gates failed. See reports/build_audit.json; benchmark was NOT frozen.")
