from __future__ import annotations

import csv
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.db import connection

from apps.career.sources.vietjobs import VietJobsSource

from .audit import (
    V3_BENCHMARK_NAME,
    V3_BENCHMARK_VERSION,
    artifact_sha256_map,
    audit_derived_label_leakage,
    audit_evidence_truncation,
    assert_audit_passes,
    run_audit,
    sha256_file,
    sha256_tree,
    verify_frozen_benchmark,
)
from .clean_index import (
    CLEAN_EMBEDDING_DIMENSION,
    CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
    CLEAN_EMBEDDING_MODEL,
    CLEAN_INDEX_TYPE,
    V3_SNAPSHOT_ACTIVE_CHUNK_COUNT,
    V3_SNAPSHOT_INDEXED_JOB_COUNT,
    CleanBenchmarkDenseRanker,
    configured_clean_index_dir,
    current_clean_corpus_identity,
    verify_clean_embedding_index,
)
from .evidence import DEFAULT_EVIDENCE_CHAR_BUDGET, EVIDENCE_PACKING_POLICY_VERSION
from .pooling import (
    POOLING_POLICY_FULL_DIRECT_UNION_V1,
    PoolingService,
    audit_pool_coverage_offline,
    load_corpus_jobs,
)
from .schema import BenchmarkManifest, CareerQuery
from .semantics import CANONICAL_INFORMATION_NEED_VERSION
from .topics import (
    BASE_QUERY_VARIANTS,
    DEFAULT_MIN_SPECIFIC_TITLE_JOBS,
    DEFAULT_RANDOM_SEED,
    SPECIFICITY_WILSON_Z,
    TOPIC_SELECTION_POLICY_VERSION,
    discover_topics,
)

BACKEND_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "career_rag_bench_auto_v3"
DEFAULT_PREFLIGHT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "career_rag_bench_auto_v3_preflight"
BENCHMARK_NAME = V3_BENCHMARK_NAME
BENCHMARK_VERSION = V3_BENCHMARK_VERSION
FROZEN_MARKERS = ("benchmark_manifest.json", "test_lock.json")
POOL_DEPTHS = (5, 10, 15, 20)
V3_SNAPSHOT_SOURCE_ROW_COUNT = 48_092
V3_SNAPSHOT_SOURCE_ROWS_NOT_INDEXED = 995
V3_SNAPSHOT_OBSERVED_FAMILY_COUNT = 15
TOPICS_PER_FAMILY = 2
QUERY_VARIANTS_PER_TOPIC = len(BASE_QUERY_VARIANTS)
V3_SNAPSHOT_DERIVED_TOPIC_COUNT = V3_SNAPSHOT_OBSERVED_FAMILY_COUNT * TOPICS_PER_FAMILY
V3_SNAPSHOT_DERIVED_QUERY_COUNT = V3_SNAPSHOT_DERIVED_TOPIC_COUNT * QUERY_VARIANTS_PER_TOPIC


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _jsonl_dump(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _find_vietjobs_csv() -> Path:
    candidates = sorted((BACKEND_ROOT / "data" / "career_eval" / "vietjobs").rglob("*.csv"))
    required = {"job_title", "description", "requirements_text", "category"}
    for path in candidates:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            try:
                header = next(reader)
            except StopIteration:
                continue
        if required.issubset(header):
            return path
    raise FileNotFoundError("Could not find the VietJobs CSV under data/career_eval/vietjobs")


def _index_configuration() -> list[str]:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename = %s ORDER BY indexname",
            ["career_careerjobchunk"],
        )
        return [row[0] for row in cursor.fetchall()]


def _source_sha() -> tuple[str, str, bool]:
    package_dir = Path(__file__).resolve().parent
    tree_sha = sha256_tree(package_dir.glob("*.py"))
    try:
        git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BACKEND_ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=BACKEND_ROOT, text=True).strip())
    except Exception:  # noqa: BLE001
        git_sha, dirty = "unknown", True
    return tree_sha, git_sha, dirty


def _assert_final_output_available(output_dir: Path) -> None:
    """Refuse both frozen and partial existing targets; never overwrite."""

    output_dir = Path(output_dir)
    if not output_dir.exists():
        return
    markers = [name for name in FROZEN_MARKERS if (output_dir / name).exists()]
    if markers:
        raise RuntimeError(
            f"Refusing to overwrite frozen benchmark {output_dir}; markers present: {', '.join(markers)}"
        )
    raise RuntimeError(
        f"Refusing to use existing benchmark output directory {output_dir}; remove it or choose a new V3 path."
    )


