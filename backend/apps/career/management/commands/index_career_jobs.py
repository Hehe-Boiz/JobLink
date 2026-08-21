from __future__ import annotations

from django.core.management.base import BaseCommand
from apps.career.indexing import CareerJobIndexer


class Command(BaseCommand):
    help = (
        "Index toàn bộ JobLink jobs vào Career RAG corpus "
        "sử dụng chunking + embedding + PostgreSQL/pgvector."
    )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting Career RAG indexing..."))
        indexer = CareerJobIndexer()
        total_chunks = indexer.index_joblink_jobs()

        self.stdout.write(
            self.style.SUCCESS(f"Career RAG indexing completed. Indexed {total_chunks} chunks.")
        )