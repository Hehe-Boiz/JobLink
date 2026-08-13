from __future__ import annotations

import hashlib
import logging
from time import perf_counter
from apps.applications.models import Application
from apps.matching.domain import MatchLevel, RequirementDecision
from apps.matching.models import ApplicationMatchAnalysis, ApplicationMatchStatus
from .document_parser import CVDocumentLoader
from .exceptions import ApplicationMatchingError
from .job_snapshot import build_job_snapshot, calculate_job_fingerprint
from .pipeline import ApplicationMatchingPipeline


logger = logging.getLogger(__name__)


def _serialize_decision(decision: RequirementDecision) -> dict:

    requirement = decision.requirement
    candidate_skill = decision.candidate_skill
    candidate_data = None
    if candidate_skill is not None:
        candidate_data = {
            "canonical_skill": candidate_skill.canonical_skill,
            "matched_alias": candidate_skill.matched_alias,
            "evidence_text": candidate_skill.evidence_text,
            "section": candidate_skill.section.value,
            "evidence_strength": float(candidate_skill.evidence_strength),
            "chunk_key": candidate_skill.chunk_key,
            "is_negated": candidate_skill.is_negated,
        }

    return {
        "requirement_id": requirement.requirement_id,
        "requirement_text": requirement.original_text,
        "requirement_skill": requirement.canonical_skill,
        "priority": requirement.priority.value,
        "requirement_source": requirement.source,
        "requirement_chunk_key": requirement.source_chunk_key,
        "level": decision.level.value,
        "match_type": decision.match_type.value,
        "credit": float(decision.credit),
        "decision_source": decision.decision_source.value,
        "evidence_strength": float(decision.evidence_strength),
        "selected_chunk_key": decision.selected_chunk_key,
        "reason": decision.reason,
        "verified_by_llm": decision.verified_by_llm,
        "judge_confidence": (
            float(decision.judge_confidence)
            if decision.judge_confidence is not None
            else None
        ),
        "candidate_skill": candidate_data,
    }


def _build_evidence(decisions: list[RequirementDecision]) -> list[dict]:
    evidence_by_chunk: dict[str, dict] = {}
    for decision in decisions:
        if decision.level == MatchLevel.MISSING:
            continue

        candidate_skill = decision.candidate_skill
        if candidate_skill is None:
            continue
        chunk_key = candidate_skill.chunk_key
        evidence = evidence_by_chunk.get(chunk_key)

        if evidence is None:
            evidence = {
                "chunk_key": chunk_key,
                "text": candidate_skill.evidence_text,
                "section": candidate_skill.section.value,
                "evidence_strength": float(candidate_skill.evidence_strength),
                "skills": [],
            }

            evidence_by_chunk[chunk_key] = evidence

        skill_name = candidate_skill.canonical_skill
        if skill_name not in evidence["skills"]:
            evidence["skills"].append(skill_name)

    return list(evidence_by_chunk.values())

class ApplicationMatchingService:
    PARSER_VERSION = "document-text-v2"
    MATCHER_VERSION = "static-skill-v3"
    SCORING_VERSION = "required-preferred-evidence-v1"

    def __init__(self, document_loader: CVDocumentLoader | None = None, pipeline: ApplicationMatchingPipeline | None = None) -> None:
        self._document_loader = document_loader or CVDocumentLoader()
        self._pipeline = pipeline or ApplicationMatchingPipeline(document_loader=(self._document_loader))

    def run(self, application: Application) -> ApplicationMatchAnalysis:
        started_at = perf_counter()
        analysis = ApplicationMatchAnalysis.objects.create(
                application=application,
                status=ApplicationMatchStatus.PENDING,
                parser_version=self.PARSER_VERSION,
                matcher_version=self.MATCHER_VERSION,
                scoring_version=self.SCORING_VERSION,
            )

        try:

            job_snapshot = build_job_snapshot(application.job)
            analysis.job_snapshot = (job_snapshot)
            analysis.job_fingerprint = calculate_job_fingerprint(job_snapshot)
            analysis.status = ApplicationMatchStatus.PARSING
            analysis.save()
            parsed_cv = self._document_loader.load(application.cv)
            analysis.cv_hash = (hashlib.sha256(parsed_cv.content).hexdigest())
            analysis.status = ApplicationMatchStatus.MATCHING
            analysis.save()
            result = self._pipeline.run_parsed(parsed_cv=parsed_cv, job_snapshot=job_snapshot)
            matched = [
                _serialize_decision(decision)
                for decision in result.matched
            ]
            partial = [
                _serialize_decision(decision)
                for decision in result.partial
            ]
            missing = [
                _serialize_decision(decision)
                for decision in result.missing
            ]
            positive_decisions = [*result.matched, *result.partial,]
            evidence = _build_evidence(positive_decisions)
            analysis.final_score = result.final_score
            analysis.matched_skills = matched
            analysis.partial_skills = partial
            analysis.missing_skills = missing
            analysis.evidence = evidence
            analysis.breakdown = result.breakdown
            analysis.explanation = ""
            analysis.status = ApplicationMatchStatus.COMPLETED

        except ApplicationMatchingError as exc:
            analysis.status = ApplicationMatchStatus.FAILED
            analysis.error_code = exc.__class__.__name__
            analysis.error_message = str(exc)

        except Exception as exc:
            logger.exception("Unexpected matching error: application_id=%s", application.id)
            analysis.status = ApplicationMatchStatus.FAILED
            analysis.error_code = exc.__class__.__name__
            analysis.error_message = "Đã xảy ra lỗi khi phân tích hồ sơ."
        finally:
            analysis.processing_ms = round(perf_counter() - started_at * 1000)
            analysis.save()

        return analysis