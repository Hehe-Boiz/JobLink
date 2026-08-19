from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from apps.career.evaluation.career_qa_oracle import canonical_skill, sha256_file


DEFAULT_BOOTSTRAP_SAMPLES = 2000
DEFAULT_SEED = 20260819


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _norm(value: Any) -> str | None:
    if value is None:
        return None
    text = " ".join(str(value).strip().casefold().split())
    return text or None


def _intent_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _skills(value: Iterable[Any] | None) -> set[str]:
    return {canonical_skill(str(item)) for item in (value or []) if canonical_skill(str(item))}


def _plan_exact(pred: dict[str, Any], gold: dict[str, Any]) -> float:
    return float(
        _intent_value(pred.get("intent")) == gold["intent"]
        and _norm(pred.get("category")) == _norm(gold.get("category"))
        and _norm(pred.get("location")) == _norm(gold.get("location"))
        and _skills(pred.get("skills")) == _skills(gold.get("skills"))
        and _skills(pred.get("candidate_skills")) == _skills(gold.get("candidate_skills"))
    )


def _intent_correct(pred: dict[str, Any], gold: dict[str, Any]) -> float:
    return float(_intent_value(pred.get("intent")) == gold["intent"])


def _skill_set_f1(pred: dict[str, Any], gold: dict[str, Any]) -> float:
    pred_skills = _skills(pred.get("skills")) | _skills(pred.get("candidate_skills"))
    gold_skills = _skills(gold.get("skills")) | _skills(gold.get("candidate_skills"))
    if not pred_skills and not gold_skills:
        return 1.0
    if not pred_skills or not gold_skills:
        return 0.0
    intersection = len(pred_skills & gold_skills)
    precision = intersection / len(pred_skills)
    recall = intersection / len(gold_skills)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _stat_map(stats: Sequence[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {canonical_skill(str(stat["skill"])): stat for stat in stats}


def _ranking(stats: Sequence[dict[str, Any]]) -> list[str]:
    return [canonical_skill(str(stat["skill"])) for stat in stats]


def _recall_at_k(predicted: Sequence[str], oracle_stats: Sequence[dict[str, Any]], k: int) -> float:
    gold = set(_ranking(oracle_stats)[:k])
    if not gold:
        return 0.0
    return len(set(predicted[:k]) & gold) / len(gold)


def _weighted_ndcg_at_k(predicted: Sequence[str], oracle_stats: Sequence[dict[str, Any]], k: int) -> float:
    relevance = {canonical_skill(str(stat["skill"])): float(stat["coverage"]) for stat in oracle_stats}
    dcg = sum(relevance.get(skill, 0.0) / math.log2(rank + 1) for rank, skill in enumerate(predicted[:k], start=1))
    ideal = sorted(relevance.values(), reverse=True)[:k]
    idcg = sum(gain / math.log2(rank + 1) for rank, gain in enumerate(ideal, start=1))
    return dcg / idcg if idcg else 0.0


def _coverage_mae_pp(pred_stats: Sequence[dict[str, Any]], oracle_stats: Sequence[dict[str, Any]], k: int) -> float:
    pred = _stat_map(pred_stats)
    oracle_top = oracle_stats[:k]
    if not oracle_top:
        return 0.0
    errors = []
    for gold in oracle_top:
        skill = canonical_skill(str(gold["skill"]))
        predicted_coverage = float(pred.get(skill, {}).get("coverage", 0.0))
        errors.append(abs(predicted_coverage - float(gold["coverage"])) * 100.0)
    return sum(errors) / len(errors)


def _comparison_coverage_mae_pp(pred: dict[str, Any], gold: dict[str, Any]) -> float:
    pred_stats = _stat_map(pred.get("skills", []))
    errors = []
    for gold_stat in gold["skills"]:
        skill = canonical_skill(str(gold_stat["skill"]))
        predicted_coverage = float(pred_stats.get(skill, {}).get("coverage", 0.0))
        errors.append(abs(predicted_coverage - float(gold_stat["coverage"])) * 100.0)
    return sum(errors) / len(errors) if errors else 0.0


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _bootstrap_ci(values: Sequence[float], *, samples: int, seed: int) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    if len(values) == 1:
        return values[0], values[0]
    rng = random.Random(seed)
    means = []
    n = len(values)
    for _ in range(samples):
        means.append(_mean([values[rng.randrange(n)] for _ in range(n)]))
    means.sort()
    lo = means[int(0.025 * (samples - 1))]
    hi = means[int(0.975 * (samples - 1))]
    return lo, hi


def _extract_result_stats(result: Any, attr: str = "skills") -> list[dict[str, Any]]:
    values = getattr(result, attr, ()) or ()
    return [
        {
            "skill": getattr(item, "skill"),
            "job_count": int(getattr(item, "job_count")),
            "coverage": float(getattr(item, "coverage")),
        }
        for item in values
    ]


def _generate_predictions_joblink(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joblink.settings")

    import django
    from django.apps import apps

    if not apps.ready:
        django.setup()

    try:
        from apps.career.market import CareerMarketAnalyzer
        from apps.career.query_planner import CareerQueryPlanner
    except ImportError as exc:
        raise RuntimeError(
            "JobLink production benchmark adapter requires apps.career.market and apps.career.query_planner. "
            "Create those core modules first or evaluate a --predictions JSONL file."
        ) from exc

    planner = CareerQueryPlanner()
    analyzer = CareerMarketAnalyzer()
    predictions: list[dict[str, Any]] = []

    for row in rows:
        plan = planner.plan(row["query"])
        intent = _intent_value(plan.intent)
        pred_plan = {
            "intent": intent,
            "category": getattr(plan, "category", None),
            "location": getattr(plan, "location", None),
            "skills": list(getattr(plan, "skills", ()) or ()),
            "candidate_skills": list(getattr(plan, "candidate_skills", ()) or ()),
        }
        result_payload: dict[str, Any] = {}

        try:
            if intent == "skill_demand":
                result = analyzer.skill_distribution(
                    category=pred_plan["category"], location=pred_plan["location"], limit=50
                )
                result_payload = {"cohort_size": int(result.cohort_size), "skill_stats": _extract_result_stats(result)}
            elif intent == "skill_comparison" and len(pred_plan["skills"]) >= 2:
                result = analyzer.compare_skills(
                    pred_plan["skills"][0],
                    pred_plan["skills"][1],
                    category=pred_plan["category"],
                    location=pred_plan["location"],
                )
                result_payload = {
                    "cohort_size": int(result.cohort_size),
                    "skills": [
                        {"skill": result.first.skill, "job_count": int(result.first.job_count), "coverage": float(result.first.coverage)},
                        {"skill": result.second.skill, "job_count": int(result.second.job_count), "coverage": float(result.second.coverage)},
                    ],
                    "winner": result.winner,
                }
            elif intent == "skill_cooccurrence" and pred_plan["skills"]:
                result = analyzer.skill_cooccurrence(
                    pred_plan["skills"][0], category=pred_plan["category"], location=pred_plan["location"], limit=50
                )
                result_payload = {
                    "cohort_size": int(result.cohort_size),
                    "anchor_skill": result.anchor_skill,
                    "anchor_job_count": int(result.anchor_job_count),
                    "skill_stats": _extract_result_stats(result),
                }
            elif intent == "candidate_skill_gap":
                result = analyzer.candidate_skill_gap(
                    pred_plan["candidate_skills"],
                    category=pred_plan["category"],
                    location=pred_plan["location"],
                    limit=50,
                )
                result_payload = {
                    "cohort_size": int(result.cohort_size),
                    "candidate_skills": list(result.candidate_skills),
                    "skill_stats": _extract_result_stats(result, "recommended_skills"),
                }
        except Exception as exc:
            result_payload = {"error": f"{type(exc).__name__}: {exc}"}

        predictions.append({"query_id": row["query_id"], "predicted_plan": pred_plan, "result": result_payload})

    return predictions


def _gold_rows(benchmark_dir: Path, split: str) -> list[dict[str, Any]]:
    if split == "dev":
        return _load_jsonl(benchmark_dir / "dev.jsonl")
    query_rows = {row["query_id"]: row for row in _load_jsonl(benchmark_dir / "test_queries.jsonl")}
    gold_rows = _load_jsonl(benchmark_dir / "test_gold.jsonl")
    return [{**gold, "query": query_rows[gold["query_id"]]["query"]} for gold in gold_rows]


def _evaluate(gold_rows: Sequence[dict[str, Any]], predictions: Sequence[dict[str, Any]], top_k: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    pred_by_id = {row["query_id"]: row for row in predictions}
    missing = [row["query_id"] for row in gold_rows if row["query_id"] not in pred_by_id]
    if missing:
        raise ValueError(f"Missing predictions for {len(missing)} queries, e.g. {missing[:5]}")

    per_query: list[dict[str, Any]] = []
    for gold in gold_rows:
        pred = pred_by_id[gold["query_id"]]
        plan = pred.get("predicted_plan", {})
        result = pred.get("result", {})
        metrics: dict[str, float] = {
            "intent_accuracy": _intent_correct(plan, gold["expected_plan"]),
            "full_plan_accuracy": _plan_exact(plan, gold["expected_plan"]),
            "planner_skill_f1": _skill_set_f1(plan, gold["expected_plan"]),
        }

        family = gold["family"]
        gt = gold["ground_truth"]
        if family == "skill_demand":
            pred_stats = result.get("skill_stats", [])
            predicted_ranking = _ranking(pred_stats)
            metrics["skill_recall@5"] = _recall_at_k(predicted_ranking, gt["skill_stats"], top_k)
            metrics["skill_ndcg@5"] = _weighted_ndcg_at_k(predicted_ranking, gt["skill_stats"], top_k)
            metrics["coverage_mae_pp@5"] = _coverage_mae_pp(pred_stats, gt["skill_stats"], top_k)
        elif family == "skill_comparison":
            predicted_winner = canonical_skill(str(result.get("winner", "")))
            metrics["comparison_accuracy"] = float(predicted_winner == canonical_skill(gt["winner"]))
            metrics["comparison_coverage_mae_pp"] = _comparison_coverage_mae_pp(result, gt)
        elif family == "skill_cooccurrence":
            pred_stats = result.get("skill_stats", [])
            predicted_ranking = _ranking(pred_stats)
            metrics["cooccurrence_recall@5"] = _recall_at_k(predicted_ranking, gt["skill_stats"], top_k)
            metrics["cooccurrence_ndcg@5"] = _weighted_ndcg_at_k(predicted_ranking, gt["skill_stats"], top_k)
            metrics["conditional_coverage_mae_pp@5"] = _coverage_mae_pp(pred_stats, gt["skill_stats"], top_k)
        elif family == "candidate_skill_gap":
            pred_stats = result.get("skill_stats", [])
            predicted_ranking = _ranking(pred_stats)
            metrics["gap_recall@5"] = _recall_at_k(predicted_ranking, gt["skill_stats"], top_k)
            metrics["gap_ndcg@5"] = _weighted_ndcg_at_k(predicted_ranking, gt["skill_stats"], top_k)

        per_query.append({"query_id": gold["query_id"], "family": family, "metrics": metrics})

    metric_values: dict[str, list[float]] = defaultdict(list)
    for row in per_query:
        for name, value in row["metrics"].items():
            metric_values[name].append(float(value))

    summary = {name: _mean(values) for name, values in sorted(metric_values.items())}
    by_family: dict[str, dict[str, float]] = {}
    for family in sorted({row["family"] for row in per_query}):
        family_values: dict[str, list[float]] = defaultdict(list)
        for row in per_query:
            if row["family"] != family:
                continue
            for name, value in row["metrics"].items():
                family_values[name].append(float(value))
        by_family[family] = {name: _mean(values) for name, values in sorted(family_values.items())}

    return {"summary": summary, "by_family": by_family}, per_query


def _add_confidence_intervals(report: dict[str, Any], per_query: Sequence[dict[str, Any]], samples: int, seed: int) -> None:
    metric_values: dict[str, list[float]] = defaultdict(list)
    for row in per_query:
        for name, value in row["metrics"].items():
            metric_values[name].append(float(value))
    report["summary_95ci"] = {
        name: {"low": _bootstrap_ci(values, samples=samples, seed=seed + index)[0],
               "high": _bootstrap_ci(values, samples=samples, seed=seed + index)[1]}
        for index, (name, values) in enumerate(sorted(metric_values.items()))
    }


def _git_commit() -> str | None:
    try:
        backend_root = Path(__file__).resolve().parents[3]
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=backend_root.parent, text=True).strip()
    except Exception:
        return None


def _print_report(report: dict[str, Any]) -> None:
    print("Career Intelligence QA")
    print("=" * 72)
    ci = report.get("summary_95ci", {})
    for name, value in report["summary"].items():
        bounds = ci.get(name)
        suffix = f"  95% CI [{bounds['low']:.4f}, {bounds['high']:.4f}]" if bounds else ""
        if "mae_pp" in name:
            print(f"{name:36s}: {value:.3f} pp{suffix}")
        else:
            print(f"{name:36s}: {value:.4f}{suffix}")
    print("\nBy family")
    for family, metrics in report["by_family"].items():
        print(f"\n{family}")
        for name, value in metrics.items():
            print(f"  {name:34s}: {value:.3f} pp" if "mae_pp" in name else f"  {name:34s}: {value:.4f}")


def run(*, benchmark_dir: Path, split: str, predictions_path: Path | None, generate_with_joblink: bool,
        output_predictions: Path | None, output_report: Path, bootstrap_samples: int, seed: int,
        allow_test: bool) -> None:
    if split == "test" and not allow_test:
        raise SystemExit("Refusing to run frozen TEST without --allow-test. Tune on DEV only.")

    manifest = json.loads((benchmark_dir / "manifest.json").read_text(encoding="utf-8"))
    gold_rows = _gold_rows(benchmark_dir, split)

    if predictions_path is not None and generate_with_joblink:
        raise ValueError("Choose either --predictions or --generate-with-joblink, not both.")
    if predictions_path is None and not generate_with_joblink:
        raise ValueError("Provide --predictions or use --generate-with-joblink.")

    if predictions_path is not None:
        predictions = _load_jsonl(predictions_path)
    else:
        predictions = _generate_predictions_joblink(gold_rows)
        if output_predictions:
            _write_jsonl(output_predictions, predictions)

    report, per_query = _evaluate(gold_rows, predictions, int(manifest["top_k"]))
    _add_confidence_intervals(report, per_query, bootstrap_samples, seed)
    report["benchmark_version"] = manifest["benchmark_version"]
    report["split"] = split
    report["query_count"] = len(gold_rows)
    report["system_commit"] = _git_commit()
    report["prediction_sha256"] = sha256_file(output_predictions) if output_predictions and output_predictions.exists() else (
        sha256_file(predictions_path) if predictions_path else None
    )
    report["per_query"] = per_query

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    _print_report(report)

    if split == "test":
        receipt = {
            "benchmark_version": manifest["benchmark_version"],
            "benchmark_test_gold_sha256": manifest["artifacts"]["test_gold_sha256"],
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "system_commit": report["system_commit"],
            "prediction_sha256": report["prediction_sha256"],
            "report_sha256": sha256_file(output_report),
        }
        receipt_path = output_report.with_name(output_report.stem + "_test_receipt.json")
        receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nFrozen TEST receipt: {receipt_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--generate-with-joblink", action="store_true")
    parser.add_argument("--output-predictions", type=Path)
    parser.add_argument("--output-report", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=DEFAULT_BOOTSTRAP_SAMPLES)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--allow-test", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run(
        benchmark_dir=args.benchmark_dir,
        split=args.split,
        predictions_path=args.predictions,
        generate_with_joblink=args.generate_with_joblink,
        output_predictions=args.output_predictions,
        output_report=args.output_report,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        allow_test=args.allow_test,
    )


if __name__ == "__main__":
    main()
