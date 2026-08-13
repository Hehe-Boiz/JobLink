from decimal import Decimal

from apps.matching.domain import CandidateSkill, JobRequirement, MatchLevel, MatchType, DecisionSource, RequirementDecision
from .skill_catalog import RELATED_SKILLS


EXACT_CREDIT = Decimal("1.00")
ALIAS_CREDIT = Decimal("1.00")
MISSING_CREDIT = Decimal("0.00")


class SkillMatcher:
    def match(self, candidate_skills: dict[str, CandidateSkill], requirements: list[JobRequirement]) -> list[RequirementDecision]:
        decisions: list[RequirementDecision] = []
        for requirement in requirements:
            requirement_skill = requirement.canonical_skill
            if requirement_skill is None:
                decisions.append(
                    self._build_decision(
                        requirement=requirement,
                        level=MatchLevel.MISSING,
                        match_type=MatchType.NONE,
                        credit=MISSING_CREDIT,
                        reason="Requirement has no canonical skill.",
                    )
                )
                continue

            candidate_skill = candidate_skills.get(requirement_skill)
            if candidate_skill is not None and not candidate_skill.is_negated:
                if candidate_skill.matched_alias.casefold() == requirement_skill.casefold():
                    match_type = MatchType.EXACT
                    credit = EXACT_CREDIT
                else:
                    match_type = MatchType.ALIAS
                    credit = ALIAS_CREDIT

                decisions.append(
                    self._build_decision(
                        requirement=requirement,
                        level=MatchLevel.MATCHED,
                        match_type=match_type,
                        credit=credit,
                        candidate_skill=candidate_skill,
                        reason="Direct canonical skill match.",
                    )
                )
                continue

            related_match = self._find_best_related(requirement_skill=requirement_skill, candidate_skills=candidate_skills,)
            if related_match is not None:
                related_skill, credit = related_match

                decisions.append(
                    self._build_decision(
                        requirement=requirement,
                        level=MatchLevel.PARTIAL,
                        match_type=MatchType.RELATED,
                        credit=credit,
                        candidate_skill=related_skill,
                        reason="Related skill match.",
                    )
                )
                continue

            # Missing
            decisions.append(
                self._build_decision(
                    requirement=requirement,
                    level=MatchLevel.MISSING,
                    match_type=MatchType.NONE,
                    credit=MISSING_CREDIT,
                    reason="No direct or related skill found.",
                )
            )

        return decisions

    @staticmethod
    def _find_best_related(requirement_skill: str, candidate_skills: dict[str, CandidateSkill]) -> tuple[CandidateSkill, Decimal] | None:
        related_skills = RELATED_SKILLS.get(requirement_skill, {})
        best_skill: CandidateSkill | None = None
        best_credit: Decimal | None = None

        for skill_name, credit in related_skills.items():
            candidate_skill = candidate_skills.get(skill_name)

            if candidate_skill is None or candidate_skill.is_negated:
                continue

            if best_credit is None or credit > best_credit:
                best_skill = candidate_skill
                best_credit = credit

        if best_skill is None or best_credit is None:
            return None

        return best_skill, best_credit

    @staticmethod
    def _build_decision(*, requirement: JobRequirement, level: MatchLevel, match_type: MatchType, credit: Decimal, reason: str, candidate_skill: CandidateSkill | None = None) -> RequirementDecision:
        if match_type == MatchType.RELATED:
            decision_source = DecisionSource.RELATED_RULE
        else:
            decision_source = DecisionSource.STATIC_MATCHER

        evidence_strength = (
            candidate_skill.evidence_strength
            if candidate_skill is not None
            else Decimal("0.00")
        )

        return RequirementDecision(
            requirement=requirement,
            level=level,
            match_type=match_type,
            credit=credit,
            candidate_skill=candidate_skill,
            evidence_strength=evidence_strength,
            decision_source=decision_source,
            reason=reason,
        )