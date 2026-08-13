from __future__ import annotations

import re

from apps.matching.domain import DocumentSection, JobRequirement, RequirementPriority, TextSegment

from .exceptions import EmptyJobRequirementsError
from .hashing import sha256_text
from .skill_extractor import SkillExtractor
from .text import normalize_for_matching, normalize_text, remove_bullet_prefix

PREFERRED_MARKERS = (
    "preferred",
    "nice to have",
    "good to have",
    "is a plus",
    "would be a plus",
    "bonus",
    "optional",
    "not required",

    "uu tien",
    "loi the",
    "diem cong",
    "khong bat buoc",
)

def split_requirement_clauses(text: str) -> list[str]:
    text = normalize_text(text) #-> chuẩn hóa lại những khoảng trắng

    if not text:
        return []

    raw_clauses = re.split(
        r"\n+|(?<=[.!?;])\s+",
        text,
    )
    clauses = []

    for raw_clause in raw_clauses:
        clause = remove_bullet_prefix(raw_clause)
        if clause:
            clauses.append(clause)


    return clauses


def make_job_segment(text: str, index: int, source: str) -> TextSegment:

    normalized_text = normalize_for_matching(text)
    short_hash = sha256_text(f"{source}|{normalized_text}")[:8]
    stable_key = (f"{source}:{index}:{short_hash}")

    return TextSegment(
        index=index,
        stable_key=stable_key,
        text=text,
        normalized_text=normalized_text,
        section=DocumentSection.UNKNOWN,
        source=source,
    )


class JobRequirementExtractor:

    def __init__(self, skill_extractor: SkillExtractor | None = None) -> None:
        self._skill_extractor = skill_extractor or SkillExtractor()

    def extract(self, job_snapshot: dict) -> list[JobRequirement]:

        extracted: dict[str, JobRequirement] = {}
        self._extract_from_requirements(job_snapshot.get("requirements", ""),extracted)
        self._extract_from_tags(job_snapshot.get("tags", []), extracted)

        if not extracted:
            raise EmptyJobRequirementsError(
                "Không trích xuất được skill nào "
                "từ Job requirements hoặc tags."
            )

        return sorted(
            extracted.values(),
            key=lambda requirement: (
                0
                if requirement.priority == RequirementPriority.REQUIRED
                else 1,
                requirement.canonical_skill,
            ),
        )

    def _extract_from_requirements(self, requirements_text, extracted: dict[str, JobRequirement]) -> None:
        clauses = split_requirement_clauses(requirements_text)

        for index, clause in enumerate(clauses):
            segment = make_job_segment(text=clause, index=index, source="REQUIREMENTS")
            priority = self._classify_priority(clause)
            occurrences = self._skill_extractor.extract_occurrences([segment])
            for occurrence in occurrences:
                requirement = JobRequirement(
                    requirement_id=f"{segment.stable_key}:{occurrence.canonical_skill}",
                    original_text=segment.text,
                    normalized_text=segment.normalized_text,
                    priority=priority,
                    canonical_skill=occurrence.canonical_skill,
                    source="REQUIREMENTS",
                    source_chunk_key=segment.stable_key,
                )

                self._merge_requirement(extracted, requirement)


    def _extract_from_tags(self, tags, extracted) -> None:
        for index, tag in enumerate(tags):
            if not tag:
                continue
            segment = make_job_segment(text=str(tag), index=index, source="TAG")
            occurrences = self._skill_extractor.extract_occurrences([segment])

            for occurrence in occurrences:
                requirement = JobRequirement(
                    requirement_id=f"{segment.stable_key}:{occurrence.canonical_skill}",
                    original_text=segment.text,
                    normalized_text=segment.normalized_text,
                    priority=RequirementPriority.PREFERRED,
                    canonical_skill=occurrence.canonical_skill,
                    source="TAG",
                    source_chunk_key=segment.stable_key
                )

                self._merge_requirement(extracted, requirement)

    @staticmethod
    def _classify_priority(text: str,) -> RequirementPriority:
        normalized = normalize_for_matching(text)

        for marker in PREFERRED_MARKERS:
            if marker in normalized:
                return RequirementPriority.PREFERRED

        return RequirementPriority.REQUIRED

    "REQUIRED > PREFERRED, REQUIREMENTS > TAG"
    @staticmethod
    def _merge_requirement(extracted: dict[str, JobRequirement], incoming: JobRequirement) -> None:
        existing = extracted.get(incoming.canonical_skill)

        if existing is None:
            extracted[incoming.canonical_skill] = incoming
            return

        if (existing.priority == RequirementPriority.PREFERRED and incoming.priority == RequirementPriority.REQUIRED):
            extracted[incoming.canonical_skill] = incoming
            return

        if (existing.priority == incoming.priority and existing.source == "TAG" and incoming.source == "REQUIREMENTS"):
            extracted[incoming.canonical_skill] = incoming