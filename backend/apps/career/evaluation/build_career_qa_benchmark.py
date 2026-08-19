from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Sequence

from apps.career.normalization import normalize_key
from apps.career.evaluation.career_qa_oracle import (
    BENCHMARK_VERSION,
    OracleCluster,
    SkillStat,
    canonical_skill,
    filter_cohort,
    load_oracle_clusters,
    sha256_file,
    skill_cooccurrence,
    skill_distribution,
    stats_to_json,
)


BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "benchmark_career_qa_v1"
DEFAULT_SEED = 20260819
DEFAULT_PER_FAMILY_PER_SPLIT = 20
DEFAULT_TOP_K = 5
DEFAULT_MIN_COHORT = 30
DEFAULT_MIN_SKILL_SUPPORT = 5
DEFAULT_MIN_ANCHOR_SUPPORT = 20
DEFAULT_MIN_COMPARISON_GAP_PP = 3.0

FAMILY_SKILL_DEMAND = "skill_demand"
FAMILY_SKILL_COMPARISON = "skill_comparison"
FAMILY_SKILL_COOCCURRENCE = "skill_cooccurrence"
FAMILY_CANDIDATE_SKILL_GAP = "candidate_skill_gap"
FAMILIES = (
    FAMILY_SKILL_DEMAND,
    FAMILY_SKILL_COMPARISON,
    FAMILY_SKILL_COOCCURRENCE,
    FAMILY_CANDIDATE_SKILL_GAP,
)


DEV_TEMPLATES = {
    FAMILY_SKILL_DEMAND: (
        "Trong mảng {category}{location_clause}, những kỹ năng kỹ thuật nào đang xuất hiện nhiều nhất?",
        "{category}{location_clause}: thị trường hiện yêu cầu các skill nào nhiều nhất?",
        "Nếu nhắm việc {category}{location_clause}, mình nên chú ý những kỹ năng nào đang có demand cao?",
        "Các job {category}{location_clause} hiện thường yêu cầu stack/kỹ năng gì?",
    ),
    FAMILY_SKILL_COMPARISON: (
        "Trong job {category}{location_clause}, {skill_a} hay {skill_b} được yêu cầu nhiều hơn?",
        "Ở thị trường {category}{location_clause}, giữa {skill_a} và {skill_b} skill nào phổ biến hơn?",
        "Nếu theo {category}{location_clause}, demand cho {skill_a} so với {skill_b} bên nào cao hơn?",
        "{skill_a} hay {skill_b} xuất hiện nhiều hơn trong các vị trí {category}{location_clause}?",
    ),
    FAMILY_SKILL_COOCCURRENCE: (
        "Trong job {category}{location_clause} có {anchor}, những skill nào thường đi kèm nhất?",
        "Nếu một vị trí {category}{location_clause} yêu cầu {anchor}, nó còn hay yêu cầu thêm kỹ năng nào?",
        "{anchor} thường xuất hiện cùng những kỹ năng nào trong nhóm job {category}{location_clause}?",
        "Với các job {category}{location_clause} dùng {anchor}, stack đi kèm phổ biến là gì?",
    ),
    FAMILY_CANDIDATE_SKILL_GAP: (
        "Mình đã có {known_skills}. Nếu nhắm {category}{location_clause}, những skill demand cao nào mình còn thiếu?",
        "Profile hiện có {known_skills}; với thị trường {category}{location_clause}, nên ưu tiên bổ sung skill nào đang được yêu cầu nhiều?",
        "Nếu đã biết {known_skills} và muốn theo {category}{location_clause}, market-demand gap còn lại là gì?",
        "Đối chiếu {known_skills} với job {category}{location_clause}, những kỹ năng phổ biến nào chưa có trong profile?",
    ),
}

