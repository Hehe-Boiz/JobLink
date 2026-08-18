from __future__ import annotations

import math
from collections.abc import Sequence


def recall_at_k(ranked_doc_ids: Sequence[str], relevant_doc_ids: set[str], k: int) -> float:
    if not relevant_doc_ids:
        return 0.0

    retrieved = set(ranked_doc_ids[:k])
    hits = len(retrieved & relevant_doc_ids)
    return hits / len(relevant_doc_ids)


def reciprocal_rank_at_k(ranked_doc_ids: Sequence[str], relevant_doc_ids: set[str], k: int) -> float:
    for rank, doc_id in enumerate(ranked_doc_ids[:k], start=1):
        if doc_id in relevant_doc_ids:
            return 1.0 / rank

    return 0.0


def ndcg_at_k(ranked_doc_ids: Sequence[str], relevant_doc_ids: set[str], k: int) -> float:
    if not relevant_doc_ids:
        return 0.0

    dcg = 0.0

    for rank, doc_id in enumerate(ranked_doc_ids[:k], start=1,):
        if doc_id in relevant_doc_ids:
            dcg += 1.0 / math.log2(rank + 1)

    ideal_hits = min(len(relevant_doc_ids), k)
    idcg = sum(
        1.0 / math.log2(rank + 1)
        for rank in range(1, ideal_hits + 1)
    )

    if idcg == 0.0:
        return 0.0

    return dcg / idcg


def evaluate_ranking(ranked_doc_ids: Sequence[str], relevant_doc_ids: set[str]) -> dict[str, float]:
    return {
        "recall@5": recall_at_k(ranked_doc_ids, relevant_doc_ids, 5),
        "recall@10": recall_at_k(ranked_doc_ids, relevant_doc_ids, 10),
        "recall@20": recall_at_k(ranked_doc_ids, relevant_doc_ids, 20),
        "mrr@10": reciprocal_rank_at_k(ranked_doc_ids, relevant_doc_ids, 10),
        "ndcg@10": ndcg_at_k(ranked_doc_ids, relevant_doc_ids, 10),
    }


def mean_metrics(results: Sequence[dict[str, float]]) -> dict[str, float]:
    if not results:
        return {}

    metric_names = results[0].keys()
    return {
        metric: sum(
            result[metric]
            for result in results
        )/ len(results)
        for metric in metric_names
    }