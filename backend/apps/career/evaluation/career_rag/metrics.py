from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean
from typing import Callable, Iterable

from .schema import Nugget


def dcg(grades: list[int]) -> float:
    return sum(((2**grade) - 1) / math.log2(index + 2) for index, grade in enumerate(grades))


def ndcg_at_k(ranked_job_keys: list[str], qrels: dict[str, int], k: int) -> float:
    gains = [qrels.get(key, 0) for key in ranked_job_keys[:k]]
    actual = dcg(gains)
    ideal = dcg(sorted(qrels.values(), reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0


def strong_precision_at_k(ranked_job_keys: list[str], qrels: dict[str, int], k: int) -> float:
    top = ranked_job_keys[:k]
    if not top:
        return 0.0
    return sum(1 for key in top if qrels.get(key, 0) >= 2) / len(top)


def evidence_nugget_recall_at_k(ranked_job_keys: list[str], nuggets: list[Nugget], k: int) -> float:
    if not nuggets:
        return 0.0
    selected = set(ranked_job_keys[:k])
    total_weight = sum(nugget.weight for nugget in nuggets)
    covered = sum(
        nugget.weight for nugget in nuggets if selected.intersection(nugget.support_job_keys)
    )
    return covered / total_weight if total_weight > 0 else 0.0


def weighted_nugget_scores(matched_ids: set[str], predicted_supported_claims: int, nuggets: list[Nugget]) -> dict[str, float]:
    weights = {nugget.nugget_id: nugget.weight for nugget in nuggets}
    matched_weight = sum(weights.get(nugget_id, 0.0) for nugget_id in matched_ids)
    total_weight = sum(weights.values())
    recall = matched_weight / total_weight if total_weight else 0.0
    precision_denominator = matched_weight + max(0, predicted_supported_claims - len(matched_ids))
    precision = matched_weight / precision_denominator if precision_denominator else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def robustness(scores: list[float]) -> dict[str, float]:
    if not scores:
        return {"mean": 0.0, "worst": 0.0, "best": 0.0, "gap": 0.0}
    best = max(scores)
    worst = min(scores)
    return {"mean": mean(scores), "worst": worst, "best": best, "gap": best - worst}


def bootstrap_ci(values: list[float], *, samples: int = 2000, seed: int = 20260819, alpha: float = 0.05) -> tuple[float, float]:
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    boot = []
    n = len(values)
    for _ in range(samples):
        boot.append(mean(values[rng.randrange(n)] for _ in range(n)))
    boot.sort()
    low_index = max(0, int((alpha / 2) * samples))
    high_index = min(samples - 1, int((1 - alpha / 2) * samples) - 1)
    return boot[low_index], boot[high_index]


def paired_bootstrap(deltas: list[float], *, samples: int = 2000, seed: int = 20260819) -> dict[str, float | list[float]]:
    low, high = bootstrap_ci(deltas, samples=samples, seed=seed)
    return {"mean_delta": mean(deltas) if deltas else 0.0, "ci95": [low, high]}


def macro_topic_metric(query_rows: list[dict], metric_name: str) -> tuple[float, list[float], dict[str, dict[str, float]]]:
    by_topic: dict[str, list[float]] = defaultdict(list)
    for row in query_rows:
        by_topic[row["topic_id"]].append(float(row[metric_name]))
    topic_summary = {topic_id: robustness(values) for topic_id, values in by_topic.items()}
    topic_means = [summary["mean"] for summary in topic_summary.values()]
    return (mean(topic_means) if topic_means else 0.0, topic_means, topic_summary)