def _create_building_directory(output_dir: Path) -> Path:
    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(20):
        candidate = output_dir.parent / f"{output_dir.name}.building-{os.getpid()}-{secrets.token_hex(8)}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a unique same-filesystem V3 build directory")


def _finalize_candidate(candidate_dir: Path, output_dir: Path) -> None:
    if Path(output_dir).exists():
        raise RuntimeError(f"Benchmark output appeared during construction; refusing to replace {output_dir}")
    Path(candidate_dir).replace(Path(output_dir))


def _construct_offline_pooler(corpus_jobs: list, *, clean_index_dir: Path | None = None) -> PoolingService:
    """Construct local retrieval diagnostics without allowing model downloads."""

    previous = {
        key: os.environ.get(key)
        for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    }
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        index_dir = Path(clean_index_dir or configured_clean_index_dir())
        return PoolingService(
            corpus_jobs,
            dense_ranker=CleanBenchmarkDenseRanker(index_dir),
        )
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _corpus_snapshot(*, seed: int = DEFAULT_RANDOM_SEED, max_pool: int = 80) -> dict:
    csv_path = _find_vietjobs_csv()
    dataset_sha = sha256_file(csv_path)
    source_records = list(VietJobsSource(dataset_dir=csv_path.parent).iter_records())
    raw_rows = len(source_records)
    source_ids = {record.source_job_id for record in source_records}
    corpus_jobs = load_corpus_jobs(source="vietjobs")
    corpus_by_key = {job.job_key: job for job in corpus_jobs}
    db_job_ids = {job.source_job_id for job in corpus_jobs}
    source_rows_not_indexed = source_ids - db_job_ids
    db_only_source_ids = db_job_ids - source_ids
    clean_identity = current_clean_corpus_identity()
    chunk = {"count": clean_identity["indexed_chunk_count"], "sha256": clean_identity["chunk_context_sha256"]}
    membership_sha = clean_identity["corpus_membership_sha256"]
    leakage = audit_derived_label_leakage(source="vietjobs")
    truncation = audit_evidence_truncation(corpus_jobs, cutoff=DEFAULT_EVIDENCE_CHAR_BUDGET)
    clean_index_dir = configured_clean_index_dir()
    clean_index = verify_clean_embedding_index(clean_index_dir)
    provenance = clean_index.get("provenance", {})
    blockers: list[str] = []
    if len(source_ids) != raw_rows:
        blockers.append(
            f"VietJobsSource produced duplicate source_job_id values: {raw_rows - len(source_ids)}"
        )
    if raw_rows != V3_SNAPSHOT_SOURCE_ROW_COUNT:
        blockers.append(
            f"frozen source row count drift: expected {V3_SNAPSHOT_SOURCE_ROW_COUNT}, got {raw_rows}"
        )
    if not corpus_jobs:
        blockers.append("no active VietJobs jobs are available")
    if db_only_source_ids:
        blockers.append(f"DB-only VietJobs source IDs: {len(db_only_source_ids)}")
    if len(db_job_ids) != V3_SNAPSHOT_INDEXED_JOB_COUNT:
        blockers.append(
            f"indexed job count drift: expected {V3_SNAPSHOT_INDEXED_JOB_COUNT}, got {len(db_job_ids)}"
        )
    if len(source_rows_not_indexed) != V3_SNAPSHOT_SOURCE_ROWS_NOT_INDEXED:
        blockers.append(
            "source rows absent from the frozen index drift: expected "
            f"{V3_SNAPSHOT_SOURCE_ROWS_NOT_INDEXED}, got {len(source_rows_not_indexed)}"
        )
    if chunk["count"] != V3_SNAPSHOT_ACTIVE_CHUNK_COUNT:
        blockers.append(
            f"indexed chunk count drift: expected {V3_SNAPSHOT_ACTIVE_CHUNK_COUNT}, got {chunk['count']}"
        )
    if not leakage["passed"]:
        blockers.append("forbidden derived metadata exists in active VietJobs rows")
    if not clean_index["passed"]:
        blockers.append("clean benchmark index is invalid: " + "; ".join(clean_index["blockers"]))

    try:
        topics, queries, dev_family_ids, test_family_ids = discover_topics(corpus_jobs, random_seed=seed)
    except Exception as exc:  # noqa: BLE001
        topics, queries, dev_family_ids, test_family_ids = [], [], [], []
        blockers.append(f"topic construction failed: {exc}")
    queries_by_topic: dict[str, list[CareerQuery]] = defaultdict(list)
    for query in queries:
        queries_by_topic[query.topic_id].append(query)
    topic_shape_ok = (
        all(not topic.known_skills for topic in topics)
        and all(not query.known_skills for query in queries)
        and all(
            len(queries_by_topic[topic.topic_id]) == QUERY_VARIANTS_PER_TOPIC
            and {query.variant for query in queries_by_topic[topic.topic_id]} == set(BASE_QUERY_VARIANTS)
            for topic in topics
        )
        and not set(dev_family_ids).intersection(test_family_ids)
    )
    if not topic_shape_ok:
        blockers.append("topic/query construction shape or family split invariant failed")
    families = defaultdict(list)
    for topic in topics:
        families[topic.family_id].append(topic)
    expected_topic_counts_ok = (
        len(families) == V3_SNAPSHOT_OBSERVED_FAMILY_COUNT
        and len(topics) == V3_SNAPSHOT_DERIVED_TOPIC_COUNT
        and len(queries) == V3_SNAPSHOT_DERIVED_QUERY_COUNT
        and all(
            len(rows) == TOPICS_PER_FAMILY
            and {topic.scope for topic in rows} == {"broad", "specific"}
            for rows in families.values()
        )
    )
    if not expected_topic_counts_ok:
        blockers.append(
            "frozen topic snapshot drift: expected "
            f"{V3_SNAPSHOT_OBSERVED_FAMILY_COUNT} families / "
            f"{V3_SNAPSHOT_DERIVED_TOPIC_COUNT} topics / "
            f"{V3_SNAPSHOT_DERIVED_QUERY_COUNT} queries with broad+specific pairs"
        )

    pooling_report: dict
    try:
        pooler = _construct_offline_pooler(corpus_jobs, clean_index_dir=clean_index_dir)
        pooling_report = audit_pool_coverage_offline(
            pooler, topics, queries_by_topic, depths=POOL_DEPTHS, max_pool=max_pool
        )
    except Exception as exc:  # noqa: BLE001
        pooling_report = {
            "mode": "unavailable", "external_llm_calls": 0,
            "retrieval_systems_run": [], "error": str(exc),
            "pooling_policy": POOLING_POLICY_FULL_DIRECT_UNION_V1,
        }
        blockers.append(f"real offline pooling audit unavailable: {exc}")

    try:
        index_configuration = _index_configuration()
    except Exception as exc:  # noqa: BLE001
        index_configuration = []
        blockers.append(f"index configuration audit unavailable: {exc}")
    corpus_manifest = {
        "benchmark": BENCHMARK_NAME,
        "dataset_filename": csv_path.name,
        "dataset_path": str(csv_path.relative_to(BACKEND_ROOT)),
        "dataset_sha256": dataset_sha,
        "raw_row_count": raw_rows,
        "db_unique_job_count": len(db_job_ids),
        "source_rows_not_indexed": len(source_rows_not_indexed),
        "db_only_source_id_count": len(db_only_source_ids),
        "db_chunk_count": chunk["count"],
        "snapshot_contract": {
            "scope": "CareerRAGBench-Auto-V3 frozen VietJobs snapshot; not a universal methodology constant",
            "source_row_count": V3_SNAPSHOT_SOURCE_ROW_COUNT,
            "indexed_job_count": V3_SNAPSHOT_INDEXED_JOB_COUNT,
            "active_chunk_count": V3_SNAPSHOT_ACTIVE_CHUNK_COUNT,
            "source_rows_not_indexed": V3_SNAPSHOT_SOURCE_ROWS_NOT_INDEXED,
            "snapshot_observed_family_count": V3_SNAPSHOT_OBSERVED_FAMILY_COUNT,
            "topics_per_family": TOPICS_PER_FAMILY,
            "query_variants_per_topic": QUERY_VARIANTS_PER_TOPIC,
            "derived_topic_count": V3_SNAPSHOT_DERIVED_TOPIC_COUNT,
            "derived_query_count": V3_SNAPSHOT_DERIVED_QUERY_COUNT,
        },
        "corpus_identity_policy": "frozen-index-membership-v1",
        "historical_selection_reconstructible": False,
        "corpus_membership_sha256": membership_sha,
        "corpus_chunks_sha256": chunk["sha256"],
        "corpus_identity_note": (
            "The frozen corpus is identified by the dataset SHA256, indexed "
            "source_job_id membership SHA256, and active chunk/context SHA256; "
            "the historical filtering membership is not reconstructed from code."
        ),
        "clean_embedding_index_type": CLEAN_INDEX_TYPE,
        "clean_embedding_model": CLEAN_EMBEDDING_MODEL,
        "clean_embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
        "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
        "clean_embedding_vectors_sha256": provenance.get("vectors_sha256"),
        "clean_embedding_chunk_map_sha256": provenance.get("chunk_map_sha256"),
        "clean_embedding_provenance_sha256": sha256_file(clean_index_dir / "embedding_provenance.json") if clean_index.get("provenance") else None,
        "clean_embedding_corpus_membership_sha256": provenance.get("corpus_membership_sha256"),
        "clean_embedding_chunk_context_sha256": provenance.get("chunk_context_sha256"),
        "embedding_model": CLEAN_EMBEDDING_MODEL,
        "embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
        "embedding_source_sha256": provenance.get("embedding_source_sha256"),
        "existing_chunk_rows_policy": "use-frozen-rows-without-rechunk-v1",
        "historical_chunking_provenance": "UNVERIFIED",
        "clean_embedding_index_dir": str(clean_index_dir),
        "embedding_provenance": provenance,
        "evidence_packing_policy_version": EVIDENCE_PACKING_POLICY_VERSION,
        "evidence_char_budget": DEFAULT_EVIDENCE_CHAR_BUDGET,
        "evidence_truncation_audit": truncation,
        "index_configuration": index_configuration,
        "forbidden_derived_metadata_keys": [
            "technical_skills", "soft_skills", "gold_nuggets", "judge_labels", "derived_role_labels",
        ],
    }
    return {
        "csv_path": csv_path, "dataset_sha": dataset_sha, "source_records": source_records,
        "raw_rows": raw_rows, "source_ids": source_ids, "corpus_jobs": corpus_jobs,
        "corpus_by_key": corpus_by_key, "db_job_ids": db_job_ids,
        "source_rows_not_indexed": source_rows_not_indexed, "db_only_source_ids": db_only_source_ids,
        "chunk": chunk, "membership_sha": membership_sha, "leakage": leakage,
        "truncation": truncation, "provenance": provenance, "clean_index": clean_index,
        "clean_index_dir": clean_index_dir, "topics": topics, "queries": queries,
        "queries_by_topic": queries_by_topic, "dev_family_ids": dev_family_ids,
        "test_family_ids": test_family_ids, "topic_shape_ok": topic_shape_ok,
        "pooling": pooling_report, "pooling_policy": POOLING_POLICY_FULL_DIRECT_UNION_V1,
        "corpus_manifest": corpus_manifest, "blockers": blockers,
    }


