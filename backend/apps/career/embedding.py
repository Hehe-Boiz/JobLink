from __future__ import annotations

from collections.abc import Sequence
import numpy as np
from sentence_transformers import SentenceTransformer
from .domain import JobKnowledgeChunk


DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
DEFAULT_BATCH_SIZE = 32

class CareerEmbeddingService:
    def __init__(
        self,
        model_name: str = DEFAULT_EMBEDDING_MODEL,
        batch_size: int = DEFAULT_BATCH_SIZE,
        device: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.batch_size = batch_size
        self.model = SentenceTransformer(model_name, device=device)

    @property
    def dimension(self) -> int:

        dimension = self.model.get_embedding_dimension()

        if dimension is None:
            raise RuntimeError("Could not determine embedding dimension")

        return dimension

    def embed_chunks(self, chunks: Sequence[JobKnowledgeChunk]) -> np.ndarray:
        if not chunks:
            return np.empty((0, self.dimension), dtype=np.float32)

        texts = [
            chunk.embedding_text
            for chunk in chunks
        ]

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embeddings.astype(
            np.float32,
            copy=False,
        )

    def embed_query(self, query: str) -> np.ndarray:
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("Query must not be empty")

        query_text = f"query: {normalized_query}"
        embedding = self.model.encode(
            query_text,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

        return embedding.astype(
            np.float32,
            copy=False,
        )