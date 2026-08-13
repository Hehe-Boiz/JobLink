from __future__ import annotations

import re
from .skill_catalog import SKILL_ALIASES
from dataclasses import dataclass
from decimal import Decimal

from apps.matching.domain import CandidateSkill, DocumentSection, SkillOccurrence, TextSegment
from .text import normalize_for_matching

SECTION_EVIDENCE_STRENGTH = {
    DocumentSection.WORK_EXPERIENCE: Decimal("1.00"),
    DocumentSection.PROJECTS: Decimal("0.85"),
    DocumentSection.CERTIFICATIONS: Decimal("0.75"),
    DocumentSection.SUMMARY: Decimal("0.60"),
    DocumentSection.SKILLS: Decimal("0.50"),
    DocumentSection.UNKNOWN: Decimal("0.45"),
    DocumentSection.EDUCATION: Decimal("0.40"),
    DocumentSection.AWARDS: Decimal("0.40"),
}

NEGATION_MARKERS = (
    "no experience with",
    "no knowledge of",
    "not familiar with",
    "never used",
    "without experience",
    "chua co kinh nghiem",
    "khong co kinh nghiem",
    "chua tung su dung",
)


WEAK_CLAIM_MARKERS = (
    "currently learning",
    "learning",
    "basic knowledge",
    "basic understanding",
    "familiar with",
    "dang hoc",
    "dang tim hieu",
    "kien thuc co ban",
)

@dataclass(frozen=True)
class CompiledSkillPattern:
    canonical_skill: str
    alias: str
    pattern: re.Pattern

class SkillExtractor:
    def __init__(self, skill_aliases: dict[str, tuple[str, ...]] | None = None) -> None:
        self._skill_aliases = (skill_aliases or SKILL_ALIASES)
        self._patterns = self._compile_patterns()

    def extract(self, segments: list[TextSegment]) -> dict[str, CandidateSkill]:
        occurrences = self.extract_occurrences(segments)

        return self.select_candidate_skills(occurrences)

    # gom occurrence từ tất cả segment
    def extract_occurrences(self, segments: list[TextSegment]) -> list[SkillOccurrence]:
        occurrences = []

        for segment in segments:
            occurrences.extend(self._extract_from_segment(segment))

        return occurrences

    def _compile_patterns(self):
        compiled_patterns = []

        for canonical_skill, aliases in (self._skill_aliases.items()):
            unique_aliases = dict.fromkeys( # tạo dict mà mỗi phần tử đầu vào trở thành một key để loại duplicate 
                    (
                        canonical_skill,
                        *aliases,
                    )
                )
            
            for alias in unique_aliases:
                compiled_patterns.append(
                    CompiledSkillPattern(
                        canonical_skill=canonical_skill,
                        alias=alias,
                        pattern=self._build_pattern(alias),
                    )
                )
            compiled_patterns.sort(
                key=lambda item: len(item.alias),
                reverse=True,
            )

        return compiled_patterns
        
    @staticmethod
    def _build_pattern(alias: str) -> re.Pattern:
        escaped_alias = re.escape(alias) # để cho dấu như . và + được hiểu là ký tự thật, không phải cú pháp regex

        # xử lý riêng ngôn ngữ c
        if alias.casefold() == "c": # đưa chuỗi về chữ thường
            return re.compile(
                r"(?<![A-Za-z0-9])c"
                r"(?![A-Za-z0-9+#])",
                re.IGNORECASE, # bỏ qua in hoa hay thường 
            )
        
        return re.compile(
            rf"(?<![A-Za-z0-9])"
            rf"{escaped_alias}"
            rf"(?![A-Za-z0-9])",
            re.IGNORECASE,
        )

    @staticmethod
    def _left_context(text: str, match_start: int, max_chars: int = 100,) -> str:
        start = max(0, match_start - max_chars)

        context = text[start:match_start]

        # chia phần context thành các mảnh khi gặp ranh giới câu hoặc từ chuyển ý
        parts = re.split(
            r"[.!?;\n]"
            r"|\bbut\b"
            r"|\bhowever\b"
            r"|\bnhưng\b",
            context,
            flags=re.IGNORECASE,
        )

        return normalize_for_matching(parts[-1])

    # kiểm tra xem skill có nằm trong câu phủ định không ?
    def _is_negated(self, text: str, match_start: int) -> bool:
        context = self._left_context(text, match_start)


        for marker in NEGATION_MARKERS:
            if marker in context:
                return True

        return False

    def _is_weak_claim(self, text: str, match_start: int) -> bool:
        context = self._left_context(text, match_start)

        for marker in WEAK_CLAIM_MARKERS:
            if marker in context:
                return True

        return False

    @staticmethod
    def _to_candidate_skill(occurrence: SkillOccurrence,) -> CandidateSkill:
        strength = (
            SECTION_EVIDENCE_STRENGTH.get(
                occurrence.segment.section,
                Decimal("0.45"), # nếu section không có trong dict thì mặc định 0.45
            )
        )

        if occurrence.is_negated:
            strength = Decimal("0.00")

        elif occurrence.is_weak_claim:
            strength = min(strength, Decimal("0.25"),)

        return CandidateSkill(
            canonical_skill=occurrence.canonical_skill,
            matched_alias=occurrence.matched_alias,
            evidence_text=occurrence.segment.text,
            section=occurrence.segment.section,
            evidence_strength=strength,
            chunk_key=occurrence.segment.stable_key,
            is_negated=occurrence.is_negated,
            is_weak_claim=occurrence.is_weak_claim,
        )

    # kiếm tất cả các nơi skill xuất hiện 
    def _extract_from_segment(self, segment: TextSegment) -> list[SkillOccurrence]:
        candidates = []

        for compiled in self._patterns:
            # Lấy regex hiện tại, tìm tất cả vị trí nó xuất hiện trong segment.text, rồi lặp qua từng kết quả match một.
            for match in compiled.pattern.finditer(segment.text):
                candidates.append(
                    SkillOccurrence(
                        canonical_skill=(compiled.canonical_skill), # tên thật của skill
                        matched_alias=compiled.alias,
                        segment=segment,
                        start=match.start(), # index bắt đầu phát hiện
                        end=match.end(), # index kết thúc
                        is_negated=self._is_negated(segment.text,match.start()),
                        is_weak_claim=self._is_weak_claim(segment.text, match.start()),
                    )
                )

        candidates.sort(
            key=lambda item: (
                -(item.end - item.start),
                item.start,
            )
        )

        selected = []

        for candidate in candidates:
            if self._overlaps_any(candidate, selected):
                continue

            selected.append(candidate)

        selected.sort(key=lambda item: item.start)
        return selected

    @staticmethod
    def _overlaps_any(candidate: SkillOccurrence, selected: list[SkillOccurrence]) -> bool:

        for existing in selected:
            is_overlap = (candidate.start < existing.end and existing.start < candidate.end)

            if is_overlap:
                return True

        return False

    def select_candidate_skills(self, occurrences: list[SkillOccurrence]) -> dict[str, CandidateSkill]:
        best_by_skill = {}

        for occurrence in occurrences:
            candidate = self._to_candidate_skill(occurrence) # lấy lần lượt trong list 

            current = best_by_skill.get(candidate.canonical_skill) # lấy cái hiện tại trong dict 

            if (current is None or candidate.evidence_strength > current.evidence_strength): # nếu điểm lớn hơn thì lấy 
                best_by_skill[candidate.canonical_skill] = candidate 

        return best_by_skill