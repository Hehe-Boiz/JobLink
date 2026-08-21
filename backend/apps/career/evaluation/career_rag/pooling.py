from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import replace
from typing import Iterable

from rank_bm25 import BM25Okapi

from apps.career.models import CareerJobChunk
from apps.career.retrieval import CareerRetriever

from .schema import CareerQuery, CareerTopic, CorpusJob, PooledCandidate

RRF_K = 60
INDEPENDENT_POOL_SYSTEMS = ("bm25", "dense", "title")


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


def _pool_coverage_scope(
    variant_rankings: dict[str, dict[str, list[str]]],
    *,
    depth: int,
    max_pool: int,
) -> dict:
    system_sets = {
        system: {
            key
            for rankings in variant_rankings.values()
            for key in rankings.get(system, [])[:depth]
        }
        for system in INDEPENDENT_POOL_SYSTEMS
    }
    direct_union = set().union(*system_sets.values())
    unique_contribution = {
        system: sorted(
            values
            - set().union(
                *(
                    system_sets[other]
                    for other in INDEPENDENT_POOL_SYSTEMS
                    if other != system
                )
            )
        )
        for system, values in system_sets.items()
    }
    pairwise_overlap = {
        f"{left}&{right}": len(system_sets[left] & system_sets[right])
        for index, left in enumerate(INDEPENDENT_POOL_SYSTEMS)
        for right in INDEPENDENT_POOL_SYSTEMS[index + 1 :]
    }

    aggregate_scores: dict[str, float] = defaultdict(float)
    rrf_new_candidates: set[str] = set()
    for rankings in variant_rankings.values():
        bm25 = rankings.get("bm25", [])[:depth]
        dense = rankings.get("dense", [])[:depth]
        rrf = PoolingService.rrf([bm25, dense], depth)
        rrf_new_candidates.update(set(rrf) - (set(bm25) | set(dense)))
        for _, ranking in (
            ("bm25", bm25),
            ("dense", dense),
            ("title", rankings.get("title", [])[:depth]),
            ("rrf", rrf),
        ):
            for rank, key in enumerate(ranking, start=1):
                aggregate_scores[key] += 1.0 / (RRF_K + rank)

    aggregate_order = sorted(
        aggregate_scores,
        key=lambda key: (-aggregate_scores[key], key),
    )
    selected = set(aggregate_order[:max_pool])
    dropped = set(aggregate_order[max_pool:])
    return {
        "depth": depth,
        "max_pool": max_pool,
        "direct_union_size": len(direct_union),
        "direct_system_counts": {
            system: len(system_sets[system])
            for system in INDEPENDENT_POOL_SYSTEMS
        },
        "pairwise_overlap_counts": pairwise_overlap,
        "unique_contribution": unique_contribution,
        "unique_contribution_counts": {
            system: len(keys)
            for system, keys in unique_contribution.items()
        },
        "rrf_new_candidates": sorted(rrf_new_candidates),
        "aggregate_rrf_candidate_count": len(aggregate_order),
        "candidate_count_before_max_pool": len(aggregate_order),
        "resulting_candidate_count": len(selected),
        "candidate_count_after_max_pool": len(selected),
        "max_pool_dropped_count": len(dropped),
        "max_pool_drops_system_unique": {
            system: sorted(set(keys) & dropped)
            for system, keys in unique_contribution.items()
        },
        "max_pool_drops_system_unique_counts": {
            system: len(set(keys) & dropped)
            for system, keys in unique_contribution.items()
        },
        "max_pool_truncates_system_unique": any(
            set(keys) & dropped
            for keys in unique_contribution.values()
        ),
    }


def audit_pool_coverage(
    rankings_by_topic: dict[str, dict[str, dict[str, list[str]]]],
    *,
    depths: tuple[int, ...] = (5, 10, 15, 20),
    max_pool: int = 80,
) -> dict:
    """Audit independent-pool coverage without invoking retrieval or an LLM.

    ``rankings_by_topic`` is intentionally a diagnostic input: topic -> query
    variant -> independent-system rankings. The helper mirrors current RRF
    candidate accounting but never changes production pooling semantics.
    """

    if not depths or any(depth <= 0 for depth in depths):
        raise ValueError("depths must contain only positive values")
    if max_pool <= 0:
        raise ValueError("max_pool must be positive")

    depth_reports: dict[str, dict] = {}
    for depth in depths:
        topic_reports = {
            topic_id: _pool_coverage_scope(
                variant_rankings,
                depth=depth,
                max_pool=max_pool,
            )
            for topic_id, variant_rankings in sorted(rankings_by_topic.items())
        }

        aggregate_variants: dict[str, dict[str, list[str]]] = {}
        for topic_id, variant_rankings in sorted(rankings_by_topic.items()):
            for variant, rankings in sorted(variant_rankings.items()):
                aggregate_variants[f"{topic_id}:{variant}"] = rankings

        depth_reports[str(depth)] = {
            "topics": topic_reports,
            "aggregate": _pool_coverage_scope(
                aggregate_variants,
                depth=depth,
                max_pool=max_pool,
            ),
        }
    return {
        "depths": list(depths),
        "max_pool": max_pool,
        "independent_systems": list(INDEPENDENT_POOL_SYSTEMS),
        "pooling_policy_changed": False,
        "reports": depth_reports,
    }


