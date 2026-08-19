from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from django.db.models import Q

from .models import CareerJobChunk
from .normalization import normalize_key


# ============================================================
# Domain
# ============================================================


@dataclass(frozen=True, slots=True)
class CareerMarketJob:
    source: str
    source_job_id: str
    job_title: str
    category_key: str | None
    location_key: str | None
    experience_level: str | None
    employment_type: str | None
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class SkillStat:
    skill: str
    job_count: int
    coverage: float


@dataclass(frozen=True, slots=True)
class SkillDistributionResult:
    cohort_size: int
    skills: tuple[SkillStat, ...]


@dataclass(frozen=True, slots=True)
class SkillComparisonResult:
    cohort_size: int
    first: SkillStat
    second: SkillStat
    winner: str | None
    job_count_difference: int
    coverage_difference: float


@dataclass(frozen=True, slots=True)
class SkillCooccurrenceResult:
    cohort_size: int
    anchor_skill: str
    anchor_job_count: int
    skills: tuple[SkillStat, ...]


@dataclass(frozen=True, slots=True)
class CandidateSkillGapResult:
    cohort_size: int
    candidate_skills: tuple[str, ...]
    recommended_skills: tuple[SkillStat, ...]


# ============================================================
# Conservative skill normalization
# ============================================================


SKILL_ALIASES: dict[str, str] = {
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "react": "React",
    "springboot": "Spring Boot",
    "spring boot": "Spring Boot",
    "spring": "Spring",
    "dotnet": ".NET",
    ".net": ".NET",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
}


def _skill_key(value: str) -> str:
    normalized = normalize_key(value)

    if normalized is None:
        return ""

    normalized = re.sub(r"\s+", " ", normalized)

    canonical = SKILL_ALIASES.get(normalized)

    if canonical is not None:
        return canonical.casefold()

    return normalized.casefold()


def canonicalize_skill(value: str) -> str:
    text = value.strip()

    if not text:
        return ""

    normalized = normalize_key(text)

    if normalized is None:
        return ""

    normalized = re.sub(r"\s+", " ", normalized)

    canonical = SKILL_ALIASES.get(normalized)

    if canonical is not None:
        return canonical

    # Giữ tên gốc cho skill chưa có alias.
    return text


def parse_technical_skills(value: Any) -> tuple[str, ...]:
    """
    technical_skills trong VietJobs có thể là:
      - list
      - tuple
      - string biểu diễn list
      - chuỗi comma/semicolon separated
    """

    if value is None:
        return ()

    raw_items: Iterable[Any]

    if isinstance(value, (list, tuple, set)):
        raw_items = value

    elif isinstance(value, str):
        text = value.strip()

        if not text:
            return ()

        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            parsed = None

        if isinstance(parsed, (list, tuple, set)):
            raw_items = parsed
        else:
            raw_items = re.split(
                r"[,;|\n]+",
                text,
            )

    else:
        raw_items = (value,)

    result: list[str] = []
    seen: set[str] = set()

    for item in raw_items:
        skill = canonicalize_skill(str(item))

        if not skill:
            continue

        key = _skill_key(skill)

        if not key or key in seen:
            continue

        seen.add(key)
        result.append(skill)

    return tuple(result)


# ============================================================
# Repository abstraction
# ============================================================


class CareerMarketRepository(Protocol):
    def load_jobs(
        self,
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
    ) -> list[CareerMarketJob]:
        ...


ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "backend": (
        "backend",
        "back-end",
        "back end",
    ),
    "frontend": (
        "frontend",
        "front-end",
        "front end",
    ),
    "fullstack": (
        "fullstack",
        "full-stack",
        "full stack",
    ),
    "ai engineer": (
        "ai engineer",
        "artificial intelligence engineer",
        "machine learning engineer",
        "ml engineer",
    ),
    "data engineer": (
        "data engineer",
        "data engineering",
    ),
    "data scientist": (
        "data scientist",
        "data science",
    ),
    "devops": (
        "devops",
        "dev ops",
    ),
}


LOCATION_ALIASES: dict[str, tuple[str, ...]] = {
    "hồ chí minh": (
        "hồ chí minh",
        "ho chi minh",
        "tp.hcm",
        "tphcm",
        "sài gòn",
        "sai gon",
    ),
    "hà nội": (
        "hà nội",
        "ha noi",
    ),
    "đà nẵng": (
        "đà nẵng",
        "da nang",
    ),
}


