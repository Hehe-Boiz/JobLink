from __future__ import annotations

from decimal import Decimal
from apps.matching.constants import SEMANTIC_MATCH_CREDIT
from apps.matching.domain import DecisionSource, FusedHit, MatchLevel, MatchType, RequirementDecision
from .skill_extractor import SECTION_EVIDENCE_STRENGTH


MIN_SEMANTIC_SIMILARITY = 0.80


class RetrievalMatcher:
    def match(self, decisions: list[RequirementDecision], retrieval_results: dict[str, list[FusedHit]]) -> list[RequirementDecision]:
        results: list[RequirementDecision] = []

        for decision in decisions:
            if decision.level != MatchLevel.MISSING:
                results.append(decision)
                continue

            requirement_id = decision.requirement.requirement_id
            hits = retrieval_results.get(requirement_id, [])
            updated_decision = self._match_missing(decision=decision, hits=hits)
            results.append(updated_decision)
        return results

    def _match_missing(self, decision: RequirementDecision, hits: list[FusedHit]) -> RequirementDecision:
        if not hits:
            return decision

        best_hit = hits[0]
        if not self._is_strong_enough(best_hit):
            return decision

        evidence_strength = SECTION_EVIDENCE_STRENGTH.get(best_hit.section, Decimal("0.45"))
        return RequirementDecision(
            requirement=decision.requirement,
            level=MatchLevel.PARTIAL,
            match_type=MatchType.SEMANTIC,
            credit=Decimal(SEMANTIC_MATCH_CREDIT),
            decision_source=DecisionSource.RETRIEVAL,
            candidate_skill=None,
            selected_chunk_key=best_hit.chunk_key,
            selected_evidence_section=best_hit.section,
            selected_evidence_text=best_hit.text,
            evidence_strength=evidence_strength,
            reason=(
                "Retrieved CV evidence is semantically related "
                "to the job requirement."
            ),
        )

    @staticmethod
    def _is_strong_enough(hit: FusedHit) -> bool:
        similarity = hit.dense_similarity
        if similarity is None:
            return False

        return similarity >= MIN_SEMANTIC_SIMILARITY