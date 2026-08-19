from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache
from typing import Any

from .normalization import normalize_key


class CareerIntent(StrEnum):
    SKILL_DEMAND = "skill_demand"
    SKILL_COMPARISON = "skill_comparison"
    SKILL_COOCCURRENCE = "skill_cooccurrence"
    CANDIDATE_SKILL_GAP = "candidate_skill_gap"


@dataclass(frozen=True, slots=True)
class CareerMarketQuery:
    intent: CareerIntent
    category: str | None = None
    location: str | None = None
    skills: tuple[str, ...] = ()
    candidate_skills: tuple[str, ...] = ()
    experience_level: str | None = None
    employment_type: str | None = None


@dataclass(frozen=True, slots=True)
class VocabularyEntry:
    surface: str
    canonical: str


HIGH_CONFIDENCE_SKILL_ALIASES = {
    "postgres": "postgresql",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "springboot": "spring boot",
    "k8s": "kubernetes",
}

LOCATION_ALIASES = {
    "tp.hcm": "hồ chí minh",
    "tphcm": "hồ chí minh",
    "hcm": "hồ chí minh",
    "sài gòn": "hồ chí minh",
    "sai gon": "hồ chí minh",
    "hn": "hà nội",
}


def _normalize_surface(value: str | None) -> str:
    normalized = normalize_key(value)
    if not normalized:
        return ""
    return re.sub(r"\s+", " ", normalized.replace("_", " ")).strip()


def _parse_skill_list(value: Any) -> list[str]:
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
    for item in raw_items:
        normalized = normalize_key(str(item).strip().strip(".,;:!?"))
        if not normalized or len(normalized) > 100:
            continue
        result.append(HIGH_CONFIDENCE_SKILL_ALIASES.get(normalized, normalized))

    return list(dict.fromkeys(result))


def _contains_surface(text: str, surface: str) -> list[tuple[int, int]]:
    if not surface:
        return []

    pattern = rf"(?<!\w){re.escape(surface)}(?!\w)"
    return [(match.start(), match.end()) for match in re.finditer(pattern, text, flags=re.IGNORECASE)]


def _extract_mentions(text: str, entries: tuple[VocabularyEntry, ...]) -> tuple[str, ...]:
    candidates: list[tuple[int, int, int, str]] = []

    for entry in entries:
        for start, end in _contains_surface(text, entry.surface):
            candidates.append((-(end - start), start, end, entry.canonical))

    candidates.sort()

    selected_spans: list[tuple[int, int]] = []
    selected: list[tuple[int, str]] = []
    seen: set[str] = set()

    for _, start, end, canonical in candidates:
        if canonical in seen:
            continue

        overlap = any(start < selected_end and end > selected_start for selected_start, selected_end in selected_spans)
        if overlap:
            continue

        selected_spans.append((start, end))
        selected.append((start, canonical))
        seen.add(canonical)

    selected.sort(key=lambda item: item[0])
    return tuple(canonical for _, canonical in selected)


