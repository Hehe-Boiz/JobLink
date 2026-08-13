import hashlib
import logging
from time import perf_counter

from apps.applications.models import Application
from apps.matching.models import ApplicationMatchAnalysis, ApplicationMatchStatus

from .document_parser import CVDocumentLoader, DocumentProcessingError
from .job_snapshot import build_job_matching_text, build_job_snapshot, calculate_job_fingerprint
from .matcher import ExactAliasMatcher, MatchingInputError
from .skill_extractor import SkillExtractor

# tạo 1 logger cho file hiện tại
logger = logging.getLogger(__name__)

class ApplicationMatchingService:
    PARSER_VERSION = "document-text-v1"
    MATCHER_VERSION = "exact-alias-v1"
    SCORING_VERSION = "required-skill-ratio-v1"

    def __init__(self, document_loader: CVDocumentLoader | None = None, skill_extractor: SkillExtractor | None = None, matcher: ExactAliasMatcher | None = None) -> None:
        self._document_loader = (document_loader or CVDocumentLoader())
        self._skill_extractor = (skill_extractor or SkillExtractor())
        self._matcher = (matcher or ExactAliasMatcher())

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
            # dựng snapshot 
            job_snapshot = build_job_snapshot(application.job)

            # đưa snapshot cho object 
            analysis.job_snapshot = job_snapshot

            # tạo fingerprint cho job 
            analysis.job_fingerprint = (
                calculate_job_fingerprint(
                    job_snapshot
                )
            )

            analysis.status = (
                ApplicationMatchStatus.PARSING
            )
            analysis.save()

            # load từ cloud về -> ParsedDocument
            parsed_cv = (
                self._document_loader.load(
                    application.cv
                )
            )

            # Tạo hash cho CV
            analysis.cv_hash = hashlib.sha256(
                parsed_cv.content
            ).hexdigest()

            # extract skill từ cv
            cv_skills = (
                self._skill_extractor.extract(
                    parsed_cv.text
                )
            )

            # tạo text của job -> Gộp requirements và tags
            job_text = build_job_matching_text(
                job_snapshot
            )

            # extract skill từ job
            job_skills = (
                self._skill_extractor.extract(
                    job_text
                )
            )

            analysis.status = (
                ApplicationMatchStatus.MATCHING
            )
            analysis.save()

            # thực hiện tính điểm
            result = self._matcher.match(
                cv_skills=cv_skills,
                job_skills=job_skills,
            )

            analysis.status = (
                ApplicationMatchStatus.EXPLAINING
            )
            analysis.save()

            # đưa kết quả vào analysis
            analysis.final_score = (
                result.final_score
            )

            analysis.matched_skills = (
                result.matched_skills
            )

            analysis.partial_skills = (
                result.partial_skills
            )

            analysis.missing_skills = (
                result.missing_skills
            )

            analysis.evidence = result.evidence
            analysis.breakdown = result.breakdown
            analysis.explanation = (
                result.explanation
            )

            analysis.status = (
                ApplicationMatchStatus.COMPLETED
            )

        except (DocumentProcessingError, MatchingInputError) as exc:
            analysis.status = (ApplicationMatchStatus.FAILED)
            analysis.error_code = (exc.__class__.__name__)
            analysis.error_message = str(exc)

        except Exception as exc:
            logger.exception(
                "Unexpected matching error: "
                "application_id=%s",
                application.id,
            )

            analysis.status = (ApplicationMatchStatus.FAILED)

            analysis.error_code = (exc.__class__.__name__)

            analysis.error_message = ("Đã xảy ra lỗi khi phân tích hồ sơ.")

        finally:
            analysis.processing_ms = round(
                (
                    perf_counter()
                    - started_at
                )
                * 1000
            )

            analysis.save()

        return analysis