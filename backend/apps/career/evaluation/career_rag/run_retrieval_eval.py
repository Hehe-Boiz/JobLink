from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .build_benchmark import DEFAULT_OUTPUT_DIR
from .clean_index import CleanBenchmarkDenseRanker, configured_clean_index_dir
from .evaluation_integrity import assert_evaluation_integrity, consume_test_lock
from .evaluation_protocol import (
    PAIRED_SIGN_FLIP_POLICY_VERSION,
    assert_test_evaluation_protocol,
    retrieval_runtime_settings,
)
from .metrics import (
    UNCERTAIN_CONDENSING_POLICY_VERSION,
    condense_uncertain_ranking,
    family_cluster_bootstrap_ci,
    family_cluster_paired_bootstrap,
    macro_topic_metric,
    ndcg_at_k,
    observed_support_coverage_at_k,
    paired_family_sign_flip_test,
    strong_precision_at_k,
)
from .pooling import PoolingService, load_corpus_jobs
from .schema import Nugget


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


def _load_qrels(output_dir: Path) -> tuple[dict[str, dict[str, int]], dict[str, set[str]]]:
    certain: dict[str, dict[str, int]] = defaultdict(dict)
    uncertain: dict[str, set[str]] = defaultdict(set)
    for row in _read_jsonl(output_dir / "qrels.silver.jsonl"):
        key = f"{row['source']}::{row['source_job_id']}"
        if key in certain[row["topic_id"]]:
            raise ValueError(f"Duplicate certain qrel for {row['topic_id']}/{key}")
        if type(row.get("grade")) is not int or row["grade"] not in {0, 1, 2, 3}:
            raise ValueError(f"Invalid certain qrel grade for {row['topic_id']}/{key}")
        certain[row["topic_id"]][key] = row["grade"]
    for row in _read_jsonl(output_dir / "qrels.uncertain.jsonl"):
        key = f"{row['source']}::{row['source_job_id']}"
        if key in uncertain[row["topic_id"]]:
            raise ValueError(f"Duplicate uncertain qrel for {row['topic_id']}/{key}")
        uncertain[row["topic_id"]].add(key)
    overlap = {
        topic_id: sorted(set(certain[topic_id]).intersection(keys))
        for topic_id, keys in uncertain.items()
        if set(certain[topic_id]).intersection(keys)
    }
    if overlap:
        raise ValueError(f"A qrel cannot be both certain and uncertain: {overlap}")
    return certain, uncertain


def _metric_ranking(
    ranking: list[str],
    *,
    qrels: dict[str, int],
    uncertain: set[str],
    k: int,
) -> dict:
    return condense_uncertain_ranking(
        ranking,
        certain_qrels=qrels,
        uncertain_job_keys=uncertain,
        k=k,
    )


