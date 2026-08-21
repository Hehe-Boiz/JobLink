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

V3_REQUIRED_ARTIFACTS = (
    "corpus_manifest.json",
    "topics.jsonl",
    "queries.jsonl",
    "pool.jsonl",
    "qrels.silver.jsonl",
    "qrels.uncertain.jsonl",
    "controls.jsonl",
    "nuggets.silver.jsonl",
    "dev_ids.json",
    "test_ids.json",
    "reports/build_audit.json",
    "reports/preflight_corpus.json",
    "reports/preflight_leakage.json",
    "reports/preflight_topics.json",
    "reports/preflight_report.json",
    "reports/preflight_embedding_provenance.json",
    "reports/preflight_evidence_truncation.json",
    "reports/preflight_pooling.json",
)
V3_BENCHMARK_NAME = "CareerRAGBench-Auto-V3"
V3_BENCHMARK_VERSION = "3.0"

FORBIDDEN_DERIVED_KEYS = {"technical_skills", "soft_skills", "gold_nuggets", "judge_labels", "derived_role_labels"}
EMBEDDING_PROVENANCE_SCHEMA_VERSION = "career-rag-embedding-provenance-v1"
EMBEDDING_INPUT_FIELD_POLICY = "raw-job-fields-only-no-forbidden-derived-fields-v1"
EMBEDDING_INDEXING_POLICY_VERSION = "career-rag-indexing-input-contract-v1"
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


def artifact_sha256_map(output_dir: Path) -> dict[str, str]:
    """Hash every artifact required to interpret a frozen V3 benchmark."""

    output_dir = Path(output_dir)
    hashes: dict[str, str] = {}
    missing: list[str] = []
    for relative in V3_REQUIRED_ARTIFACTS:
        path = output_dir / relative
        if not path.is_file():
            missing.append(relative)
            continue
        hashes[relative] = sha256_file(path)
    if missing:
        raise RuntimeError(
            "Cannot finalize V3 manifest; required artifacts are missing: "
            + ", ".join(missing)
        )
    return hashes


