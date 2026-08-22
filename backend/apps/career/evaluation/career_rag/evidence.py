from __future__ import annotations

import re

from .schema import CorpusJob

EVIDENCE_PACKING_POLICY_VERSION = "career-rag-evidence-packing-v1"
DEFAULT_EVIDENCE_CHAR_BUDGET = 5000

_SECTION_PRIORITY = {
    "required": 0,
    "responsibilities": 1,
    "preferred": 2,
    "description": 3,
    "benefits": 4,
    "other": 5,
}


def _normalized_section_label(section: str) -> str:
    return re.sub(r"\s+", " ", str(section or "").strip())


def _section_kind(section: str) -> str:
    value = _normalized_section_label(section).casefold()
    if any(term in value for term in ("preferred", "nice to have", "ưu tiên")):
        return "preferred"
    if any(
        term in value
        for term in (
            "required",
            "requirement",
            "qualification",
            "must have",
            "yêu cầu",
            "bằng cấp",
        )
    ):
        return "required"
    if any(
        term in value
        for term in (
            "responsibil",
            "duties",
            "what you",
            "trách nhiệm",
            "nhiệm vụ",
        )
    ):
        return "responsibilities"
    if any(term in value for term in ("description", "mô tả", "about the job")):
        return "description"
    if any(term in value for term in ("benefit", "phúc lợi", "đãi ngộ")):
        return "benefits"
    return "other"


def _metadata_header(job: CorpusJob) -> str:
    parts = [f"Job title: {job.job_title}"]
    if job.category_key:
        parts.append(f"Category: {job.category_key}")
    if job.location_key:
        parts.append(f"Location: {job.location_key}")
    if job.experience_level:
        parts.append(f"Experience level: {job.experience_level}")
    if job.employment_type:
        parts.append(f"Employment type: {job.employment_type}")
    return "\n\n".join(parts)


def pack_job_evidence(
    job: CorpusJob,
    *,
    char_budget: int = DEFAULT_EVIDENCE_CHAR_BUDGET,
) -> str:
    """Pack construction evidence deterministically within ``char_budget``.

    Sections are reordered by career-information usefulness. Each source chunk
    is included at most once, and only the final chunk is prefix-truncated when
    the remaining budget is insufficient.
    """

    if char_budget <= 0:
        raise ValueError("char_budget must be positive")

    header = _metadata_header(job)
    if len(header) >= char_budget:
        return header[:char_budget]

    packed = header
    remaining = char_budget - len(packed)
    seen_content: set[str] = set()
    sections = sorted(
        (
            _SECTION_PRIORITY[_section_kind(chunk.get("section", ""))],
            index,
            _normalized_section_label(chunk.get("section", "")),
            str(chunk.get("content", "")),
        )
        for index, chunk in enumerate(job.chunks)
        if str(chunk.get("content", ""))
    )

    for _, _, section, content in sections:
        normalized_content = re.sub(r"\s+", " ", content).strip()
        if not normalized_content or normalized_content in seen_content:
            continue
        seen_content.add(normalized_content)
        prefix = f"\n\n[{section}]\n"
        if remaining <= len(prefix):
            break
        content_budget = remaining - len(prefix)
        content_slice = content[:content_budget]
        if not content_slice:
            break
        block = prefix + content_slice
        packed += block
        remaining -= len(block)
        if len(content_slice) < len(content):
            break

    return packed


def evidence_sensitivity_diagnostic_input(
    job: CorpusJob,
    *,
    char_budget: int = DEFAULT_EVIDENCE_CHAR_BUDGET,
) -> dict[str, str]:
    """Prepare packed/full evidence for a future paired grading diagnostic."""

    return {
        "packed_evidence": pack_job_evidence(job, char_budget=char_budget),
        "expanded_evidence": job.raw_evidence,
        "judgment_status": "UNPROVEN_NOT_RUN",
    }