def run_retrieval_eval(
    *,
    split: str = "dev",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    top_k: int = 10,
    allow_test: bool = False,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 20260819,
    bootstrap_alpha: float = 0.05,
    clean_index_dir: Path | None = None,
) -> dict:
    output_dir = Path(output_dir)
    if split not in {"dev", "test"}:
        raise ValueError("split must be 'dev' or 'test'")
    if top_k < 10:
        raise ValueError("V3 retrieval evaluation requires top_k >= 10 for its frozen @5/@10 metrics")

    # Must precede model creation and one-shot TEST consumption.
    integrity = assert_evaluation_integrity(output_dir, clean_index_dir=clean_index_dir)
    if split == "test":
        test_protocol = assert_test_evaluation_protocol(
            output_dir,
            evaluator="RETRIEVAL",
            runtime_settings=retrieval_runtime_settings(
                top_k=top_k,
                bootstrap_seed=bootstrap_seed,
                bootstrap_samples=bootstrap_samples,
                bootstrap_alpha=bootstrap_alpha,
            ),
        )
        consume_test_lock(output_dir, evaluator="RETRIEVAL", allow_test=allow_test)
    else:
        test_protocol = None

    topics = {row["topic_id"]: row for row in _read_jsonl(output_dir / "topics.jsonl") if row["split"] == split}
    topic_family_ids = {topic_id: row["family_id"] for topic_id, row in topics.items()}
    query_rows = [row for row in _read_jsonl(output_dir / "queries.jsonl") if row["topic_id"] in topics]
    qrels, uncertain = _load_qrels(output_dir)
    nugget_rows = _read_jsonl(output_dir / "nuggets.silver.jsonl")

    nuggets: dict[str, list[Nugget]] = defaultdict(list)
    for row in nugget_rows:
        nuggets[row["topic_id"]].append(
            Nugget(
                topic_id=row["topic_id"], nugget_id=row["nugget_id"], text=row["text"],
                normalized_text=row["normalized_text"], support_job_keys=tuple(row["support_job_keys"]),
                support_count=int(row["support_count"]), prevalence=float(row["prevalence"]),
                weight=float(row["weight"]), importance=row["importance"],
            )
        )

    corpus = load_corpus_jobs(source="vietjobs")
    sidecar_dir = Path(clean_index_dir or configured_clean_index_dir())
    clean_ranker = CleanBenchmarkDenseRanker(sidecar_dir)
    pooler = PoolingService(corpus, dense_ranker=clean_ranker)
    systems = ("bm25", "clean_dense", "title", "hybrid")
    result_rows: dict[str, list[dict]] = {system: [] for system in systems}

    # Retrieve deeply enough to condense uncertain rows.  Unknown rows before
    # K certain qrels are a hard error, never a synthetic grade zero.
    retrieval_depth = max(top_k * 20, 200)
    for row in query_rows:
        query = row["text"]
        bm25 = pooler.bm25(query, retrieval_depth)
        dense = pooler.dense(query, retrieval_depth)
        title = pooler.title_lexical(query, retrieval_depth)
        # Construction freezes RRF over the independently judged top-20
        # BM25/dense lists. Extending RRF here could introduce an unpooled job.
        hybrid = pooler.rrf([bm25[:20], dense[:20]], 40)
        rankings = {"bm25": bm25, "clean_dense": dense, "title": title, "hybrid": hybrid}
        topic_id = row["topic_id"]
        metric5 = {
            system: _metric_ranking(ranking, qrels=qrels[topic_id], uncertain=uncertain[topic_id], k=5)
            for system, ranking in rankings.items()
        }
        metric10 = {
            system: _metric_ranking(ranking, qrels=qrels[topic_id], uncertain=uncertain[topic_id], k=10)
            for system, ranking in rankings.items()
        }
        for system in systems:
            rank5, rank10 = metric5[system], metric10[system]
            result_rows[system].append(
                {
                    "query_id": row["query_id"], "topic_id": topic_id, "variant": row["variant"],
                    "ranking": rank10["ranking"][:top_k],
                    "uncertain_skipped@5": rank5["uncertain_skipped"],
                    "uncertain_skipped@10": rank10["uncertain_skipped"],
                    "judged_fraction@5": rank5["judged_fraction"],
                    "judged_fraction@10": rank10["judged_fraction"],
                    "certain_fraction@5": rank5["certain_fraction"],
                    "certain_fraction@10": rank10["certain_fraction"],
                    "ndcg@5": ndcg_at_k(rank5["ranking"], qrels[topic_id], 5),
                    "ndcg@10": ndcg_at_k(rank10["ranking"], qrels[topic_id], 10),
                    "strong_precision@5": strong_precision_at_k(rank5["ranking"], qrels[topic_id], 5),
                    "strong_precision@10": strong_precision_at_k(rank10["ranking"], qrels[topic_id], 10),
                    "observed_support_coverage@5": observed_support_coverage_at_k(rank5["ranking"], nuggets[topic_id], 5),
                    "observed_support_coverage@10": observed_support_coverage_at_k(rank10["ranking"], nuggets[topic_id], 10),
                }
            )

    report: dict = {
        "split": split, "systems": {}, "paired": {},
        "qrel_policy": UNCERTAIN_CONDENSING_POLICY_VERSION,
        "bootstrap_unit": "family", "bootstrap_seed": bootstrap_seed,
        "bootstrap_samples": bootstrap_samples, "clean_index_dir": str(sidecar_dir),
        "bootstrap_alpha": bootstrap_alpha,
        "sign_flip_policy_version": PAIRED_SIGN_FLIP_POLICY_VERSION,
        "frozen_test_protocol": test_protocol,
        "family_count": len(set(topic_family_ids.values())),
        "integrity": integrity,
        "qrel_ground_truth_status": "SILVER_LLM_GENERATED_NOT_HUMAN_GOLD",
        "human_calibration_status": "NOT_PERFORMED",
        "observed_support_coverage_note": (
            "Lower-biased diagnostic coverage of adaptively verified support examples; "
            "it is not exhaustive nugget recall and is not a headline retrieval metric."
        ),
        "headline_metrics": ["ndcg@5", "ndcg@10", "strong_precision@5", "strong_precision@10"],
        "diagnostic_metrics": ["observed_support_coverage@5", "observed_support_coverage@10"],
    }
    headline_metrics = tuple(report["headline_metrics"])
    diagnostic_metrics = tuple(report["diagnostic_metrics"])
    metric_names = headline_metrics + diagnostic_metrics
    topic_metric_cache: dict[tuple[str, str, str], dict[str, float]] = {}
    for system in systems:
        system_report = {
            "queries": result_rows[system],
            "macro": {},
            "diagnostics": {},
            "robustness": {},
        }
        for metric in metric_names:
            macro, _, topic_summary = macro_topic_metric(result_rows[system], metric)
            topic_values = {topic_id: summary["mean"] for topic_id, summary in topic_summary.items()}
            ci = family_cluster_bootstrap_ci(
                topic_values, topic_family_ids, samples=bootstrap_samples, seed=bootstrap_seed,
                alpha=bootstrap_alpha,
            )
            destination = (
                system_report["macro"]
                if metric in headline_metrics
                else system_report["diagnostics"]
            )
            destination[metric] = {
                "mean": macro,
                "ci": list(ci),
                "alpha": bootstrap_alpha,
                "bootstrap_unit": "family",
            }
            if metric in {"ndcg@5", "observed_support_coverage@10"}:
                system_report["robustness"][metric] = topic_summary
            for topic_id, summary in topic_summary.items():
                topic_metric_cache[(system, metric, topic_id)] = summary
        report["systems"][system] = system_report

    for left, right in (("clean_dense", "bm25"), ("hybrid", "clean_dense")):
        comparison = {}
        for metric in ("ndcg@5", "ndcg@10", "strong_precision@5", "strong_precision@10"):
            deltas = {
                topic_id: topic_metric_cache[(left, metric, topic_id)]["mean"]
                - topic_metric_cache[(right, metric, topic_id)]["mean"]
                for topic_id in topics
            }
            comparison[metric] = family_cluster_paired_bootstrap(
                deltas, topic_family_ids, samples=bootstrap_samples, seed=bootstrap_seed,
                alpha=bootstrap_alpha,
            )
            comparison[metric].update(
                paired_family_sign_flip_test(
                    deltas,
                    topic_family_ids,
                    seed=bootstrap_seed,
                )
            )
            comparison[metric]["interpretation"] = (
                "The p-value tests a paired family-level null; practical significance "
                "must be assessed from the mean family delta and confidence interval."
            )
        report["paired"][f"{left}_minus_{right}"] = comparison

    _write_json(output_dir / "reports" / f"retrieval_{split}.json", report)
    return report