def _read_json_file(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl_file(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def verify_frozen_benchmark(output_dir: Path) -> dict:
    """Verify a frozen V3 directory without any external or paid resource."""

    output_dir = Path(output_dir)
    blockers: list[str] = []
    checks: dict[str, bool] = {}
    manifest: dict = {}

    manifest_path = output_dir / "benchmark_manifest.json"
    try:
        raw_manifest = _read_json_file(manifest_path)
        if not isinstance(raw_manifest, dict):
            raise ValueError("manifest must be a JSON object")
        manifest = raw_manifest
        checks["manifest_readable"] = True
    except Exception as exc:  # noqa: BLE001 - verifier reports all failures
        checks["manifest_readable"] = False
        blockers.append(f"manifest unreadable: {exc}")

    if manifest:
        checks["benchmark_identity"] = (
            manifest.get("benchmark_name") == V3_BENCHMARK_NAME
            and manifest.get("benchmark_version") == V3_BENCHMARK_VERSION
        )
        if not checks["benchmark_identity"]:
            blockers.append("benchmark name/version is not CareerRAGBench-Auto-V3 3.0")

        recorded = manifest.get("artifact_sha256")
        if not isinstance(recorded, dict):
            checks["artifact_manifest"] = False
            blockers.append("manifest has no artifact_sha256 mapping")
            recorded = {}
        else:
            checks["artifact_manifest"] = all(
                relative in recorded for relative in V3_REQUIRED_ARTIFACTS
            )
            missing = [relative for relative in V3_REQUIRED_ARTIFACTS if relative not in recorded]
            if missing:
                blockers.append("manifest does not bind: " + ", ".join(missing))

        artifact_ok = True
        recorded_paths = set(recorded) | set(V3_REQUIRED_ARTIFACTS)
        for relative in sorted(recorded_paths):
            if not isinstance(relative, str):
                artifact_ok = False
                blockers.append("artifact_sha256 contains a non-string path")
                continue
            relative_path = Path(relative)
            if relative_path.is_absolute() or ".." in relative_path.parts:
                artifact_ok = False
                blockers.append(f"artifact hash path escapes benchmark directory: {relative}")
                continue
            path = output_dir / relative
            expected = recorded.get(relative)
            if not path.is_file():
                artifact_ok = False
                blockers.append(f"missing bound artifact: {relative}")
                continue
            actual = sha256_file(path)
            if actual != expected:
                artifact_ok = False
                blockers.append(f"artifact hash mismatch: {relative}")
        checks["artifact_hashes"] = artifact_ok and checks.get("artifact_manifest", False)

        explicit_hash_pairs = {
            "corpus_manifest_sha256": "corpus_manifest.json",
            "topics_sha256": "topics.jsonl",
            "queries_sha256": "queries.jsonl",
            "pool_sha256": "pool.jsonl",
            "qrels_sha256": "qrels.silver.jsonl",
            "nuggets_sha256": "nuggets.silver.jsonl",
        }
        explicit_ok = True
        for field, relative in explicit_hash_pairs.items():
            path = output_dir / relative
            if not path.is_file() or manifest.get(field) != sha256_file(path):
                explicit_ok = False
                blockers.append(f"explicit manifest hash mismatch: {field}")
        checks["explicit_hashes"] = explicit_ok

    lock_ok = False
    lock_path = output_dir / "test_lock.json"
    try:
        lock = _read_json_file(lock_path)
        lock_ok = (
            isinstance(lock, dict)
            and lock.get("status") == "LOCKED"
            and lock.get("immutable") is True
            and lock.get("frozen") is True
            and lock.get("benchmark_name") == V3_BENCHMARK_NAME
            and lock.get("benchmark_version") == V3_BENCHMARK_VERSION
            and lock.get("benchmark_manifest_sha256") == sha256_file(manifest_path)
            and lock.get("test_ids_sha256") == sha256_file(output_dir / "test_ids.json")
        )
        if not lock_ok:
            blockers.append("test_lock does not bind the immutable manifest and TEST ids")
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"test_lock unreadable: {exc}")
    checks["test_lock"] = lock_ok

    try:
        corpus_manifest = _read_json_file(output_dir / "corpus_manifest.json")
        corpus_ok = (
            isinstance(corpus_manifest, dict)
            and corpus_manifest.get("benchmark") == V3_BENCHMARK_NAME
            and corpus_manifest.get("dataset_sha256") == manifest.get("dataset_sha256")
        )
        checks["corpus_manifest"] = corpus_ok
        if not corpus_ok:
            blockers.append("corpus_manifest identity does not match the V3 manifest")

        build_audit = _read_json_file(output_dir / "reports" / "build_audit.json")
        checks["build_audit"] = isinstance(build_audit, dict) and build_audit.get("passed") is True
        if not checks["build_audit"]:
            blockers.append("build_audit does not report passed=true")

        topics = _read_jsonl_file(output_dir / "topics.jsonl")
        queries = _read_jsonl_file(output_dir / "queries.jsonl")
        topic_ids = {row["topic_id"] for row in topics}
        by_topic: dict[str, list[dict]] = defaultdict(list)
        for query in queries:
            by_topic[query["topic_id"]].append(query)
        query_shape_ok = all(
            len(rows) == 3
            and {row.get("variant") for row in rows} == {"direct", "conversational", "noisy"}
            and all(row.get("topic_id") in topic_ids and row.get("known_skills") == [] for row in rows)
            for rows in by_topic.values()
        ) and len(by_topic) == len(topic_ids) and all(row.get("known_skills") == [] for row in topics)
        checks["topic_query_shape"] = query_shape_ok
        if not query_shape_ok:
            blockers.append("topics do not have exactly direct/conversational/noisy queries with empty known_skills")

        dev = set(manifest.get("dev_family_ids", []))
        test = set(manifest.get("test_family_ids", []))
        checks["family_disjoint"] = not dev.intersection(test)
        if dev.intersection(test):
            blockers.append("DEV/TEST family IDs overlap")

        qrels = _read_jsonl_file(output_dir / "qrels.silver.jsonl")
        uncertain = _read_jsonl_file(output_dir / "qrels.uncertain.jsonl")
        qrel_ok = all(
            row.get("topic_id") in topic_ids
            and type(row.get("grade")) is int
            and row.get("grade") in {0, 1, 2, 3}
            and isinstance(row.get("source"), str)
            and isinstance(row.get("source_job_id"), str)
            for row in qrels + uncertain
        )
        uncertain_ok = all(type(row.get("uncertain")) is bool for row in qrels + uncertain)
        uncertain_ok = uncertain_ok and all(row.get("uncertain") is False for row in qrels)
        uncertain_ok = uncertain_ok and all(row.get("uncertain") is True for row in uncertain)
        checks["qrel_shape"] = qrel_ok and uncertain_ok
        if not checks["qrel_shape"]:
            blockers.append("qrels contain invalid topic IDs, grades, or uncertain shape")

        from .nuggets import NUGGET_WEIGHT_POLICY, PREVALENCE_UNAVAILABLE

        nuggets = _read_jsonl_file(output_dir / "nuggets.silver.jsonl")
        strong_keys_by_topic: dict[str, set[str]] = defaultdict(set)
        for row in qrels:
            if row.get("grade", -1) >= 2 and row.get("uncertain") is False:
                strong_keys_by_topic[row["topic_id"]].add(
                    f"{row.get('source')}::{row.get('source_job_id')}"
                )
        nugget_ok = all(
            row.get("topic_id") in topic_ids
            and row.get("importance") in {"VITAL", "OKAY"}
            and row.get("weight") == NUGGET_WEIGHT_POLICY[row["importance"]]
            and row.get("prevalence") == PREVALENCE_UNAVAILABLE
            and type(row.get("support_count")) is int
            and isinstance(row.get("support_job_keys"), list)
            and all(isinstance(key, str) for key in row.get("support_job_keys", []))
            and row.get("support_count") == len(set(row.get("support_job_keys", [])))
            and set(row.get("support_job_keys", [])).issubset(
                strong_keys_by_topic[row.get("topic_id")]
            )
            for row in nuggets
        )
        checks["nugget_shape"] = nugget_ok
        if not nugget_ok:
            blockers.append("nuggets violate adaptive support/prevalence/importance policy")
    except Exception as exc:  # noqa: BLE001
        checks["construction_shape"] = False
        blockers.append(f"construction artifact shape verification failed: {exc}")

    configuration = manifest.get("configuration", {}) if manifest else {}
    provenance_report_ok = False
    try:
        provenance_report = _read_json_file(
            output_dir / "reports" / "preflight_embedding_provenance.json"
        )
        provenance_report_ok = (
            isinstance(provenance_report, dict)
            and provenance_report.get("status") == "VERIFIED_CLEAN"
        )
    except Exception:  # noqa: BLE001
        provenance_report_ok = False
    provenance_ok = provenance_report_ok and (
        configuration.get("embedding_provenance_status") == "VERIFIED_CLEAN"
        or isinstance(configuration.get("embedding_provenance"), dict)
        and configuration["embedding_provenance"].get("status") == "VERIFIED_CLEAN"
    )
    checks["embedding_provenance"] = provenance_ok
    if not provenance_ok:
        blockers.append("embedding provenance report/manifest is not VERIFIED_CLEAN")
    checks["source_hashes"] = bool(
        configuration.get("git_head") not in (None, "", "unknown")
        and isinstance(manifest.get("builder_source_sha256"), str)
        and len(manifest.get("builder_source_sha256", "")) == 64
        and isinstance(manifest.get("judge_prompt_sha256"), str)
        and len(manifest.get("judge_prompt_sha256", "")) == 64
    )
    if not checks["source_hashes"]:
        blockers.append("git/source hashes are missing")

    checks["passed"] = not blockers
    return {
        "passed": not blockers,
        "status": "PASS" if not blockers else "FAIL",
        "output_dir": str(output_dir),
        "checks": checks,
        "blockers": blockers,
    }


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
    """Report deterministic evidence-length and qualification-loss statistics."""

    if cutoff <= 0:
        raise ValueError("cutoff must be positive")

    lengths: list[int] = []
    over_cutoff = 0
    late_qualification_jobs = 0
    late_section_counts: Counter[str] = Counter()
    after_cutoff_section_count = 0
    crossing_cutoff_section_count = 0
    after_cutoff_section_jobs: set[str] = set()
    crossing_cutoff_section_jobs: set[str] = set()
    qualification_content_lost_jobs: set[str] = set()
    qualification_content_lost_chars: list[int] = []
    qualification_content_lost_total = 0
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
        section_matches = list(re.finditer(r"(?im)^\[([^\]]+)\]", evidence))
        for index, match in enumerate(section_matches):
            section = " ".join(match.group(1).split())
            if not qualification_pattern.search(section):
                continue

            section_end = (
                section_matches[index + 1].start()
                if index + 1 < len(section_matches)
                else len(evidence)
            )
            section_body_start = match.end()
            lost_start = max(cutoff, section_body_start)
            lost_chars = max(0, section_end - lost_start)

            if match.start() >= cutoff:
                late_sections.add(section)
                after_cutoff_section_count += 1
                after_cutoff_section_jobs.add(job.job_key)
            elif section_end > cutoff:
                crossing_cutoff_section_count += 1
                crossing_cutoff_section_jobs.add(job.job_key)

            if lost_chars:
                qualification_content_lost_total += lost_chars
                qualification_content_lost_chars.append(lost_chars)
                qualification_content_lost_jobs.add(job.job_key)
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
        "qualification_section_after_cutoff_count": after_cutoff_section_count,
        "qualification_section_after_cutoff_job_count": len(after_cutoff_section_jobs),
        "qualification_section_crossing_cutoff_count": crossing_cutoff_section_count,
        "qualification_section_crossing_cutoff_job_count": len(crossing_cutoff_section_jobs),
        "qualification_content_chars_lost_total": qualification_content_lost_total,
        "qualification_content_chars_lost": {
            "p50": _percentile(qualification_content_lost_chars, 0.50),
            "p90": _percentile(qualification_content_lost_chars, 0.90),
            "p95": _percentile(qualification_content_lost_chars, 0.95),
            "p99": _percentile(qualification_content_lost_chars, 0.99),
            "max": max(qualification_content_lost_chars, default=0),
        },
        "qualification_content_lost_job_count": len(qualification_content_lost_jobs),
        "qualification_content_lost_job_percentage": (
            100.0 * len(qualification_content_lost_jobs) / count
            if count
            else 0.0
        ),
        "interpretation": (
            "Qualification sections are identified by their bracketed section "
            "headers. The audit separately counts sections beginning after the "
            "cutoff, sections whose spans cross the cutoff, and qualification "
            "body characters after the cutoff."
        ),
    }


