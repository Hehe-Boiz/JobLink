from decimal import Decimal, ROUND_HALF_UP

from apps.matching.constants import EVIDENCE_WEIGHT, PREFERRED_SKILLS_WEIGHT, REQUIRED_SKILLS_WEIGHT
from apps.matching.domain import ApplicationScoreResult, MatchLevel, RequirementDecision, RequirementPriority


class DeterministicScorer:
    def score(self, decisions: list[RequirementDecision]) -> ApplicationScoreResult:

        required: list[RequirementDecision] = []
        preferred: list[RequirementDecision] = []

        for decision in decisions:
            if (decision.requirement.priority == RequirementPriority.REQUIRED):
                required.append(decision)

            elif (decision.requirement.priority == RequirementPriority.PREFERRED):
                preferred.append(decision)

        required_score = self._coverage(required)
        preferred_score = self._coverage(preferred)
        evidence_score = self._evidence_quality(decisions)

        weighted_score = Decimal("0.00")
        active_weight = Decimal("0.00")

        if required:
            weighted_score += required_score * REQUIRED_SKILLS_WEIGHT
            active_weight += REQUIRED_SKILLS_WEIGHT

        if preferred:
            weighted_score += preferred_score * PREFERRED_SKILLS_WEIGHT
            active_weight += PREFERRED_SKILLS_WEIGHT

        # Evidence quality áp dụng cho analysis
        # kể cả khi chưa tìm được positive evidence.
        if decisions:
            weighted_score += evidence_score * EVIDENCE_WEIGHT
            active_weight += EVIDENCE_WEIGHT

        if active_weight == Decimal("0.00"):
            final_score = Decimal("0.00")
        else:
            final_score = (weighted_score / active_weight * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        matched_list: list[RequirementDecision] = []
        partial_list: list[RequirementDecision] = []
        missing_list: list[RequirementDecision] = []

        for decision in decisions:
            if decision.level == MatchLevel.MATCHED:
                matched_list.append(decision)

            elif decision.level == MatchLevel.PARTIAL:
                partial_list.append(decision)

            elif decision.level == MatchLevel.MISSING:
                missing_list.append(decision)

        matched = tuple(matched_list)
        partial = tuple(partial_list)
        missing = tuple(missing_list)

        breakdown = {
            "required_skills": {
                "score": float(
                    required_score * Decimal("100")
                ),
                "count": len(required),
                "weight": float(REQUIRED_SKILLS_WEIGHT),
            },
            "preferred_skills": {
                "score": float(
                    preferred_score * Decimal("100")
                ),
                "count": len(preferred),
                "weight": float(PREFERRED_SKILLS_WEIGHT),
            },
            "evidence_quality": {
                "score": float(
                    evidence_score * Decimal("100")
                ),
                "weight": float(EVIDENCE_WEIGHT),
            },
        }

        return ApplicationScoreResult(
            final_score=final_score,
            breakdown=breakdown,
            matched=matched,
            partial=partial,
            missing=missing,
        )

    @staticmethod
    def _coverage(decisions: list[RequirementDecision]) -> Decimal:
        if not decisions:
            return Decimal("0.00")

        total_credit = sum(
            (
                decision.credit
                for decision in decisions
            ),
            Decimal("0.00"),
        )

        return total_credit / Decimal(len(decisions))

    @staticmethod
    def _evidence_quality(decisions: list[RequirementDecision]) -> Decimal:

        evidence_decisions: list[RequirementDecision] = []

        for decision in decisions:
            if decision.level != MatchLevel.MISSING:
                evidence_decisions.append(decision) 

        if not evidence_decisions:
            return Decimal("0.00")

        total_strength = sum(
            (
                decision.evidence_strength
                for decision in evidence_decisions
            ),
            Decimal("0.00"),
        )

        return total_strength / Decimal(len(evidence_decisions))