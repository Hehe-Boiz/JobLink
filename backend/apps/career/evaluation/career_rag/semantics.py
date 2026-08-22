from __future__ import annotations

import re

from .schema import CareerTopic

CANONICAL_INFORMATION_NEED_VERSION = "career-rag-canonical-information-need-v1"
CANONICAL_INFORMATION_FACETS = (
    "skills/tools, responsibilities/capabilities, "
    "experience/qualifications, and other employer requirements"
)


def display_taxonomy_label(
    value: str,
) -> str:
    text = re.sub(r"[_-]+", " ", value).strip()

    return re.sub(r"\s+", " ", text)


def topic_intent_label(topic: CareerTopic) -> str:
    """
    Canonical user-facing semantic intent.

    Broad:
        công nghệ thông tin kỹ thuật số

    Specific:
        DevOps Engineer trong lĩnh vực
        công nghệ thông tin kỹ thuật số
    """

    if topic.scope == "specific":
        domain = display_taxonomy_label(topic.category_key)

        return (f"{topic.label} trong lĩnh vực {domain}")

    return topic.label


def canonical_information_need(topic: CareerTopic) -> str:
    """Return the deterministic information need shared by construction stages."""

    domain = display_taxonomy_label(topic.category_key)

    if topic.scope == "specific":
        return (
            f"From real job postings for the occupation {topic.label} "
            f"within the career domain {domain}, identify the "
            f"{CANONICAL_INFORMATION_FACETS} that help explain what employers expect."
        )

    broad_field = topic.label or domain
    return (
        f"From real job postings in the {broad_field} career field, identify the "
        f"{CANONICAL_INFORMATION_FACETS} that help explain what employers expect."
    )
