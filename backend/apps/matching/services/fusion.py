from __future__ import annotations

from apps.matching.constants import DEFAULT_FUSION_TOP_K, DEFAULT_RRF_K
from apps.matching.domain import BM25Hit, DenseHit, FusedHit


def reciprocal_rank_fusion(dense_hits: list[DenseHit], bm25_hits: list[BM25Hit], *, top_k: int = DEFAULT_FUSION_TOP_K, rrf_k: int = DEFAULT_RRF_K) -> list[FusedHit]:
    if top_k <= 0:
        return []

    if rrf_k <= 0:
        raise ValueError("rrf_k phải lớn hơn 0.")

    fused: dict[str, dict] = {}

    for hit in dense_hits:
        entry = fused.setdefault(
            hit.chunk_key,
            {
                "chunk_key": hit.chunk_key,
                "section": hit.section,
                "text": hit.text,
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None,
                "dense_similarity": None,
                "bm25_score": None,
            },
        )

        entry["rrf_score"] += 1.0 / (rrf_k + hit.rank)
        entry["dense_rank"] = hit.rank
        entry["dense_similarity"] = hit.similarity

    for hit in bm25_hits:
        entry = fused.setdefault(
            hit.chunk_key,
            {
                "chunk_key": hit.chunk_key,
                "section": hit.section,
                "text": hit.text,
                "rrf_score": 0.0,
                "dense_rank": None,
                "bm25_rank": None,
                "dense_similarity": None,
                "bm25_score": None,
            },
        )

        entry["rrf_score"] += 1.0 / (rrf_k + hit.rank)
        entry["bm25_rank"] = hit.rank
        entry["bm25_score"] = hit.score

    ranked_entries = sorted(
        fused.values(),
        key=lambda item: (
            -item["rrf_score"],
            item["chunk_key"],
        ),
    )

    results: list[FusedHit] = []

    for rank, entry in enumerate(ranked_entries[:top_k], start=1):
        results.append(
            FusedHit(
                chunk_key=entry["chunk_key"],
                rank=rank,
                rrf_score=entry["rrf_score"],
                section=entry["section"],
                text=entry["text"],
                dense_rank=entry["dense_rank"],
                bm25_rank=entry["bm25_rank"],
                dense_similarity=entry["dense_similarity"],
                bm25_score=entry["bm25_score"],
            )
        )

    return results