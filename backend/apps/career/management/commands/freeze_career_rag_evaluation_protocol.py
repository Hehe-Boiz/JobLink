from __future__ import annotations

import os
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.career.answering import DEFAULT_ANSWER_MODEL
from apps.career.evaluation.career_rag.build_benchmark import DEFAULT_OUTPUT_DIR
from apps.career.evaluation.career_rag.evaluation_protocol import (
    PROTOCOL_RELATIVE_PATH,
    freeze_evaluation_protocol,
)


class Command(BaseCommand):
    help = "Freeze final DEV-selected CareerRAGBench-Auto-V3 TEST evaluation settings."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
        parser.add_argument("--retrieval-top-k", type=int, default=10)
        parser.add_argument("--rag-retriever", choices=("dense", "hybrid"), default="dense")
        parser.add_argument("--rag-top-k", type=int, default=5)
        parser.add_argument("--generator-model", default=None)
        parser.add_argument("--judge-model", default=None)
        parser.add_argument("--bootstrap-seed", type=int, default=20260819)
        parser.add_argument("--bootstrap-samples", type=int, default=2000)
        parser.add_argument("--alpha", type=float, default=0.05)

    def handle(self, *args, **options) -> None:
        generator_model = options["generator_model"] or os.environ.get(
            "CAREER_RAG_GENERATOR_MODEL", DEFAULT_ANSWER_MODEL
        )
        judge_model = options["judge_model"] or os.environ.get("CAREER_RAG_JUDGE_MODEL")
        if not judge_model:
            raise RuntimeError(
                "Set CAREER_RAG_JUDGE_MODEL or pass --judge-model before freezing the protocol."
            )
        output_dir = Path(options["output_dir"])
        freeze_evaluation_protocol(
            output_dir,
            retrieval_top_k=options["retrieval_top_k"],
            rag_retriever_system=options["rag_retriever"],
            rag_top_k=options["rag_top_k"],
            generator_model=generator_model,
            judge_model=judge_model,
            bootstrap_seed=options["bootstrap_seed"],
            bootstrap_samples=options["bootstrap_samples"],
            alpha=options["alpha"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Frozen evaluation protocol written to {output_dir / PROTOCOL_RELATIVE_PATH}"
            )
        )
