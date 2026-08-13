from __future__ import annotations # giúp không bị lỗi type hint vì class chưa được định nghĩa tại thời điểm Python đọc annotation

import re
import unicodedata # xử lý unicode

from apps.matching.constants import MAX_CHUNK_CHARS
from apps.matching.domain import (
    DocumentSection,
    TextSegment,
)

from .hashing import sha256_text

HARD_MAX_TOKEN_CHARS = 4000

SECTION_HEADINGS = {
    DocumentSection.SUMMARY: {
        "summary",
        "professional summary",
        "profile",
        "profile summary",
        "objective",
        "career objective",
        "about me",
        "tom tat",
        "gioi thieu",
        "muc tieu",
        "muc tieu nghe nghiep",
    },
    DocumentSection.SKILLS: {
        "skills",
        "technical skills",
        "core skills",
        "technologies",
        "tech stack",
        "ky nang",
        "ky nang chuyen mon",
        "cong nghe",
        "nang luc",
    },
    DocumentSection.WORK_EXPERIENCE: {
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "working experience",
        "kinh nghiem",
        "kinh nghiem lam viec",
        "qua trinh cong tac",
    },
    DocumentSection.PROJECTS: {
        "projects",
        "personal projects",
        "academic projects",
        "selected projects",
        "project experience",
        "du an",
        "du an ca nhan",
        "du an hoc tap",
    },
    DocumentSection.EDUCATION: {
        "education",
        "academic background",
        "academic history",
        "hoc van",
        "giao duc",
        "trinh do hoc van",
    },
    DocumentSection.CERTIFICATIONS: {
        "certifications",
        "certificates",
        "licenses and certifications",
        "chung chi",
        "chung nhan",
    },
    DocumentSection.AWARDS: {
        "awards",
        "achievements",
        "honors",
        "thanh tich",
        "giai thuong",
    },
}

#regex dùng để tìm bullet ở đầu dòng
BULLET_PREFIX_PATTERN = re.compile(
    r"^\s*(?:"
    r"[-*•●▪◦‣–—]"
    r"|"
    r"\d{1,3}[.)]"
    r")\s*"
)

# tìm vị trí để chia câu 
SENTENCE_BOUNDARY_PATTERN = re.compile(
    r"(?<=[.!?])\s+"
)

def normalize_text(text: str) -> str:

    if not isinstance(text, str):
        raise TypeError(
            "normalize_text chỉ nhận dữ liệu str."
        )

    if not text: # xử lý chuỗi rỗng
        return ""

    # Chuẩn hóa các ký tư tương đương về giống nhau thay vì lưu khác nhau 
    text = unicodedata.normalize("NFKC", text)

    # Chuẩn hóa newline từ Windows/macOS về \n.
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Non-breaking space -> space bình thường
    # Non-breaking là các dấu không cho ngắt dòng ở vị trí đó 
    text = text.replace("\u00a0", " ")

    # Xóa ký tự Unicode kh nhìn thấy đc nhưng có thể nằm chen giữa sau khi copy từ web, Word hoặc parse PDF
    text = text.replace("\u200b", "")
    text = text.replace("\u200c", "")
    text = text.replace("\u200d", "")
    text = text.replace("\ufeff", "")

    normalized_lines: list[str] = []

    for raw_line in text.split("\n"):
        # Nhiều space/tab trong cùng một dòng -> một space.
        line = re.sub(
            r"[ \t\f\v]+",
            " ",
            raw_line,
        ).strip()

        # Chuẩn hóa một số bullet Unicode.
        line = re.sub(
            r"^[•●▪◦‣]\s*",
            "- ",
            line,
        )

        normalized_lines.append(line)

    normalized_text = "\n".join(
        normalized_lines
    )

    # Không giữ quá nhiều dòng trống liên tiếp.
    normalized_text = re.sub(
        r"\n{3,}",
        "\n\n",
        normalized_text,
    )

    return normalized_text.strip()

# xóa dấu tiếng việt 
def remove_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)

    characters_without_accents: list[str] = []

    for char in decomposed:
        category = unicodedata.category(char)

        if category != "Mn": # nếu không phải dấu thì lấy
            characters_without_accents.append(char)

    without_accents = "".join(
        characters_without_accents
    )

    return (
        without_accents
        .replace("đ", "d")
        .replace("Đ", "D")
    )

