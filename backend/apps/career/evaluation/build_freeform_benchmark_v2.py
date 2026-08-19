from __future__ import annotations

import argparse
import ast
import hashlib
import json
import random
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from apps.career.normalization import (
    normalize_job_text,
    normalize_key,
)

from .vietjobs import VietJobsSource


BACKEND_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "benchmark_freeform_v2"

BENCHMARK_VERSION = "freeform-v2-strict"

DEFAULT_TOTAL_QUERIES = 600
DEFAULT_DEV_RATIO = 0.50
DEFAULT_MIN_RELEVANT_CLUSTERS = 2
DEFAULT_MAX_RELEVANT_CLUSTERS = 20
DEFAULT_MIN_HARD_NEGATIVES_TOTAL = 20
DEFAULT_MIN_HARD_NEGATIVES_PER_GROUP = 5
DEFAULT_RANDOM_SEED = 20260819

DEFAULT_MAX_CATEGORY_REUSE = 60
DEFAULT_MAX_LOCATION_REUSE = 12
DEFAULT_MAX_SKILL_REUSE = 4

DEFAULT_HARD_NEGATIVE_SAMPLE_SIZE = 50


FAMILY_CATEGORY_LOCATION = "category_location"
FAMILY_CATEGORY_SKILL = "category_skill"
FAMILY_LOCATION_SKILL = "location_skill"
FAMILY_CATEGORY_LOCATION_SKILL = "category_location_skill"

FAMILIES = (
    FAMILY_CATEGORY_LOCATION,
    FAMILY_CATEGORY_SKILL,
    FAMILY_LOCATION_SKILL,
    FAMILY_CATEGORY_LOCATION_SKILL,
)


CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "công_nghệ_thông_tin_kỹ_thuật_số": (
        "CNTT",
        "IT",
        "công nghệ thông tin",
    ),
}

LOCATION_ALIASES: dict[str, tuple[str, ...]] = {
    "hồ chí minh": (
        "TP.HCM",
        "HCM",
        "Sài Gòn",
    ),
    "thành phố hồ chí minh": (
        "TP.HCM",
        "HCM",
        "Sài Gòn",
    ),
    "tp. hồ chí minh": (
        "TP.HCM",
        "HCM",
        "Sài Gòn",
    ),
    "tp.hcm": (
        "TP.HCM",
        "HCM",
        "Sài Gòn",
    ),
    "hà nội": (
        "Hà Nội",
        "HN",
    ),
    "đà nẵng": ("Đà Nẵng",),
}


DEV_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    FAMILY_CATEGORY_LOCATION: (
        (
            "dev_cl_01",
            "Mình muốn tìm việc bên {category} ở {location}. Có vị trí nào phù hợp?",
        ),
        (
            "dev_cl_02",
            "Ở {location} có job nào thuộc mảng {category} không?",
        ),
        (
            "dev_cl_03",
            "Ưu tiên khu vực {location}, mình đang nhắm sang {category}.",
        ),
    ),
    FAMILY_CATEGORY_SKILL: (
        (
            "dev_cs_01",
            "Mình muốn làm mảng {category}, ưu tiên công việc có dùng {skill}.",
        ),
        (
            "dev_cs_02",
            "Có job {category} nào phù hợp với người có {skill} không?",
        ),
        (
            "dev_cs_03",
            "Đang tìm vị trí bên {category}; kỹ năng mình muốn tận dụng là {skill}.",
        ),
    ),
    FAMILY_LOCATION_SKILL: (
        (
            "dev_ls_01",
            "Ở {location} có công việc nào dùng {skill} không?",
        ),
        (
            "dev_ls_02",
            "Mình muốn làm ở {location}, thế mạnh là {skill}. Có job nào hợp?",
        ),
        (
            "dev_ls_03",
            "Ưu tiên {location}; tìm vị trí có liên quan đến {skill}.",
        ),
    ),
    FAMILY_CATEGORY_LOCATION_SKILL: (
        (
            "dev_cls_01",
            "Mình tìm việc {category} ở {location}, công việc nên có dùng {skill}.",
        ),
        (
            "dev_cls_02",
            "Ở {location} có job {category} nào phù hợp với kỹ năng {skill} không?",
        ),
        (
            "dev_cls_03",
            "Ưu tiên {location}, mảng {category}; thế mạnh của mình là {skill}.",
        ),
    ),
}

TEST_TEMPLATES: dict[str, tuple[tuple[str, str], ...]] = {
    FAMILY_CATEGORY_LOCATION: (
        (
            "test_cl_01",
            "{location} — mình đang nhắm mảng {category}, xem giúp các vị trí phù hợp.",
        ),
        (
            "test_cl_02",
            "Có gì cho người muốn theo {category} quanh {location}?",
        ),
        (
            "test_cl_03",
            "Muốn chuyển sang {category}; địa điểm làm việc mình ưu tiên là {location}.",
        ),
        (
            "test_cl_04",
            "Job {category} @ {location}, có lựa chọn nào đáng xem?",
        ),
        (
            "test_cl_05",
            "Khu vực {location}, mình chỉ quan tâm các vị trí thuộc {category}.",
        ),
    ),
    FAMILY_CATEGORY_SKILL: (
        (
            "test_cs_01",
            "{skill} là kỹ năng mình muốn tận dụng; có vị trí {category} nào hợp không?",
        ),
        (
            "test_cs_02",
            "{category}: tìm giúp job mà {skill} thực sự được dùng.",
        ),
        (
            "test_cs_03",
            "Nếu mình có {skill} và muốn theo {category} thì nên xem những job nào?",
        ),
        (
            "test_cs_04",
            "Job {category} + {skill}, lọc giúp các vị trí sát nhất.",
        ),
        (
            "test_cs_05",
            "Mình ưu tiên mảng {category}; profile mạnh ở {skill}.",
        ),
    ),
    FAMILY_LOCATION_SKILL: (
        (
            "test_ls_01",
            "{skill} + {location}, có vị trí nào đáng xem?",
        ),
        (
            "test_ls_02",
            "Mình muốn ở {location}; kỹ năng chính là {skill}.",
        ),
        (
            "test_ls_03",
            "Quanh {location}, lọc giúp các job có thể tận dụng {skill}.",
        ),
        (
            "test_ls_04",
            "Có việc nào ở {location} hợp với người mạnh {skill}?",
        ),
        (
            "test_ls_05",
            "Địa điểm: {location}. Kỹ năng muốn dùng: {skill}.",
        ),
    ),
    FAMILY_CATEGORY_LOCATION_SKILL: (
        (
            "test_cls_01",
            "{skill} là điểm mạnh của mình; quanh {location} có vị trí {category} nào hợp?",
        ),
        (
            "test_cls_02",
            "{category} | {location} | {skill} — lọc giúp các job sát nhất.",
        ),
        (
            "test_cls_03",
            "Mình muốn làm {category}, ở {location}; profile thiên về {skill}.",
        ),
        (
            "test_cls_04",
            "Quanh {location}, tìm job {category} mà người biết {skill} có lợi thế.",
        ),
        (
            "test_cls_05",
            "Ưu tiên {location}. Hướng nghề: {category}. Kỹ năng chính: {skill}.",
        ),
    ),
}


