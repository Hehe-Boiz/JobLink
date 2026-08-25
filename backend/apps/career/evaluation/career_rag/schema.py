from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CareerTopic:
    topic_id: str
    family_id: str
    scope: str
    label: str
    category_key: str
    title_key: str | None = None
    known_skills: tuple[str, ...] = ()
    split: str = "dev"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["known_skills"] = list(self.known_skills)
        return data


@dataclass(frozen=True, slots=True)
class CareerQuery:
    query_id: str
    topic_id: str
    variant: str
    text: str
    known_skills: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["known_skills"] = list(self.known_skills)
        return data


@dataclass(frozen=True, slots=True)
class CorpusJob:
    source: str
    source_job_id: str
    job_title: str
    category_key: str | None
    location_key: str | None
    experience_level: str | None
    employment_type: str | None
    chunks: tuple[dict[str, str], ...]

    @property
    def job_key(self) -> str:
        return f"{self.source}::{self.source_job_id}"

    @property
    def raw_evidence(self) -> str:
        parts = [f"Job title: {self.job_title}"]
        if self.category_key:
            parts.append(f"Category: {self.category_key}")
        if self.location_key:
            parts.append(f"Location: {self.location_key}")
        for chunk in self.chunks:
            section = chunk.get("section", "")
            content = chunk.get("content", "")
            if content:
                parts.append(f"[{section}]\n{content}")
        return "\n\n".join(parts)


@dataclass(frozen=True, slots=True)
class PooledCandidate:
    topic_id: str
    source: str
    source_job_id: str
    job_title: str
    category_key: str | None
    location_key: str | None
    ranks: dict[str, int] = field(default_factory=dict)
    rrf_score: float = 0.0

    @property
    def job_key(self) -> str:
        return f"{self.source}::{self.source_job_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RelevanceJudgment:
    topic_id: str
    source: str
    source_job_id: str
    grade: int
    judge_grades: tuple[int, int, int]
    uncertain: bool

    @property
    def job_key(self) -> str:
        return f"{self.source}::{self.source_job_id}"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["judge_grades"] = list(self.judge_grades)
        return data


@dataclass(frozen=True, slots=True)
class Nugget:
    """A grounded answer unit with adaptive, non-exhaustive support evidence.

    ``support_job_keys`` are only the verified support examples observed before
    adaptive verification stopped.  They are not an exhaustive support
    universe, and ``prevalence`` is the V3 unavailable sentinel.
    """
    topic_id: str
    nugget_id: str
    text: str
    normalized_text: str
    support_job_keys: tuple[str, ...]
    support_count: int
    prevalence: float
    weight: float
    importance: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["support_job_keys"] = list(self.support_job_keys)
        return data


@dataclass(frozen=True, slots=True)
class BenchmarkManifest:
    benchmark_name: str
    benchmark_version: str
    random_seed: int
    dataset_sha256: str
    corpus_manifest_sha256: str
    topics_sha256: str
    queries_sha256: str
    pool_sha256: str
    qrels_sha256: str
    nuggets_sha256: str
    judge_model: str
    judge_prompt_sha256: str
    builder_source_sha256: str
    exact_model_id_equal: bool
    dev_family_ids: tuple[str, ...]
    test_family_ids: tuple[str, ...]
    configuration: dict[str, Any] = field(default_factory=dict)
    # Generic binding for every artifact whose bytes affect interpretation or
    # evaluation.  Keeping this generic avoids adding a dataclass field for
    # every future construction report.
    artifact_sha256: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dev_family_ids"] = list(self.dev_family_ids)
        data["test_family_ids"] = list(self.test_family_ids)
        return data