def _write_preflight_reports(snapshot: dict, reports_dir: Path) -> None:
    _json_dump(reports_dir / "preflight_corpus.json", {
        "benchmark": BENCHMARK_NAME,
        "raw_vietjobs_rows": snapshot.get("raw_rows", 0),
        "indexed_vietjobs_jobs": len(snapshot.get("db_job_ids", set())),
        "indexed_vietjobs_chunks": snapshot.get("chunk", {}).get("count", 0),
        "source_rows_absent_from_db": len(snapshot.get("source_rows_not_indexed", set())),
        "db_only_source_ids": sorted(snapshot.get("db_only_source_ids", set())),
        "membership_sha256": snapshot.get("membership_sha", ""),
        "chunk_context_sha256": snapshot.get("chunk", {}).get("sha256", ""),
        "blockers": snapshot.get("blockers", []),
    })
    _json_dump(reports_dir / "preflight_leakage.json", snapshot.get("leakage", {}))
    _json_dump(reports_dir / "preflight_embedding_provenance.json", snapshot.get("provenance", {}))
    # This is the actual sidecar provenance copied into a frozen build.  It is
    # intentionally separate from the old historical-provenance report name.
    _json_dump(reports_dir / "clean_embedding_provenance.json", snapshot.get("provenance", {}))
    _json_dump(reports_dir / "preflight_evidence_truncation.json", snapshot.get("truncation", {}))
    _json_dump(reports_dir / "preflight_pooling.json", snapshot.get("pooling", {}))
    _json_dump(reports_dir / "preflight_topics.json", {
        "topic_count": len(snapshot.get("topics", [])),
        "family_count": len(snapshot.get("dev_family_ids", [])) + len(snapshot.get("test_family_ids", [])),
        "query_count": len(snapshot.get("queries", [])),
        "queries_per_topic": QUERY_VARIANTS_PER_TOPIC,
        "snapshot_observed_family_count": V3_SNAPSHOT_OBSERVED_FAMILY_COUNT,
        "topics_per_family": TOPICS_PER_FAMILY,
        "query_variants_per_topic": QUERY_VARIANTS_PER_TOPIC,
        "derived_topic_count": V3_SNAPSHOT_DERIVED_TOPIC_COUNT,
        "derived_query_count": V3_SNAPSHOT_DERIVED_QUERY_COUNT,
        "base_query_variants": list(BASE_QUERY_VARIANTS),
        "personalized_variant_present": any(query.variant == "personalized" for query in snapshot.get("queries", [])),
        "dev_test_family_overlap": sorted(set(snapshot.get("dev_family_ids", [])).intersection(snapshot.get("test_family_ids", []))),
        "selected_topics": [topic.to_dict() for topic in snapshot.get("topics", [])],
    })


