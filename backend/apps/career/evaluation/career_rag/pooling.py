from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import replace

from rank_bm25 import BM25Okapi

from apps.career.models import CareerJobChunk
from apps.career.retrieval import CareerRetriever

from .schema import CareerQuery, CorpusJob, PooledCandidate

RRF_K = 60


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


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