@dataclass(frozen=True, slots=True)
class IntentCandidate:
    family: str
    labels: tuple[str, ...]
    relevant_cluster_ids: tuple[str, ...]
    hard_negative_groups: dict[str, tuple[str, ...]]

    @property
    def intent_key(self) -> str:
        return self.family + "::" + "||".join(self.labels)

    @property
    def num_relevant(self) -> int:
        return len(self.relevant_cluster_ids)


@dataclass(frozen=True, slots=True)
class RenderedQuery:
    query_id: str
    split: str
    family: str
    query: str
    template_id: str
    surface_style: str
    intent_key: str
    labels: tuple[str, ...]
    relevant_cluster_ids: tuple[str, ...]
    hard_negative_groups: dict[str, tuple[str, ...]]


def _parse_list_value(
    value: Any,
) -> list[str]:
    if value is None:
        return []

    if isinstance(
        value,
        (list, tuple, set),
    ):
        raw_items = list(value)

    elif isinstance(
        value,
        str,
    ):
        text = value.strip()

        if not text:
            return []

        try:
            parsed = ast.literal_eval(text)
        except (
            ValueError,
            SyntaxError,
        ):
            parsed = text

        if isinstance(
            parsed,
            (list, tuple, set),
        ):
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


def _parse_locations(
    value: str | None,
) -> list[str]:
    if not value:
        return []

    result: list[str] = []

    for part in value.split(","):
        normalized = normalize_key(part)

        if normalized:
            result.append(normalized)

    return list(dict.fromkeys(result))


def _humanize_category(
    value: str,
) -> str:
    return value.replace(
        "_",
        " ",
    )


def _remove_diacritics(
    value: str,
) -> str:

    value = value.replace(
        "đ",
        "d",
    ).replace(
        "Đ",
        "D",
    )

    decomposed = unicodedata.normalize(
        "NFD",
        value,
    )

    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _normalize_for_duplicate_fingerprint(
    value: str | None,
) -> str:
    if not value:
        return ""

    return re.sub(
        r"\s+",
        " ",
        normalize_job_text(value).casefold(),
    ).strip()


