from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi
from apps.matching.constants import DEFAULT_BM25_TOP_K, DEFAULT_DENSE_TOP_K, DEFAULT_FUSION_TOP_K
from apps.matching.domain import BM25Hit, DenseHit, FusedHit, JobRequirement, TextSegment
from .embeddings import EmbeddingService
from .fusion import reciprocal_rank_fusion


class DenseRetriever:
    def __init__(self, embedding_service: EmbeddingService | None = None) -> None:
        self._embedding_service = embedding_service or EmbeddingService()

    def embed_segments(self, segments: list[TextSegment]) -> dict[str, np.ndarray]:
        if not segments:
            return {}
        return self._embedding_service.embed_segments(segments)

    def retrieve(self, requirement: JobRequirement, segments: list[TextSegment], *, segment_embeddings: dict[str, np.ndarray] | None = None, top_k: int = DEFAULT_DENSE_TOP_K) -> list[DenseHit]:
        if top_k <= 0 or not segments:
            return []

        query_text = requirement.original_text.strip()
        if not query_text:
            return []

        if segment_embeddings is None:
            segment_embeddings = self.embed_segments(segments)

        if not segment_embeddings:
            return []

        query_embedding = self._embedding_service.embed_query(query_text)
        scored_segments: list[tuple[float, TextSegment]] = []

        for segment in segments:
            passage_embedding = segment_embeddings.get(segment.stable_key)
            if passage_embedding is None:
                continue

            similarity = float(np.dot(passage_embedding, query_embedding))
            scored_segments.append((similarity, segment))

        scored_segments.sort(
            key=lambda item: (
                -item[0],
                item[1].index,
            )
        )
        results: list[DenseHit] = []
        for rank, (similarity, segment) in enumerate(scored_segments[:top_k], start=1,):
            results.append(
                DenseHit(
                    chunk_key=segment.stable_key,
                    rank=rank,
                    distance=1.0 - similarity,
                    similarity=similarity,
                    section=segment.section,
                    text=segment.text,
                )
            )

        return results

    def retrieve_many(self, requirements: list[JobRequirement], segments: list[TextSegment], *, top_k: int = DEFAULT_DENSE_TOP_K) -> dict[str, list[DenseHit]]:
        if not requirements or not segments:
            return {}

        segment_embeddings = self.embed_segments(segments)
        results: dict[str, list[DenseHit]] = {}
        for requirement in requirements:
            results[requirement.requirement_id] = self.retrieve(
                requirement=requirement,
                segments=segments,
                segment_embeddings=segment_embeddings,
                top_k=top_k,
            )

        return results


class BM25Retriever:
    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [
            token
            for token in text.split()
            if token
        ]

    def retrieve(self, requirement: JobRequirement, segments: list[TextSegment], *, top_k: int = DEFAULT_BM25_TOP_K) -> list[BM25Hit]:
        if top_k <= 0 or not segments:
            return []

        query_tokens = self._tokenize(requirement.normalized_text)
        if not query_tokens:
            return []
        
        corpus = [
            self._tokenize(segment.normalized_text)
            for segment in segments
        ]

        if not any(corpus):
            return []

        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(query_tokens)
        scored_segments: list[tuple[float, TextSegment]] = []
        for score, segment in zip(scores, segments, strict=True):
            score = float(score)
            if score <= 0.0:
                continue

            scored_segments.append((score, segment))
            
        scored_segments.sort(
            key=lambda item: (
                -item[0],
                item[1].index,
            )
        )

        results: list[BM25Hit] = []
        for rank, (score, segment) in enumerate(scored_segments[:top_k], start=1):
            results.append(
                BM25Hit(
                    chunk_key=segment.stable_key,
                    rank=rank,
                    score=score,
                    section=segment.section,
                    text=segment.text,
                )
            )

        return results

    def retrieve_many(self, requirements: list[JobRequirement], segments: list[TextSegment], *, top_k: int = DEFAULT_BM25_TOP_K) -> dict[str, list[BM25Hit]]:
        if not requirements or not segments:
            return {}

        corpus = [
            self._tokenize(segment.normalized_text)
            for segment in segments
        ]

        if not any(corpus):
            return {
                requirement.requirement_id: []
                for requirement in requirements
            }

        bm25 = BM25Okapi(corpus)
        results: dict[str, list[BM25Hit]] = {}
        for requirement in requirements:
            query_tokens = self._tokenize(requirement.normalized_text)
            if not query_tokens:
                results[requirement.requirement_id] = []
                continue
            scores = bm25.get_scores(query_tokens)
            scored_segments: list[tuple[float, TextSegment]] = []
            for score, segment in zip(scores, segments, strict=True):
                score = float(score)
                if score <= 0.0:
                    continue

                scored_segments.append((score, segment))
            scored_segments.sort(
                key=lambda item: (
                    -item[0],
                    item[1].index,
                )
            )

            hits: list[BM25Hit] = []
            for rank, (score, segment) in enumerate(scored_segments[:top_k], start=1):
                hits.append(
                    BM25Hit(chunk_key=segment.stable_key, rank=rank, score=score, section=segment.section, text=segment.text)
                )
            results[requirement.requirement_id] = hits

        return results


class HybridRetriever:
    def __init__(self, dense_retriever: DenseRetriever | None = None, bm25_retriever: BM25Retriever | None = None) -> None:
        self._dense_retriever = dense_retriever or DenseRetriever()
        self._bm25_retriever = bm25_retriever or BM25Retriever()

    def retrieve(self, requirement: JobRequirement, segments: list[TextSegment], *, top_k: int = DEFAULT_FUSION_TOP_K) -> list[FusedHit]:
        dense_hits = self._dense_retriever.retrieve(requirement=requirement, segments=segments,)
        bm25_hits = self._bm25_retriever.retrieve(requirement=requirement, segments=segments)
        return reciprocal_rank_fusion(dense_hits=dense_hits, bm25_hits=bm25_hits, top_k=top_k)

    def retrieve_many(self, requirements: list[JobRequirement], segments: list[TextSegment], *, top_k: int = DEFAULT_FUSION_TOP_K) -> dict[str, list[FusedHit]]:
        if not requirements or not segments:
            return {}

        dense_results = self._dense_retriever.retrieve_many(requirements=requirements, segments=segments)
        bm25_results = self._bm25_retriever.retrieve_many(requirements=requirements, segments=segments)
        fused_results: dict[str, list[FusedHit]] = {}

        for requirement in requirements:
            requirement_id = requirement.requirement_id

            fused_results[requirement_id] = reciprocal_rank_fusion(
                dense_hits=dense_results.get(requirement_id, []),
                bm25_hits=bm25_results.get(requirement_id, []),
                top_k=top_k,
            )

        return fused_results