def audit_pool_coverage_offline(
    pooler: "PoolingService",
    topics: Iterable[CareerTopic],
    queries_by_topic: dict[str, list[CareerQuery]],
    *,
    depths: tuple[int, ...] = (5, 10, 15, 20),
    max_pool: int = 80,
) -> dict:
    """Run the pool audit over local retriever rankings only.

    The caller supplies an already-constructed ``PoolingService`` so this
    helper can use existing local vectors and BM25 indexes without creating an
    index or contacting an LLM/API. RRF and max-pool behavior remain diagnostic
    only; this function does not change production pooling semantics.
    """

    if not depths or any(depth <= 0 for depth in depths):
        raise ValueError("depths must contain only positive values")
    if max_pool <= 0:
        raise ValueError("max_pool must be positive")

    max_depth = max(depths)
    rankings_by_topic: dict[str, dict[str, dict[str, list[str]]]] = {}
    query_count = 0
    for topic in sorted(topics, key=lambda item: item.topic_id):
        variant_rankings: dict[str, dict[str, list[str]]] = {}
        for query in queries_by_topic.get(topic.topic_id, []):
            query_count += 1
            variant_rankings[query.variant] = {
                "bm25": pooler.bm25(query.text, max_depth),
                "dense": pooler.dense(query.text, max_depth),
                "title": pooler.title_lexical(query.text, max_depth),
            }
        rankings_by_topic[topic.topic_id] = variant_rankings

    report = audit_pool_coverage(
        rankings_by_topic,
        depths=depths,
        max_pool=max_pool,
    )
    report.update(
        {
            "mode": "real_offline",
            "topic_count": len(rankings_by_topic),
            "query_count": query_count,
            "retrieval_systems_run": list(INDEPENDENT_POOL_SYSTEMS),
            "external_llm_calls": 0,
        }
    )
    return report


def load_corpus_jobs(*, source: str = "vietjobs") -> list[CorpusJob]:
    rows = (
        CareerJobChunk.objects.filter(active=True, source=source)
        .order_by("source", "source_job_id", "chunk_index")
        .values(
            "source", "source_job_id", "job_title", "category_key", "location_key",
            "experience_level", "employment_type", "section", "content", "metadata",
        )
    )
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows.iterator(chunk_size=4000):
        key = (row["source"], row["source_job_id"])
        item = grouped.setdefault(
            key,
            {
                "source": row["source"],
                "source_job_id": row["source_job_id"],
                "job_title": row["job_title"],
                "category_key": row["category_key"],
                "location_key": row["location_key"],
                "experience_level": row["experience_level"],
                "employment_type": row["employment_type"],
                "chunks": [],
            },
        )
        item["chunks"].append({"section": row["section"], "content": row["content"]})
    return [CorpusJob(**{**item, "chunks": tuple(item["chunks"])}) for item in grouped.values()]


class PoolingService:
    def __init__(self, corpus_jobs: list[CorpusJob], retriever: CareerRetriever | None = None) -> None:
        self.jobs = corpus_jobs
        self.by_key = {job.job_key: job for job in corpus_jobs}
        self.keys = [job.job_key for job in corpus_jobs]
        self.retriever = retriever or CareerRetriever()
        self._bm25 = BM25Okapi([_tokens(job.raw_evidence) for job in corpus_jobs])
        self._title_bm25 = BM25Okapi([_tokens(job.job_title) for job in corpus_jobs])

    def bm25(self, query: str, depth: int) -> list[str]:
        scores = self._bm25.get_scores(_tokens(query))
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self.keys[i]))[:depth]
        return [self.keys[i] for i in order]

    def title_lexical(self, query: str, depth: int) -> list[str]:
        scores = self._title_bm25.get_scores(_tokens(query))
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self.keys[i]))[:depth]
        return [self.keys[i] for i in order]

    def dense(self, query: str, depth: int) -> list[str]:
        jobs = self.retriever.search(
            query,
            top_k=depth,
            candidate_multiplier=20,
            evidence_per_job=2,
            source="vietjobs",
        )
        return [f"{job.source}::{job.source_job_id}" for job in jobs]

    @staticmethod
    def rrf(rankings: list[list[str]], depth: int, k: int = RRF_K) -> list[str]:
        scores: dict[str, float] = defaultdict(float)
        for ranking in rankings:
            for rank, key in enumerate(ranking, start=1):
                scores[key] += 1.0 / (k + rank)
        return [key for key, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:depth]]

    def pool_topic(self, topic_id: str, queries: list[CareerQuery], *, depth: int = 20, max_pool: int = 80) -> list[PooledCandidate]:
        rank_map: dict[str, dict[str, int]] = defaultdict(dict)
        aggregate_rrf: dict[str, float] = defaultdict(float)

        for query in queries:
            bm25 = self.bm25(query.text, depth)
            dense = self.dense(query.text, depth)
            title = self.title_lexical(query.text, depth)
            hybrid = self.rrf([bm25, dense], depth)
            systems = {"bm25": bm25, "dense": dense, "title": title, "rrf": hybrid}
            for system, ranking in systems.items():
                name = f"{system}:{query.variant}"
                for rank, key in enumerate(ranking, start=1):
                    rank_map[key][name] = rank
                    aggregate_rrf[key] += 1.0 / (RRF_K + rank)

        ordered = sorted(aggregate_rrf, key=lambda key: (-aggregate_rrf[key], key))[:max_pool]
        result: list[PooledCandidate] = []
        for key in ordered:
            job = self.by_key.get(key)
            if job is None:
                continue
            result.append(
                PooledCandidate(
                    topic_id=topic_id,
                    source=job.source,
                    source_job_id=job.source_job_id,
                    job_title=job.job_title,
                    category_key=job.category_key,
                    location_key=job.location_key,
                    ranks=rank_map[key],
                    rrf_score=aggregate_rrf[key],
                )
            )
        return result