def run_construction_preflight(
    *,
    output_dir: Path = DEFAULT_PREFLIGHT_OUTPUT_DIR,
    seed: int = DEFAULT_RANDOM_SEED,
    max_pool: int = 80,
    judge_model: str | None = None,
) -> dict:
    """Run all free V3 checks; this function never creates a JudgeClient."""

    report_dir = Path(output_dir)
    report_dir.mkdir(parents=True, exist_ok=True)
    try:
        snapshot = _corpus_snapshot(seed=seed, max_pool=max_pool)
    except Exception as exc:  # noqa: BLE001
        snapshot = {
            "blockers": [f"corpus preflight failed: {exc}"],
            "provenance": {"status": "UNVERIFIED", "reason": "corpus preflight failed"},
            "clean_index": {"passed": False, "status": "FAIL", "blockers": ["corpus preflight failed"]},
            "pooling": {"mode": "unavailable", "external_llm_calls": 0, "error": str(exc)},
            "topics": [], "queries": [], "dev_family_ids": [], "test_family_ids": [],
            "raw_rows": 0, "db_job_ids": set(), "source_rows_not_indexed": set(),
            "db_only_source_ids": set(), "chunk": {"count": 0, "sha256": ""},
            "membership_sha": "", "leakage": {"passed": False, "sample_offenders": []},
            "truncation": {},
        }
    blockers = list(snapshot.get("blockers", []))
    if snapshot.get("provenance", {}).get("status") != "VERIFIED_CLEAN" and not any("clean benchmark index" in item for item in blockers):
        blockers.append("clean embedding provenance is not VERIFIED_CLEAN")
    if not snapshot.get("clean_index", {}).get("passed", False):
        blockers.append("clean benchmark sidecar is missing or invalid")
    paid_configuration = {
        "openai_sdk_available": importlib.util.find_spec("openai") is not None,
        "api_key_configured": bool(getattr(settings, "CKEY_API_KEY", "")),
        "judge_model_configured": bool(judge_model or os.environ.get("CAREER_RAG_JUDGE_MODEL")),
    }
    if not all(paid_configuration.values()):
        blockers.append("paid-build configuration is incomplete (SDK, API key, or judge model)")
    snapshot["blockers"] = sorted(set(blockers))
    snapshot["readiness"] = {
        "status": "READY_FOR_PAID_BUILD" if not snapshot["blockers"] else "BLOCKED",
        "blockers": snapshot["blockers"], "external_llm_calls": 0,
    }
    _write_preflight_reports(snapshot, report_dir)
    report = {
        "benchmark": BENCHMARK_NAME, "version": BENCHMARK_VERSION,
        "readiness": snapshot["readiness"],
        "corpus": {
            "raw_vietjobs_rows": snapshot.get("raw_rows", 0),
            "indexed_vietjobs_jobs": len(snapshot.get("db_job_ids", set())),
            "indexed_vietjobs_chunks": snapshot.get("chunk", {}).get("count", 0),
            "membership_sha256": snapshot.get("membership_sha", ""),
            "chunk_context_sha256": snapshot.get("chunk", {}).get("sha256", ""),
        },
        "leakage": snapshot.get("leakage", {}),
        "embedding_provenance": snapshot.get("provenance", {}),
        "clean_index": snapshot.get("clean_index", {}),
        "paid_configuration": paid_configuration,
        "topics": {"topic_count": len(snapshot.get("topics", [])), "query_count": len(snapshot.get("queries", [])), "family_count": len(snapshot.get("dev_family_ids", [])) + len(snapshot.get("test_family_ids", []))},
        "pooling": snapshot.get("pooling", {}), "evidence_truncation": snapshot.get("truncation", {}),
        "annotation_status": {
            "qrels": "SILVER_LLM_GENERATED_NOT_HUMAN_GOLD",
            "judge_views": "multi-view consistency judgments from one judge model",
            "human_calibration_status": "NOT_PERFORMED",
        },
        "blockers": snapshot["blockers"], "external_llm_calls": 0,
    }
    _json_dump(report_dir / "preflight_report.json", report)
    return {**snapshot, "report": report}