@lru_cache(maxsize=1)
def _load_corpus_vocabulary() -> tuple[
    tuple[VocabularyEntry, ...],
    tuple[VocabularyEntry, ...],
    tuple[VocabularyEntry, ...],
]:
    from .models import CareerJobChunk

    base = CareerJobChunk.objects.filter(active=True)

    category_keys = {
        value
        for value in base.exclude(category_key__isnull=True).values_list("category_key", flat=True).distinct()
        if value
    }

    categories = tuple(sorted(
        (VocabularyEntry(surface=_normalize_surface(key), canonical=key) for key in category_keys),
        key=lambda entry: (-len(entry.surface), entry.surface),
    ))

    location_values = {
        value
        for value in base.exclude(location_key__isnull=True).values_list("location_key", flat=True).distinct()
        if value
    }

    locations: dict[str, str] = {}

    for value in location_values:
        for part in str(value).split(","):
            canonical = normalize_key(part)
            surface = _normalize_surface(part)

            if canonical and surface:
                locations[surface] = canonical

    for alias, canonical in LOCATION_ALIASES.items():
        locations[_normalize_surface(alias)] = canonical

    location_entries = tuple(sorted(
        (VocabularyEntry(surface=surface, canonical=canonical) for surface, canonical in locations.items()),
        key=lambda entry: (-len(entry.surface), entry.surface),
    ))

    rows = (
        base.order_by("source", "source_job_id", "chunk_index")
        .distinct("source", "source_job_id")
        .values_list("metadata", flat=True)
    )

    skill_values: set[str] = set()

    for metadata in rows.iterator(chunk_size=2000):
        if not isinstance(metadata, dict):
            continue

        skill_values.update(_parse_skill_list(metadata.get("technical_skills")))

    skill_surfaces: dict[str, str] = {}

    for skill in skill_values:
        surface = _normalize_surface(skill)

        if surface:
            skill_surfaces[surface] = skill

    for alias, canonical in HIGH_CONFIDENCE_SKILL_ALIASES.items():
        if canonical in skill_values:
            skill_surfaces[_normalize_surface(alias)] = canonical

    skills = tuple(sorted(
        (VocabularyEntry(surface=surface, canonical=canonical) for surface, canonical in skill_surfaces.items()),
        key=lambda entry: (-len(entry.surface), entry.surface),
    ))

    return categories, location_entries, skills


