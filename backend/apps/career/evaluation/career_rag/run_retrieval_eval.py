from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from .build_benchmark import DEFAULT_OUTPUT_DIR
from .metrics import (
    bootstrap_ci,
    evidence_nugget_recall_at_k,
    macro_topic_metric,
    ndcg_at_k,
    paired_bootstrap,
    strong_precision_at_k,
)
from .pooling import PoolingService, load_corpus_jobs
from .schema import CareerQuery, Nugget


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _guard_test(output_dir: Path, allow_test: bool) -> None:
    if not allow_test:
        raise RuntimeError("TEST is locked. Re-run explicitly with --allow-test only after DEV choices are frozen.")
    marker = output_dir / "reports" / "TEST_ALREADY_RUN.lock"
    if marker.exists():
        raise RuntimeError("TEST has already been run for this frozen benchmark. Refusing a second run.")
    marker.write_text("TEST evaluation consumed.\n", encoding="utf-8")


def run_retrieval_eval(
    *,
    split: str = "dev",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    top_k: int = 10,
    allow_test: bool = False,
    bootstrap_samples: int = 2000,
) -> dict:
    output_dir = Path(output_dir)
    if split not in {"dev", "test"}:
        raise ValueError("split must be 'dev' or 'test'")
    if split == "test":
        _guard_test(output_dir, allow_test)

    topics = {row["topic_id"]: row for row in _read_jsonl(output_dir / "topics.jsonl") if row["split"] == split}
    query_rows = [row for row in _read_jsonl(output_dir / "queries.jsonl") if row["topic_id"] in topics]
    qrel_rows = _read_jsonl(output_dir / "qrels.silver.jsonl")
    nugget_rows = _read_jsonl(output_dir / "nuggets.silver.jsonl")

    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    for row in qrel_rows:
        qrels[row["topic_id"]][f"{row['source']}::{row['source_job_id']}"] = int(row["grade"])

    nuggets: dict[str, list[Nugget]] = defaultdict(list)
    for row in nugget_rows:
        nuggets[row["topic_id"]].append(
            Nugget(
                topic_id=row["topic_id"],
                nugget_id=row["nugget_id"],
                text=row["text"],
                normalized_text=row["normalized_text"],
                support_job_keys=tuple(row["support_job_keys"]),
                support_count=int(row["support_count"]),
                prevalence=float(row["prevalence"]),
                weight=float(row["weight"]),
                importance=row["importance"],
            )
        )

    corpus = load_corpus_jobs()
    pooler = PoolingService(corpus)
    systems = ("bm25", "dense", "hybrid")
    result_rows: dict[str, list[dict]] = {system: [] for system in systems}

    for row in query_rows:
        query = row["text"]
        depth = max(top_k, 10)
        bm25 = pooler.bm25(query, depth)
        dense = pooler.dense(query, depth)
        hybrid = pooler.rrf([bm25, dense], depth)
        rankings = {"bm25": bm25, "dense": dense, "hybrid": hybrid}
        topic_id = row["topic_id"]
        for system, ranking in rankings.items():
            result_rows[system].append(
                {
                    "query_id": row["query_id"],
                    "topic_id": topic_id,
                    "variant": row["variant"],
                    "ranking": ranking[:top_k],
                    "ndcg@5": ndcg_at_k(ranking, qrels[topic_id], 5),
                    "ndcg@10": ndcg_at_k(ranking, qrels[topic_id], 10),
                    "strong_precision@5": strong_precision_at_k(ranking, qrels[topic_id], 5),
                    "strong_precision@10": strong_precision_at_k(ranking, qrels[topic_id], 10),
                    "nugget_recall@5": evidence_nugget_recall_at_k(ranking, nuggets[topic_id], 5),
                    "nugget_recall@10": evidence_nugget_recall_at_k(ranking, nuggets[topic_id], 10),
                    "context_precision@5": strong_precision_at_k(ranking, qrels[topic_id], 5),
                    "context_precision@10": strong_precision_at_k(ranking, qrels[topic_id], 10),
                }
            )

    report: dict = {"split": split, "systems": {}, "paired": {}}
    metric_names = (
        "ndcg@5", "ndcg@10", "strong_precision@5", "strong_precision@10",
        "nugget_recall@5", "nugget_recall@10", "context_precision@5", "context_precision@10",
    )
    topic_metric_cache: dict[tuple[str, str], dict[str, float]] = {}
    for system in systems:
        system_report = {"queries": result_rows[system], "macro": {}, "robustness": {}}
        for metric in metric_names:
            macro, topic_means, topic_summary = macro_topic_metric(result_rows[system], metric)
            ci = bootstrap_ci(topic_means, samples=bootstrap_samples)
            system_report["macro"][metric] = {"mean": macro, "ci95": list(ci)}
            if metric in {"ndcg@5", "nugget_recall@10"}:
                system_report["robustness"][metric] = topic_summary
            for topic_id, summary in topic_summary.items():
                topic_metric_cache[(system, metric, topic_id)] = summary
        report["systems"][system] = system_report

    for left, right in (("dense", "bm25"), ("hybrid", "dense")):
        comparison = {}
        for metric in ("ndcg@5", "ndcg@10", "nugget_recall@10"):
            deltas = []
            for topic_id in topics:
                a = topic_metric_cache[(left, metric, topic_id)]["mean"]
                b = topic_metric_cache[(right, metric, topic_id)]["mean"]
                deltas.append(a - b)
            comparison[metric] = paired_bootstrap(deltas, samples=bootstrap_samples)
        report["paired"][f"{left}_minus_{right}"] = comparison

    report_path = output_dir / "reports" / f"retrieval_{split}.json"
    _write_json(report_path, report)
    return report
