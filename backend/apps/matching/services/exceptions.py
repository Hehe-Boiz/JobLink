class ApplicationMatchingError(Exception):
    """
    Base exception của toàn bộ matching pipeline.
    """


class PermanentMatchingError(ApplicationMatchingError):
    """
    Retry không giải quyết được lỗi này.

    Ví dụ:
    - file sai định dạng;
    - CV rỗng;
    - Job không có requirement;
    - cấu hình sai.
    """


class TransientMatchingError(ApplicationMatchingError):
    """
    Lỗi có thể biến mất khi retry.

    Ví dụ:
    - Cloudinary timeout;
    - OpenSearch tạm ngừng;
    - embedding provider timeout;
    """


# Document errors
class DocumentDownloadError(TransientMatchingError):
    """Không tải được document do lỗi mạng/provider."""


class InvalidDocumentError(PermanentMatchingError):
    """File rỗng, corrupt, encrypted hoặc không hợp lệ."""


class UnsupportedDocumentError(PermanentMatchingError):
    """Định dạng file chưa được hệ thống hỗ trợ."""


class EmptyDocumentError(PermanentMatchingError):
    """Parse/OCR xong nhưng document không có nội dung."""


class OCRProcessingError(TransientMatchingError):
    """OCR provider thất bại tạm thời."""


# Extraction errors
class EmptyJobRequirementsError(PermanentMatchingError):
    """Không tìm thấy requirement đủ điều kiện để chấm."""


# ML/retrieval errors
class EmbeddingError(TransientMatchingError):
    """Embedding model/provider không xử lý được request."""


class RetrievalError(TransientMatchingError):
    """Base error của evidence retrieval."""


class OpenSearchUnavailableError(RetrievalError):
    """OpenSearch không sẵn sàng hoặc query thất bại."""


class RerankerError(TransientMatchingError):
    """Cross-encoder reranker không xử lý được request."""


# LLM/configuration errors
class LLMContractError(TransientMatchingError):
    """
    LLM trả JSON sai schema hoặc invent evidence ID.

    Có thể retry có giới hạn rồi fallback deterministic.
    """


class ConfigurationError(PermanentMatchingError):
    """Cấu hình bắt buộc bị thiếu hoặc không hợp lệ."""