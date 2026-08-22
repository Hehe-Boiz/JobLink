from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean

from .schema import Nugget

UNCERTAIN_CONDENSING_POLICY_VERSION = "condense-uncertain-v1"


def dcg(grades: list[int]) -> float:
    return sum(((2**grade) - 1) / math.log2(index + 2) for index, grade in enumerate(grades))


def _strict_grades(ranked_job_keys: list[str], qrels: dict[str, int], k: int) -> list[int]:
    keys = ranked_job_keys[:k]
    unknown = [key for key in keys if key not in qrels]
    if unknown:
        raise ValueError(
            "Unjudged document encountered in top-K; expand/rebuild qrel pool rather than treating it as grade 0. "
            f"unjudged_job_keys={sorted(set(unknown))}"
        )
    return [qrels[key] for key in keys]


def ndcg_at_k(ranked_job_keys: list[str], qrels: dict[str, int], k: int) -> float:
    gains = _strict_grades(ranked_job_keys, qrels, k)
    actual = dcg(gains)
    ideal = dcg(sorted(qrels.values(), reverse=True)[:k])
    return actual / ideal if ideal > 0 else 0.0


def strong_precision_at_k(ranked_job_keys: list[str], qrels: dict[str, int], k: int) -> float:
    top = ranked_job_keys[:k]
    if k <= 0:
        raise ValueError("k must be positive")
    if not top:
        return 0.0
    return sum(1 for grade in _strict_grades(top, qrels, k) if grade >= 2) / k


def condense_uncertain_ranking(
    ranked_job_keys: list[str],
    *,
    certain_qrels: dict[str, int],
    uncertain_job_keys: set[str],
    k: int,
) -> dict:
    """Remove uncertain judgments without allowing an unknown document through.

    The returned ranking has metric positions occupied exclusively by certain
    qrels.  An unjudged key encountered before the requested metric horizon is
    a benchmark-coverage error, never an implicit grade zero.
    """

    if k <= 0:
        raise ValueError("k must be positive")
    overlap = set(certain_qrels).intersection(uncertain_job_keys)
    if overlap:
        raise ValueError(f"qrel key is both certain and uncertain: {sorted(overlap)}")
    condensed: list[str] = []
    uncertain_skipped = 0
    unjudged: list[str] = []
    examined = 0
    judged = 0
    for key in ranked_job_keys:
        examined += 1
        if key in uncertain_job_keys:
            uncertain_skipped += 1
            judged += 1
            continue
        if key not in certain_qrels:
            unjudged.append(key)
            break
        judged += 1
        condensed.append(key)
        if len(condensed) == k:
            break
    if unjudged:
        raise ValueError(
            "Unjudged document encountered in top-K; expand/rebuild qrel pool rather than treating it as grade 0. "
            f"unjudged_job_keys={sorted(set(unjudged))}; judged_fraction@{k}="
            f"{judged / examined if examined else 0.0:.6f}"
        )
    if len(condensed) < k:
        raise ValueError(
            f"Ranking ended before {k} certain judged documents after uncertainty condensation; "
            "expand/rebuild qrel pool."
        )
    return {
        "ranking": condensed,
        "uncertain_skipped": uncertain_skipped,
        "judged_fraction": judged / examined if examined else 0.0,
        "certain_fraction": len(condensed) / examined if examined else 0.0,
        "examined": examined,
    }


def observed_support_coverage_at_k(ranked_job_keys: list[str], nuggets: list[Nugget], k: int) -> float:
    """Lower-biased diagnostic coverage of observed support examples.

    Adaptive verification may stop before every true supporting job is found,
    so this quantity is neither exhaustive nugget recall nor a headline metric.
    """

    if not nuggets:
        return 0.0
    selected = set(ranked_job_keys[:k])
    total_weight = sum(nugget.weight for nugget in nuggets)
    covered = sum(
        nugget.weight for nugget in nuggets if selected.intersection(nugget.support_job_keys)
    )
    return covered / total_weight if total_weight > 0 else 0.0


def weighted_nugget_coverage(matched_ids: set[str], nuggets: list[Nugget]) -> float:
    """Return weighted gold-nugget coverage for an answer.

    The judge returns matched gold IDs, but it does not emit an independent
    set of predicted answer nuggets.  That is sufficient for coverage and not
    for a defensible nugget precision denominator.
    """

    weights = {nugget.nugget_id: nugget.weight for nugget in nuggets}
    matched_weight = sum(weights.get(nugget_id, 0.0) for nugget_id in matched_ids)
    total_weight = sum(weights.values())
    return matched_weight / total_weight if total_weight else 0.0


def robustness(scores: list[float]) -> dict[str, float]:
    if not scores:
        return {"mean": 0.0, "worst": 0.0, "best": 0.0, "gap": 0.0}
    best = max(scores)
    worst = min(scores)
    return {"mean": mean(scores), "worst": worst, "best": best, "gap": best - worst}


