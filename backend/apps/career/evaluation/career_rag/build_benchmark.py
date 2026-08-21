from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
from collections import defaultdict
from pathlib import Path

from django.conf import settings
from django.db import connection

from apps.career.answering import DEFAULT_ANSWER_MODEL
from apps.career.sources.vietjobs import VietJobsSource

from .audit import audit_derived_label_leakage, assert_audit_passes, run_audit, sha256_file, sha256_text, sha256_tree
from .judges import JUDGE_PROMPT_VERSION, JudgeClient, build_and_judge_controls, judge_candidates
from .nuggets import DEFAULT_VITAL_PREVALENCE, NUGGET_PROMPT_VERSION, build_nuggets_for_topic
from .pooling import PoolingService, load_corpus_jobs
from .schema import BenchmarkManifest, CareerQuery, CareerTopic, Nugget, RelevanceJudgment
from .topics import (
    DEFAULT_MIN_SPECIFIC_TITLE_JOBS,
    DEFAULT_RANDOM_SEED,
    SPECIFICITY_WILSON_Z,
    TOPIC_SELECTION_POLICY_VERSION,
    discover_topics,
    load_skill_hints_from_csv,
)

BACKEND_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "career_rag_bench_auto_v2"
BENCHMARK_NAME = "CareerRAGBench-Auto-V2"
BENCHMARK_VERSION = "2.0"


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
    table = "career_careerjobchunk"
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT indexdef FROM pg_indexes WHERE tablename = %s ORDER BY indexname",
            [table],
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