def _build_benchmark_into(output_dir: Path, *, judge_model: str, seed: int, pool_depth: int, max_pool: int) -> dict:
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    if pool_depth != max(POOL_DEPTHS):
        raise RuntimeError(
            f"CareerRAGBench-Auto-V3 requires pool_depth={max(POOL_DEPTHS)} "
            "because the pooling decision rule is frozen at depth=20."
        )
    free = run_construction_preflight(
        output_dir=reports_dir,
        seed=seed,
        max_pool=max_pool,
        judge_model=judge_model,
    )
    if free["readiness"]["status"] != "READY_FOR_PAID_BUILD":
        raise RuntimeError("CareerRAGBench-Auto-V3 free preflight blocked construction: " + "; ".join(free["readiness"]["blockers"]))
    if not getattr(settings, "CKEY_API_KEY", ""):
        raise RuntimeError("CKEY_API_KEY is not configured; silver benchmark construction requires an LLM judge.")
    if not judge_model:
        raise RuntimeError("judge_model is required after free V3 preflight")

    # Keep all OpenAI-dependent construction code out of free preflight.  This
    # import occurs only after the explicit paid-build gate has succeeded.
    from .judges import JUDGE_PROMPT_VERSION, JudgeClient, build_and_judge_controls, judge_candidates
    from .nuggets import (
        IMPORTANCE_EVIDENCE_PREVIEW_JOBS,
        NUGGET_IMPORTANCE_POLICY_VERSION,
        NUGGET_PROMPT_VERSION,
        NUGGET_SUPPORT_SEMANTICS_VERSION,
        NUGGET_WEIGHT_POLICY,
        PREVALENCE_POLICY_VERSION,
        PREVALENCE_UNAVAILABLE,
        build_nuggets_for_topic,
    )
    from apps.career.answering import DEFAULT_ANSWER_MODEL

    # Preserve the exact provenance bytes whose hash is frozen below.  Vectors
    # deliberately remain external; the manifest binds their SHA instead.
    shutil.copyfile(
        free["clean_index_dir"] / "embedding_provenance.json",
        reports_dir / "clean_embedding_provenance.json",
    )

    corpus_jobs = free["corpus_jobs"]
    corpus_by_key = free["corpus_by_key"]
    topics, queries = free["topics"], free["queries"]
    queries_by_topic = free["queries_by_topic"]
    output_dir.mkdir(parents=True, exist_ok=True)
    _json_dump(output_dir / "corpus_manifest.json", free["corpus_manifest"])
    _jsonl_dump(output_dir / "topics.jsonl", [topic.to_dict() for topic in topics])
    _jsonl_dump(output_dir / "queries.jsonl", [query.to_dict() for query in queries])
    pooler = _construct_offline_pooler(corpus_jobs, clean_index_dir=free["clean_index_dir"])
    candidates_by_topic = {}
    pool_rows: list[dict] = []
    for topic in topics:
        candidates = pooler.pool_topic(
            topic.topic_id,
            queries_by_topic[topic.topic_id],
            depth=pool_depth,
            max_pool=max_pool,
        )
        candidates_by_topic[topic.topic_id] = candidates
        pool_rows.extend(candidate.to_dict() for candidate in candidates)
    _jsonl_dump(output_dir / "pool.jsonl", pool_rows)

    judge = JudgeClient(judge_model)
    all_qrels = []
    for topic in topics:
        all_qrels.extend(judge_candidates(judge, topic, candidates_by_topic[topic.topic_id], corpus_by_key))
    certain_qrels = [qrel for qrel in all_qrels if not qrel.uncertain]
    uncertain_qrels = [qrel for qrel in all_qrels if qrel.uncertain]
    _jsonl_dump(output_dir / "qrels.silver.jsonl", [qrel.to_dict() for qrel in certain_qrels])
    _jsonl_dump(output_dir / "qrels.uncertain.jsonl", [qrel.to_dict() for qrel in uncertain_qrels])
    controls = build_and_judge_controls(judge, topics, corpus_jobs, queries_by_topic)
    _jsonl_dump(output_dir / "controls.jsonl", [control.to_dict() for control in controls])
    qrels_by_topic = defaultdict(list)
    for qrel in all_qrels:
        qrels_by_topic[qrel.topic_id].append(qrel)
    nuggets = []
    for topic in topics:
        nuggets.extend(build_nuggets_for_topic(judge, topic, qrels_by_topic[topic.topic_id], corpus_by_key))
    _jsonl_dump(output_dir / "nuggets.silver.jsonl", [nugget.to_dict() for nugget in nuggets])
    _json_dump(output_dir / "dev_ids.json", {"family_ids": free["dev_family_ids"], "topic_ids": [topic.topic_id for topic in topics if topic.split == "dev"]})
    _json_dump(output_dir / "test_ids.json", {"family_ids": free["test_family_ids"], "topic_ids": [topic.topic_id for topic in topics if topic.split == "test"]})
    audit_report = run_audit(
        topics=topics,
        pool=[candidate for candidates in candidates_by_topic.values() for candidate in candidates],
        qrels=all_qrels,
        nuggets=nuggets,
        controls=[control.to_dict() for control in controls],
    )
    _json_dump(reports_dir / "build_audit.json", audit_report)
    assert_audit_passes(audit_report)

    builder_tree_sha, git_sha, git_dirty = _source_sha()
    prompt_sha = sha256_tree([Path(__file__).resolve().parent / name for name in ("judges.py", "nuggets.py", "semantics.py", "evidence.py")])
    judge_prompt_sha = prompt_sha
    generator_model = os.environ.get("CAREER_RAG_GENERATOR_MODEL", DEFAULT_ANSWER_MODEL)
    manifest = BenchmarkManifest(
        benchmark_name=BENCHMARK_NAME, benchmark_version=BENCHMARK_VERSION, random_seed=seed,
        dataset_sha256=free["dataset_sha"], corpus_manifest_sha256=sha256_file(output_dir / "corpus_manifest.json"),
        topics_sha256=sha256_file(output_dir / "topics.jsonl"), queries_sha256=sha256_file(output_dir / "queries.jsonl"),
        pool_sha256=sha256_file(output_dir / "pool.jsonl"), qrels_sha256=sha256_file(output_dir / "qrels.silver.jsonl"),
        nuggets_sha256=sha256_file(output_dir / "nuggets.silver.jsonl"), judge_model=judge_model,
        judge_prompt_sha256=judge_prompt_sha, builder_source_sha256=builder_tree_sha,
        exact_model_id_equal=(judge_model == generator_model),
        dev_family_ids=tuple(free["dev_family_ids"]), test_family_ids=tuple(free["test_family_ids"]),
        configuration={
            "topic_selection_policy": TOPIC_SELECTION_POLICY_VERSION,
            "specific_title_selection": "log1p(local_support)*wilson_lower_bound(local_support/global_support)",
            "specific_title_min_support": DEFAULT_MIN_SPECIFIC_TITLE_JOBS, "specificity_wilson_z": SPECIFICITY_WILSON_Z,
            "canonical_information_need_version": CANONICAL_INFORMATION_NEED_VERSION,
            "base_query_variants": list(BASE_QUERY_VARIANTS), "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "nugget_prompt_version": NUGGET_PROMPT_VERSION, "nugget_importance_policy_version": NUGGET_IMPORTANCE_POLICY_VERSION,
            "importance_evidence_preview_jobs": IMPORTANCE_EVIDENCE_PREVIEW_JOBS, "nugget_weight_policy": NUGGET_WEIGHT_POLICY,
            "nugget_support_semantics": "support_job_keys are verified support examples observed before adaptive stop; they are not an exhaustive support universe",
            "nugget_support_semantics_version": NUGGET_SUPPORT_SEMANTICS_VERSION,
            "prevalence_definition": "unavailable under adaptive verification", "prevalence_policy_version": PREVALENCE_POLICY_VERSION,
            "prevalence_unavailable_sentinel": PREVALENCE_UNAVAILABLE,
            "evidence_packing_policy_version": EVIDENCE_PACKING_POLICY_VERSION, "evidence_char_budget": DEFAULT_EVIDENCE_CHAR_BUDGET,
            "pool_depth": pool_depth, "max_pool": max_pool, "pooling_policy": free["pooling_policy"],
            "rrf_k": 60, "uncertain_rule": "max(judge_grades)-min(judge_grades)>=2", "min_strong_relevant_per_topic": 5,
            "known_skills_policy": "empty-for-base-v3", "embedding_provenance": free["provenance"],
            "generator_model_requested": generator_model,
            "generator_model_reported": None,
            "judge_model_requested": judge_model,
            "judge_model_reported": None,
            "exact_model_id_equal": judge_model == generator_model,
            "exact_model_id_equal_basis": "requested model IDs; runtime-reported IDs unavailable during construction",
            "generator_model_family": None,
            "judge_model_family": None,
            "family_metadata_source": None,
            "family_relation": "UNVERIFIED",
            "relevance_judgment_design": "multi-view consistency judgments from one judge model",
            "qrel_ground_truth_status": "SILVER_LLM_GENERATED_NOT_HUMAN_GOLD",
            "human_calibration_status": "NOT_PERFORMED",
            "embedding_provenance_status": free["provenance"]["status"],
            "clean_embedding_index_type": CLEAN_INDEX_TYPE,
            "clean_embedding_model": CLEAN_EMBEDDING_MODEL,
            "clean_embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
            "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
            "clean_embedding_vectors_sha256": free["provenance"]["vectors_sha256"],
            "clean_embedding_chunk_map_sha256": free["provenance"]["chunk_map_sha256"],
            "clean_embedding_provenance_sha256": sha256_file(free["clean_index_dir"] / "embedding_provenance.json"),
            "clean_embedding_corpus_membership_sha256": free["provenance"]["corpus_membership_sha256"],
            "clean_embedding_chunk_context_sha256": free["provenance"]["chunk_context_sha256"],
            "git_head": git_sha, "git_dirty_at_freeze": git_dirty,
        },
        artifact_sha256=artifact_sha256_map(output_dir),
    )
    manifest_path = output_dir / "benchmark_manifest.json"
    _json_dump(manifest_path, manifest.to_dict())
    _json_dump(output_dir / "test_lock.json", {
        "status": "LOCKED", "immutable": True, "frozen": True,
        "benchmark_name": BENCHMARK_NAME, "benchmark_version": BENCHMARK_VERSION,
        "benchmark_manifest_sha256": sha256_file(manifest_path), "test_ids_sha256": sha256_file(output_dir / "test_ids.json"),
        "policy": "Do not evaluate TEST until DEV retriever/generator/prompt are frozen. A benchmark bug after TEST requires a new benchmark version.",
    })
    verification = verify_frozen_benchmark(output_dir)
    if not verification["passed"]:
        raise RuntimeError("Fresh V3 freeze failed offline verification: " + "; ".join(verification["blockers"]))
    return {"output_dir": str(output_dir), "topics": len(topics), "queries": len(queries), "qrels": len(certain_qrels), "uncertain_qrels": len(uncertain_qrels), "nuggets": len(nuggets), "audit": audit_report, "verification": verification}


def build_benchmark(*, output_dir: Path = DEFAULT_OUTPUT_DIR, judge_model: str, seed: int = DEFAULT_RANDOM_SEED, pool_depth: int = 20, max_pool: int = 80) -> dict:
    """Build in a sibling candidate and atomically publish one immutable V3."""

    output_dir = Path(output_dir)
    _assert_final_output_available(output_dir)
    candidate = _create_building_directory(output_dir)
    try:
        result = _build_benchmark_into(candidate, judge_model=judge_model, seed=seed, pool_depth=pool_depth, max_pool=max_pool)
        _finalize_candidate(candidate, output_dir)
        result["output_dir"] = str(output_dir)
        return result
    except Exception:
        if candidate.exists():
            shutil.rmtree(candidate)
        raise
