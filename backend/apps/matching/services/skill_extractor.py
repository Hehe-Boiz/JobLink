import re
from dataclasses import dataclass # tạo class chỉ để chứa dữ liệu

from .skill_catalog import SKILL_ALIASES

@dataclass(frozen=True)
class SkillOccurrence:
    canonical_name: str
    matched_alias: str
    evidence: str

class SkillExtractor:
    def __init__(self, skill_aliases: dict[str, tuple[str, ...]] | None = None) -> None:
        self._skill_aliases = (skill_aliases or SKILL_ALIASES)
        self._compiled_patterns = (self._compile_patterns())

    def extract(self, text: str) -> dict[str, SkillOccurrence]:
        segments = self._split_segments(text)
        occurrences: dict[str, SkillOccurrence] = {}

        for canonical_name, alias_patterns in (self._compiled_patterns.items()):
            occurrence = self._find_first_occurrence(
                canonical_name=canonical_name,
                alias_patterns=alias_patterns,
                segments=segments,
            )

            if occurrence is not None:
                occurrences[canonical_name] = occurrence

        return occurrences

    def _compile_patterns(self):
        compiled = {}

        for canonical_name, aliases in (self._skill_aliases.items()):
            unique_aliases = list( # chuyện lại dict về thành list để nó độc nhất 
                dict.fromkeys( # tạo dict mà mỗi phần tử đầu vào trở thành một key
                    (
                        canonical_name,
                        *aliases,
                    )
                )
            )

            alias_patterns = []

            for alias in unique_aliases:
                pattern = self._build_pattern(alias)

                pair = (
                    alias,
                    pattern,
                )

                alias_patterns.append(pair)
            compiled[canonical_name] = alias_patterns

        return compiled
        
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

    # segment theo regax    
    @staticmethod
    def _split_segments(text: str) -> list[str]:
        raw_segments = re.split( # dùng regax để xác định vị trí cần tách
            r"[\r\n]+|(?<=[.!?])\s+",
            text,
        )

        cleaned_segments = []

        for segment in raw_segments:
            if segment.strip():
                cleaned_segment = " ".join(
                    segment.split()
                )
                cleaned_segments.append(
                    cleaned_segment
                )

        return cleaned_segments

    # tìm ra trong cái skill đó trong segment và lấy ra cái đầu tiên
    @staticmethod
    def _find_first_occurrence(canonical_name: str, alias_patterns, segments: list[str]) -> SkillOccurrence | None:
        for segment in segments:
            for alias, pattern in alias_patterns:
                if pattern.search(segment):
                    return SkillOccurrence(
                        canonical_name=canonical_name,
                        matched_alias=alias,
                        evidence=segment[:500],
                    )

        return None