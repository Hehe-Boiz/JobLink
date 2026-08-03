from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP # Đây là quy tắc làm tròn

from .skill_extractor import SkillOccurrence


class MatchingInputError(Exception):
    pass

# frozen=True làm object gần như bất biến — immutable sau khi được tạo.
@dataclass(frozen=True)
class MatchResult:
    final_score: Decimal
    matched_skills: list[str]
    partial_skills: list[str]
    missing_skills: list[str]
    evidence: list[dict]
    breakdown: dict
    explanation: str

class ExactAliasMatcher:
    def match(self, cv_skills: dict[str, SkillOccurrence], job_skills: dict[str, SkillOccurrence]) -> MatchResult:
        if not job_skills:
            raise MatchingInputError(
                "Không trích xuất được kỹ năng nào "
                "từ yêu cầu công việc."
            )

        cv_skill_names = set(cv_skills)
        job_skill_names = set(job_skills)

        matched = sorted(
            cv_skill_names.intersection(
                job_skill_names
            )
        )

        missing = sorted(
            job_skill_names.difference(
                cv_skill_names
            )
        )

        partial: list[str] = []

        matched_count = Decimal(
            len(matched)
        )

        total_count = Decimal(
            len(job_skill_names)
        )

        final_score = (matched_count* Decimal("100")/ total_count).quantize(
            Decimal("0.01"), # làm tròn ở số thập phân thứ 2
            rounding=ROUND_HALF_UP,
        )

        evidence = []

        for skill in matched:
            item = {
                "skill": skill,
                "match_type": "EXACT_OR_ALIAS",
                "matched_by": (
                    cv_skills[skill].matched_alias
                ),
                "cv_evidence": (
                    cv_skills[skill].evidence
                ),
                "job_evidence": (
                    job_skills[skill].evidence
                ),
            }

            evidence.append(item)

        breakdown = {
            "required_skills": {
                "matched_count": len(matched),
                "missing_count": len(missing),
                "total_count": len(job_skill_names),
                "score": float(final_score),
                "weight": 1.0,
            },
            "policy": (
                "required-skill-ratio-v1"
            ),
        }

        explanation = (
            self._build_explanation(
                matched=matched,
                missing=missing,
                total=len(job_skill_names),
                score=final_score,
            )
        )

        return MatchResult(
            final_score=final_score,
            matched_skills=matched,
            partial_skills=partial,
            missing_skills=missing,
            evidence=evidence,
            breakdown=breakdown,
            explanation=explanation,
        )

    @staticmethod
    def _build_explanation(matched: list[str], missing: list[str], total: int, score: Decimal) -> str:
        matched_text = (
            ", ".join(matched)
            if matched
            else "Không có"
        )

        missing_text = (
            ", ".join(missing)
            if missing
            else "Không có"
        )

        return (
            f"CV thể hiện {len(matched)}/{total} "
            f"kỹ năng được nhận diện trong yêu cầu, "
            f"tương ứng {score}/100. "
            f"Kỹ năng đã khớp: {matched_text}. "
            f"Kỹ năng chưa tìm thấy bằng chứng "
            f"trong CV: {missing_text}."
        )