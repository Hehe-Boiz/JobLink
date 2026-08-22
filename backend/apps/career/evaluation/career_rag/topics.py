from __future__ import annotations

import math
import random
import re
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable

from apps.career.normalization import normalize_key

from .semantics import topic_intent_label
from .schema import CareerQuery, CareerTopic, CorpusJob


DEFAULT_RANDOM_SEED = 20260819
# Preferred only.
DEFAULT_MIN_FAMILY_JOBS = 100

# Preferred specific-title support.
DEFAULT_MIN_SPECIFIC_TITLE_JOBS = 8

HARD_MIN_SPECIFIC_TITLE_JOBS = 8
SPECIFICITY_WILSON_Z = 1.96
TOPIC_SELECTION_POLICY_VERSION = "all-supported-nongeneric-wilson-specificity-v3"
BASE_QUERY_VARIANTS = ("direct", "conversational", "noisy")

GENERIC_CATEGORY_TOKENS = {
    "khac",
    "other",
    "others",
    "misc",
    "miscellaneous",
}


DIRECT_TEMPLATES = (
    "{label} cần những kỹ năng/công cụ, trách nhiệm/năng lực và yêu cầu kinh nghiệm/bằng cấp nào?",
    "Để theo {label}, nhà tuyển dụng thường yêu cầu kỹ năng/công cụ, trách nhiệm/năng lực và kinh nghiệm/bằng cấp gì?",
)

CONVERSATIONAL_TEMPLATES = (
    (
        "Mình muốn làm {label}; các JD thường cần "
        "kỹ năng/công cụ, trách nhiệm/năng lực và kinh nghiệm/bằng cấp nào?"
    ),
    (
        "Nếu muốn đi theo {label} thì nên tập trung "
        "vào kỹ năng/công cụ, trách nhiệm/năng lực và yêu cầu kinh nghiệm/bằng cấp nào?"
    ),
)

NOISY_TEMPLATES = (
    "jd {label_ascii} can skill tool, trach nhiem nang luc, kinh nghiem bang cap gi",
    "lam {label_ascii} can biet skill cong cu, viec phai lam va yeu cau kinh nghiem gi",
)

