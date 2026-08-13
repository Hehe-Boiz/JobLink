from __future__ import annotations

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from apps.matching.constants import DEFAULT_RERANK_TOP_K
from apps.matching.domain import FusedHit, JobRequirement, RerankedHit


DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_RERANK_BATCH_SIZE = 8
DEFAULT_RERANK_MAX_LENGTH = 512


class CrossEncoderReranker:
    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        device: str | None = None,
        batch_size: int = DEFAULT_RERANK_BATCH_SIZE,
        max_length: int = DEFAULT_RERANK_MAX_LENGTH,
    ) -> None:
        self._model_name = model_name
        self._device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._batch_size = batch_size
        self._max_length = max_length

        self._tokenizer = None
        self._model = None

    def _get_tokenizer(self):
        if self._tokenizer is None:
            self._tokenizer = AutoTokenizer.from_pretrained(self._model_name)
        return self._tokenizer

    def _get_model(self):
        if self._model is None:
            self._model = (AutoModelForSequenceClassification.from_pretrained(self._model_name).to(self._device))
            self._model.eval()
        return self._model

    def _score_pairs(self, query: str, passages: list[str]) -> list[float]:
        if not passages:
            return []

        tokenizer = self._get_tokenizer()
        model = self._get_model()
        scores: list[float] = []

        for start in range(0, len(passages), self._batch_size):
            batch_passages = passages[start:start + self._batch_size]
            queries = [query] * len(batch_passages)
            inputs = tokenizer(
                queries,
                batch_passages,
                padding=True,
                truncation=True,
                max_length=self._max_length,
                return_tensors="pt",
            )

            inputs = {
                key: value.to(self._device)
                for key, value in inputs.items()
            }

            with torch.no_grad():
                logits = model(**inputs, return_dict=True).logits.view(-1)
                batch_scores = torch.sigmoid(logits.float())
            scores.extend(batch_scores.cpu().tolist())

        return scores

    def rerank(self, requirement: JobRequirement, hits: list[FusedHit], *, top_k: int = DEFAULT_RERANK_TOP_K) -> list[RerankedHit]:
        if top_k <= 0 or not hits:
            return []

        query = requirement.original_text.strip()
        if not query:
            return []

        passages = [
            hit.text
            for hit in hits
        ]

        scores = self._score_pairs(query=query, passages=passages,)
        scored_hits = list(zip(scores, hits, strict=True))

        scored_hits.sort(
            key=lambda item: (
                -item[0],
                item[1].rank,
            )
        )

        results: list[RerankedHit] = []

        for rank, (score, hit) in enumerate(scored_hits[:top_k], start=1):
            results.append(
                RerankedHit(
                    chunk_key=hit.chunk_key,
                    rank=rank,
                    reranker_score=score,
                    section=hit.section,
                    text=hit.text,
                    fused_rank=hit.rank,
                    rrf_score=hit.rrf_score,
                )
            )

        return results

    def rerank_many(self, requirements: list[JobRequirement], fused_results: dict[str, list[FusedHit]], *, top_k: int = DEFAULT_RERANK_TOP_K) -> dict[str, list[RerankedHit]]:
        results: dict[str, list[RerankedHit]] = {}
        for requirement in requirements:
            requirement_id = requirement.requirement_id
            hits = fused_results.get(requirement_id, [])
            results[requirement_id] = self.rerank(requirement=requirement, hits=hits, top_k=top_k,)

        return results