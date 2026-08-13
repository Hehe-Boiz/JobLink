from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

# file dùng để biết feature này loại data hay state nào 

# Cho biết 1 đoạn CV thuộc phần nào 
class DocumentSection(str, Enum):
    SUMMARY = "SUMMARY"
    SKILLS = "SKILLS"
    WORK_EXPERIENCE = "WORK_EXPERIENCE"
    PROJECTS = "PROJECTS"
    EDUCATION = "EDUCATION"
    CERTIFICATIONS = "CERTIFICATIONS"
    AWARDS = "AWARDS"
    UNKNOWN = "UNKNOWN"


class RequirementPriority(str, Enum):
    REQUIRED = "REQUIRED"
    PREFERRED = "PREFERRED"


class MatchLevel(str, Enum):
    MATCHED = "MATCHED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class MatchType(str, Enum):
    EXACT = "EXACT"
    ALIAS = "ALIAS"
    RELATED = "RELATED"
    SEMANTIC = "SEMANTIC"
    NONE = "NONE"


class RetrievalMode(str, Enum):
    EXACT_ONLY = "exact_only"
    EXACT_RELATED = "exact_related"
    DENSE = "dense"
    HYBRID = "hybrid"
    HYBRID_RERANKED = "hybrid_reranked"
    HYBRID_RERANKED_LLM = "hybrid_reranked_llm"


class DecisionSource(str, Enum):
    STATIC_MATCHER = "STATIC_MATCHER"
    RELATED_RULE = "RELATED_RULE"
    RETRIEVAL = "RETRIEVAL"
    LLM_JUDGE = "LLM_JUDGE"


# Structured document types
@dataclass(frozen=True, slots=True)
class TextSegment:
    """
    Một đoạn nhỏ lấy từ CV hoặc Job.

    stable_key:
        ID ổn định, ví dụ "PROJECTS:2:a91b7c".

    text:
        Nội dung nguyên bản để hiển thị làm evidence.

    normalized_text:
        Nội dung đã chuẩn hóa để search/matching.
    """

    index: int
    stable_key: str
    text: str
    normalized_text: str
    section: DocumentSection
    source: str

    page_number: int | None = None
    start_offset: int | None = None
    end_offset: int | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True, slots=True)
class SkillOccurrence:
    """
    Một lần skill xuất hiện trong một TextSegment.

    Ví dụ:
        canonical_skill = "postgresql"
        matched_alias = "postgres"
    """

    canonical_skill: str
    matched_alias: str
    segment: TextSegment
    start: int
    end: int

    is_negated: bool = False


@dataclass(frozen=True, slots=True)
class CandidateSkill:
    canonical_skill: str
    matched_alias: str
    evidence_text: str
    section: DocumentSection
    evidence_strength: Decimal
    chunk_key: str

    is_negated: bool = False

@dataclass(frozen=True, slots=True)
class JobRequirement:
    requirement_id: str
    original_text: str
    normalized_text: str
    priority: RequirementPriority

    canonical_skill: str | None = None
    source: str = "REQUIREMENTS"
    source_chunk_key: str | None = None
    extraction_method: str = "RULE"
    confidence: Decimal = Decimal("1.00")


# Retrieval hits
@dataclass(frozen=True, slots=True)
class DenseHit:
    """
    Một CV chunk được tìm bằng embedding/pgvector.
    """

    chunk_key: str
    rank: int
    distance: float
    similarity: float
    section: DocumentSection
    text: str


@dataclass(frozen=True, slots=True)
class BM25Hit:
    """
    Một CV chunk được tìm bằng OpenSearch/BM25.
    """

    chunk_key: str
    rank: int
    score: float
    section: DocumentSection
    text: str


@dataclass(frozen=True, slots=True)
class FusedHit:
    """
    Kết quả sau khi gộp dense và BM25.
    """

    chunk_key: str
    rank: int
    rrf_score: float
    section: DocumentSection
    text: str

    dense_rank: int | None = None
    bm25_rank: int | None = None
    dense_similarity: float | None = None
    bm25_score: float | None = None


@dataclass(frozen=True, slots=True)
class RerankedHit:
    """
    Kết quả sau cross-encoder reranker.
    """

    chunk_key: str
    rank: int
    reranker_score: float
    section: DocumentSection
    text: str

    fused_rank: int | None = None
    rrf_score: float | None = None


# Judgement and final decision
@dataclass(frozen=True, slots=True)
class SemanticJudgement:
    """
    Output đã validate từ semantic/LLM judge.

    LLM chỉ được chọn chunk ID đã được cung cấp.
    """

    requirement_id: str
    level: MatchLevel
    evidence_chunk_keys: tuple[str, ...]
    reason: str
    confidence: Decimal


@dataclass(frozen=True, slots=True)
class RequirementDecision:
    """
    Quyết định cuối cho đúng một Job requirement.
    """

    requirement: JobRequirement
    level: MatchLevel
    match_type: MatchType
    credit: Decimal
    decision_source: DecisionSource

    candidate_skill: CandidateSkill | None = None
    selected_chunk_key: str | None = None
    evidence_strength: Decimal = Decimal("0.00")
    reason: str = ""

    verified_by_llm: bool = False
    judge_confidence: Decimal | None = None

    selected_chunk_key: str | None = None
    selected_evidence_text: str | None = None
    selected_evidence_section: DocumentSection | None = None


# Policy and scoring results
@dataclass(frozen=True, slots=True)
class ApplicationScoreResult:
    final_score: Decimal
    breakdown: dict[str, Any]

    matched: tuple[RequirementDecision, ...]
    partial: tuple[RequirementDecision, ...]
    missing: tuple[RequirementDecision, ...]


@dataclass(frozen=True, slots=True)
class ExplanationResult:
    """
    Kết quả explanation cuối.

    provider:
        template, openai hoặc provider khác.

    cited_chunk_keys:
        Các evidence chunk thật sự được dùng.
    """

    text: str
    provider: str
    cited_chunk_keys: tuple[str, ...] = ()