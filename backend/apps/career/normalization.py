from __future__ import annotations

import html
import re

from bs4 import BeautifulSoup


MULTIPLE_SPACES_PATTERN = re.compile(r"[ \t]+")
MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{3,}")


def normalize_job_text(value: str | None) -> str:
    if not value:
        return ""

    text = html.unescape(value)
    text = _html_to_text(text)
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    lines = [
        _normalize_line(line)
        for line in text.splitlines()
    ]

    text = "\n".join(lines)
    text = MULTIPLE_NEWLINES_PATTERN.sub("\n\n", text)

    return text.strip()


def normalize_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = MULTIPLE_SPACES_PATTERN.sub(" ", value.strip()).lower()

    return normalized or None


def _html_to_text(value: str) -> str:
    soup = BeautifulSoup(value, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()

    return soup.get_text(separator="\n")


def _normalize_line(line: str) -> str:
    line = line.replace("\xa0", " ")
    line = MULTIPLE_SPACES_PATTERN.sub(" ", line)

    return line.strip()