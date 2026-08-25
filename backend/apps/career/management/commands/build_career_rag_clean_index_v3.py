from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.career.evaluation.career_rag.clean_index import (
    build_clean_embedding_index,
    configured_clean_index_dir,
)


class Command(BaseCommand):
    help = "Build the immutable benchmark-only CareerRAGBench-Auto-V3 clean embedding sidecar."
    requires_system_checks: list = []

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(configured_clean_index_dir()))
        parser.add_argument("--batch-size", type=int, default=32)
        parser.add_argument("--device", default=None)

    def handle(self, *args, **options) -> None:
        result = build_clean_embedding_index(
            output_dir=Path(options["output_dir"]),
            batch_size=options["batch_size"],
            device=options["device"],
        )
        self.stdout.write(self.style.SUCCESS(f"Clean V3 sidecar finalized at {result['output_dir']}"))
