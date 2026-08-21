from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.career.evaluation.career_rag.build_benchmark import (
    DEFAULT_PREFLIGHT_OUTPUT_DIR,
    run_construction_preflight,
)


class Command(BaseCommand):
    help = "Run the offline, pre-paid CareerRAGBench-Auto-V3 construction preflight."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(DEFAULT_PREFLIGHT_OUTPUT_DIR))
        parser.add_argument("--seed", type=int, default=20260819)
        parser.add_argument("--max-pool", type=int, default=80)

    def handle(self, *args, **options) -> None:
        report = run_construction_preflight(
            output_dir=Path(options["output_dir"]),
            seed=options["seed"],
            max_pool=options["max_pool"],
        )
        self.stdout.write(json.dumps(report["report"], ensure_ascii=False, indent=2, sort_keys=True))
        if report["readiness"]["status"] != "READY_FOR_PAID_BUILD":
            raise CommandError(
                "CareerRAGBench-Auto-V3 preflight BLOCKED: "
                + "; ".join(report["readiness"]["blockers"])
            )
        self.stdout.write(self.style.SUCCESS("READY_FOR_PAID_BUILD"))
