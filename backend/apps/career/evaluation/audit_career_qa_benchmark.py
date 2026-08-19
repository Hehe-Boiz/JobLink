from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path
from typing import Any

from apps.career.evaluation.career_qa_oracle import canonical_skill, sha256_file


FORBIDDEN_ORACLE_IMPORTS = {
    "apps.career.market",
    "apps.career.query_planner",
    "apps.career.retrieval",
    "apps.career.answering",
}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _norm_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _audit_oracle_independence(oracle_path: Path) -> list[str]:
    errors: list[str] = []
    tree = ast.parse(oracle_path.read_text(encoding="utf-8"), filename=str(oracle_path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in FORBIDDEN_ORACLE_IMPORTS:
        if forbidden in imported:
            errors.append(f"Oracle imports production module: {forbidden}")
    return errors


def _audit_skill_stats(stats: list[dict[str, Any]], denominator: int, top_k: int, prefix: str) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    previous_count: int | None = None
    for index, stat in enumerate(stats):
        skill = canonical_skill(str(stat.get("skill", "")))
        count = int(stat.get("job_count", -1))
        coverage = float(stat.get("coverage", -1.0))
        if not skill:
            errors.append(f"{prefix}: empty skill at rank {index + 1}")
        if skill in seen:
            errors.append(f"{prefix}: duplicate skill {skill}")
        seen.add(skill)
        if count < 0 or count > denominator:
            errors.append(f"{prefix}: invalid count {count}/{denominator} for {skill}")
        expected = count / denominator if denominator else 0.0
        if abs(coverage - expected) > 1e-9:
            errors.append(f"{prefix}: coverage mismatch for {skill}: {coverage} != {expected}")
        if previous_count is not None and count > previous_count:
            errors.append(f"{prefix}: ranking not sorted at {skill}")
        previous_count = count

    if len(stats) >= top_k + 1 and stats[top_k - 1]["job_count"] == stats[top_k]["job_count"]:
        errors.append(f"{prefix}: unresolved tie at top-{top_k} boundary")
    return errors


def audit_benchmark(benchmark_dir: Path, dataset_dir: Path | None = None) -> None:
    manifest_path = benchmark_dir / "manifest.json"
    dev_path = benchmark_dir / "dev.jsonl"
    test_queries_path = benchmark_dir / "test_queries.jsonl"
    test_gold_path = benchmark_dir / "test_gold.jsonl"
    clusters_path = benchmark_dir / "clusters.jsonl"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dev = _load_jsonl(dev_path)
    test_queries = _load_jsonl(test_queries_path)
    test_gold = _load_jsonl(test_gold_path)
    clusters = _load_jsonl(clusters_path)
    errors: list[str] = []

    expected_hashes = {
        dev_path: manifest["artifacts"]["dev_sha256"],
        test_queries_path: manifest["artifacts"]["test_queries_sha256"],
        test_gold_path: manifest["artifacts"]["test_gold_sha256"],
        clusters_path: manifest["corpus"]["clusters_sha256"],
    }
    for path, expected in expected_hashes.items():
        actual = sha256_file(path)
        if actual != expected:
            errors.append(f"Hash mismatch: {path.name}: {actual} != {expected}")

    if len(clusters) != manifest["corpus"]["duplicate_clusters"]:
        errors.append("Cluster count does not match manifest.")
    raw_docs = sum(len(cluster["source_job_ids"]) for cluster in clusters)
    if raw_docs != manifest["corpus"]["raw_documents"]:
        errors.append("Raw document count does not match manifest.")

    expected_per_family = manifest["per_family_per_split"]
    for split_name, rows in (("dev", dev), ("test", test_gold)):
        counts = Counter(row["family"] for row in rows)
        for family in manifest["families"]:
            if counts[family] != expected_per_family:
                errors.append(f"{split_name}: {family} count {counts[family]} != {expected_per_family}")

    dev_ids = {row["query_id"] for row in dev}
    test_query_ids = {row["query_id"] for row in test_queries}
    test_gold_ids = {row["query_id"] for row in test_gold}
    if len(dev_ids) != len(dev):
        errors.append("Duplicate query_id inside DEV.")
    if len(test_query_ids) != len(test_queries):
        errors.append("Duplicate query_id inside TEST queries.")
    if test_query_ids != test_gold_ids:
        errors.append("TEST query IDs and TEST gold IDs differ.")
    if dev_ids & test_query_ids:
        errors.append("DEV and TEST query IDs overlap.")

    dev_signatures = {row["latent_signature"] for row in dev}
    test_signatures = {row["latent_signature"] for row in test_gold}
    if dev_signatures & test_signatures:
        errors.append(f"DEV/TEST latent signature leakage: {len(dev_signatures & test_signatures)} overlaps.")

    dev_templates = {row["template_id"] for row in dev}
    test_templates = {row["template_id"] for row in test_gold}
    if dev_templates & test_templates:
        errors.append("DEV/TEST template IDs overlap.")

    normalized_dev_queries = {_norm_text(row["query"]) for row in dev}
    normalized_test_queries = {_norm_text(row["query"]) for row in test_queries}
    if normalized_dev_queries & normalized_test_queries:
        errors.append("Exact normalized query text overlaps DEV/TEST.")

    forbidden_test_fields = {"expected_plan", "oracle_cohort", "ground_truth", "family", "latent_signature", "template_id"}
    for row in test_queries:
        leaked = forbidden_test_fields & row.keys()
        if leaked:
            errors.append(f"{row['query_id']}: TEST public query leaks fields {sorted(leaked)}")

    top_k = int(manifest["top_k"])
    gates = manifest["quality_gates"]
    min_cohort = int(gates["min_cohort"])
    min_skill_support = int(gates["min_skill_support"])
    min_anchor_support = int(gates["min_anchor_support"])
    min_gap_pp = float(gates["min_comparison_gap_pp"])

    for row in [*dev, *test_gold]:
        prefix = row["query_id"]
        cohort_size = int(row["oracle_cohort"]["cluster_count"])
        cohort_ids = row["oracle_cohort"]["cluster_ids"]
        if cohort_size != len(cohort_ids):
            errors.append(f"{prefix}: cohort_count != len(cluster_ids)")
        if len(set(cohort_ids)) != len(cohort_ids):
            errors.append(f"{prefix}: duplicate cluster IDs in cohort")
        if cohort_size < min_cohort:
            errors.append(f"{prefix}: cohort {cohort_size} < min_cohort {min_cohort}")

        gt = row["ground_truth"]
        family = row["family"]
        if family == "skill_demand":
            stats = gt["skill_stats"]
            errors.extend(_audit_skill_stats(stats, cohort_size, top_k, prefix))
            if not stats or stats[0]["job_count"] < min_skill_support:
                errors.append(f"{prefix}: top skill below min support")
        elif family == "skill_comparison":
            stats = gt["skills"]
            errors.extend(_audit_skill_stats(stats, cohort_size, top_k=2, prefix=prefix))
            if any(stat["job_count"] < min_skill_support for stat in stats):
                errors.append(f"{prefix}: comparison skill below min support")
            actual_gap = abs(stats[0]["coverage"] - stats[1]["coverage"]) * 100.0
            if abs(actual_gap - gt["coverage_gap_pp"]) > 1e-9:
                errors.append(f"{prefix}: stored comparison gap is wrong")
            if actual_gap < min_gap_pp:
                errors.append(f"{prefix}: comparison gap {actual_gap:.3f}pp < {min_gap_pp}pp")
            expected_winner = stats[0]["skill"] if stats[0]["coverage"] > stats[1]["coverage"] else stats[1]["skill"]
            if gt["winner"] != expected_winner:
                errors.append(f"{prefix}: wrong comparison winner")
        elif family == "skill_cooccurrence":
            anchor_count = int(gt["anchor_job_count"])
            if anchor_count < min_anchor_support or anchor_count > cohort_size:
                errors.append(f"{prefix}: invalid anchor support {anchor_count}")
            errors.extend(_audit_skill_stats(gt["skill_stats"], anchor_count, top_k, prefix))
            anchor = canonical_skill(gt["anchor_skill"])
            if any(canonical_skill(stat["skill"]) == anchor for stat in gt["skill_stats"]):
                errors.append(f"{prefix}: anchor appears in its own co-skill ranking")
        elif family == "candidate_skill_gap":
            known = {canonical_skill(skill) for skill in gt["candidate_skills"]}
            errors.extend(_audit_skill_stats(gt["skill_stats"], cohort_size, top_k, prefix))
            overlap = known & {canonical_skill(stat["skill"]) for stat in gt["skill_stats"]}
            if overlap:
                errors.append(f"{prefix}: known candidate skills leaked into gap ranking: {sorted(overlap)}")
        else:
            errors.append(f"{prefix}: unknown family {family}")

    oracle_path = Path(__file__).with_name("career_qa_oracle.py")
    errors.extend(_audit_oracle_independence(oracle_path))

    if dataset_dir is not None:
        from apps.career.evaluation.vietjobs import VietJobsSource
        csv_path = VietJobsSource(dataset_dir)._find_dataset_csv()
        actual = sha256_file(csv_path)
        expected = manifest["corpus"]["dataset_sha256"]
        if actual != expected:
            errors.append(f"Dataset hash mismatch: {actual} != {expected}")

    if errors:
        print("BENCHMARK AUDIT: FAIL")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print("BENCHMARK AUDIT: PASS")
    print(f"Version: {manifest['benchmark_version']}")
    print(f"DEV: {len(dev)}")
    print(f"TEST: {len(test_gold)}")
    print(f"Raw docs: {manifest['corpus']['raw_documents']}")
    print(f"Duplicate clusters: {manifest['corpus']['duplicate_clusters']}")
    print("No DEV/TEST latent-signature leakage.")
    print("No public TEST gold leakage.")
    print("Oracle does not import production planner/market/retrieval/answering modules.")
    print("All deterministic arithmetic and quality gates are internally consistent.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-dir", type=Path, required=True)
    parser.add_argument("--dataset-dir", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    audit_benchmark(args.benchmark_dir, args.dataset_dir)


if __name__ == "__main__":
    main()