TEST_TEMPLATES = {
    FAMILY_SKILL_DEMAND: (
        "Nhìn các JD thuộc {category}{location_clause}, công nghệ/kỹ năng nào đang có mặt nhiều nhất?",
        "Mặt bằng tuyển dụng {category}{location_clause} đang chuộng những skill kỹ thuật nào?",
        "Cho mình bức tranh demand kỹ năng của nhóm việc {category}{location_clause}.",
        "Nếu chỉ nhìn dữ liệu job {category}{location_clause}, top skill theo tần suất yêu cầu là gì?",
        "Stack nào đang nổi bật nhất trong các tin tuyển dụng {category}{location_clause}?",
    ),
    FAMILY_SKILL_COMPARISON: (
        "So trên các JD {category}{location_clause}: {skill_a} với {skill_b}, cái nào có coverage cao hơn?",
        "Với {category}{location_clause}, nhà tuyển dụng nhắc {skill_a} nhiều hơn hay {skill_b} nhiều hơn?",
        "{skill_a} vs {skill_b} trong thị trường {category}{location_clause}: bên nào đang có demand lớn hơn?",
        "Nếu chọn theo độ phổ biến trong JD {category}{location_clause}, {skill_a} hay {skill_b} thắng?",
        "Tần suất yêu cầu {skill_a} và {skill_b} ở {category}{location_clause} bên nào cao hơn?",
    ),
    FAMILY_SKILL_COOCCURRENCE: (
        "Condition trên các job {category}{location_clause} có {anchor}: skill nào đồng xuất hiện nhiều nhất?",
        "Trong subset {category}{location_clause} dùng {anchor}, thường thấy thêm những công nghệ nào?",
        "Các JD {category}{location_clause} nhắc {anchor} thường kéo theo skill gì?",
        "Nếu filter job {category}{location_clause} theo {anchor}, top co-skill là gì?",
        "Quanh {anchor}, các kỹ năng đồng xuất hiện phổ biến trong {category}{location_clause} là gì?",
    ),
    FAMILY_CANDIDATE_SKILL_GAP: (
        "Giả sử profile đã có {known_skills}; so với demand của {category}{location_clause}, phần thiếu đáng chú ý là gì?",
        "Từ dữ liệu JD {category}{location_clause}, bỏ các skill mình đã có ({known_skills}) thì top demand còn lại là gì?",
        "Mình có {known_skills}. Market gap theo tần suất tuyển dụng của {category}{location_clause} còn những skill nào?",
        "Nếu loại {known_skills} khỏi ranking kỹ năng {category}{location_clause}, những skill nào đứng đầu?",
        "Đối chiếu profile {known_skills} với demand {category}{location_clause}: top missing skills là gì?",
    ),
}


@dataclass(frozen=True, slots=True)
class Scope:
    category: str
    location: str | None
    cohort_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Candidate:
    family: str
    latent_signature: str
    category: str
    location: str | None
    skills: tuple[str, ...]
    candidate_skills: tuple[str, ...]
    cohort_ids: tuple[str, ...]
    ground_truth: dict[str, Any]


def _humanize(value: str) -> str:
    return value.replace("_", " ")


def _location_clause(location: str | None) -> str:
    return f" ở {location}" if location else ""


def _boundary_is_stable(stats: Sequence[SkillStat], k: int) -> bool:
    if len(stats) < k:
        return False
    if len(stats) == k:
        return True
    return stats[k - 1].job_count != stats[k].job_count


def _scope_signature(category: str, location: str | None) -> str:
    return f"{category}::{location or '*'}"


def _skill_stat_map(stats: Sequence[SkillStat]) -> dict[str, SkillStat]:
    return {stat.skill: stat for stat in stats}


def _build_scopes(clusters: Sequence[OracleCluster], min_cohort: int) -> list[Scope]:
    scopes: list[Scope] = []
    categories = sorted({cluster.category for cluster in clusters if cluster.category})
    for category in categories:
        category_cohort = filter_cohort(clusters, category=category)
        if len(category_cohort) < min_cohort:
            continue
        scopes.append(Scope(category=category, location=None, cohort_ids=tuple(cluster.cluster_id for cluster in category_cohort)))
        locations = sorted({location for cluster in category_cohort for location in cluster.locations})
        for location in locations:
            cohort = filter_cohort(category_cohort, location=location)
            if len(cohort) >= min_cohort:
                scopes.append(Scope(category=category, location=location, cohort_ids=tuple(cluster.cluster_id for cluster in cohort)))
    return scopes


def _clusters_by_id(clusters: Sequence[OracleCluster]) -> dict[str, OracleCluster]:
    return {cluster.cluster_id: cluster for cluster in clusters}


def _scope_clusters(scope: Scope, cluster_map: dict[str, OracleCluster]) -> list[OracleCluster]:
    return [cluster_map[cluster_id] for cluster_id in scope.cohort_ids]


def _demand_candidate(scope: Scope, cohort: Sequence[OracleCluster], top_k: int,
                      min_skill_support: int) -> Candidate | None:
    stats = skill_distribution(cohort)
    if len(stats) < top_k or stats[0].job_count < min_skill_support or not _boundary_is_stable(stats, top_k):
        return None
    ground_truth = {"skill_stats": stats_to_json(stats), "top_k": top_k}
    signature = f"{FAMILY_SKILL_DEMAND}::{_scope_signature(scope.category, scope.location)}"
    return Candidate(FAMILY_SKILL_DEMAND, signature, scope.category, scope.location, (), (), scope.cohort_ids, ground_truth)


