from abc import ABC, abstractmethod
from dataclasses import dataclass
from io import BytesIO #đọc DOCX trực tiếp từ bytes mà không phải lưu file tạm xuống ổ cứng
from pathlib import Path
from urllib.parse import unquote, urlparse
import fitz
import pymupdf
import requests
from docx import Document

class DocumentProcessingError(Exception):
    """Lỗi xảy ra khi tải hoặc đọc tài liệu."""


@dataclass(frozen=True)
class ParsedDocument:
    content: bytes
    text: str
    extension: str


class DocumentParser(ABC):
    @abstractmethod
    def parse(self, content: bytes) -> str:
        raise NotImplementedError

class PDFDocumentParser(DocumentParser):
    def parse(self, content):
        try:
            document = fitz.open(stream=content, filetype="pdf")

        except Exception as exc:
            raise DocumentProcessingError("File PDF không hợp lệ hoặc đã bị hỏng.") from exc

        try: 
            pages =[]
            for page in document:
                page_text = page.get_text("text")
                pages.append(page_text)

        finally:
            document.close()

        text = "\n".join(pages).strip()

        if not text:
            raise DocumentProcessingError(
                "Không đọc được chữ từ PDF. "
                "CV có thể là file scan và cần OCR."
            )

        return text

class DOCXDocumentParser(DocumentParser):
    def parse(self, content: bytes):
        try:
            document = Document(
                BytesIO(content)
            )
        except Exception as exc:
            raise DocumentProcessingError(
                "File DOCX không hợp lệ hoặc đã bị hỏng."
            ) from exc

        blocks = []

        for paragraph in document.paragraphs:
            text = paragraph.text.strip()

            if text:
                blocks.append(text)

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    text = cell.text.strip()

                    if text:
                        blocks.append(text)

        text = "\n".join(blocks).strip()

        if not text:
            raise DocumentProcessingError(
                "Không đọc được nội dung từ DOCX."
            )

        return text


class CVDocumentLoader:
    def __init__(self) -> None:
        self._parsers: dict[str, DocumentParser] = {
            ".pdf": PDFDocumentParser(),
            ".docx": DOCXDocumentParser(),
        }

    def load(self, cv_field) -> ParsedDocument:
        if not cv_field:
            raise DocumentProcessingError("Application không có CV.")

        try:
            url = cv_field.url
        except Exception as exc:
            raise DocumentProcessingError("Không lấy được URL của CV.") from exc

        try:
            response = requests.get(
                url,
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise DocumentProcessingError("Không thể tải CV từ Cloudinary.") from exc

        extension = self._detect_extension(
            cv_field=cv_field,
            url=url,
            content_type=response.headers.get("Content-Type",""), 
        )

        parser = self._parsers.get(extension)

        if parser is None:
            raise DocumentProcessingError(
                f"Chưa hỗ trợ định dạng CV: "
                f"{extension or 'không xác định'}."
            )

        text = parser.parse(response.content)

        return ParsedDocument(
            content=response.content, # nếu có sẽ chứa toàn bộ nội dung file đã tải dưới dạng byte
            text=text,
            extension=extension,
        )

    def _detect_extension(self, cv_field, url: str, content_type: str,) -> str:
        # xem đuôi file
        candidates = [
            str(cv_field),
            url,
        ]

        for candidate in candidates:
            path = unquote(
                urlparse(candidate).path # urlparse sẽ tách thành từng thành phần  -> chỉ lấy phần path
            )

            # suffix -> lấy đuôi file
            extension = Path(path).suffix.lower()

            if extension in self._parsers:
                return extension

        normalized_content_type = (content_type.split(";")[0].strip().lower())

        content_type_map = {
            "application/pdf": ".pdf",
            (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ): ".docx",
        }

        return content_type_map.get(
            normalized_content_type,
            "",
        )