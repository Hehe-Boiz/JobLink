from __future__ import annotations
from collections.abc import Sequence
import numpy as np
from sentence_transformers import SentenceTransformer
from apps.matching.domain import TextSegment
from .exceptions import EmbeddingError

DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
DEFAULT_BATCH_SIZE = 32


class EmbeddingService:
    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL, device: str | None = None, batch_size: int = DEFAULT_BATCH_SIZE,) -> None:
        self.model_name = model_name
        self._device = device
        self._batch_size = batch_size
        self._model: SentenceTransformer | None = None

    @property
    def dimension(self) -> int:
        model = self._get_model()
        dimension = model.get_sentence_embedding_dimension()
        if dimension is None:
            raise EmbeddingError("Không xác định được embedding dimension.")

        return dimension

    def embed_query(self, text: str) -> np.ndarray:
        text = text.strip()
        if not text:
            raise ValueError("Query text không được rỗng.")
        embeddings = self._encode([f"query: {text}"])
        return embeddings[0]

    def embed_passages(self, texts: Sequence[str]) -> np.ndarray:
        prepared_texts: list[str] = []

        for text in texts:
            cleaned_text = text.strip()
            if not cleaned_text:
                continue
            prepared_texts.append(f"passage: {cleaned_text}")

        if not prepared_texts:
            return np.empty((0, self.dimension), dtype=np.float32,)

        return self._encode(prepared_texts)

    def embed_segments(self, segments: Sequence[TextSegment]) -> dict[str, np.ndarray]:
        valid_segments = [
            segment
            for segment in segments
            if segment.text.strip()
        ]

        if not valid_segments:
            return {}

        embeddings = self.embed_passages(
            [
                segment.text
                for segment in valid_segments
            ]
        )

        result: dict[str, np.ndarray] = {}
        for segment, embedding in zip(valid_segments, embeddings, strict=True):
            result[segment.stable_key] = embedding
        return result

    def _encode(self, texts: Sequence[str]) -> np.ndarray:
        model = self._get_model()

        try:
            embeddings = model.encode(
                list(texts),
                batch_size=self._batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

        except Exception as exc:
            raise EmbeddingError("Không thể tạo text embeddings.") from exc

        return np.asarray(embeddings, dtype=np.float32)

    def _get_model(self,) -> SentenceTransformer:

        if self._model is not None:
            return self._model

        try:
            self._model = SentenceTransformer(self.model_name, device=self._device,)

        except Exception as exc:
            raise EmbeddingError(f"Không thể load embedding model '{self.model_name}'.") from exc

        return self._model