def _comparison_candidates(scope: Scope, cohort: Sequence[OracleCluster], min_skill_support: int,
                           min_gap_pp: float, max_skills: int = 12) -> list[Candidate]:
    stats = [stat for stat in skill_distribution(cohort) if stat.job_count >= min_skill_support][:max_skills]
    result: list[Candidate] = []
    for first, second in combinations(stats, 2):
        gap_pp = abs(first.coverage - second.coverage) * 100.0
        if gap_pp < min_gap_pp:
            continue
        winner = first.skill if first.coverage > second.coverage else second.skill
        ground_truth = {
            "skills": [
                {"skill": first.skill, "job_count": first.job_count, "coverage": first.coverage},
                {"skill": second.skill, "job_count": second.job_count, "coverage": second.coverage},
            ],
            "winner": winner,
            "coverage_gap_pp": gap_pp,
        }
        pair = tuple(sorted((first.skill, second.skill)))
        signature = f"{FAMILY_SKILL_COMPARISON}::{_scope_signature(scope.category, scope.location)}::{pair[0]}::{pair[1]}"
        result.append(Candidate(FAMILY_SKILL_COMPARISON, signature, scope.category, scope.location, pair, (), scope.cohort_ids, ground_truth))
    return result


def _cooccurrence_candidates(scope: Scope, cohort: Sequence[OracleCluster], top_k: int,
                             min_anchor_support: int, min_skill_support: int, max_anchors: int = 12) -> list[Candidate]:
    anchors = [stat for stat in skill_distribution(cohort) if stat.job_count >= min_anchor_support][:max_anchors]
    result: list[Candidate] = []
    for anchor in anchors:
        anchor_count, stats = skill_cooccurrence(cohort, anchor.skill)
        stats = [stat for stat in stats if stat.job_count >= min_skill_support]
        if len(stats) < top_k or not _boundary_is_stable(stats, top_k):
            continue
        ground_truth = {"anchor_skill": anchor.skill, "anchor_job_count": anchor_count, "skill_stats": stats_to_json(stats), "top_k": top_k}
        signature = f"{FAMILY_SKILL_COOCCURRENCE}::{_scope_signature(scope.category, scope.location)}::{anchor.skill}"
        result.append(Candidate(FAMILY_SKILL_COOCCURRENCE, signature, scope.category, scope.location, (anchor.skill,), (), scope.cohort_ids, ground_truth))
    return result


def _gap_candidates(scope: Scope, cohort: Sequence[OracleCluster], top_k: int,
                    min_skill_support: int, rng: random.Random, max_candidates: int = 8) -> list[Candidate]:
    stats = [stat for stat in skill_distribution(cohort) if stat.job_count >= min_skill_support]
    if len(stats) < top_k + 3:
        return []

    pool = [stat.skill for stat in stats[: min(12, len(stats))]]
    known_sets: set[tuple[str, ...]] = set()
    attempts = 0
    while len(known_sets) < max_candidates and attempts < 100:
        attempts += 1
        size = 2 if attempts % 2 else 3
        size = min(size, len(pool))
        known = tuple(sorted(rng.sample(pool, size)))
        if any(skill in pool[:5] for skill in known):
            known_sets.add(known)

    result: list[Candidate] = []
    for known in sorted(known_sets):
        missing = [stat for stat in stats if stat.skill not in known]
        if len(missing) < top_k or not _boundary_is_stable(missing, top_k):
            continue
        ground_truth = {"candidate_skills": list(known), "skill_stats": stats_to_json(missing), "top_k": top_k}
        signature = f"{FAMILY_CANDIDATE_SKILL_GAP}::{_scope_signature(scope.category, scope.location)}::{'|'.join(known)}"
        result.append(Candidate(FAMILY_CANDIDATE_SKILL_GAP, signature, scope.category, scope.location, (), known, scope.cohort_ids, ground_truth))
    return result