def _ascii(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(
        char
        for char in normalized
        if not unicodedata.combining(char)
    )

    return (
        ascii_text
        .replace("Đ", "D")
        .replace("đ", "d")
    )

def _display_label(value: str) -> str:
    text = re.sub(r"[_\-]+", " ", value).strip()
    return re.sub(r"\s+", " ", text)


def _is_generic_category(value: str) -> bool:
    ascii_value = _ascii(value).casefold()
    tokens = {
        token
        for token in re.split(r"[_\-\s]+", ascii_value)
        if token
    }

    return bool(tokens & GENERIC_CATEGORY_TOKENS)


def _count_topic_support(jobs: Iterable[CorpusJob]) -> tuple[
    Counter[str],
    dict[str, Counter[str]],
    dict[tuple[str, str], Counter[str]],
]:
    category_jobs: Counter[str] = Counter()
    title_jobs: dict[str, Counter[str]] = defaultdict(Counter)
    title_display: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    seen: set[str] = set()

    for job in jobs:
        if job.job_key in seen:
            continue

        seen.add(job.job_key)
        category = normalize_key(job.category_key)
        title_key = normalize_key(job.job_title)

        if not category:
            continue

        category_jobs[category] += 1

        if title_key:
            title_jobs[category][title_key] += 1
            title_display[(category, title_key)][job.job_title.strip()] += 1

    return (category_jobs, title_jobs, title_display)


def _global_title_support(
    title_jobs: dict[str, Counter[str]],
) -> Counter[str]:
    totals: Counter[str] = Counter()

    for counter in title_jobs.values():
        totals.update(counter)

    return totals


def _wilson_lower_bound(successes: int, total: int, *, z: float = SPECIFICITY_WILSON_Z) -> float:
    if total <= 0:
        return 0.0

    p = successes / total
    z2 = z * z

    denominator = 1.0 + z2 / total
    center = p + z2 / (2.0 * total)
    margin = z * math.sqrt(p * (1.0 - p) / total + z2 / (4.0 * total * total))

    return (center - margin) / denominator


def _specific_title_score(*, local_support: int, global_support: int) -> float:
    return math.log1p(local_support) * _wilson_lower_bound(local_support, global_support)

def _select_categories(
    category_jobs: Counter[str],
    title_jobs: dict[str, Counter[str]],
    *,
    min_family_jobs: int,
    preferred_specific_support: int,
    hard_min_specific_support: int,
) -> tuple[list[str], int, list[str]]:
    """
    Select every meaningful family satisfying
    frozen-corpus support constraints.

    Selection is independent from retrieval
    results, LLM judgments, DEV metrics and
    TEST metrics.
    """

    effective_specific_support = max(preferred_specific_support, hard_min_specific_support)

    best_specific_support = {
        category: max(title_jobs[category].values(), default=0)
        for category
        in category_jobs
    }

    generic_excluded = sorted(
        category
        for category
        in category_jobs
        if _is_generic_category(category)
    )

    selected = [
        category
        for category
        in category_jobs
        if (
            not _is_generic_category(category)
            and category_jobs[category] >= min_family_jobs
            and best_specific_support[category] >= effective_specific_support
        )
    ]

    selected.sort(
        key=lambda category: (
            -category_jobs[category],
            -best_specific_support[category],
            category,
        )
    )

    if not selected:
        raise RuntimeError("No career family satisfies the frozen topic eligibility policy.")

    return (selected, effective_specific_support, generic_excluded)

def discover_topics(
    jobs: Iterable[CorpusJob],
    *,
    min_family_jobs: int = DEFAULT_MIN_FAMILY_JOBS,
    min_specific_title_jobs: int = DEFAULT_MIN_SPECIFIC_TITLE_JOBS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> tuple[
    list[CareerTopic],
    list[CareerQuery],
    list[str],
    list[str],
]:
    jobs = list(jobs)

    (category_jobs, title_jobs, title_display) = _count_topic_support(jobs)
    global_title_jobs = (_global_title_support(title_jobs))
    (selected_categories, effective_specific_support, generic_excluded) = _select_categories(
        category_jobs,
        title_jobs,
        min_family_jobs=min_family_jobs,
        preferred_specific_support=min_specific_title_jobs,
        hard_min_specific_support=HARD_MIN_SPECIFIC_TITLE_JOBS,
    )

    family_count = len(selected_categories)
    broad_support_floor = min(
        category_jobs[category]
        for category
        in selected_categories
    )

    print(
        "Topic selection policy: "
        f"{TOPIC_SELECTION_POLICY_VERSION}; "
        f"families={family_count}; "
        "preferred_specific_support="
        f"{min_specific_title_jobs}; "
        "effective_specific_support="
        f"{effective_specific_support}; "
        "hard_floor="
        f"{HARD_MIN_SPECIFIC_TITLE_JOBS}; "
        "broad_support_floor="
        f"{broad_support_floor}; "
        "generic_categories_excluded="
        f"{len(generic_excluded)}."
    )

    if broad_support_floor < min_family_jobs:
        print(
            "Topic selection note: "
            "preferred broad-family support "
            f">={min_family_jobs} is not "
            f"attainable for all "
            f"{family_count} families; "
            "observed selected-family floor="
            f"{broad_support_floor}."
        )

    shuffled = list(selected_categories)
    random.Random(random_seed).shuffle(shuffled)
    dev_categories = set(shuffled[:family_count // 2])
    test_categories = set(shuffled[family_count // 2:])

    if dev_categories & test_categories:
        raise RuntimeError("Family-disjoint DEV/TEST split invariant failed.")

    split_by_family = {
        category: "dev"
        for category
        in dev_categories
    }

    split_by_family.update(
        {
            category: "test"
            for category
            in test_categories
        }
    )

    topics: list[CareerTopic] = []
    queries: list[CareerQuery] = []
    family_id_by_category: dict[str, str] = {}

    for (family_index, category) in enumerate(selected_categories, start=1):
        split = split_by_family[category]

        family_id = (
            f"family-{family_index:02d}-"
            f"{category}"
        )

        family_id_by_category[category] = family_id
        broad_label = _display_label(category)

        topics.append(
            CareerTopic(
                topic_id=f"{family_id}-broad",
                family_id=family_id,
                scope="broad",
                label=broad_label,
                category_key=category,
                split=split,
            )
        )

        specific_candidates = [
            (title_key, count)
            for (title_key, count)
            in title_jobs[category].items()
            if count >= effective_specific_support
        ]

        specific_candidates.sort(
            key=lambda item: (
                -_specific_title_score(
                    local_support=item[1],
                    global_support=global_title_jobs[item[0]],
                ),
                -item[1],
                item[0],
            )
        )

        if not specific_candidates:
            raise RuntimeError(
                "Internal topic-selection "
                "invariant failed for family "
                f"{category!r}: no title "
                "has support >= "
                f"{effective_specific_support}."
            )

        title_key = specific_candidates[0][0]
        display_counter = title_display[(category, title_key)]
        specific_label = (
            display_counter.most_common(1)[0][0]
            if display_counter
            else _display_label(title_key)
        )

        topics.append(
            CareerTopic(
                topic_id=f"{family_id}-specific",
                family_id=family_id,
                scope="specific",
                label=specific_label,
                category_key=category,
                title_key=title_key,
                split=split,
            )
        )

    for topic in topics:
        queries.extend(generate_query_variants(topic, random_seed=random_seed))

    dev_family_ids = [
        family_id_by_category[category]
        for category
        in selected_categories
        if category
        in dev_categories
    ]

    test_family_ids = [
        family_id_by_category[category]
        for category
        in selected_categories
        if category
        in test_categories
    ]

    if len(topics) != family_count * 2:
        raise RuntimeError(f"Expected {family_count * 2} topics, constructed {len(topics)}.")

    if len(queries) != family_count * 2 * len(BASE_QUERY_VARIANTS):
        raise RuntimeError(
            f"Expected {family_count * 2 * len(BASE_QUERY_VARIANTS)} queries, "
            f"constructed {len(queries)}."
        )

    queries_by_topic = defaultdict(list)
    for query in queries:
        queries_by_topic[query.topic_id].append(query)
    for topic in topics:
        topic_queries = queries_by_topic[topic.topic_id]
        variants = tuple(query.variant for query in topic_queries)
        if len(topic_queries) != len(BASE_QUERY_VARIANTS) or set(variants) != set(BASE_QUERY_VARIANTS):
            raise RuntimeError(
                f"Base query variant invariant failed for {topic.topic_id}: {variants!r}"
            )
        if any(query.topic_id != topic.topic_id for query in topic_queries):
            raise RuntimeError(f"Query topic mismatch for {topic.topic_id}.")

    if len(dev_family_ids) + len(test_family_ids) != family_count:
        raise RuntimeError("Family split count invariant failed.")

    if set(dev_family_ids) & set(test_family_ids):
        raise RuntimeError("DEV/TEST family overlap detected.")

    return (topics, queries, dev_family_ids, test_family_ids)


def generate_query_variants(
    topic: CareerTopic,
    *,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[CareerQuery]:
    rng = random.Random(f"{random_seed}:{topic.topic_id}")
    label = topic_intent_label(topic)
    texts = [
        rng.choice(DIRECT_TEMPLATES).format(label=label),
        rng.choice(CONVERSATIONAL_TEMPLATES).format(label=label),
        rng.choice(NOISY_TEMPLATES).format(label_ascii=_ascii(label)),
    ]

    variants = BASE_QUERY_VARIANTS

    return [
        CareerQuery(
            query_id=f"{topic.topic_id}-q{index}",
            topic_id=topic.topic_id,
            variant=variant,
            text=text,
            known_skills=(),
        )
        for (index,(variant, text)) in enumerate(zip(variants, texts, strict=True), start=1)
    ]
