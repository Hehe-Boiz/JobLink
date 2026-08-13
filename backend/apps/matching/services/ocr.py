# sudo apt install tesseract-ocr
# sudo apt install tesseract-ocr-eng tesseract-ocr-vie

from io import BytesIO

import pymupdf
import pytesseract
from PIL import Image

from apps.matching.constants import (
    MAX_DOCUMENT_PAGES,
    MAX_EXTRACTED_TEXT_CHARS,
)

from .exceptions import (
    EmptyDocumentError,
    InvalidDocumentError,
    OCRProcessingError,
)


class PDFOCRService:
    # dpi: Render trang PDF thành một ảnh với độ chi tiết tương đương 200 điểm trên mỗi inch.
    def __init__(self, language: str = "eng+vie", dpi: int = 200) -> None:
        self.language = language
        self.dpi = dpi

    def extract_text(self,content: bytes) -> str:
        if not content.startswith(b"%PDF-"):
            raise InvalidDocumentError("File không phải PDF hợp lệ.")

        document = None

        try:
            document = pymupdf.open(stream=content, filetype="pdf")

            if document.needs_pass:
                raise InvalidDocumentError("PDF được bảo vệ bằng mật khẩu.")

            if document.page_count <= 0:
                raise EmptyDocumentError("PDF không có trang nào.")

            if document.page_count > MAX_DOCUMENT_PAGES:
                raise InvalidDocumentError(f"PDF vượt quá giới hạn {MAX_DOCUMENT_PAGES} trang.")

            pages_text = []
            total_chars = 0

            for page in document:
                page_text = self._ocr_page(page)

                if not page_text:
                    continue

                total_chars += len(page_text)

                if (total_chars > MAX_EXTRACTED_TEXT_CHARS):
                    raise InvalidDocumentError("Nội dung CV vượt quá giới hạn xử lý.")

                pages_text.append(page_text)

        except (InvalidDocumentError, EmptyDocumentError, OCRProcessingError):
            raise

        except Exception as exc:
            raise OCRProcessingError("Không thể OCR file PDF.") from exc

        finally:
            if document is not None:
                document.close()

        text = "\n".join(pages_text).strip()

        if not text:
            raise EmptyDocumentError("OCR không đọc được nội dung từ PDF.")

        return text

    def _ocr_page(self, page) -> str:
        """
        Biến một PDF page thành ảnh,
        sau đó cho Tesseract đọc chữ.
        """

        try:
            pixmap = page.get_pixmap(dpi=self.dpi, alpha=False) # -> Biến trang PDF thành ảnh raster

            image_bytes = pixmap.tobytes("png") # -> Chuyển ảnh pixmap thành dữ liệu PNG dạng bytes trong RAM.

            image = Image.open(BytesIO(image_bytes)) # Pillow không đọc trực tiếp đống bytes thường -> biến thành object giống file nằm trong RAM

            text = pytesseract.image_to_string(image, lang=self.language)

            return text.strip()

        except pytesseract.TesseractNotFoundError as exc:
            raise OCRProcessingError("Không tìm thấy Tesseract OCR trên hệ thống.") from exc

        except Exception as exc:
            raise OCRProcessingError("Không thể OCR một trang PDF.") from exc