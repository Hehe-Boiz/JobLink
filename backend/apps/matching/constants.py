from decimal import Decimal

SCORE_SCOPE = "SUBMITTED_CV_VS_JOB_REQUIREMENTS"


# Algorithm versions
PARSER_VERSION = "document-text-v2"
STRUCTURED_EXTRACTOR_VERSION = "cv-jd-structured-v2"
SKILL_CATALOG_VERSION = "technical-skills-v2"
MATCHER_VERSION = "exact-alias-related-v2"
DECISION_VERSION = "requirement-decision-v1"
SCORING_VERSION = "application-full-score-v1"
CRITICAL_POLICY_VERSION = "critical-policy-v1"

# Chưa được dùng cho đến khi embedding/retrieval thực sự được nối vào pipeline.
EMBEDDING_VERSION = "sentence-transformer-v1"
RETRIEVAL_VERSION = "bm25-dense-rrf-v1"
RERANKER_VERSION = "cross-encoder-v1"
PROMPT_VERSION = "application-grounded-explanation-v1"
OPENSEARCH_INDEX_VERSION = "cv-evidence-v1"


# Retrieval modes
RETRIEVAL_MODE_EXACT_ONLY = "exact_only"
RETRIEVAL_MODE_EXACT_RELATED = "exact_related"
RETRIEVAL_MODE_DENSE = "dense"
RETRIEVAL_MODE_HYBRID = "hybrid"
RETRIEVAL_MODE_HYBRID_RERANKED = "hybrid_reranked"
RETRIEVAL_MODE_HYBRID_RERANKED_LLM = (
    "hybrid_reranked_llm"
)

ALLOWED_RETRIEVAL_MODES = frozenset({
    RETRIEVAL_MODE_EXACT_ONLY,
    RETRIEVAL_MODE_EXACT_RELATED,
    RETRIEVAL_MODE_DENSE,
    RETRIEVAL_MODE_HYBRID,
    RETRIEVAL_MODE_HYBRID_RERANKED,
    RETRIEVAL_MODE_HYBRID_RERANKED_LLM,
})


# Hiện tại code mới có exact/alias.
# Khi related matcher hoàn thành, mới dùng exact_related thật sự.
DEFAULT_RETRIEVAL_MODE = RETRIEVAL_MODE_EXACT_ONLY


# Matching credits
EXACT_MATCH_CREDIT = "1.00"
ALIAS_MATCH_CREDIT = "1.00"
SEMANTIC_MATCH_CREDIT = "0.75"
DEFAULT_PARTIAL_MATCH_CREDIT = "0.50"
MISSING_MATCH_CREDIT = "0.00"


# Retrieval defaults
DEFAULT_DENSE_TOP_K = 10
DEFAULT_BM25_TOP_K = 10
DEFAULT_FUSION_TOP_K = 10
DEFAULT_RERANK_TOP_K = 5

# RRF thường dùng hằng số k để giảm ảnh hưởng quá mạnh
# của các vị trí đứng đầu.
DEFAULT_RRF_K = 60


# Document limits
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_TEXT_CHARS = 100_000
MAX_DOCUMENT_PAGES = 50
MAX_EVIDENCE_CHUNKS = 500
MAX_CHUNK_CHARS = 1_500

REQUIRED_SKILLS_WEIGHT = Decimal("0.70")
PREFERRED_SKILLS_WEIGHT = Decimal("0.20")
EVIDENCE_WEIGHT = Decimal("0.10")