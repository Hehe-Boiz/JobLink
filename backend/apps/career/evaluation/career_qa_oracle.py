from __future__ import annotations

import ast
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from apps.career.normalization import normalize_job_text, normalize_key
from apps.career.evaluation.vietjobs import VietJobsSource


BENCHMARK_VERSION = "career-intelligence-qa-v1"
CLUSTER_PREFIX = "VJC-"

# Only high-confidence surface equivalences. Do not add broad "related skills" here.
SKILL_ALIASES = {
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node.js": "node.js",
    "springboot": "spring boot",
    "spring boot": "spring boot",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
}


@dataclass(frozen=True, slots=True)
class OracleCluster:
    cluster_id: str
    source_job_ids: tuple[str, ...]
    category: str | None
    locations: tuple[str, ...]
    skills: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SkillStat:
    skill: str
    job_count: int
    coverage: float


def parse_list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            parsed = text
        raw_items = list(parsed) if isinstance(parsed, (list, tuple, set)) else re.split(r"[,;|\n]+", str(parsed))
    else:
        raw_items = [value]

    result: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        normalized = normalize_key(str(item))
        if not normalized or len(normalized) > 100 or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def parse_locations(value: str | None) -> list[str]:
    if not value:
        return []
    result = [normalize_key(part) for part in value.split(",")]
    return list(dict.fromkeys(item for item in result if item))


def canonical_skill(value: str) -> str:
    normalized = normalize_key(value) or ""
    return SKILL_ALIASES.get(normalized, normalized)


def normalize_for_duplicate_fingerprint(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", normalize_job_text(value).casefold()).strip()


def duplicate_fingerprint(*, title: str, description: str, requirements: str, benefits: str, category: str | None,
                          locations: Sequence[str], raw_normalized_skills: Sequence[str]) -> str:
    # Keep this payload semantically aligned with build_freeform_benchmark_v2.py.
    # IMPORTANT: use normalized raw skills here, not canonical aliases, so duplicate cluster IDs remain compatible.
    payload = {
        "title": normalize_for_duplicate_fingerprint(title),
        "description": normalize_for_duplicate_fingerprint(description),
        "requirements": normalize_for_duplicate_fingerprint(requirements),
        "benefits": normalize_for_duplicate_fingerprint(benefits),
        "category": category or "",
        "locations": sorted(locations),
        "skills": sorted(raw_normalized_skills),
    }
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def cluster_id_from_fingerprint(fingerprint: str) -> str:
    return CLUSTER_PREFIX + fingerprint[:20]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_oracle_clusters(dataset_dir: Path) -> tuple[list[OracleCluster], Path]:
    source = VietJobsSource(dataset_dir)
    csv_path = source._find_dataset_csv()
    grouped: dict[str, dict[str, Any]] = {}

    for record in source.iter_records():
        category = normalize_key(record.category_key)
        locations = tuple(sorted(parse_locations(record.location_key)))
        raw_skills = parse_list_value(record.metadata.get("technical_skills"))
        canonical_skills = tuple(sorted(dict.fromkeys(canonical_skill(skill) for skill in raw_skills if canonical_skill(skill))))
        fingerprint = duplicate_fingerprint(
            title=record.title,
            description=record.description,
            requirements=record.requirements,
            benefits=record.benefits,
            category=category,
            locations=locations,
            raw_normalized_skills=raw_skills,
        )
        cluster_id = cluster_id_from_fingerprint(fingerprint)
        item = grouped.setdefault(cluster_id, {
            "source_job_ids": [],
            "category": category,
            "locations": locations,
            "skills": canonical_skills,
        })
        item["source_job_ids"].append(record.source_job_id)

        # A cryptographic duplicate fingerprint should imply identical benchmark fields.
        if item["category"] != category or item["locations"] != locations or item["skills"] != canonical_skills:
            raise ValueError(f"Inconsistent records inside duplicate cluster {cluster_id}")

    clusters = [
        OracleCluster(
            cluster_id=cluster_id,
            source_job_ids=tuple(sorted(item["source_job_ids"])),
            category=item["category"],
            locations=tuple(item["locations"]),
            skills=tuple(item["skills"]),
        )
        for cluster_id, item in sorted(grouped.items())
    ]
    return clusters, csv_path


def filter_cohort(clusters: Iterable[OracleCluster], *, category: str | None = None,
                  location: str | None = None) -> list[OracleCluster]:
    category_key = normalize_key(category)
    location_key = normalize_key(location)
    result: list[OracleCluster] = []
    for cluster in clusters:
        if category_key and cluster.category != category_key:
            continue
        if location_key and location_key not in cluster.locations:
            continue
        result.append(cluster)
    return result


def skill_distribution(clusters: Sequence[OracleCluster]) -> list[SkillStat]:
    cohort_size = len(clusters)
    if cohort_size == 0:
        return []

    counter: Counter[str] = Counter()
    for cluster in clusters:
        counter.update(set(cluster.skills))

    return [
        SkillStat(skill=skill, job_count=count, coverage=count / cohort_size)
        for skill, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]


def skill_cooccurrence(clusters: Sequence[OracleCluster], anchor_skill: str) -> tuple[int, list[SkillStat]]:
    anchor = canonical_skill(anchor_skill)
    anchor_clusters = [cluster for cluster in clusters if anchor in cluster.skills]
    anchor_count = len(anchor_clusters)
    if anchor_count == 0:
        return 0, []

    counter: Counter[str] = Counter()
    for cluster in anchor_clusters:
        counter.update(skill for skill in set(cluster.skills) if skill != anchor)

    stats = [
        SkillStat(skill=skill, job_count=count, coverage=count / anchor_count)
        for skill, count in sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ]
    return anchor_count, stats


def cluster_counts(clusters: Sequence[OracleCluster]) -> tuple[Counter[str], Counter[str]]:
    categories: Counter[str] = Counter()
    locations: Counter[str] = Counter()
    for cluster in clusters:
        if cluster.category:
            categories[cluster.category] += 1
        for location in cluster.locations:
            locations[location] += 1
    return categories, locations


def stats_to_json(stats: Sequence[SkillStat]) -> list[dict[str, Any]]:
    return [{"skill": stat.skill, "job_count": stat.job_count, "coverage": stat.coverage} for stat in stats]