def _candidate_pool(clusters: Sequence[OracleCluster], *, top_k: int, min_cohort: int,
                    min_skill_support: int, min_anchor_support: int,
                    min_comparison_gap_pp: float, rng: random.Random) -> dict[str, list[Candidate]]:
    cluster_map = _clusters_by_id(clusters)
    pool = {family: [] for family in FAMILIES}
    for scope in _build_scopes(clusters, min_cohort):
        cohort = _scope_clusters(scope, cluster_map)
        demand = _demand_candidate(scope, cohort, top_k, min_skill_support)
        if demand:
            pool[FAMILY_SKILL_DEMAND].append(demand)
        pool[FAMILY_SKILL_COMPARISON].extend(
            _comparison_candidates(scope, cohort, min_skill_support, min_comparison_gap_pp)
        )
        pool[FAMILY_SKILL_COOCCURRENCE].extend(
            _cooccurrence_candidates(scope, cohort, top_k, min_anchor_support, min_skill_support)
        )
        pool[FAMILY_CANDIDATE_SKILL_GAP].extend(
            _gap_candidates(scope, cohort, top_k, min_skill_support, rng)
        )
    return pool


def _select_diverse(candidates: Sequence[Candidate], count: int, rng: random.Random) -> list[Candidate]:
    remaining = list(candidates)
    rng.shuffle(remaining)
    selected: list[Candidate] = []
    category_use: Counter[str] = Counter()
    location_use: Counter[str] = Counter()
    scope_use: Counter[tuple[str, str | None]] = Counter()

    while remaining and len(selected) < count:
        best_index = min(
            range(len(remaining)),
            key=lambda i: (
                scope_use[(remaining[i].category, remaining[i].location)],
                category_use[remaining[i].category],
                location_use[remaining[i].location or "*"],
                i,
            ),
        )
        item = remaining.pop(best_index)
        selected.append(item)
        category_use[item.category] += 1
        location_use[item.location or "*"] += 1
        scope_use[(item.category, item.location)] += 1

    if len(selected) < count:
        raise RuntimeError(f"Only {len(selected)} quality-gated candidates available; need {count}.")
    return selected


def _render(candidate: Candidate, split: str, rng: random.Random, query_index: int) -> dict[str, Any]:
    templates = DEV_TEMPLATES if split == "dev" else TEST_TEMPLATES
    family_templates = templates[candidate.family]
    template_index = query_index % len(family_templates)
    template = family_templates[template_index]
    category = _humanize(candidate.category)
    location_clause = _location_clause(candidate.location)

    values: dict[str, str] = {"category": category, "location_clause": location_clause}
    if candidate.family == FAMILY_SKILL_COMPARISON:
        values["skill_a"], values["skill_b"] = candidate.skills
    elif candidate.family == FAMILY_SKILL_COOCCURRENCE:
        values["anchor"] = candidate.skills[0]
    elif candidate.family == FAMILY_CANDIDATE_SKILL_GAP:
        values["known_skills"] = ", ".join(candidate.candidate_skills)

    query = template.format(**values)
    template_id = f"{split}_{candidate.family}_{template_index + 1:02d}"
    expected_plan = {
        "intent": candidate.family,
        "category": candidate.category,
        "location": candidate.location,
        "skills": list(candidate.skills),
        "candidate_skills": list(candidate.candidate_skills),
    }
    return {
        "query_id": f"CIQA-{split.upper()}-{query_index + 1:04d}",
        "split": split,
        "family": candidate.family,
        "query": query,
        "template_id": template_id,
        "latent_signature": candidate.latent_signature,
        "expected_plan": expected_plan,
        "oracle_cohort": {"cluster_count": len(candidate.cohort_ids), "cluster_ids": list(candidate.cohort_ids)},
        "ground_truth": candidate.ground_truth,
    }


def _sha256_jsonl(path: Path) -> str:
    return sha256_file(path)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=BACKEND_ROOT.parent, text=True).strip()
    except Exception:
        return None