class DjangoCareerMarketRepository:
    """
    Lấy JOB duy nhất từ bảng CareerJobChunk.

    CareerJobChunk là chunk-level nên bắt buộc collapse:
        many chunks -> one job
    trước khi tính thống kê.
    """

    def load_jobs(
        self,
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
    ) -> list[CareerMarketJob]:

        queryset = CareerJobChunk.objects.filter(
            active=True,
        )

        if source:
            queryset = queryset.filter(
                source=normalize_key(source)
            )

        if experience_level:
            queryset = queryset.filter(
                experience_level__icontains=normalize_key(
                    experience_level
                )
            )

        if employment_type:
            queryset = queryset.filter(
                employment_type__icontains=normalize_key(
                    employment_type
                )
            )

        if location:
            queryset = self._filter_location(
                queryset,
                location,
            )

        if category:
            queryset = self._filter_category(
                queryset,
                category,
            )

        # PostgreSQL DISTINCT ON.
        #
        # Job A có thể có 5 chunks nhưng chỉ được xuất hiện 1 lần.
        rows = (
            queryset
            .order_by(
                "source",
                "source_job_id",
                "chunk_index",
            )
            .distinct(
                "source",
                "source_job_id",
            )
            .values(
                "source",
                "source_job_id",
                "job_title",
                "category_key",
                "location_key",
                "experience_level",
                "employment_type",
                "metadata",
            )
        )

        return [
            CareerMarketJob(
                source=row["source"],
                source_job_id=row["source_job_id"],
                job_title=row["job_title"],
                category_key=row["category_key"],
                location_key=row["location_key"],
                experience_level=row["experience_level"],
                employment_type=row["employment_type"],
                metadata=dict(
                    row["metadata"] or {}
                ),
            )
            for row in rows
        ]

    @staticmethod
    def _filter_category(queryset, category: str):
        normalized = normalize_key(category)

        if normalized is None:
            return queryset

        aliases = ROLE_ALIASES.get(
            normalized,
            (normalized,),
        )

        condition = Q()

        for alias in aliases:
            condition |= Q(
                job_title__icontains=alias
            )

            condition |= Q(
                category_key__icontains=alias
            )

        return queryset.filter(condition)

    @staticmethod
    def _filter_location(queryset, location: str):
        normalized = normalize_key(location)

        if normalized is None:
            return queryset

        aliases = LOCATION_ALIASES.get(
            normalized,
            (normalized,),
        )

        condition = Q()

        for alias in aliases:
            condition |= Q(
                location_key__icontains=alias
            )

        return queryset.filter(condition)


# ============================================================
# Market analyzer
# ============================================================


