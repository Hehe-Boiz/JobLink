import hashlib
import json
import re

from bs4 import BeautifulSoup


BLOCK_TAGS = [
    "p",
    "div",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "section",
    "article",
    "tr",
]


def clean_html(value: str) -> str:
    soup = BeautifulSoup(
        value or "", # trả về value nếu None thì trả về ""
        "html.parser", # phân tích chuỗi này theo cú pháp html 
    )

    for tag in soup(["script", "style"]): # từ object của BeatutifulSoup tìm toàn bộ thẻ này
        tag.decompose() # xóa thẻ đó và nội dung bên trong của thẻ đó khỏi html

    for tag in soup.find_all("br"):
        tag.replace_with("\n")

    for tag in soup.find_all(BLOCK_TAGS):
        tag.append("\n")


    raw_text = soup.get_text( # -> nó sẽ làm việc như trên cái tree vậy
        separator=" ", # Thẻ inline như strong, i, span được nối bằng dấu cách.
        strip=False,
    )

    lines = []

    for line in raw_text.splitlines(): # tách text ngăn cách bởi \n thành list
        cleaned_line = " ".join(line.split()) # clean những khoảng cách thừa
        if cleaned_line:
            cleaned_line = clean_punctuation_spacing(
                cleaned_line
            )
            lines.append(cleaned_line)


    return "\n".join(lines) # trả ra nguyên đoạn text

def clean_punctuation_spacing(text: str) -> str:
    return re.sub(
        r"\s+([,.;:!?])",
        r"\1",
        text,
    )

def build_job_snapshot(job) -> dict:
    tags = sorted(
        job.tags.values_list(
            "name",
            flat=True, # để nó khỏi trả ra tuple
        )
    )

    return {
        "job_id": job.id,
        "title": job.title,
        "requirements": clean_html(job.requirements),
        "experience_level": (job.experience_level),
        "tags": tags,
    }

def build_job_matching_text(snapshot: dict) -> str:
    parts = [
        snapshot.get("requirements", ""),
        *snapshot.get("tags", []),
    ]

    valid_parts = []

    for part in parts:
        if part:
            valid_parts.append(part)

    return "\n".join(valid_parts)

def calculate_job_fingerprint(snapshot: dict) -> str:

    canonical_json = json.dumps( #biến dictionary thành chuỗi json 
        snapshot,
        ensure_ascii=False, # Giữ nguyên Unicode và tiếng Việt
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8") # Chuyển chuỗi thành bytes vì sh256 không nhận trực tiếp chuỗi Python. Nó cần dữ liệu dạng bytes
    ).hexdigest() # -> chuyển từ object hash sang chuỗi