def _duplicate_fingerprint(
    *,
    title: str,
    description: str,
    requirements: str,
    benefits: str,
    category: str | None,
    locations: list[str],
    skills: list[str],
) -> str:
    payload = {
        "title": (_normalize_for_duplicate_fingerprint(title)),
        "description": (_normalize_for_duplicate_fingerprint(description)),
        "requirements": (_normalize_for_duplicate_fingerprint(requirements)),
        "benefits": (_normalize_for_duplicate_fingerprint(benefits)),
        "category": category or "",
        "locations": sorted(locations),
        "skills": sorted(skills),
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _cluster_id_from_fingerprint(
    fingerprint: str,
) -> str:
    return "VJC-" + fingerprint[:20]


def _sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def _relevance_bin(
    count: int,
) -> str:
    if count == 2:
        return "2"

    if count <= 5:
        return "3-5"

    if count <= 10:
        return "6-10"

    return "11-20"


def _category_surface(
    category_key: str,
    *,
    style: str,
    rng: random.Random,
) -> str:
    canonical = _humanize_category(category_key)

    aliases = CATEGORY_ALIASES.get(
        category_key,
        (),
    )

    if (
        style
        in {
            "alias",
            "mixed",
        }
        and aliases
    ):
        return rng.choice(aliases)

    return canonical


def _location_surface(
    location_key: str,
    *,
    style: str,
    rng: random.Random,
) -> str:
    aliases = LOCATION_ALIASES.get(
        location_key,
        (),
    )

    if (
        style
        in {
            "alias",
            "mixed",
        }
        and aliases
    ):
        return rng.choice(aliases)

    return location_key


def _skill_surface(
    skill: str,
) -> str:

    return skill


def _surface_style_for_index(
    split: str,
    index: int,
) -> str:
    if split == "dev":
        styles = (
            "canonical",
            "canonical",
            "alias",
        )
    else:
        styles = (
            "canonical",
            "alias",
            "mixed",
            "no_diacritics",
            "canonical",
        )

    return styles[index % len(styles)]


def _render_query_text(
    candidate: IntentCandidate,
    *,
    split: str,
    ordinal: int,
    rng: random.Random,
) -> tuple[
    str,
    str,
    str,
]:
    template_pool = (DEV_TEMPLATES if split == "dev" else TEST_TEMPLATES)[candidate.family]

    (
        template_id,
        template,
    ) = template_pool[ordinal % len(template_pool)]

    style = _surface_style_for_index(
        split,
        ordinal,
    )

    category = None
    location = None
    skill = None

    if candidate.family == FAMILY_CATEGORY_LOCATION:
        (
            category,
            location,
        ) = candidate.labels

    elif candidate.family == FAMILY_CATEGORY_SKILL:
        (
            category,
            skill,
        ) = candidate.labels

    elif candidate.family == FAMILY_LOCATION_SKILL:
        (
            location,
            skill,
        ) = candidate.labels

    elif candidate.family == FAMILY_CATEGORY_LOCATION_SKILL:
        (
            category,
            location,
            skill,
        ) = candidate.labels

    else:
        raise ValueError(f"Unknown family: {candidate.family}")

    values = {
        "category": (
            _category_surface(
                category,
                style=style,
                rng=rng,
            )
            if category
            else ""
        ),
        "location": (
            _location_surface(
                location,
                style=style,
                rng=rng,
            )
            if location
            else ""
        ),
        "skill": (_skill_surface(skill) if skill else ""),
    }

    query = re.sub(
        r"\s+",
        " ",
        template.format(**values),
    ).strip()

    if style == "no_diacritics":
        query = _remove_diacritics(query)

    return (
        query,
        template_id,
        style,
    )


class VietJobsFreeFormBenchmarkBuilderV2:
    def __init__(
        self,
        source: VietJobsSource | None = None,
    ) -> None:
        self.source = source or VietJobsSource()

    def build(
        self,
        *,
        output_dir: Path = (DEFAULT_OUTPUT_DIR),
        total_queries: int = (DEFAULT_TOTAL_QUERIES),
        dev_ratio: float = (DEFAULT_DEV_RATIO),
        min_relevant: int = (DEFAULT_MIN_RELEVANT_CLUSTERS),
        max_relevant: int = (DEFAULT_MAX_RELEVANT_CLUSTERS),
        min_hard_total: int = (DEFAULT_MIN_HARD_NEGATIVES_TOTAL),
        min_hard_per_group: int = (DEFAULT_MIN_HARD_NEGATIVES_PER_GROUP),
        random_seed: int = (DEFAULT_RANDOM_SEED),
        max_category_reuse: int = (DEFAULT_MAX_CATEGORY_REUSE),
        max_location_reuse: int = (DEFAULT_MAX_LOCATION_REUSE),
        max_skill_reuse: int = (DEFAULT_MAX_SKILL_REUSE),
        allow_smaller: bool = False,
    ) -> dict:
        self._validate_args(
            total_queries=total_queries,
            dev_ratio=dev_ratio,
            min_relevant=min_relevant,
            max_relevant=max_relevant,
            min_hard_total=min_hard_total,
            min_hard_per_group=(min_hard_per_group),
            max_category_reuse=(max_category_reuse),
            max_location_reuse=(max_location_reuse),
            max_skill_reuse=(max_skill_reuse),
        )

        rng = random.Random(random_seed)

        dataset_csv = self.source._find_dataset_csv()

        dataset_fingerprint = {
            "path_name": (dataset_csv.name),
            "size_bytes": (dataset_csv.stat().st_size),
            "sha256": (_sha256_file(dataset_csv)),
        }

        print("Building duplicate clusters and field indexes...")

        indexes = self._build_indexes()

        print("Building candidates...")

        candidates_by_family = self._build_candidates(
            indexes=indexes,
            min_relevant=min_relevant,
            max_relevant=max_relevant,
            min_hard_total=(min_hard_total),
            min_hard_per_group=(min_hard_per_group),
        )

        availability = {family: len(items) for family, items in candidates_by_family.items()}

        print(
            "Candidate availability:",
            availability,
        )

        selected = self._balanced_select_round_robin(
            candidates_by_family=(candidates_by_family),
            total_queries=(total_queries),
            rng=rng,
            max_category_reuse=(max_category_reuse),
            max_location_reuse=(max_location_reuse),
            max_skill_reuse=(max_skill_reuse),
            allow_smaller=(allow_smaller),
        )

        (
            dev_candidates,
            test_candidates,
        ) = self._stratified_split(
            selected=selected,
            dev_ratio=dev_ratio,
            rng=rng,
        )

        dev_queries = self._render_split(
            dev_candidates,
            split="dev",
            rng=rng,
        )

        test_queries = self._render_split(
            test_candidates,
            split="test",
            rng=rng,
        )

        self._validate_rendered_benchmark(
            dev_queries=(dev_queries),
            test_queries=(test_queries),
            min_relevant=(min_relevant),
            max_relevant=(max_relevant),
            min_hard_total=(min_hard_total),
            min_hard_per_group=(min_hard_per_group),
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        dev_dir = output_dir / "dev"

        test_dir = output_dir / "test"

        dev_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        test_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        dev_paths = self._write_split(
            split_dir=dev_dir,
            queries=dev_queries,
        )

        test_paths = self._write_split(
            split_dir=test_dir,
            queries=test_queries,
        )

        cluster_map_path = output_dir / "doc_to_cluster.json"

        cluster_members_path = output_dir / "cluster_members.json"

        with cluster_map_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                indexes["doc_to_cluster"],
                file,
                ensure_ascii=False,
                indent=2,
            )

        with cluster_members_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                {cluster_id: sorted(members) for cluster_id, members in indexes["cluster_members"].items()},
                file,
                ensure_ascii=False,
                indent=2,
            )

        benchmark_card_path = output_dir / "BENCHMARK_CARD.md"

        judging_protocol_path = output_dir / "HUMAN_JUDGMENT_PROTOCOL.md"

        self._write_benchmark_card(benchmark_card_path)

        self._write_human_judgment_protocol(judging_protocol_path)

        generator_path = Path(__file__)

        generator_fingerprint = {
            "path_name": (generator_path.name),
            "sha256": (_sha256_file(generator_path) if generator_path.exists() else None),
        }

        manifest = self._build_manifest(
            dev_queries=dev_queries,
            test_queries=test_queries,
            random_seed=(random_seed),
            min_relevant=(min_relevant),
            max_relevant=(max_relevant),
            min_hard_total=(min_hard_total),
            min_hard_per_group=(min_hard_per_group),
            max_category_reuse=(max_category_reuse),
            max_location_reuse=(max_location_reuse),
            max_skill_reuse=(max_skill_reuse),
            availability=(availability),
            indexes=indexes,
            dataset_fingerprint=(dataset_fingerprint),
            generator_fingerprint=(generator_fingerprint),
        )

        manifest_path = output_dir / "manifest.json"

        with manifest_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                manifest,
                file,
                ensure_ascii=False,
                indent=2,
            )

        test_lock = {
            "benchmark_version": (BENCHMARK_VERSION),
            "policy": (
                "Freeze TEST before tuning. "
                "Do not inspect hidden TEST "
                "audit labels or qrels to choose "
                "models, parsers, routing logic, "
                "weights, thresholds, aliases, "
                "or templates."
            ),
            "dataset_sha256": (dataset_fingerprint["sha256"]),
            "generator_sha256": (generator_fingerprint["sha256"]),
            "queries_sha256": (_sha256_file(test_paths["queries"])),
            "qrels_clusters_sha256": (_sha256_file(test_paths["qrels_clusters"])),
            "audit_sha256": (_sha256_file(test_paths["audit"])),
            "hard_negatives_sha256": (_sha256_file(test_paths["hard_negatives"])),
            "doc_to_cluster_sha256": (_sha256_file(cluster_map_path)),
        }

        test_lock_path = output_dir / "test_lock.json"

        with test_lock_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                test_lock,
                file,
                ensure_ascii=False,
                indent=2,
            )

        print()
        print("Free-form benchmark v2 built.")
        print(f"Output: {output_dir}")
        print(f"DEV:  {len(dev_queries)}")
        print(f"TEST: {len(test_queries)}")
        print("Official strict evaluation unit: duplicate cluster.")
        print("Public query files expose ONLY query_id + query.")

        return manifest

    def _build_indexes(
        self,
    ) -> dict[str, Any]:
        category_clusters: dict[
            str,
            set[str],
        ] = defaultdict(set)

        location_clusters: dict[
            str,
            set[str],
        ] = defaultdict(set)

        skill_clusters: dict[
            str,
            set[str],
        ] = defaultdict(set)

        category_location: dict[
            tuple[str, str],
            set[str],
        ] = defaultdict(set)

        category_skill: dict[
            tuple[str, str],
            set[str],
        ] = defaultdict(set)

        location_skill: dict[
            tuple[str, str],
            set[str],
        ] = defaultdict(set)

        category_location_skill: dict[
            tuple[
                str,
                str,
                str,
            ],
            set[str],
        ] = defaultdict(set)

        doc_to_cluster: dict[
            str,
            str,
        ] = {}

        cluster_members: dict[
            str,
            set[str],
        ] = defaultdict(set)

        doc_count = 0

        for record in self.source.iter_records():
            doc_id = f"{record.source}:{record.source_job_id}"

            category = normalize_key(record.category_key)

            locations = _parse_locations(record.location_key)

            skills = _parse_list_value(record.metadata.get("technical_skills"))

            fingerprint = _duplicate_fingerprint(
                title=record.title,
                description=(record.description),
                requirements=(record.requirements),
                benefits=(record.benefits),
                category=category,
                locations=locations,
                skills=skills,
            )

            cluster_id = _cluster_id_from_fingerprint(fingerprint)

            doc_to_cluster[doc_id] = cluster_id

            cluster_members[cluster_id].add(doc_id)

            if category:
                category_clusters[category].add(cluster_id)

            for location in locations:
                location_clusters[location].add(cluster_id)

            for skill in skills:
                skill_clusters[skill].add(cluster_id)

            if category:
                for location in locations:
                    category_location[
                        (
                            category,
                            location,
                        )
                    ].add(cluster_id)

                for skill in skills:
                    category_skill[
                        (
                            category,
                            skill,
                        )
                    ].add(cluster_id)

                for location in locations:
                    for skill in skills:
                        category_location_skill[
                            (
                                category,
                                location,
                                skill,
                            )
                        ].add(cluster_id)

            for location in locations:
                for skill in skills:
                    location_skill[
                        (
                            location,
                            skill,
                        )
                    ].add(cluster_id)

            doc_count += 1

        duplicate_cluster_sizes = [len(members) for members in (cluster_members.values()) if len(members) > 1]

        return {
            "doc_count": (doc_count),
            "cluster_count": len(cluster_members),
            "duplicate_cluster_count": len(duplicate_cluster_sizes),
            "duplicate_doc_count": sum(size for size in (duplicate_cluster_sizes)),
            "max_duplicate_cluster_size": (
                max(
                    duplicate_cluster_sizes,
                    default=1,
                )
            ),
            "doc_to_cluster": (doc_to_cluster),
            "cluster_members": (cluster_members),
            "category_clusters": (category_clusters),
            "location_clusters": (location_clusters),
            "skill_clusters": (skill_clusters),
            FAMILY_CATEGORY_LOCATION: (category_location),
            FAMILY_CATEGORY_SKILL: (category_skill),
            FAMILY_LOCATION_SKILL: (location_skill),
            FAMILY_CATEGORY_LOCATION_SKILL: (category_location_skill),
        }

    def _build_candidates(
        self,
        *,
        indexes: dict[str, Any],
        min_relevant: int,
        max_relevant: int,
        min_hard_total: int,
        min_hard_per_group: int,
    ) -> dict[
        str,
        list[IntentCandidate],
    ]:
        result = {family: [] for family in FAMILIES}

        for family in FAMILIES:
            for (
                labels,
                positives,
            ) in indexes[family].items():
                if not (min_relevant <= len(positives) <= max_relevant):
                    continue

                hard_groups = self._hard_negative_groups(
                    family=family,
                    labels=labels,
                    positives=positives,
                    indexes=indexes,
                )

                if any(len(group) < min_hard_per_group for group in hard_groups.values()):
                    continue

                hard_union = {cluster_id for group in hard_groups.values() for cluster_id in group}

                if len(hard_union) < min_hard_total:
                    continue

                result[family].append(
                    IntentCandidate(
                        family=family,
                        labels=tuple(labels),
                        relevant_cluster_ids=tuple(sorted(positives)),
                        hard_negative_groups={name: tuple(sorted(group)) for name, group in hard_groups.items()},
                    )
                )

        return result

    @staticmethod
    def _hard_negative_groups(
        *,
        family: str,
        labels: tuple[str, ...],
        positives: set[str],
        indexes: dict[str, Any],
    ) -> dict[
        str,
        set[str],
    ]:
        category_clusters = indexes["category_clusters"]

        location_clusters = indexes["location_clusters"]

        skill_clusters = indexes["skill_clusters"]

        category_location = indexes[FAMILY_CATEGORY_LOCATION]

        category_skill = indexes[FAMILY_CATEGORY_SKILL]

        location_skill = indexes[FAMILY_LOCATION_SKILL]

        if family == FAMILY_CATEGORY_LOCATION:
            (
                category,
                location,
            ) = labels

            return {
                "category_not_location": (
                    category_clusters.get(
                        category,
                        set(),
                    )
                    - positives
                ),
                "location_not_category": (
                    location_clusters.get(
                        location,
                        set(),
                    )
                    - positives
                ),
            }

        if family == FAMILY_CATEGORY_SKILL:
            (
                category,
                skill,
            ) = labels

            return {
                "category_not_skill": (
                    category_clusters.get(
                        category,
                        set(),
                    )
                    - positives
                ),
                "skill_not_category": (
                    skill_clusters.get(
                        skill,
                        set(),
                    )
                    - positives
                ),
            }

        if family == FAMILY_LOCATION_SKILL:
            (
                location,
                skill,
            ) = labels

            return {
                "location_not_skill": (
                    location_clusters.get(
                        location,
                        set(),
                    )
                    - positives
                ),
                "skill_not_location": (
                    skill_clusters.get(
                        skill,
                        set(),
                    )
                    - positives
                ),
            }

        if family == FAMILY_CATEGORY_LOCATION_SKILL:
            (
                category,
                location,
                skill,
            ) = labels

            return {
                "category_location_not_skill": (
                    category_location.get(
                        (
                            category,
                            location,
                        ),
                        set(),
                    )
                    - positives
                ),
                "category_skill_not_location": (
                    category_skill.get(
                        (
                            category,
                            skill,
                        ),
                        set(),
                    )
                    - positives
                ),
                "location_skill_not_category": (
                    location_skill.get(
                        (
                            location,
                            skill,
                        ),
                        set(),
                    )
                    - positives
                ),
            }

        raise ValueError(f"Unknown family: {family}")

    def _balanced_select_round_robin(
        self,
        *,
        candidates_by_family: dict[
            str,
            list[IntentCandidate],
        ],
        total_queries: int,
        rng: random.Random,
        max_category_reuse: int,
        max_location_reuse: int,
        max_skill_reuse: int,
        allow_smaller: bool,
    ) -> list[IntentCandidate]:
        base = total_queries // len(FAMILIES)

        remainder = total_queries % len(FAMILIES)

        targets = {family: (base + (1 if index < remainder else 0)) for index, family in enumerate(FAMILIES)}

        ordered_by_family = {
            family: (
                self._balanced_candidate_order(
                    candidates_by_family[family],
                    rng=rng,
                )
            )
            for family in FAMILIES
        }

        cursors = {family: 0 for family in FAMILIES}

        selected_counts = {family: 0 for family in FAMILIES}

        category_reuse = Counter()
        location_reuse = Counter()
        skill_reuse = Counter()

        selected: list[IntentCandidate] = []

        while True:
            progressed = False

            for family in FAMILIES:
                if selected_counts[family] >= targets[family]:
                    continue

                items = ordered_by_family[family]

                while cursors[family] < len(items):
                    candidate = items[cursors[family]]

                    cursors[family] += 1

                    (
                        category,
                        location,
                        skill,
                    ) = self._candidate_components(candidate)

                    if category and category_reuse[category] >= max_category_reuse:
                        continue

                    if location and location_reuse[location] >= max_location_reuse:
                        continue

                    if skill and skill_reuse[skill] >= max_skill_reuse:
                        continue

                    selected.append(candidate)

                    selected_counts[family] += 1

                    if category:
                        category_reuse[category] += 1

                    if location:
                        location_reuse[location] += 1

                    if skill:
                        skill_reuse[skill] += 1

                    progressed = True
                    break

            if all(selected_counts[family] >= targets[family] for family in FAMILIES):
                break

            if not progressed:
                break

        deficits = {
            family: (targets[family] - selected_counts[family])
            for family in FAMILIES
            if (selected_counts[family] < targets[family])
        }

        if deficits and not allow_smaller:
            raise RuntimeError(
                "Could not satisfy balanced "
                "benchmark targets under reuse "
                f"constraints. Deficits={deficits}. "
                "Do not silently weaken the "
                "benchmark; inspect availability "
                "or explicitly use --allow-smaller."
            )

        return selected

    @staticmethod
    def _balanced_candidate_order(
        candidates: list[IntentCandidate],
        *,
        rng: random.Random,
    ) -> list[IntentCandidate]:
        bins: dict[
            str,
            list[IntentCandidate],
        ] = defaultdict(list)

        for candidate in candidates:
            bins[_relevance_bin(candidate.num_relevant)].append(candidate)

        for values in bins.values():
            rng.shuffle(values)

        order = (
            "2",
            "3-5",
            "6-10",
            "11-20",
        )

        output: list[IntentCandidate] = []

        while True:
            added = False

            for key in order:
                if not bins[key]:
                    continue

                output.append(bins[key].pop())

                added = True

            if not added:
                break

        return output

    @staticmethod
    def _candidate_components(
        candidate: IntentCandidate,
    ) -> tuple[
        str | None,
        str | None,
        str | None,
    ]:
        if candidate.family == FAMILY_CATEGORY_LOCATION:
            category, location = candidate.labels

            return (
                category,
                location,
                None,
            )

        if candidate.family == FAMILY_CATEGORY_SKILL:
            category, skill = candidate.labels

            return (
                category,
                None,
                skill,
            )

        if candidate.family == FAMILY_LOCATION_SKILL:
            location, skill = candidate.labels

            return (
                None,
                location,
                skill,
            )

        if candidate.family == FAMILY_CATEGORY_LOCATION_SKILL:
            (
                category,
                location,
                skill,
            ) = candidate.labels

            return (
                category,
                location,
                skill,
            )

        raise ValueError(f"Unknown family: {candidate.family}")

    def _stratified_split(
        self,
        *,
        selected: list[IntentCandidate],
        dev_ratio: float,
        rng: random.Random,
    ) -> tuple[
        list[IntentCandidate],
        list[IntentCandidate],
    ]:
        strata: dict[
            tuple[str, str],
            list[IntentCandidate],
        ] = defaultdict(list)

        for candidate in selected:
            strata[
                (
                    candidate.family,
                    _relevance_bin(candidate.num_relevant),
                )
            ].append(candidate)

        dev: list[IntentCandidate] = []

        test: list[IntentCandidate] = []

        for (
            _stratum,
            items,
        ) in sorted(strata.items()):
            items = list(items)

            rng.shuffle(items)

            if len(items) == 1:
                if len(dev) <= len(test):
                    dev.extend(items)
                else:
                    test.extend(items)

                continue

            dev_count = int(round(len(items) * dev_ratio))

            dev_count = min(
                max(
                    dev_count,
                    1,
                ),
                len(items) - 1,
            )

            dev.extend(items[:dev_count])

            test.extend(items[dev_count:])

        rng.shuffle(dev)

        rng.shuffle(test)

        return (
            dev,
            test,
        )

    def _render_split(
        self,
        candidates: list[IntentCandidate],
        *,
        split: str,
        rng: random.Random,
    ) -> list[RenderedQuery]:
        by_family_counter = Counter()

        output: list[RenderedQuery] = []

        for global_index, candidate in enumerate(
            candidates,
            start=1,
        ):
            ordinal = by_family_counter[candidate.family]

            (
                query,
                template_id,
                style,
            ) = _render_query_text(
                candidate,
                split=split,
                ordinal=ordinal,
                rng=rng,
            )

            prefix = "D" if split == "dev" else "T"

            query_id = f"FFB2-{prefix}-{global_index:04d}"

            output.append(
                RenderedQuery(
                    query_id=query_id,
                    split=split,
                    family=(candidate.family),
                    query=query,
                    template_id=(template_id),
                    surface_style=(style),
                    intent_key=(candidate.intent_key),
                    labels=(candidate.labels),
                    relevant_cluster_ids=(candidate.relevant_cluster_ids),
                    hard_negative_groups=(candidate.hard_negative_groups),
                )
            )

            by_family_counter[candidate.family] += 1

        return output

    @staticmethod
    def _write_split(
        *,
        split_dir: Path,
        queries: list[RenderedQuery],
    ) -> dict[str, Path]:
        queries_path = split_dir / "queries.jsonl"

        qrels_clusters_path = split_dir / "qrels.clusters.jsonl"

        audit_path = split_dir / "intents.audit.jsonl"

        hard_negatives_path = split_dir / "hard_negatives.audit.jsonl"

        with queries_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for item in queries:
                file.write(
                    json.dumps(
                        {
                            "query_id": (item.query_id),
                            "query": (item.query),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        with qrels_clusters_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for item in queries:
                for cluster_id in item.relevant_cluster_ids:
                    file.write(
                        json.dumps(
                            {
                                "query_id": (item.query_id),
                                "cluster_id": (cluster_id),
                                "relevance": 1,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

        with audit_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for item in queries:
                hard_union = {cluster_id for values in (item.hard_negative_groups.values()) for cluster_id in values}

                file.write(
                    json.dumps(
                        {
                            "query_id": (item.query_id),
                            "split": (item.split),
                            "family": (item.family),
                            "intent_key": (item.intent_key),
                            "canonical_labels": list(item.labels),
                            "template_id": (item.template_id),
                            "surface_style": (item.surface_style),
                            "num_relevant_clusters": len(item.relevant_cluster_ids),
                            "relevance_bin": (_relevance_bin(len(item.relevant_cluster_ids))),
                            "num_hard_negative_clusters": len(hard_union),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        with hard_negatives_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            for item in queries:
                groups = {
                    name: {
                        "count": len(cluster_ids),
                        "sample_cluster_ids": list(cluster_ids[:DEFAULT_HARD_NEGATIVE_SAMPLE_SIZE]),
                    }
                    for name, cluster_ids in item.hard_negative_groups.items()
                }

                file.write(
                    json.dumps(
                        {
                            "query_id": (item.query_id),
                            "groups": groups,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        return {
            "queries": (queries_path),
            "qrels_clusters": (qrels_clusters_path),
            "audit": (audit_path),
            "hard_negatives": (hard_negatives_path),
        }

    @staticmethod
    def _validate_rendered_benchmark(
        *,
        dev_queries: list[RenderedQuery],
        test_queries: list[RenderedQuery],
        min_relevant: int,
        max_relevant: int,
        min_hard_total: int,
        min_hard_per_group: int,
    ) -> None:
        if not dev_queries:
            raise RuntimeError("DEV split is empty.")

        if not test_queries:
            raise RuntimeError("TEST split is empty.")

        all_queries = dev_queries + test_queries

        query_ids = [item.query_id for item in all_queries]

        if len(query_ids) != len(set(query_ids)):
            raise RuntimeError("Duplicate query IDs.")

        normalized_query_texts = [
            re.sub(
                r"\s+",
                " ",
                item.query.casefold().strip(),
            )
            for item in all_queries
        ]

        if len(normalized_query_texts) != len(set(normalized_query_texts)):
            raise RuntimeError("Duplicate query texts.")

        dev_intents = {item.intent_key for item in dev_queries}

        test_intents = {item.intent_key for item in test_queries}

        if dev_intents & test_intents:
            raise RuntimeError("Full-intent leakage across DEV/TEST.")

        dev_template_ids = {item.template_id for item in dev_queries}

        test_template_ids = {item.template_id for item in test_queries}

        if dev_template_ids & test_template_ids:
            raise RuntimeError("Template leakage across DEV/TEST.")

        for split_name, items in (
            (
                "DEV",
                dev_queries,
            ),
            (
                "TEST",
                test_queries,
            ),
        ):
            family_counts = Counter(item.family for item in items)

            missing_families = [family for family in FAMILIES if family_counts[family] == 0]

            if missing_families:
                raise RuntimeError(f"{split_name} is missing families: {missing_families}")

        for item in all_queries:
            relevant_count = len(item.relevant_cluster_ids)

            if not (min_relevant <= relevant_count <= max_relevant):
                raise RuntimeError(f"Invalid relevant-cluster count for {item.query_id}: {relevant_count}")

            hard_union = {cluster_id for values in (item.hard_negative_groups.values()) for cluster_id in values}

            if len(hard_union) < min_hard_total:
                raise RuntimeError(f"Insufficient total hard negatives for {item.query_id}")

            for (
                group_name,
                values,
            ) in item.hard_negative_groups.items():
                if len(values) < min_hard_per_group:
                    raise RuntimeError(f"Insufficient hard-negative group {group_name} for {item.query_id}")

    @staticmethod
    def _build_manifest(
        *,
        dev_queries: list[RenderedQuery],
        test_queries: list[RenderedQuery],
        random_seed: int,
        min_relevant: int,
        max_relevant: int,
        min_hard_total: int,
        min_hard_per_group: int,
        max_category_reuse: int,
        max_location_reuse: int,
        max_skill_reuse: int,
        availability: dict[
            str,
            int,
        ],
        indexes: dict[
            str,
            Any,
        ],
        dataset_fingerprint: dict,
        generator_fingerprint: dict,
    ) -> dict:
        def summarize(
            items: Iterable[RenderedQuery],
        ) -> dict:
            items = list(items)

            family_counts = Counter(item.family for item in items)

            category_counts = Counter()
            location_counts = Counter()
            skill_counts = Counter()

            relevance_bins = Counter(_relevance_bin(len(item.relevant_cluster_ids)) for item in items)

            styles = Counter(item.surface_style for item in items)

            for item in items:
                (
                    category,
                    location,
                    skill,
                ) = VietJobsFreeFormBenchmarkBuilderV2._candidate_components(
                    IntentCandidate(
                        family=item.family,
                        labels=item.labels,
                        relevant_cluster_ids=(item.relevant_cluster_ids),
                        hard_negative_groups=(item.hard_negative_groups),
                    )
                )

                if category:
                    category_counts[category] += 1

                if location:
                    location_counts[location] += 1

                if skill:
                    skill_counts[skill] += 1

            relevant_counts = [len(item.relevant_cluster_ids) for item in items]

            return {
                "num_queries": (len(items)),
                "family_counts": dict(family_counts),
                "relevance_bins": dict(relevance_bins),
                "surface_style_counts": dict(styles),
                "unique_categories": len(category_counts),
                "unique_locations": len(location_counts),
                "unique_skills": len(skill_counts),
                "top_categories": (category_counts.most_common(10)),
                "top_locations": (location_counts.most_common(10)),
                "top_skills": (skill_counts.most_common(10)),
                "relevant_clusters_per_query": {
                    "min": min(relevant_counts),
                    "mean": (sum(relevant_counts) / len(relevant_counts)),
                    "max": max(relevant_counts),
                },
            }

        return {
            "benchmark_version": (BENCHMARK_VERSION),
            "dataset": ("dinhieufam/VietJobs"),
            "dataset_fingerprint": (dataset_fingerprint),
            "generator_fingerprint": (generator_fingerprint),
            "retrieval_unit": ("exact-duplicate equivalence cluster"),
            "ground_truth_construct": ("strict canonical metadata constraint satisfaction"),
            "ground_truth_is_human_judged": (False),
            "random_seed": (random_seed),
            "actual_total_queries": (len(dev_queries) + len(test_queries)),
            "candidate_availability": (availability),
            "corpus": {
                "document_count": (indexes["doc_count"]),
                "cluster_count": (indexes["cluster_count"]),
                "duplicate_cluster_count": (indexes["duplicate_cluster_count"]),
                "duplicate_doc_count": (indexes["duplicate_doc_count"]),
                "max_duplicate_cluster_size": (indexes["max_duplicate_cluster_size"]),
            },
            "constraints": {
                "min_relevant_clusters": (min_relevant),
                "max_relevant_clusters": (max_relevant),
                "min_hard_negatives_total": (min_hard_total),
                "min_hard_negatives_per_group": (min_hard_per_group),
                "max_category_reuse": (max_category_reuse),
                "max_location_reuse": (max_location_reuse),
                "max_skill_reuse": (max_skill_reuse),
            },
            "split_policy": {
                "full_intent_disjoint": True,
                "template_disjoint": True,
                "stratified_by_family_and_relevance_bin": (True),
                "component_labels_may_overlap": (True),
                "public_query_file_contains_family": (False),
                "public_query_id_encodes_intent": (False),
                "dev_for_tuning": True,
                "test_frozen": True,
            },
            "limitations": [
                ("Strict metadata qrels can mark semantically equivalent unlabelled jobs as non-relevant."),
                ("Source taxonomy errors are inherited by automatic qrels."),
                (
                    "Skill wording is mostly "
                    "canonical, so this strict track "
                    "does not fully test semantic "
                    "skill synonym understanding."
                ),
                (
                    "The benchmark intentionally "
                    "selects focused intents with "
                    "2-20 relevant clusters; it is "
                    "not a broad-query benchmark."
                ),
                (
                    "A separate human-judged "
                    "semantic track is required "
                    "before claiming general "
                    "production relevance quality."
                ),
            ],
            "dev": summarize(dev_queries),
            "test": summarize(test_queries),
        }

    @staticmethod
    def _write_benchmark_card(
        path: Path,
    ) -> None:
        path.write_text(
            """# JobLink VietJobs Free-Form Benchmark v2 — Strict Track

## What this benchmark measures

This is a **strict constraint-satisfaction retrieval benchmark** over VietJobs.

It tests whether a retriever can recover job listings satisfying conjunctions
of canonical structured constraints when users express those constraints with
varied surface wording.

Query families:

1. category + location
2. category + skill
3. location + skill
4. category + location + skill

## What it does NOT measure

This is NOT a complete human relevance benchmark.

Automatic qrels inherit source metadata quality. A semantically appropriate job
with an equivalent but differently-labelled skill can be a false negative.
A source category error can also create a wrong positive.

Therefore do NOT present this strict score as "human relevance accuracy".

## Public-vs-hidden files

Public retrieval input:

- `queries.jsonl`: `query_id`, `query` only.

Hidden/audit files:

- `intents.audit.jsonl`
- `hard_negatives.audit.jsonl`
- `qrels.clusters.jsonl`

The public file intentionally does NOT expose `family`, canonical filters, or
canonical labels.

## Duplicate handling

Exact duplicate job records are mapped to equivalence clusters using normalized
title, description, requirements, benefits, category, locations, and skills.

Official strict evaluation is cluster-level:

1. map each retrieved document ID through `doc_to_cluster.json`,
2. collapse duplicate cluster IDs while preserving first occurrence,
3. score the cluster ranking against `qrels.clusters.jsonl`.

This prevents duplicate listings from artificially inflating or depressing
retrieval metrics.

## Hard negatives

Every query must have near-miss clusters for EACH required contrast.

For example, category + location + skill requires:

- correct category + location, wrong skill,
- correct category + skill, wrong location,
- correct location + skill, wrong category.

Candidates that do not have enough hard negatives in every group are excluded.

## DEV / TEST

DEV and TEST are:

- disjoint by full canonical intent,
- disjoint by template pool,
- stratified by query family and relevant-set cardinality.

Individual components such as a skill or location MAY appear in both splits.
Therefore this tests unseen combinations/surface forms, not unseen vocabulary.

If you need lexical OOD generalization, build an additional held-out-skill
challenge split.

## Metric protocol

Because relevant-set size ranges from 2 to 20:

Primary ranking metrics:

- nDCG@10
- MRR@10
- Recall@20

Secondary:

- Recall@5
- Recall@10, reported together with relevance-cardinality bins.

Important: Recall@10 cannot reach 1.0 for a query with more than 10 relevant
clusters. Never compare aggregate Recall@10 without also reporting the qrel
cardinality distribution.

## Freeze protocol

Tune only on DEV.

Before any TEST-based model changes, freeze:

- corpus fingerprint,
- generator fingerprint,
- test queries,
- test cluster qrels,
- test audit metadata.

`test_lock.json` records their hashes.

If you inspect TEST outcomes and then modify parser/retriever logic, TEST has
become development data and must no longer be reported as a held-out score.

## Required companion evaluation

Before claiming production-grade Career RAG retrieval quality, add a separate
human-judged semantic relevance track using pooled candidates from multiple
retrieval systems.

See `HUMAN_JUDGMENT_PROTOCOL.md`.
""",
            encoding="utf-8",
        )

    @staticmethod
    def _write_human_judgment_protocol(
        path: Path,
    ) -> None:
        path.write_text(
            """# Human-Judged Semantic Retrieval Track — Protocol

The strict benchmark is reproducible but cannot replace human relevance
judgments.

## Goal

Create a second, smaller TEST set that evaluates whether returned jobs are
actually useful for a human information need, including semantic equivalents
that metadata-exact qrels miss.

## Query source

Prefer 100-200 natural queries written independently from the strict template
generator.

Use:

- real anonymized user queries when available,
- otherwise human-written queries from multiple writers,
- multiple constraint types,
- abbreviations,
- Vietnamese without diacritics,
- code-switching,
- multiple skills,
- experience constraints,
- soft preferences,
- OR / exclusion cases.

Do not write queries while looking at a specific retrieval system's results.

## Candidate pooling

For each query, pool top candidates from diverse systems, for example:

- BM25,
- dense E5-small,
- E2.1 hybrid,
- E3 field-aware,
- one reranker system if available.

Deduplicate equivalent job listings before judgment.

The judge must not know which system retrieved a candidate.

## Judgment scale

Recommended graded scale:

- 0 = not relevant / violates a required constraint,
- 1 = partially relevant / plausible but misses an important preference,
- 2 = relevant,
- 3 = highly relevant / strong match to the information need.

Record a short reason for 0 and ambiguous 1 judgments.

## Quality control

Use at least two independent judges on a substantial subset.

Report agreement.

Adjudicate disagreements before freezing the final TEST qrels.

Keep the judgment rubric frozen.

## Evaluation

Use graded nDCG@10 as the primary metric.

Also report:

- Recall@20 where judged pools permit it,
- MRR@10,
- Success@5,
- hard-constraint violation rate,
- duplicate intrusion rate.

## Reporting

Always separate:

1. strict automatic metadata score,
2. human-judged semantic score.

Never merge them into a single headline number.
""",
            encoding="utf-8",
        )

    @staticmethod
    def _validate_args(
        *,
        total_queries: int,
        dev_ratio: float,
        min_relevant: int,
        max_relevant: int,
        min_hard_total: int,
        min_hard_per_group: int,
        max_category_reuse: int,
        max_location_reuse: int,
        max_skill_reuse: int,
    ) -> None:
        if total_queries < len(FAMILIES) * 2:
            raise ValueError("total_queries too small.")

        if not (0.0 < dev_ratio < 1.0):
            raise ValueError("dev_ratio must be between 0 and 1.")

        if min_relevant <= 0:
            raise ValueError("min_relevant must be > 0.")

        if max_relevant < min_relevant:
            raise ValueError("max_relevant must be >= min_relevant.")

        if min_hard_total < 0 or min_hard_per_group < 0:
            raise ValueError("hard-negative minimums must be >= 0.")

        if any(
            value <= 0
            for value in (
                max_category_reuse,
                max_location_reuse,
                max_skill_reuse,
            )
        ):
            raise ValueError("reuse limits must be > 0.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Build JobLink VietJobs Free-Form Benchmark v2 (strict cluster-level track)")
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    parser.add_argument(
        "--total-queries",
        type=int,
        default=DEFAULT_TOTAL_QUERIES,
    )

    parser.add_argument(
        "--dev-ratio",
        type=float,
        default=DEFAULT_DEV_RATIO,
    )

    parser.add_argument(
        "--min-relevant",
        type=int,
        default=(DEFAULT_MIN_RELEVANT_CLUSTERS),
    )

    parser.add_argument(
        "--max-relevant",
        type=int,
        default=(DEFAULT_MAX_RELEVANT_CLUSTERS),
    )

    parser.add_argument(
        "--min-hard-total",
        type=int,
        default=(DEFAULT_MIN_HARD_NEGATIVES_TOTAL),
    )

    parser.add_argument(
        "--min-hard-per-group",
        type=int,
        default=(DEFAULT_MIN_HARD_NEGATIVES_PER_GROUP),
    )

    parser.add_argument(
        "--max-category-reuse",
        type=int,
        default=(DEFAULT_MAX_CATEGORY_REUSE),
    )

    parser.add_argument(
        "--max-location-reuse",
        type=int,
        default=(DEFAULT_MAX_LOCATION_REUSE),
    )

    parser.add_argument(
        "--max-skill-reuse",
        type=int,
        default=(DEFAULT_MAX_SKILL_REUSE),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
    )

    parser.add_argument(
        "--allow-smaller",
        action="store_true",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    builder = VietJobsFreeFormBenchmarkBuilderV2()

    builder.build(
        output_dir=(args.output_dir),
        total_queries=(args.total_queries),
        dev_ratio=(args.dev_ratio),
        min_relevant=(args.min_relevant),
        max_relevant=(args.max_relevant),
        min_hard_total=(args.min_hard_total),
        min_hard_per_group=(args.min_hard_per_group),
        random_seed=(args.seed),
        max_category_reuse=(args.max_category_reuse),
        max_location_reuse=(args.max_location_reuse),
        max_skill_reuse=(args.max_skill_reuse),
        allow_smaller=(args.allow_smaller),
    )


if __name__ == "__main__":
    main()
