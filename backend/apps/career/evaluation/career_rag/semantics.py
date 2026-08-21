from __future__ import annotations

import re

from .schema import CareerTopic


def display_taxonomy_label(
    value: str,
) -> str:
    text = re.sub(
        r"[_\\-]+",
        " ",
        value,
    ).strip()

    return re.sub(
        r"\\s+",
        " ",
        text,
    )


def topic_intent_label(
    topic: CareerTopic,
) -> str:
    """
    Canonical user-facing semantic intent.

    Broad:
        công nghệ thông tin kỹ thuật số

    Specific:
        DevOps Engineer trong lĩnh vực
        công nghệ thông tin kỹ thuật số
    """

    if topic.scope == "specific":
        domain = display_taxonomy_label(
            topic.category_key
        )

        return (
            f"{topic.label} "
            f"trong lĩnh vực {domain}"
        )

    return topic.label


def topic_description(
    topic: CareerTopic,
) -> str:
    """
    Canonical structured semantic intent
    used by LLM-based benchmark components.
    """

    if topic.scope == "specific":
        domain = display_taxonomy_label(
            topic.category_key
        )

        return (
            "specific occupation/specialization: "
            f"{topic.label}; "
            f"career domain: {domain}"
        )

    return (
        "broad career field/domain: "
        f"{topic.label}"
    )
