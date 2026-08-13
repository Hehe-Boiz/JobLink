from __future__ import annotations

from apps.matching.domain import ApplicationScoreResult, MatchLevel

from .document_parser import CVDocumentLoader, ParsedDocument
from .job_extractor import JobRequirementExtractor
from .matcher import SkillMatcher
from .scorer import DeterministicScorer
from .skill_extractor import SkillExtractor
from .text import build_text_segments
from .retrieval import HybridRetriever
from .retrieval_matcher import RetrievalMatcher


class ApplicationMatchingPipeline:
    def __init__(
        self,
        document_loader: CVDocumentLoader | None = None,
        skill_extractor: SkillExtractor | None = None,
        job_extractor: JobRequirementExtractor | None = None,
        matcher: SkillMatcher | None = None,
        scorer: DeterministicScorer | None = None,
        retriever: HybridRetriever | None = None,
        retrieval_matcher: RetrievalMatcher | None = None,
    ) -> None:
        self._document_loader = document_loader or CVDocumentLoader()
        self._skill_extractor = skill_extractor or SkillExtractor()
        self._job_extractor = job_extractor or JobRequirementExtractor(self._skill_extractor)
        self._matcher = matcher or SkillMatcher()
        self._scorer = scorer or DeterministicScorer()
        self._retriever = retriever or HybridRetriever()
        self._retrieval_matcher = retrieval_matcher or RetrievalMatcher()
        

    def run(self, cv_field, job_snapshot: dict) -> ApplicationScoreResult:
        parsed_cv = self._document_loader.load(cv_field)

        return self.run_parsed(parsed_cv=parsed_cv, job_snapshot=job_snapshot)

    def run_parsed(self, parsed_cv: ParsedDocument, job_snapshot: dict) -> ApplicationScoreResult:
        segments = build_text_segments(parsed_cv.text)
        candidate_skills = self._skill_extractor.extract(segments)
        requirements = self._job_extractor.extract(job_snapshot)
        decisions = self._matcher.match(candidate_skills=candidate_skills, requirements=requirements)
        unresolved_requirements = [
            decision.requirement
            for decision in decisions
            if decision.level == MatchLevel.MISSING
        ]

        retrieval_results = self._retriever.retrieve_many(requirements=unresolved_requirements, segments=segments)
        decisions = self._retrieval_matcher.match(decisions=decisions, retrieval_results=retrieval_results)


        return self._scorer.score(decisions)