from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pgvector.django import CosineDistance

from .embedding import CareerEmbeddingService
from .models import CareerJobChunk
from .normalization import normalize_key


DEFAULT_TOP_K = 5
DEFAULT_CANDIDATE_MULTIPLIER = 5
DEFAULT_EVIDENCE_PER_JOB = 2


@dataclass(frozen=True, slots=True)
class CareerEvidenceChunk:
    """
    Một chunk evidence được retrieval tìm thấy cho một job.
    """

    chunk_id: str
    section: str
    content: str

    distance: float
    similarity: float


@dataclass(frozen=True, slots=True)
class CareerRetrievedJob:
    """
    Kết quả retrieval ở level job.

    Một job có thể có nhiều chunk evidence liên quan,
    nhưng job chỉ xuất hiện một lần trong kết quả cuối.
    """

    source: str
    source_job_id: str

    job_title: str
    company_name: str

    location_key: str | None
    experience_level: str | None
    employment_type: str | None
    category_key: str | None

    published_at: datetime | None
    source_url: str | None

    score: float

    evidence: tuple[CareerEvidenceChunk, ...]


class CareerRetriever:
    """
    Dense retriever cho Career Intelligence RAG.

    Pipeline:

        user query
            ↓
        embed_query()
            ↓
        query vector
            ↓
        metadata filters
            ↓
        cosine distance với CareerJobChunk.embedding
            ↓
        candidate chunks
            ↓
        group theo job
            ↓
        Top-K unique jobs + evidence
    """

    def __init__(
        self,
        embedder: CareerEmbeddingService | None = None,
    ) -> None:
        self.embedder = (
            embedder
            or CareerEmbeddingService()
        )

    def search(
        self,
        query: str,
        *,
        top_k: int = DEFAULT_TOP_K,
        candidate_multiplier: int = DEFAULT_CANDIDATE_MULTIPLIER,
        evidence_per_job: int = DEFAULT_EVIDENCE_PER_JOB,
        source: str | None = None,
        location_key: str | None = None,
        experience_level: str | None = None,
        employment_type: str | None = None,
        category_key: str | None = None,
    ) -> list[CareerRetrievedJob]:
        """
        Tìm các job liên quan nhất tới query.

        top_k:
            Số JOB cuối cùng cần trả về.

        candidate_multiplier:
            Retrieve nhiều chunk hơn top_k trước,
            sau đó mới collapse về unique jobs.

        evidence_per_job:
            Tối đa bao nhiêu chunk evidence được giữ cho mỗi job.
        """

        self._validate_search_args(query=query, top_k=top_k, candidate_multiplier=candidate_multiplier, evidence_per_job=evidence_per_job)
        query_vector = self.embedder.embed_query(query)
        candidate_limit = top_k * candidate_multiplier
        queryset = CareerJobChunk.objects.filter(active=True)

        queryset = self._apply_filters(
            queryset=queryset,
            source=source,
            location_key=location_key,
            experience_level=experience_level,
            employment_type=employment_type,
            category_key=category_key,
        )

        candidates = (
            queryset
            .annotate(
                distance=CosineDistance(
                    "embedding",
                    query_vector.tolist(),
                )
            )
            .order_by("distance")[
                :candidate_limit
            ]
        )

        return self._collapse_to_jobs(
            candidates=candidates,
            top_k=top_k,
            evidence_per_job=evidence_per_job,
        )

    @staticmethod
    def _apply_filters(
        queryset,
        *,
        source: str | None,
        location_key: str | None,
        experience_level: str | None,
        employment_type: str | None,
        category_key: str | None,
    ):
        """
        Apply metadata filters trước vector ranking.
        """

        normalized_filters = {
            "source": normalize_key(source),
            "location_key": normalize_key(
                location_key
            ),
            "experience_level": normalize_key(
                experience_level
            ),
            "employment_type": normalize_key(
                employment_type
            ),
            "category_key": normalize_key(
                category_key
            ),
        }

        filters = {
            key: value
            for key, value
            in normalized_filters.items()
            if value is not None
        }

        if filters:
            queryset = queryset.filter(**filters)

        return queryset

    @staticmethod
    def _collapse_to_jobs(
        candidates,
        *,
        top_k: int,
        evidence_per_job: int,
    ) -> list[CareerRetrievedJob]:
        """
        Collapse chunk-level ranking thành job-level ranking.

        Ví dụ raw retrieval:

            rank 1 → Job A / REQUIRED
            rank 2 → Job A / DESCRIPTION
            rank 3 → Job A / RESPONSIBILITIES
            rank 4 → Job B / REQUIRED
            rank 5 → Job C / REQUIRED

        Không được trả:

            A
            A
            A
            B
            C

        mà phải thành:

            A
            B
            C

        đồng thời giữ các chunk tốt nhất làm evidence.
        """

        jobs: dict[tuple[str, str], dict] = {}
        for chunk in candidates:
            job_key = (
                chunk.source,
                chunk.source_job_id,
            )

            distance = float(chunk.distance)
            similarity = 1.0 - distance
            evidence = CareerEvidenceChunk(
                chunk_id=chunk.chunk_id,
                section=chunk.section,
                content=chunk.content,
                distance=distance,
                similarity=similarity,
            )

            if job_key not in jobs:
                jobs[job_key] = {
                    "source": chunk.source,
                    "source_job_id": chunk.source_job_id,
                    "job_title": chunk.job_title,
                    "company_name": chunk.company_name,
                    "location_key": chunk.location_key,
                    "experience_level": chunk.experience_level,
                    "employment_type": chunk.employment_type,
                    "category_key": chunk.category_key,
                    "published_at": chunk.published_at,
                    "source_url": chunk.source_url,
                    "score": similarity,
                    "evidence": [evidence],
                }

                continue

            current_evidence = jobs[job_key]["evidence"]

            if len(current_evidence) < evidence_per_job:
                current_evidence.append(evidence)

        ranked_jobs = sorted(
            jobs.values(),
            key=lambda item: item["score"],
            reverse=True,
        )

        return [
            CareerRetrievedJob(
                source=item["source"],
                source_job_id=item["source_job_id"],
                job_title=item["job_title"],
                company_name=item["company_name"],
                location_key=item["location_key"],
                experience_level=item["experience_level"],
                employment_type=item["employment_type"],
                category_key=item["category_key"],
                published_at=item["published_at"],
                source_url=item["source_url"],
                score=item["score"],
                evidence=tuple(item["evidence"]),
            )
            for item in ranked_jobs[:top_k]
        ]

    @staticmethod
    def _validate_search_args(
        *,
        query: str,
        top_k: int,
        candidate_multiplier: int,
        evidence_per_job: int,
    ) -> None:
        if not query.strip():
            raise ValueError("Query must not be empty")

        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        if candidate_multiplier <= 0:
            raise ValueError("candidate_multiplier must be greater than 0")

        if evidence_per_job <= 0:
            raise ValueError("evidence_per_job must be greater than 0")