def embedding_provenance_expected_contract(
    *,
    backend_root: Path,
    corpus_membership_sha256: str,
    corpus_chunks_sha256: str,
) -> dict:
    """Return the durable fields a clean V3 index manifest must contain."""

    chunking_path = backend_root / "apps" / "career" / "chunking.py"
    embedding_path = backend_root / "apps" / "career" / "embedding.py"
    forbidden_fields = sorted(FORBIDDEN_DERIVED_KEYS)
    return {
        "provenance_schema_version": EMBEDDING_PROVENANCE_SCHEMA_VERSION,
        "embedding_model": "intfloat/multilingual-e5-small",
        "embedding_dimension": 384,
        "chunking_source_sha256": sha256_file(chunking_path),
        "embedding_source_sha256": sha256_file(embedding_path),
        "input_field_policy": EMBEDDING_INPUT_FIELD_POLICY,
        "forbidden_derived_fields": forbidden_fields,
        "forbidden_derived_fields_excluded": True,
        "corpus_membership_sha256": corpus_membership_sha256,
        "corpus_chunks_sha256": corpus_chunks_sha256,
        "chunk_context_sha256": corpus_chunks_sha256,
        "indexing_policy_version": EMBEDDING_INDEXING_POLICY_VERSION,
    }


def embedding_provenance_contract(
    *,
    backend_root: Path,
    corpus_membership_sha256: str,
    corpus_chunks_sha256: str,
    forbidden_derived_metadata_present: bool,
    provenance_path: Path | None = None,
) -> dict:
    """Verify an explicit historical index manifest without inspecting vectors.

    Current metadata cleanliness and current source code are observations, not
    historical proof of what was embedded. A clean status therefore requires a
    durable artifact with matching hashes, an explicit clean status, an
    indexing timestamp, and an explicit exclusion declaration.
    """

    expected = embedding_provenance_expected_contract(
        backend_root=backend_root,
        corpus_membership_sha256=corpus_membership_sha256,
        corpus_chunks_sha256=corpus_chunks_sha256,
    )
    report = {
        "status": "UNVERIFIED",
        **expected,
        "expected_contract": expected,
        "provenance_artifact_path": str(provenance_path) if provenance_path else None,
        "indexing_timestamp": None,
        "input_field_policy": (
            "UNVERIFIED: the historical embedding input fields are not proven; "
            f"expected clean policy would be {expected['input_field_policy']}."
        ),
        "forbidden_derived_fields_excluded": None,
        "forbidden_derived_metadata_present": bool(forbidden_derived_metadata_present),
        "requires_verified_clean_for_freeze": True,
        "missing_evidence": [],
        "mismatched_fields": [],
    }

    if provenance_path is None:
        report["missing_evidence"] = ["provenance_artifact"]
        report["reason"] = (
            "No durable historical embedding provenance artifact was supplied; "
            "current metadata and source code cannot prove the frozen vector input contract."
        )
        return report

    try:
        artifact = json.loads(Path(provenance_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report["missing_evidence"] = ["readable_provenance_artifact"]
        report["reason"] = f"Could not read provenance artifact: {exc}"
        return report

    if not isinstance(artifact, dict):
        report["missing_evidence"] = ["object_provenance_artifact"]
        report["reason"] = "Provenance artifact must be a JSON object."
        return report

    artifact_status = artifact.get("status", artifact.get("provenance_status"))
    report["indexing_timestamp"] = artifact.get("indexing_timestamp")
    report["input_field_policy"] = artifact.get(
        "input_field_policy",
        report["input_field_policy"],
    )
    report["forbidden_derived_fields_excluded"] = artifact.get(
        "forbidden_derived_fields_excluded",
    )
    included = artifact.get("derived_fields_included")
    if included is None:
        included = artifact.get("forbidden_derived_fields_included")
    explicitly_leaked = (
        artifact_status == "VERIFIED_LEAKED"
        or artifact.get("forbidden_derived_fields_excluded") is False
        or included is True
        or (isinstance(included, (list, tuple, set)) and bool(included))
    )
    if explicitly_leaked:
        report["status"] = "VERIFIED_LEAKED"
        report["forbidden_derived_fields_excluded"] = False
        report["reason"] = "The provenance artifact explicitly records forbidden derived fields in embedding input."
        return report

    required_fields = list(expected)
    mismatched = [
        field
        for field in required_fields
        if artifact.get(field) != expected[field]
    ]
    if mismatched:
        report["mismatched_fields"] = mismatched

    missing: list[str] = []
    if artifact_status != "VERIFIED_CLEAN":
        missing.append("explicit_verified_clean_status")
    if artifact.get("indexing_timestamp") in (None, ""):
        missing.append("indexing_timestamp")
    if artifact.get("forbidden_derived_fields_excluded") is not True:
        missing.append("forbidden_derived_fields_excluded=true")
    report["missing_evidence"] = missing

    if not mismatched and not missing:
        report["status"] = "VERIFIED_CLEAN"
        report["reason"] = "Durable clean provenance matched the V3 corpus, source, model, dimension, and policy contract."
    else:
        report["reason"] = "The supplied provenance artifact was incomplete or did not match the V3 contract."
    return report


def embedding_provenance_is_freeze_safe(contract: dict) -> bool:
    return contract.get("status") == "VERIFIED_CLEAN"


def audit_derived_label_leakage(*, source: str = "vietjobs") -> dict:
    offenders: list[dict] = []
    rows = CareerJobChunk.objects.filter(active=True, source=source).values("chunk_id", "metadata")
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
        "derived_label_leakage": audit_derived_label_leakage(source="vietjobs"),
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