def family_cluster_bootstrap_ci(
    topic_values: dict[str, float],
    topic_family_ids: dict[str, str],
    *,
    samples: int = 2000,
    seed: int = 20260819,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap families, preserving all broad/specific topic siblings."""

    if samples <= 0:
        raise ValueError("samples must be positive")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    family_values: dict[str, list[float]] = defaultdict(list)
    for topic_id, value in topic_values.items():
        try:
            family_id = topic_family_ids[topic_id]
        except KeyError as exc:
            raise ValueError(f"Missing family_id for topic {topic_id}") from exc
        family_values[family_id].append(float(value))
    family_ids = sorted(family_values)
    if not family_ids:
        return (0.0, 0.0)
    rng = random.Random(seed)
    boot: list[float] = []
    for _ in range(samples):
        sampled: list[float] = []
        for _ in family_ids:
            sampled.extend(family_values[family_ids[rng.randrange(len(family_ids))]])
        boot.append(mean(sampled))
    boot.sort()
    low_index = max(0, int((alpha / 2) * samples))
    high_index = min(samples - 1, int((1 - alpha / 2) * samples) - 1)
    return boot[low_index], boot[high_index]


def aggregate_topic_values_by_family(
    topic_values: dict[str, float],
    topic_family_ids: dict[str, str],
) -> dict[str, float]:
    """Aggregate related broad/specific topic values into family values."""

    grouped: dict[str, list[float]] = defaultdict(list)
    for topic_id, value in topic_values.items():
        try:
            family_id = topic_family_ids[topic_id]
        except KeyError as exc:
            raise ValueError(f"Missing family_id for topic {topic_id}") from exc
        grouped[family_id].append(float(value))
    return {
        family_id: mean(values)
        for family_id, values in sorted(grouped.items())
    }


def family_cluster_paired_bootstrap(
    topic_deltas: dict[str, float],
    topic_family_ids: dict[str, str],
    *,
    samples: int = 2000,
    seed: int = 20260819,
    alpha: float = 0.05,
) -> dict[str, float | list[float]]:
    family_deltas = aggregate_topic_values_by_family(topic_deltas, topic_family_ids)
    low, high = family_cluster_bootstrap_ci(
        family_deltas,
        {family_id: family_id for family_id in family_deltas},
        samples=samples,
        seed=seed,
        alpha=alpha,
    )
    return {
        "mean_family_delta": mean(family_deltas.values()) if family_deltas else 0.0,
        "ci": [low, high],
        "alpha": alpha,
        "bootstrap_unit": "family",
        "family_count": len(family_deltas),
    }


def paired_family_sign_flip_test(
    topic_deltas: dict[str, float],
    topic_family_ids: dict[str, str],
    *,
    exact_max_assignments: int = 65_536,
    monte_carlo_samples: int = 100_000,
    seed: int = 20260819,
) -> dict[str, float | int | str]:
    """Two-sided paired sign-flip test over family-level mean deltas."""

    if exact_max_assignments <= 0:
        raise ValueError("exact_max_assignments must be positive")
    if monte_carlo_samples <= 0:
        raise ValueError("monte_carlo_samples must be positive")

    family_deltas = aggregate_topic_values_by_family(topic_deltas, topic_family_ids)
    values = [family_deltas[family_id] for family_id in sorted(family_deltas)]
    if not values:
        return {
            "mean_family_delta": 0.0,
            "paired_sign_flip_p_value": 1.0,
            "test_mode": "exact",
            "assignments": 1,
            "family_count": 0,
        }

    observed = abs(mean(values))
    assignment_count = 1 << len(values)

    def is_as_extreme(signed_sum: float) -> bool:
        return abs(signed_sum / len(values)) >= observed - 1e-15

    if assignment_count <= exact_max_assignments:
        extreme = 0
        for mask in range(assignment_count):
            signed_sum = sum(
                value if mask & (1 << index) else -value
                for index, value in enumerate(values)
            )
            extreme += int(is_as_extreme(signed_sum))
        p_value = extreme / assignment_count
        mode = "exact"
        assignments = assignment_count
    else:
        rng = random.Random(seed)
        extreme = 0
        for _ in range(monte_carlo_samples):
            signed_sum = sum(value if rng.getrandbits(1) else -value for value in values)
            extreme += int(is_as_extreme(signed_sum))
        p_value = (extreme + 1) / (monte_carlo_samples + 1)
        mode = "monte_carlo"
        assignments = monte_carlo_samples

    return {
        "mean_family_delta": mean(values),
        "paired_sign_flip_p_value": p_value,
        "test_mode": mode,
        "assignments": assignments,
        "family_count": len(values),
    }


def macro_topic_metric(query_rows: list[dict], metric_name: str) -> tuple[float, list[float], dict[str, dict[str, float]]]:
    by_topic: dict[str, list[float]] = defaultdict(list)
    for row in query_rows:
        by_topic[row["topic_id"]].append(float(row[metric_name]))
    topic_summary = {topic_id: robustness(values) for topic_id, values in by_topic.items()}
    topic_means = [summary["mean"] for summary in topic_summary.values()]
    return (mean(topic_means) if topic_means else 0.0, topic_means, topic_summary)
