from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.career.evaluation.career_rag.audit import verify_frozen_benchmark
from apps.career.evaluation.career_rag.build_benchmark import DEFAULT_OUTPUT_DIR


class Command(BaseCommand):
    help = "Verify a frozen CareerRAGBench-Auto-V3 directory without LLM/API access."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))

    def handle(self, *args, **options) -> None:
        report = verify_frozen_benchmark(Path(options["output_dir"]))
        self.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        if not report["passed"]:
            raise CommandError("Frozen V3 verification failed")
        self.stdout.write(self.style.SUCCESS("PASS"))
