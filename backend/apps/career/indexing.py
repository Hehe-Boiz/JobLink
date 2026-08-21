from __future__ import annotations

from collections.abc import Iterable
from django.db import transaction
from .chunking import JobKnowledgeChunker
from .domain import RawJobRecord
from .embedding import CareerEmbeddingService
from .knowledge import JobKnowledgeBuilder
from .models import CareerJobChunk
from .sources.joblink import JobLinkJobSource


class CareerJobIndexer:
    def __init__(
        self,
        builder: JobKnowledgeBuilder | None = None,
        chunker: JobKnowledgeChunker | None = None,
        embedder: CareerEmbeddingService | None = None,
    ) -> None:
        self.builder = builder or JobKnowledgeBuilder()
        self.chunker = chunker or JobKnowledgeChunker()
        self.embedder = embedder or CareerEmbeddingService()

    def index_record(self, record: RawJobRecord,) -> int:
        document = self.builder.build(record)
        chunks = self.chunker.chunk(document)
        embeddings = self.embedder.embed_chunks(chunks)

        rows = [
            CareerJobChunk(
                chunk_id=chunk.chunk_id,
                chunk_index=chunk.chunk_index,
                source=chunk.source,
                source_job_id=chunk.source_job_id,
                job_title=chunk.title,
                company_name=chunk.company_name,
                section=chunk.section.value,
                content=chunk.content,
                location_key=chunk.location_key,
                experience_level=chunk.experience_level,
                employment_type=chunk.employment_type,
                category_key=chunk.category_key,
                active=chunk.is_active,
                published_at=chunk.published_at,
                source_url=chunk.source_url,
                metadata=dict(chunk.metadata),
                embedding=embedding.tolist(),
            )
            for chunk, embedding in zip(chunks, embeddings, strict=True)
        ]

        self._replace_job_chunks(source=record.source, source_job_id=record.source_job_id, rows=rows)

        return len(rows)

    def index_records(self, records: Iterable[RawJobRecord],) -> int:
        total_chunks = 0
        for record in records:
            total_chunks += self.index_record(record)

        return total_chunks

    def index_joblink_jobs(self) -> int:
        source = JobLinkJobSource()
        return self.index_records(source.iter_records(active_only=False))

    @staticmethod
    def _replace_job_chunks(source: str, source_job_id: str, rows: list[CareerJobChunk]) -> None:
        with transaction.atomic():
            CareerJobChunk.objects.filter(source=source, source_job_id=source_job_id).delete()

            if rows:
                CareerJobChunk.objects.bulk_create(rows, batch_size=500)