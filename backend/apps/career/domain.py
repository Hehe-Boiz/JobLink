from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class JobKnowledgeSection(str, Enum):
    DESCRIPTION = "DESCRIPTION"
    RESPONSIBILITIES = "RESPONSIBILITIES"
    REQUIRED_QUALIFICATIONS = "REQUIRED_QUALIFICATIONS"
    PREFERRED_QUALIFICATIONS = "PREFERRED_QUALIFICATIONS"
    BENEFITS = "BENEFITS"


@dataclass(frozen=True, slots=True)
class RawJobRecord:
    source: str
    source_job_id: str

    title: str
    company_name: str

    description: str = ""
    requirements: str = ""
    benefits: str = ""

    location_key: str | None = None
    experience_level: str | None = None
    employment_type: str | None = None
    category_key: str | None = None

    is_active: bool = True
    published_at: datetime | None = None
    source_url: str | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class JobKnowledgeDocument:
    source: str
    source_job_id: str

    title: str
    company_name: str

    sections: dict[JobKnowledgeSection, str]

    location_key: str | None = None
    experience_level: str | None = None
    employment_type: str | None = None
    category_key: str | None = None

    is_active: bool = True
    published_at: datetime | None = None
    source_url: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JobKnowledgeChunk:
    chunk_id: str
    chunk_index: int

    source: str
    source_job_id: str

    title: str
    company_name: str

    section: JobKnowledgeSection

    content: str
    embedding_text: str

    location_key: str | None = None
    experience_level: str | None = None
    employment_type: str | None = None
    category_key: str | None = None

    is_active: bool = True
    published_at: datetime | None = None
    source_url: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)