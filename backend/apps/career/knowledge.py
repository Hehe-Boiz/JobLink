from __future__ import annotations

import re
from .domain import JobKnowledgeDocument, JobKnowledgeSection, RawJobRecord
from .normalization import normalize_job_text, normalize_key


HEADER_ALIASES: dict[str, JobKnowledgeSection] = {
    # Description
    "description": JobKnowledgeSection.DESCRIPTION,
    "job description": JobKnowledgeSection.DESCRIPTION,
    "mô tả": JobKnowledgeSection.DESCRIPTION,
    "mô tả công việc": JobKnowledgeSection.DESCRIPTION,

    # Responsibilities
    "responsibilities": JobKnowledgeSection.RESPONSIBILITIES,
    "job responsibilities": JobKnowledgeSection.RESPONSIBILITIES,
    "duties": JobKnowledgeSection.RESPONSIBILITIES,
    "your responsibilities": JobKnowledgeSection.RESPONSIBILITIES,
    "trách nhiệm": JobKnowledgeSection.RESPONSIBILITIES,
    "nhiệm vụ": JobKnowledgeSection.RESPONSIBILITIES,
    "công việc": JobKnowledgeSection.RESPONSIBILITIES,
    "nội dung công việc": JobKnowledgeSection.RESPONSIBILITIES,

    # Required qualifications
    "requirements": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "job requirements": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "required qualifications": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "qualifications": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "must have": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "yêu cầu": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "yêu cầu công việc": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "yêu cầu ứng viên": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
    "yêu cầu bắt buộc": JobKnowledgeSection.REQUIRED_QUALIFICATIONS,

    # Preferred qualifications
    "preferred": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "preferred qualifications": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "nice to have": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "good to have": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "preferred skills": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "ưu tiên": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "điểm cộng": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,
    "lợi thế": JobKnowledgeSection.PREFERRED_QUALIFICATIONS,

    # Benefits
    "benefits": JobKnowledgeSection.BENEFITS,
    "benefit": JobKnowledgeSection.BENEFITS,
    "what we offer": JobKnowledgeSection.BENEFITS,
    "perks": JobKnowledgeSection.BENEFITS,
    "quyền lợi": JobKnowledgeSection.BENEFITS,
    "quyền lợi được hưởng": JobKnowledgeSection.BENEFITS,
    "phúc lợi": JobKnowledgeSection.BENEFITS,
}


HEADER_EDGE_PATTERN = re.compile(r"^[\s\-–—•*:]+|[\s:：\-–—]+$")


class JobKnowledgeBuilder:
    def build(self, record: RawJobRecord) -> JobKnowledgeDocument:
        self._validate_record(record)
        sections: dict[JobKnowledgeSection, str] = {}
        self._extract_and_merge(
            sections=sections,
            text=record.description,
            default_section=JobKnowledgeSection.DESCRIPTION,
        )
        self._extract_and_merge(
            sections=sections,
            text=record.requirements,
            default_section=JobKnowledgeSection.REQUIRED_QUALIFICATIONS,
        )
        self._extract_and_merge(
            sections=sections,
            text=record.benefits,
            default_section=JobKnowledgeSection.BENEFITS,
        )

        return JobKnowledgeDocument(
            source=record.source.strip(),
            source_job_id=record.source_job_id.strip(),
            title=normalize_job_text(record.title),
            company_name=normalize_job_text(record.company_name),
            sections=sections,
            location_key=normalize_key(record.location_key),
            experience_level=normalize_key(record.experience_level),
            employment_type=normalize_key(record.employment_type),
            category_key=normalize_key(record.category_key),
            is_active=record.is_active,
            published_at=record.published_at,
            source_url=record.source_url,
            metadata=dict(record.metadata),
        )

    def _extract_and_merge(self, sections: dict[JobKnowledgeSection, str], text: str, default_section: JobKnowledgeSection) -> None:
        normalized_text = normalize_job_text(text)
        if not normalized_text:
            return

        extracted_sections = self._split_sections(text=normalized_text, default_section=default_section)
        for section, content in extracted_sections.items():
            self._merge_section(sections=sections, section=section, content=content)

    def _split_sections(self, text: str, default_section: JobKnowledgeSection) -> dict[JobKnowledgeSection, str]:
        result: dict[JobKnowledgeSection, list[str]] = {}
        current_section = default_section

        for line in text.splitlines():
            stripped_line = line.strip()

            if not stripped_line:
                continue

            detected_section = self._detect_header(stripped_line)
            if detected_section is not None:
                current_section = detected_section
                continue

            result.setdefault(current_section, []).append(stripped_line)

        return {
            section: "\n".join(lines).strip()
            for section, lines in result.items()
            if lines
        }

    def _detect_header(self, line: str) -> JobKnowledgeSection | None:
        if len(line) > 80:
            return None

        normalized_header = HEADER_EDGE_PATTERN.sub("", line.lower().strip())

        return HEADER_ALIASES.get(normalized_header)

    @staticmethod
    def _merge_section(sections: dict[JobKnowledgeSection, str], section: JobKnowledgeSection, content: str) -> None:
        content = content.strip()
        if not content:
            return

        existing_content = sections.get(section)
        if existing_content:
            sections[section] = f"{existing_content}\n\n{content}"
        else:
            sections[section] = content

    @staticmethod
    def _validate_record(record: RawJobRecord) -> None:
        if not record.source.strip():
            raise ValueError("RawJobRecord.source must not be empty")

        if not record.source_job_id.strip():
            raise ValueError("RawJobRecord.source_job_id must not be empty")

        if not record.title.strip():
            raise ValueError("RawJobRecord.title must not be empty")