def build_benchmark(*, dataset_dir: Path, output_dir: Path, seed: int, per_family_per_split: int,
                    top_k: int, min_cohort: int, min_skill_support: int, min_anchor_support: int,
                    min_comparison_gap_pp: float) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    clusters, csv_path = load_oracle_clusters(dataset_dir)

    clusters_path = output_dir / "clusters.jsonl"
    _write_jsonl(clusters_path, (
        {
            "cluster_id": cluster.cluster_id,
            "source_job_ids": list(cluster.source_job_ids),
            "category": cluster.category,
            "locations": list(cluster.locations),
            "skills": list(cluster.skills),
        }
        for cluster in clusters
    ))

    pool = _candidate_pool(
        clusters,
        top_k=top_k,
        min_cohort=min_cohort,
        min_skill_support=min_skill_support,
        min_anchor_support=min_anchor_support,
        min_comparison_gap_pp=min_comparison_gap_pp,
        rng=rng,
    )

    required_per_family = 2 * per_family_per_split
    selected_by_family: dict[str, list[Candidate]] = {}
    for family in FAMILIES:
        if len(pool[family]) < required_per_family:
            raise RuntimeError(
                f"{family}: only {len(pool[family])} quality-gated candidates; "
                f"need {required_per_family}. Do not lower gates blindly—inspect corpus coverage first."
            )
        selected_by_family[family] = _select_diverse(pool[family], required_per_family, rng)

    dev_candidates: list[Candidate] = []
    test_candidates: list[Candidate] = []
    for family in FAMILIES:
        selected = selected_by_family[family]
        dev_candidates.extend(selected[:per_family_per_split])
        test_candidates.extend(selected[per_family_per_split:])

    rng.shuffle(dev_candidates)
    rng.shuffle(test_candidates)

    dev_rows = [_render(candidate, "dev", rng, index) for index, candidate in enumerate(dev_candidates)]
    test_rows = [_render(candidate, "test", rng, index) for index, candidate in enumerate(test_candidates)]

    dev_path = output_dir / "dev.jsonl"
    test_queries_path = output_dir / "test_queries.jsonl"
    test_gold_path = output_dir / "test_gold.jsonl"
    _write_jsonl(dev_path, dev_rows)
    _write_jsonl(test_queries_path, (
        {"query_id": row["query_id"], "split": "test", "query": row["query"]} for row in test_rows
    ))
    _write_jsonl(test_gold_path, (
        {key: value for key, value in row.items() if key != "query"} for row in test_rows
    ))

    manifest = {
        "benchmark_version": BENCHMARK_VERSION,
        "seed": seed,
        "top_k": top_k,
        "per_family_per_split": per_family_per_split,
        "dev_queries": len(dev_rows),
        "test_queries": len(test_rows),
        "families": list(FAMILIES),
        "quality_gates": {
            "min_cohort": min_cohort,
            "min_skill_support": min_skill_support,
            "min_anchor_support": min_anchor_support,
            "min_comparison_gap_pp": min_comparison_gap_pp,
            "stable_top_k_boundary_required": True,
        },
        "corpus": {
            "dataset_file": csv_path.name,
            "dataset_sha256": sha256_file(csv_path),
            "raw_documents": sum(len(cluster.source_job_ids) for cluster in clusters),
            "duplicate_clusters": len(clusters),
            "clusters_sha256": sha256_file(clusters_path),
        },
        "artifacts": {
            "dev_sha256": sha256_file(dev_path),
            "test_queries_sha256": sha256_file(test_queries_path),
            "test_gold_sha256": sha256_file(test_gold_path),
        },
        "builder_commit": _git_commit(),
        "notes": [
            "Ground truth is generated by career_qa_oracle.py and does not call production market/planner/retrieval/answering code.",
            "Unit of market counting is exact-duplicate cluster, not chunk or raw document.",
            "A skill is counted at most once per duplicate cluster.",
            "DEV and TEST have disjoint latent signatures and disjoint template pools.",
            "No automatically generated challenge set is claimed as natural-language challenge data.",
        ],
    }
    with (output_dir / "manifest.json").open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2, sort_keys=True)

    print(f"Built {BENCHMARK_VERSION}")
    print(f"Dataset: {csv_path}")
    print(f"Raw docs: {manifest['corpus']['raw_documents']}")
    print(f"Duplicate clusters: {manifest['corpus']['duplicate_clusters']}")
    print(f"DEV: {len(dev_rows)}")
    print(f"TEST: {len(test_rows)}")
    for family in FAMILIES:
        print(f"{family}: DEV={sum(row['family'] == family for row in dev_rows)} TEST={sum(row['family'] == family for row in test_rows)}")
    print(f"Output: {output_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--per-family-per-split", type=int, default=DEFAULT_PER_FAMILY_PER_SPLIT)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--min-cohort", type=int, default=DEFAULT_MIN_COHORT)
    parser.add_argument("--min-skill-support", type=int, default=DEFAULT_MIN_SKILL_SUPPORT)
    parser.add_argument("--min-anchor-support", type=int, default=DEFAULT_MIN_ANCHOR_SUPPORT)
    parser.add_argument("--min-comparison-gap-pp", type=float, default=DEFAULT_MIN_COMPARISON_GAP_PP)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_benchmark(
        dataset_dir=args.dataset_dir, output_dir=args.output_dir, seed=args.seed,
        per_family_per_split=args.per_family_per_split, top_k=args.top_k, min_cohort=args.min_cohort,
        min_skill_support=args.min_skill_support, min_anchor_support=args.min_anchor_support,
        min_comparison_gap_pp=args.min_comparison_gap_pp,
    )


if __name__ == "__main__":
    main()