def normalize_for_matching(text: str) -> str:
    # thực hiện chuẩn hóa tổng quát tách dòng với đoạn
    normalized = normalize_text(text)
    # xóa dấu của tiếng việt 
    normalized = remove_accents(normalized)
    normalized = normalized.casefold()

    # Giữ:
    # - chữ và số: \w
    # - whitespace
    # - các ký tự kỹ thuật + # . / -
    normalized = re.sub(
        r"[^\w\s+#./-]", # ^ là phủ định những dấu bên trong 
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return normalized.strip()

def is_bullet_line(line: str) -> bool:

    return bool(BULLET_PREFIX_PATTERN.match(line))


def remove_bullet_prefix(line: str) -> str:
    return BULLET_PREFIX_PATTERN.sub("", line, count=1).strip()

def detect_section_heading(text: str,) -> DocumentSection | None:
    candidate = remove_bullet_prefix(text)
    candidate = normalize_for_matching(candidate)

    if not candidate:
        return None

    # Heading CV thường ngắn.
    # Điều này tránh xem một câu dài là heading.
    if len(candidate) > 60:
        return None

    for section, headings in SECTION_HEADINGS.items():
        if candidate in headings:
            return section

    return None


def split_paragraphs(text: str) -> list[str]:

    normalized = normalize_text(text)

    if not normalized:
        return []

    paragraphs: list[str] = []
    current_lines: list[str] = []

    def flush_current_paragraph() -> None:
        if not current_lines:
            return

        paragraph = " ".join(
            current_lines
        ).strip()

        if paragraph:
            paragraphs.append(paragraph)

        current_lines.clear()

    for line in normalized.splitlines():
        line = line.strip()

        if not line: # -> gặp chuỗi rỗng thì kết thúc paragraphs 
            flush_current_paragraph()
            continue

        section = detect_section_heading(line)

        if section is not None:
            flush_current_paragraph()

            # Giữ heading trong kết quả để build_text_segments
            # biết lúc nào phải đổi section.
            paragraphs.append(line)
            continue

        if is_bullet_line(line):
            flush_current_paragraph() # -> nếu là bullet thì ngắt từ đây luôn 

            bullet_content = remove_bullet_prefix(line)

            if bullet_content:
                current_lines.append(bullet_content)

            continue

        current_lines.append(line)

    flush_current_paragraph()

    return paragraphs


def split_sentences(text: str) -> list[str]:

    normalized = normalize_text(text)
    normalized = normalized.replace("\n", " ").strip()

    if not normalized:
        return []

    sentences = SENTENCE_BOUNDARY_PATTERN.split(normalized)

    cleaned_sentences: list[str] = []

    for sentence in sentences:
        cleaned_sentence = sentence.strip()

        if cleaned_sentence:
            cleaned_sentences.append(cleaned_sentence)

    return cleaned_sentences


def split_by_words(text: str, max_chars: int) -> list[str]:

    if max_chars <= 0:
        raise ValueError("max_chars phải lớn hơn 0.")

    words = text.split()

    if not words:
        return []

    chunks: list[str] = []
    current_words: list[str] = []

    for word in words:
        # Trường hợp URL hoặc token dài bất thường.
        if len(word) > max_chars:
            # Lưu chunk đang xây dựng trước.
            if current_words:
                chunks.append(" ".join(current_words))
                current_words.clear()

            # Token chỉ hơi dài:
            # giữ nguyên trong một chunk riêng.
            if len(word) <= HARD_MAX_TOKEN_CHARS:
                chunks.append(word)
                continue

            # Token dài bất thường:
            # cắt thành các phần để bảo vệ hệ thống.
            for start in range(0, len(word), max_chars):
                token_part = word[
                    start:start + max_chars
                ]

                chunks.append(token_part)

            continue

        candidate = " ".join([*current_words, word])

        if len(candidate) <= max_chars:
            current_words.append(word)
            continue

        if current_words:
            chunks.append(
                " ".join(current_words)
            )

        current_words = [word]

    if current_words:
        chunks.append(
            " ".join(current_words)
        )

    return chunks


def split_long_paragraph(paragraph: str, max_chars: int = MAX_CHUNK_CHARS,) -> list[str]:
    """
    Paragraph ngắn được giữ nguyên.
    Paragraph dài: ưu tiên chia theo câu, câu quá dài thì chia theo từ.
    """

    paragraph = paragraph.strip()

    if not paragraph:
        return []

    if len(paragraph) <= max_chars:
        return [paragraph]

    sentences = split_sentences(paragraph)

    chunks: list[str] = []
    current_chunk = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(split_by_words(sentence, max_chars))
            continue

        candidate = (f"{current_chunk} {sentence}".strip())

        if len(candidate) <= max_chars:
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append(current_chunk)

        current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def make_stable_chunk_key(section: DocumentSection, index: int, normalized_text: str) -> str:
    """
    Tạo key ổn định cho evidence chunk.

    Ví dụ:
        PROJECTS:2:a91b7c3d
    """

    hash_input = f"{section.value}|{normalized_text}"

    short_hash = sha256_text(hash_input)[:8]

    return (
        f"{section.value}:"
        f"{index}:"
        f"{short_hash}"
    )

def build_text_segments(text: str, max_chunk_chars: int = MAX_CHUNK_CHARS) -> list[TextSegment]:
    """
    Pipeline chính của text.py.

    raw text
    → paragraphs
    → section detection
    → chunking
    → TextSegment[]
    """

    if max_chunk_chars <= 0:
        raise ValueError("max_chunk_chars phải lớn hơn 0.")

    paragraphs = split_paragraphs(text)

    segments: list[TextSegment] = []
    current_section = DocumentSection.UNKNOWN

    for paragraph in paragraphs:
        detected_section = detect_section_heading(paragraph)

        if detected_section is not None:
            current_section = detected_section
            continue

        chunks = split_long_paragraph(paragraph, max_chars=max_chunk_chars)

        for chunk_text in chunks:
            chunk_text = chunk_text.strip()

            if not chunk_text:
                continue

            normalized_text = normalize_for_matching(chunk_text)

            if not normalized_text:
                continue

            index = len(segments)

            stable_key = make_stable_chunk_key(
                section=current_section,
                index=index,
                normalized_text=normalized_text,
            )

            segment = TextSegment(
                index=index,
                stable_key=stable_key,
                text=chunk_text,
                normalized_text=normalized_text,
                section=current_section,
            )

            segments.append(segment)

    return segments