def build_benchmark(
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    judge_model: str,
    seed: int = DEFAULT_RANDOM_SEED,
    pool_depth: int = 20,
    max_pool: int = 80,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = output_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    if not getattr(settings, "CKEY_API_KEY", ""):
        raise RuntimeError("CKEY_API_KEY is not configured; silver benchmark construction requires an LLM judge.")

    csv_path = _find_vietjobs_csv()
    dataset_sha = sha256_file(csv_path)
    from apps.career.models import CareerJobChunk

    # -----------------------------------------------------
    # CareerRAGBench-Auto-V2 freezes the ACTUAL indexed
    # VietJobs retrieval corpus.
    #
    # Historical audit:
    #
    #   source rows                  48,092
    #   indexed DB jobs             47,097
    #   indexed chunks             152,379
    #   source rows absent from DB      995
    #   DB-only source IDs                0
    #
    # The surviving historical code does not reproduce the
    # exact 995-row selection membership perfectly.
    #
    # Therefore we do NOT mislabel all 995 as
    # "exact duplicates".
    #
    # Corpus identity is frozen by:
    #
    #   dataset SHA256
    #   indexed source_job_id membership SHA256
    #   indexed chunk/context SHA256
    #   embedding/chunk/index configuration
    # -----------------------------------------------------

    source_records = list(
        VietJobsSource(
            dataset_dir=csv_path.parent
        ).iter_records()
    )

    raw_rows = len(source_records)

    source_ids = {
        record.source_job_id
        for record in source_records
    }

    if len(source_ids) != raw_rows:
        raise RuntimeError(
            "VietJobsSource produced duplicate "
            "source_job_id values."
        )

    if raw_rows != 48_092:
        raise RuntimeError(
            "Frozen source corpus drift detected. "
            "Expected 48,092 VietJobs source records, "
            f"got {raw_rows:,}."
        )

    corpus_jobs = load_corpus_jobs(
        source="vietjobs"
    )

    if not corpus_jobs:
        raise RuntimeError(
            "CareerJobChunk contains no active VietJobs "
            "corpus. Index the corpus before building "
            "the benchmark."
        )

    corpus_by_key = {
        job.job_key: job
        for job in corpus_jobs
    }

    db_job_ids = {
        job.source_job_id
        for job in corpus_jobs
    }

    db_unique_jobs = len(db_job_ids)

    source_rows_not_indexed = (
        source_ids - db_job_ids
    )

    db_only_source_ids = (
        db_job_ids - source_ids
    )

    # -----------------------------------------------------
    # Leakage must fail BEFORE pools / LLM judging.
    # -----------------------------------------------------

    leakage_preflight = (
        audit_derived_label_leakage()
    )

    if not leakage_preflight["passed"]:
        _json_dump(
            reports_dir
            / "preflight_leakage.json",
            leakage_preflight,
        )

        raise RuntimeError(
            "Derived-label leakage detected in "
            "CareerJobChunk.metadata. "
            "Do not build silver qrels until "
            "technical_skills/soft_skills leakage "
            "is removed."
        )

    if db_only_source_ids:
        raise RuntimeError(
            "Frozen DB contains VietJobs source_job_id "
            "values absent from the frozen CSV. "
            f"DB-only count={len(db_only_source_ids):,}"
        )

    # -----------------------------------------------------
    # Freeze chunk/context identity.
    # Include fields that affect retrieval/context.
    # -----------------------------------------------------

    chunk_queryset = (
        CareerJobChunk.objects
        .filter(
            active=True,
            source="vietjobs",
        )
        .order_by(
            "source_job_id",
            "chunk_index",
            "chunk_id",
        )
        .values_list(
            "source_job_id",
            "chunk_id",
            "chunk_index",
            "job_title",
            "section",
            "content",
            "location_key",
            "experience_level",
            "employment_type",
            "category_key",
        )
    )

    db_chunk_count = (
        chunk_queryset.count()
    )

    if (
        db_unique_jobs != 47_097
        or db_chunk_count != 152_379
    ):
        raise RuntimeError(
            "Frozen corpus drift detected. "
            "Expected 47,097 indexed VietJobs jobs "
            "and 152,379 active chunks; got "
            f"{db_unique_jobs:,} jobs and "
            f"{db_chunk_count:,} chunks."
        )

    corpus_membership_sha256 = (
        sha256_text(
            "\n".join(
                sorted(db_job_ids)
            )
        )
    )

    chunk_hasher = hashlib.sha256()

    for (
        source_job_id,
        chunk_id,
        chunk_index,
        job_title,
        section,
        content,
        location_key,
        experience_level,
        employment_type,
        category_key,
    ) in chunk_queryset.iterator(
        chunk_size=4000
    ):
        payload = json.dumps(
            {
                "source_job_id": (
                    source_job_id
                ),
                "chunk_id": chunk_id,
                "chunk_index": (
                    chunk_index
                ),
                "job_title": job_title,
                "section": section,
                "content": content,
                "location_key": (
                    location_key
                ),
                "experience_level": (
                    experience_level
                ),
                "employment_type": (
                    employment_type
                ),
                "category_key": (
                    category_key
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        chunk_hasher.update(
            payload.encode("utf-8")
        )

        chunk_hasher.update(
            b"\n"
        )

    corpus_chunks_sha256 = (
        chunk_hasher.hexdigest()
    )

    print()
    print(
        "========== FROZEN CORPUS =========="
    )
    print(
        f"Raw source rows       : "
        f"{raw_rows:,}"
    )
    print(
        f"Indexed jobs          : "
        f"{db_unique_jobs:,}"
    )
    print(
        f"Source rows not in DB : "
        f"{len(source_rows_not_indexed):,}"
    )
    print(
        f"DB-only source IDs    : "
        f"{len(db_only_source_ids):,}"
    )
    print(
        f"Indexed chunks        : "
        f"{db_chunk_count:,}"
    )
    print(
        "Membership SHA256     : "
        f"{corpus_membership_sha256}"
    )
    print(
        "Chunks SHA256         : "
        f"{corpus_chunks_sha256}"
    )
    print(
        "==================================="
    )
    print()

    category_hints, title_hints = load_skill_hints_from_csv(csv_path)
    topics, queries, dev_family_ids, test_family_ids = discover_topics(
        corpus_jobs,
        random_seed=seed,
        category_skill_hints=category_hints,
        title_skill_hints=title_hints,
    )
    queries_by_topic: dict[str, list[CareerQuery]] = defaultdict(list)
    for query in queries:
        queries_by_topic[query.topic_id].append(query)

    corpus_manifest = {
        "benchmark": BENCHMARK_NAME,
        "dataset_filename": csv_path.name,
        "dataset_path": str(csv_path.relative_to(BACKEND_ROOT)),
        "dataset_sha256": dataset_sha,
        "raw_row_count": raw_rows,
        "db_unique_job_count": db_unique_jobs,
        "source_rows_not_indexed": (
            len(source_rows_not_indexed)
        ),
        "db_only_source_id_count": (
            len(db_only_source_ids)
        ),
        "db_chunk_count": db_chunk_count,
        "corpus_identity_policy": (
            "frozen-index-membership-v1"
        ),
        "historical_selection_reconstructible": False,
        "corpus_membership_sha256": (
            corpus_membership_sha256
        ),
        "corpus_chunks_sha256": (
            corpus_chunks_sha256
        ),
        "corpus_identity_note": (
            "48,092 VietJobs source records map to "
            "the frozen production retrieval corpus "
            "of 47,097 indexed jobs and 152,379 "
            "active chunks. The exact historical "
            "filtering/dedup membership is not "
            "perfectly reconstructible from surviving "
            "code; CareerRAGBench-Auto-V2 therefore "
            "defines corpus identity using the dataset "
            "SHA256 plus frozen indexed source_job_id "
            "membership and chunk/context hashes."
        ),
        "embedding_model": "intfloat/multilingual-e5-small",
        "embedding_dimension": 384,
        "chunking": {
            "target_tokens": 220,
            "max_tokens": 480,
            "forced_split_overlap_tokens": 40,
            "chunking_source_sha256": sha256_file(BACKEND_ROOT / "apps" / "career" / "chunking.py"),
        },
        "index_configuration": _index_configuration(),
        "forbidden_derived_metadata_keys": ["technical_skills", "soft_skills", "gold_nuggets", "judge_labels", "derived_role_labels"],
    }
    corpus_manifest_path = output_dir / "corpus_manifest.json"
    _json_dump(corpus_manifest_path, corpus_manifest)

    topics_path = output_dir / "topics.jsonl"
    queries_path = output_dir / "queries.jsonl"
    _jsonl_dump(topics_path, [topic.to_dict() for topic in topics])
    _jsonl_dump(queries_path, [query.to_dict() for query in queries])

    pooler = PoolingService(corpus_jobs)
    pool_rows = []
    candidates_by_topic = {}
    for topic in topics:
        candidates = pooler.pool_topic(topic.topic_id, queries_by_topic[topic.topic_id], depth=pool_depth, max_pool=max_pool)
        candidates_by_topic[topic.topic_id] = candidates
        pool_rows.extend(candidate.to_dict() for candidate in candidates)
    pool_path = output_dir / "pool.jsonl"
    _jsonl_dump(pool_path, pool_rows)

    judge = JudgeClient(judge_model)
    all_qrels: list[RelevanceJudgment] = []
    for topic in topics:
        all_qrels.extend(judge_candidates(judge, topic, candidates_by_topic[topic.topic_id], corpus_by_key))

    certain_qrels = [qrel for qrel in all_qrels if not qrel.uncertain]
    uncertain_qrels = [qrel for qrel in all_qrels if qrel.uncertain]
    qrels_path = output_dir / "qrels.silver.jsonl"
    uncertain_path = output_dir / "qrels.uncertain.jsonl"
    _jsonl_dump(qrels_path, [qrel.to_dict() for qrel in certain_qrels])
    _jsonl_dump(uncertain_path, [qrel.to_dict() for qrel in uncertain_qrels])

    controls = build_and_judge_controls(judge, topics, corpus_jobs, queries_by_topic)
    controls_rows = [control.to_dict() for control in controls]
    _jsonl_dump(output_dir / "controls.jsonl", controls_rows)

    nuggets: list[Nugget] = []
    qrels_by_topic: dict[str, list[RelevanceJudgment]] = defaultdict(list)
    for qrel in all_qrels:
        qrels_by_topic[qrel.topic_id].append(qrel)
    for topic in topics:
        nuggets.extend(build_nuggets_for_topic(judge, topic, qrels_by_topic[topic.topic_id], corpus_by_key))
    nuggets_path = output_dir / "nuggets.silver.jsonl"
    _jsonl_dump(nuggets_path, [nugget.to_dict() for nugget in nuggets])

    _json_dump(output_dir / "dev_ids.json", {"family_ids": dev_family_ids, "topic_ids": [t.topic_id for t in topics if t.split == "dev"]})
    _json_dump(output_dir / "test_ids.json", {"family_ids": test_family_ids, "topic_ids": [t.topic_id for t in topics if t.split == "test"]})

    audit_report = run_audit(topics=topics, qrels=all_qrels, nuggets=nuggets, controls=controls_rows)
    _json_dump(reports_dir / "build_audit.json", audit_report)
    assert_audit_passes(audit_report)

    builder_tree_sha, git_sha, git_dirty = _source_sha()
    prompt_sha = sha256_tree(
        [
            (
                Path(__file__).resolve().parent
                / "judges.py"
            ),
            (
                Path(__file__).resolve().parent
                / "nuggets.py"
            ),
            (
                Path(__file__).resolve().parent
                / "semantics.py"
            ),
        ]
    )
    generator_model = os.environ.get("CAREER_RAG_GENERATOR_MODEL", DEFAULT_ANSWER_MODEL)
    manifest = BenchmarkManifest(
        benchmark_name=BENCHMARK_NAME,
        benchmark_version=BENCHMARK_VERSION,
        random_seed=seed,
        dataset_sha256=dataset_sha,
        corpus_manifest_sha256=sha256_file(corpus_manifest_path),
        topics_sha256=sha256_file(topics_path),
        queries_sha256=sha256_file(queries_path),
        pool_sha256=sha256_file(pool_path),
        qrels_sha256=sha256_file(qrels_path),
        nuggets_sha256=sha256_file(nuggets_path),
        judge_model=judge_model,
        judge_prompt_sha256=prompt_sha,
        builder_source_sha256=builder_tree_sha,
        judge_model_same_as_generator=(judge_model == generator_model),
        dev_family_ids=tuple(dev_family_ids),
        test_family_ids=tuple(test_family_ids),
        configuration={
            "topic_selection_policy": (
                TOPIC_SELECTION_POLICY_VERSION
            ),
            "specific_title_selection": (
                "log1p(local_support)"
                "*wilson_lower_bound("
                "local_support/global_support)"
            ),
            "specific_title_min_support": (
                DEFAULT_MIN_SPECIFIC_TITLE_JOBS
            ),
            "specificity_wilson_z": (
                SPECIFICITY_WILSON_Z
            ),
            "judge_prompt_version": (
                JUDGE_PROMPT_VERSION
            ),
            "nugget_prompt_version": (
                NUGGET_PROMPT_VERSION
            ),
            "pool_depth": pool_depth,
            "max_pool": max_pool,
            "rrf_k": 60,
            "uncertain_rule": "max(judge_grades)-min(judge_grades)>=2",
            "min_strong_relevant_per_topic": 5,
            "vital_prevalence_threshold": DEFAULT_VITAL_PREVALENCE,
            "git_head": git_sha,
            "git_dirty_at_freeze": git_dirty,
        },
    )
    manifest_path = output_dir / "benchmark_manifest.json"
    _json_dump(manifest_path, manifest.to_dict())
    _json_dump(
        output_dir / "test_lock.json",
        {
            "status": "LOCKED",
            "benchmark_manifest_sha256": sha256_file(manifest_path),
            "test_ids_sha256": sha256_file(output_dir / "test_ids.json"),
            "policy": "Do not evaluate TEST until DEV retriever/generator/prompt are frozen. A benchmark bug after TEST requires a new benchmark version.",
        },
    )
    return {"output_dir": str(output_dir), "topics": len(topics), "queries": len(queries), "qrels": len(certain_qrels), "uncertain_qrels": len(uncertain_qrels), "nuggets": len(nuggets), "audit": audit_report}
