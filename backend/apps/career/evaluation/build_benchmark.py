from __future__ import annotations

import ast
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from apps.career.normalization import normalize_key

from .vietjobs import VietJobsSource


BACKEND_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "benchmark"

DEFAULT_MAX_QUERIES = 300
DEFAULT_MIN_RELEVANT = 2
DEFAULT_MAX_RELEVANT = 20
DEFAULT_RANDOM_SEED = 42


def _parse_list_value(value: Any) -> list[str]:
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

        if isinstance(parsed, (list, tuple, set)):
            raw_items = list(parsed)
        else:
            raw_items = [parsed]

    else:
        raw_items = [value]

    result: list[str] = []

    for item in raw_items:
        normalized = normalize_key(str(item))
        if not normalized:
            continue

        if len(normalized) > 100:
            continue

        result.append(normalized)

    return list(dict.fromkeys(result))


def _parse_locations(value: str | None) -> list[str]:
    if not value:
        return []

    locations: list[str] = []
    for part in value.split(","):
        normalized = normalize_key(part)

        if normalized:
            locations.append(normalized)

    return list(dict.fromkeys(locations))


def _humanize_category(value: str) -> str:
    return value.replace("_", " ")


class VietJobsBenchmarkBuilder:
    FAMILY_CATEGORY_LOCATION = ("category_location")
    FAMILY_CATEGORY_SKILL = ("category_skill")
    FAMILY_LOCATION_SKILL = ("location_skill")

    def __init__(self, source: VietJobsSource | None = None) -> None:
        self.source = source or VietJobsSource()

    def build(
        self,
        *,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
        max_queries: int = DEFAULT_MAX_QUERIES,
        min_relevant: int = DEFAULT_MIN_RELEVANT,
        max_relevant: int = DEFAULT_MAX_RELEVANT,
        random_seed: int = DEFAULT_RANDOM_SEED,
    ) -> tuple[Path, Path]:

        if max_queries <= 0:
            raise ValueError("max_queries must be greater than 0")

        if min_relevant <= 0:
            raise ValueError("min_relevant must be greater than 0")

        if max_relevant < min_relevant:
            raise ValueError("max_relevant must be >= min_relevant")

        buckets = self._build_relevance_buckets()
        candidates = self._build_candidates(buckets=buckets, min_relevant=min_relevant, max_relevant=max_relevant)
        selected = self._balanced_sample(candidates=candidates, max_queries=max_queries, random_seed=random_seed)
        output_dir.mkdir(parents=True, exist_ok=True)
        queries_path = output_dir / "queries.jsonl"
        qrels_path = output_dir / "qrels.jsonl"
        manifest_path = output_dir / "manifest.json"
        self._write_queries(selected=selected, output_path=queries_path)
        self._write_qrels(selected=selected, output_path=qrels_path)
        self._write_manifest(selected=selected, output_path=manifest_path, min_relevant=min_relevant, max_relevant=max_relevant, random_seed=random_seed,)

        return (queries_path, qrels_path)

    def _build_relevance_buckets(self) -> dict[str,dict[tuple[str, str], set[str]]]:
        category_location: dict[tuple[str, str], set[str]] = defaultdict(set)
        category_skill: dict[tuple[str, str], set[str]] = defaultdict(set)
        location_skill: dict[tuple[str, str], set[str]] = defaultdict(set)
        for record in self.source.iter_records():
            doc_id = f"{record.source}:{record.source_job_id}"
            category = normalize_key(record.category_key)
            locations = _parse_locations(record.location_key)
            skills = _parse_list_value(record.metadata.get("technical_skills"))
            if category:
                for location in locations:
                    category_location[(category, location)].add(doc_id)

                for skill in skills:
                    category_skill[(category, skill)].add(doc_id)

            for location in locations:
                for skill in skills:
                    location_skill[(location, skill)].add(doc_id)

        return {
            self.FAMILY_CATEGORY_LOCATION: (category_location),
            self.FAMILY_CATEGORY_SKILL: (category_skill),
            self.FAMILY_LOCATION_SKILL: (location_skill),
        }

    def _build_candidates(
        self,
        *,
        buckets: dict[str,dict[tuple[str, str], set[str]]],
        min_relevant: int,
        max_relevant: int,
    ) -> dict[str, list[dict]]:
        candidates: dict[str, list[dict]] = {}
        for family, groups in buckets.items():
            family_candidates: list[dict] = []
            for labels, doc_ids in groups.items():
                relevance_count = len(doc_ids)

                if not min_relevant <= relevance_count <= max_relevant:
                    continue

                query, filters = self._make_query(family=family, labels=labels)
                family_candidates.append(
                    {
                        "family": family,
                        "query": query,
                        "filters": filters,
                        "relevant_doc_ids": (
                            sorted(doc_ids)
                        ),
                    }
                )

            candidates[family] = family_candidates

        return candidates

    def _make_query(self, *, family: str, labels: tuple[str, str]) -> tuple[str, dict]:
        first, second = labels
        if family == self.FAMILY_CATEGORY_LOCATION:
            category = first
            location = second

            return (
                (
                    "Tìm việc trong lĩnh vực "
                    f"{_humanize_category(category)} "
                    f"tại {location}."
                ),
                {
                    "category_key": category,
                    "location_key": location,
                },
            )

        if family == self.FAMILY_CATEGORY_SKILL:
            category = first
            skill = second

            return (
                (
                    "Tìm việc trong lĩnh vực "
                    f"{_humanize_category(category)} "
                    f"cần kỹ năng {skill}."
                ),
                {
                    "category_key": category,
                    "technical_skill": skill,
                },
            )

        if family == self.FAMILY_LOCATION_SKILL:
            location = first
            skill = second

            return (
                (
                    f"Tìm việc tại {location} "
                    f"cần kỹ năng {skill}."
                ),
                {
                    "location_key": location,
                    "technical_skill": skill,
                },
            )

        raise ValueError(f"Unknown benchmark family: {family}")

    @staticmethod
    def _balanced_sample(*, candidates: dict[str,list[dict]], max_queries: int, random_seed: int) -> list[dict]:
        rng = random.Random(random_seed)
        pools: dict[str, list[dict]] = {}

        for family, items in candidates.items():
            shuffled = list(items)
            rng.shuffle(shuffled)
            pools[family] = shuffled
        selected: list[dict] = []
        families = list(pools.keys())
        while (len(selected) < max_queries):
            added = False
            for family in families:
                if len(selected) >= max_queries:
                    break

                if not pools[family]:
                    continue

                selected.append(pools[family].pop())
                added = True

            if not added:
                break

        return selected

    @staticmethod
    def _write_queries(*, selected: list[dict], output_path: Path) -> None:
        with output_path.open("w", encoding="utf-8") as file:
            for index, item in enumerate(selected, start=1):
                query_id = f"VJ-{index:04d}"
                payload = {
                    "query_id": query_id,
                    "query": item["query"],
                    "family": item["family"],
                    "filters": item["filters"],
                    "num_relevant": len(item["relevant_doc_ids"]),
                }

                file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_qrels(*, selected: list[dict], output_path: Path) -> None:
        with output_path.open("w", encoding="utf-8") as file:
            for index, item in enumerate(selected, start=1):
                query_id = f"VJ-{index:04d}"

                for doc_id in item["relevant_doc_ids"]:
                    payload = {
                        "query_id": query_id,
                        "doc_id": doc_id,
                        "relevance": 1,
                    }

                    file.write(json.dumps(payload, ensure_ascii=False)+ "\n")

    @staticmethod
    def _write_manifest(*, selected: list[dict], output_path: Path, min_relevant: int, max_relevant: int, random_seed: int) -> None:
        family_counts: dict[str, int] = defaultdict(int)
        for item in selected:
            family_counts[item["family"]] += 1

        payload = {
            "dataset": "dinhieufam/VietJobs",
            "num_queries": len(selected),
            "min_relevant": min_relevant,
            "max_relevant": max_relevant,
            "random_seed": random_seed,
            "family_counts": dict(family_counts),
        }

        with output_path.open("w", encoding="utf-8",) as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    builder = VietJobsBenchmarkBuilder()
    queries_path, qrels_path = builder.build()
    print("Benchmark generated.")
    print(f"Queries: {queries_path}")
    print(f"Qrels:   {qrels_path}")


if __name__ == "__main__":
    main()