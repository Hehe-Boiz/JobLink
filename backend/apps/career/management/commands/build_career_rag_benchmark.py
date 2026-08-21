from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from apps.career.evaluation.career_rag.build_benchmark import DEFAULT_OUTPUT_DIR, build_benchmark


class Command(BaseCommand):
    help = "Build and freeze CareerRAGBench-Auto-V2 (silver benchmark)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
        parser.add_argument("--judge-model", default=None)
        parser.add_argument("--seed", type=int, default=20260819)
        parser.add_argument("--pool-depth", type=int, default=20)
        parser.add_argument("--max-pool", type=int, default=80)

    def handle(self, *args, **options) -> None:
        import os

        judge_model = options["judge_model"] or os.environ.get("CAREER_RAG_JUDGE_MODEL")
        if not judge_model:
            raise RuntimeError("Set CAREER_RAG_JUDGE_MODEL or pass --judge-model.")
        result = build_benchmark(
            output_dir=Path(options["output_dir"]),
            judge_model=judge_model,
            seed=options["seed"],
            pool_depth=options["pool_depth"],
            max_pool=options["max_pool"],
        )
        self.stdout.write(self.style.SUCCESS(f"CareerRAGBench-Auto-V2 frozen at {result['output_dir']}"))
        self.stdout.write(
            f"topics={result['topics']} queries={result['queries']} qrels={result['qrels']} "
            f"uncertain={result['uncertain_qrels']} nuggets={result['nuggets']}"
        )