class CareerMarketAnalyzer:
    def __init__(
        self,
        repository: CareerMarketRepository | None = None,
    ) -> None:
        self.repository = (
            repository
            or DjangoCareerMarketRepository()
        )

    # --------------------------------------------------------
    # A. Skill demand
    # --------------------------------------------------------

    def skill_distribution(
        self,
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
        limit: int = 20,
    ) -> SkillDistributionResult:

        jobs = self._load_unique_jobs(
            source=source,
            category=category,
            location=location,
            experience_level=experience_level,
            employment_type=employment_type,
        )

        return self._distribution_from_jobs(
            jobs,
            limit=limit,
        )

    # --------------------------------------------------------
    # B. Skill comparison
    # --------------------------------------------------------

    def compare_skills(
        self,
        first_skill: str,
        second_skill: str,
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
    ) -> SkillComparisonResult:

        jobs = self._load_unique_jobs(
            source=source,
            category=category,
            location=location,
            experience_level=experience_level,
            employment_type=employment_type,
        )

        cohort_size = len(jobs)

        first = canonicalize_skill(first_skill)
        second = canonicalize_skill(second_skill)

        counts = self._count_skills(jobs)

        first_key = _skill_key(first)
        second_key = _skill_key(second)

        first_count = counts.get(
            first_key,
            0,
        )

        second_count = counts.get(
            second_key,
            0,
        )

        first_stat = SkillStat(
            skill=first,
            job_count=first_count,
            coverage=(
                first_count / cohort_size
                if cohort_size
                else 0.0
            ),
        )

        second_stat = SkillStat(
            skill=second,
            job_count=second_count,
            coverage=(
                second_count / cohort_size
                if cohort_size
                else 0.0
            ),
        )

        winner: str | None

        if first_count > second_count:
            winner = first

        elif second_count > first_count:
            winner = second

        else:
            winner = None

        return SkillComparisonResult(
            cohort_size=cohort_size,
            first=first_stat,
            second=second_stat,
            winner=winner,
            job_count_difference=abs(
                first_count - second_count
            ),
            coverage_difference=abs(
                first_stat.coverage
                - second_stat.coverage
            ),
        )

    # --------------------------------------------------------
    # C. Skill co-occurrence
    # --------------------------------------------------------

    def skill_cooccurrence(
        self,
        anchor_skill: str,
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
        limit: int = 20,
    ) -> SkillCooccurrenceResult:

        jobs = self._load_unique_jobs(
            source=source,
            category=category,
            location=location,
            experience_level=experience_level,
            employment_type=employment_type,
        )

        anchor = canonicalize_skill(
            anchor_skill
        )

        anchor_key = _skill_key(anchor)

        anchor_jobs: list[CareerMarketJob] = []

        for job in jobs:
            job_skill_keys = {
                _skill_key(skill)
                for skill in self._job_skills(job)
            }

            if anchor_key in job_skill_keys:
                anchor_jobs.append(job)

        counts = self._count_skills(
            anchor_jobs
        )

        counts.pop(
            anchor_key,
            None,
        )

        display_names = self._display_names(
            anchor_jobs
        )

        denominator = len(
            anchor_jobs
        )

        stats = [
            SkillStat(
                skill=display_names.get(
                    key,
                    key,
                ),
                job_count=count,
                coverage=(
                    count / denominator
                    if denominator
                    else 0.0
                ),
            )
            for key, count
            in counts.most_common(limit)
        ]

        return SkillCooccurrenceResult(
            cohort_size=len(jobs),
            anchor_skill=anchor,
            anchor_job_count=denominator,
            skills=tuple(stats),
        )

    # --------------------------------------------------------
    # D. Candidate skill gap
    # --------------------------------------------------------

    def candidate_skill_gap(
        self,
        candidate_skills: Iterable[str],
        *,
        source: str | None = None,
        category: str | None = None,
        location: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
        limit: int = 10,
    ) -> CandidateSkillGapResult:

        normalized_candidate: list[str] = []
        candidate_keys: set[str] = set()

        for value in candidate_skills:
            skill = canonicalize_skill(
                value
            )

            key = _skill_key(skill)

            if not key:
                continue

            if key in candidate_keys:
                continue

            candidate_keys.add(key)
            normalized_candidate.append(
                skill
            )

        distribution = self.skill_distribution(
            source=source,
            category=category,
            location=location,
            experience_level=experience_level,
            employment_type=employment_type,
            limit=1000,
        )

        recommendations = [
            stat
            for stat in distribution.skills
            if _skill_key(stat.skill)
            not in candidate_keys
        ][:limit]

        return CandidateSkillGapResult(
            cohort_size=distribution.cohort_size,
            candidate_skills=tuple(
                normalized_candidate
            ),
            recommended_skills=tuple(
                recommendations
            ),
        )

    # ========================================================
    # Internal
    # ========================================================

    def _load_unique_jobs(
        self,
        **filters,
    ) -> list[CareerMarketJob]:

        jobs = self.repository.load_jobs(
            **filters
        )

        # Nếu sau này duplicate cluster id được persist,
        # analyzer tự dùng luôn.
        #
        # Hiện tại fallback:
        #     source + source_job_id
        seen: set[tuple[str, str]] = set()
        result: list[CareerMarketJob] = []

        for job in jobs:
            cluster_id = (
                job.metadata.get(
                    "duplicate_cluster_id"
                )
                or job.metadata.get(
                    "exact_duplicate_cluster_id"
                )
            )

            if cluster_id:
                key = (
                    "cluster",
                    str(cluster_id),
                )
            else:
                key = (
                    job.source,
                    job.source_job_id,
                )

            if key in seen:
                continue

            seen.add(key)
            result.append(job)

        return result

    @staticmethod
    def _job_skills(
        job: CareerMarketJob,
    ) -> tuple[str, ...]:

        return parse_technical_skills(
            job.metadata.get(
                "technical_skills"
            )
        )

    def _count_skills(
        self,
        jobs: Iterable[CareerMarketJob],
    ) -> Counter[str]:

        counts: Counter[str] = Counter()

        for job in jobs:
            # Set -> một skill chỉ được count
            # tối đa 1 lần / job.
            unique_skills = {
                _skill_key(skill)
                for skill in self._job_skills(job)
                if _skill_key(skill)
            }

            counts.update(
                unique_skills
            )

        return counts

    def _display_names(
        self,
        jobs: Iterable[CareerMarketJob],
    ) -> dict[str, str]:

        result: dict[str, str] = {}

        for job in jobs:
            for skill in self._job_skills(job):
                key = _skill_key(skill)

                result.setdefault(
                    key,
                    skill,
                )

        return result

    def _distribution_from_jobs(
        self,
        jobs: list[CareerMarketJob],
        *,
        limit: int,
    ) -> SkillDistributionResult:

        cohort_size = len(jobs)

        if cohort_size == 0:
            return SkillDistributionResult(
                cohort_size=0,
                skills=(),
            )

        counts = self._count_skills(
            jobs
        )

        display_names = self._display_names(
            jobs
        )

        stats = [
            SkillStat(
                skill=display_names.get(
                    key,
                    key,
                ),
                job_count=count,
                coverage=count / cohort_size,
            )
            for key, count
            in counts.most_common(limit)
        ]

        return SkillDistributionResult(
            cohort_size=cohort_size,
            skills=tuple(stats),
        )