class CareerQueryPlanner:
    GAP_CUES = (
        "còn thiếu",
        "chưa có",
        "bổ sung",
        "skill gap",
        "market gap",
        "market-demand gap",
        "đối chiếu",
        "profile hiện có",
        "profile đã có",
        "mình đã có",
        "tôi đã có",
        "nếu đã biết",
        "nên học thêm",
        "cần học thêm",
    )

    COOCCURRENCE_CUES = (
        "đi kèm",
        "xuất hiện cùng",
        "đồng xuất hiện",
        "co-skill",
        "hay yêu cầu thêm",
        "thường yêu cầu thêm",
        "kéo theo",
        "stack đi kèm",
        "thường đi với",
    )

    def plan(self, question: str) -> CareerMarketQuery:
        text = _normalize_surface(question)

        if not text:
            raise ValueError("Question must not be empty")

        categories, locations, skill_vocab = _load_corpus_vocabulary()

        category_mentions = _extract_mentions(text, categories)
        location_mentions = _extract_mentions(text, locations)

        category = category_mentions[0] if category_mentions else None
        location = location_mentions[0] if location_mentions else None

        intent = self._detect_intent(text)

        if intent == CareerIntent.CANDIDATE_SKILL_GAP:
            candidate_skills = self._extract_candidate_skills(text, skill_vocab)

            return CareerMarketQuery(
                intent=intent,
                category=category,
                location=location,
                candidate_skills=candidate_skills,
            )

        if intent == CareerIntent.SKILL_COMPARISON:
            skills = self._extract_comparison_skills(text, skill_vocab)

            return CareerMarketQuery(
                intent=intent,
                category=category,
                location=location,
                skills=skills,
            )

        if intent == CareerIntent.SKILL_COOCCURRENCE:
            skills = self._extract_cooccurrence_skill(text, skill_vocab)

            return CareerMarketQuery(
                intent=intent,
                category=category,
                location=location,
                skills=skills,
            )

        return CareerMarketQuery(
            intent=CareerIntent.SKILL_DEMAND,
            category=category,
            location=location,
        )

    def _detect_intent(self, text: str) -> CareerIntent:
        if self._has_any(text, self.GAP_CUES):
            return CareerIntent.CANDIDATE_SKILL_GAP

        # Phải check co-occurrence TRƯỚC comparison.
        # "nó còn hay yêu cầu thêm kỹ năng nào?"
        # có chữ "hay" nhưng không phải A vs B.
        if (
            self._has_any(text, self.COOCCURRENCE_CUES)
            or re.search(r"\bcó .+?,\s*những skill nào", text)
            or re.search(r"\byêu cầu .+?,\s*nó còn", text)
            or re.search(r"\bdùng .+?,\s*stack", text)
        ):
            return CareerIntent.SKILL_COOCCURRENCE

        if (
            ("giữa " in text and " và " in text)
            or " so với " in text
            or (" hay " in text and "được yêu cầu nhiều hơn" in text)
            or (" hay " in text and "xuất hiện nhiều hơn" in text)
            or "phổ biến hơn" in text
            or "bên nào cao hơn" in text
        ):
            return CareerIntent.SKILL_COMPARISON

        return CareerIntent.SKILL_DEMAND

    def _extract_comparison_skills(
        self,
        text: str,
        skill_vocab: tuple[VocabularyEntry, ...],
    ) -> tuple[str, ...]:
        patterns = (
            # A hay B xuất hiện nhiều hơn trong ...?
            r"^(?P<a>.+?)\s+hay\s+(?P<b>.+?)"
            r"\s+xuất hiện nhiều hơn(?:\s+trong|\?|$)",

            # giữa A và B skill nào phổ biến hơn?
            r"\bgiữa\s+(?P<a>.+?)\s+và\s+(?P<b>.+?)"
            r"(?:\s+skill nào|\s+kỹ năng nào|\s+phổ biến hơn|\s+bên nào|\?|$)",

            # demand cho A so với B bên nào cao hơn?
            r"\bdemand cho\s+(?P<a>.+?)\s+so với\s+(?P<b>.+?)"
            r"(?:\s+bên nào|\s+skill nào|\s+kỹ năng nào|\s+cao hơn|\?|$)",

            # ..., A hay B được yêu cầu nhiều hơn?
            r"(?:^|,\s*)(?P<a>[^,]+?)\s+hay\s+(?P<b>.+?)"
            r"\s+được yêu cầu nhiều hơn",
        )

        for pattern in patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            first = self._best_skill(match.group("a"), skill_vocab)
            second = self._best_skill(match.group("b"), skill_vocab)

            if first and second and first != second:
                return first, second

        return ()

    def _extract_cooccurrence_skill(
        self,
        text: str,
        skill_vocab: tuple[VocabularyEntry, ...],
    ) -> tuple[str, ...]:
        patterns = (
            # autocad thường xuất hiện cùng những kỹ năng nào trong ...?
            r"^(?P<body>.+?)\s+thường xuất hiện cùng những kỹ năng nào"
            r"(?:\s+trong|\?|$)",

            # ... có excel, những skill nào...
            r"\bcó\s+(?P<body>.+?),\s*những skill",

            # ... dùng javascript, stack đi kèm...
            r"\bdùng\s+(?P<body>.+?),\s*stack",

            # ... yêu cầu python, nó còn hay yêu cầu...
            r"\byêu cầu\s+(?P<body>.+?),\s*nó còn",
        )

        for pattern in patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            skill = self._best_skill(match.group("body"), skill_vocab)

            if skill:
                return (skill,)

        return ()

    def _extract_candidate_skills(
        self,
        text: str,
        skill_vocab: tuple[VocabularyEntry, ...],
    ) -> tuple[str, ...]:
        patterns = (
            # Đối chiếu A, B với job ...
            r"\bđối chiếu\s+(?P<body>.+?)\s+với job\b",

            # Mình đã có A, B. Nếu nhắm ...
            r"\b(?:mình|tôi)\s+đã có\s+(?P<body>.+?)"
            r"(?:\.\s*nếu|\s+nếu nhắm)",

            # Profile hiện có A, B; với thị trường ...
            r"\bprofile hiện có\s+(?P<body>.+?);\s*với\b",

            # Nếu đã biết A, B và muốn theo ...
            r"\bnếu đã biết\s+(?P<body>.+?)\s+và muốn theo\b",
        )

        for pattern in patterns:
            match = re.search(pattern, text)

            if not match:
                continue

            mentions = _extract_mentions(match.group("body"), skill_vocab)

            if mentions:
                return mentions

        return ()

    @staticmethod
    def _best_skill(
        text: str,
        skill_vocab: tuple[VocabularyEntry, ...],
    ) -> str | None:
        mentions = _extract_mentions(text, skill_vocab)

        if not mentions:
            return None

        return mentions[0]

    @staticmethod
    def _has_any(text: str, cues: tuple[str, ...]) -> bool:
        return any(cue in text for cue in cues)

