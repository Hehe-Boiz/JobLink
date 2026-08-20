from __future__ import annotations

import os
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.career.answering import DEFAULT_ANSWER_MODEL
from apps.career.evaluation.career_rag.build_benchmark import DEFAULT_OUTPUT_DIR
from apps.career.evaluation.career_rag.run_rag_eval import run_rag_eval
from apps.career.evaluation.career_rag.run_retrieval_eval import run_retrieval_eval


class Command(BaseCommand):
    help = "Evaluate frozen CareerRAGBench-Auto-V1 on DEV or explicitly unlocked TEST."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--kind", choices=("retrieval", "rag"), default="retrieval")
        parser.add_argument("--split", choices=("dev", "test"), default="dev")
        parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
        parser.add_argument("--allow-test", action="store_true")
        parser.add_argument("--retriever", choices=("dense", "hybrid"), default="dense")
        parser.add_argument("--judge-model", default=None)
        parser.add_argument("--generator-model", default=None)

    def handle(self, *args, **options) -> None:
        output_dir = Path(options["output_dir"])
        if options["kind"] == "retrieval":
            report = run_retrieval_eval(
                split=options["split"],
                output_dir=output_dir,
                allow_test=options["allow_test"],
            )
            self.stdout.write(self.style.SUCCESS(f"Retrieval {options['split']} evaluation complete."))
            for system, data in report["systems"].items():
                ndcg5 = data["macro"]["ndcg@5"]["mean"]
                nugget10 = data["macro"]["nugget_recall@10"]["mean"]
                self.stdout.write(f"{system}: nDCG@5={ndcg5:.4f} nugget_recall@10={nugget10:.4f}")
            return

        judge_model = options["judge_model"] or os.environ.get("CAREER_RAG_JUDGE_MODEL")
        if not judge_model:
            raise RuntimeError("RAG evaluation requires CAREER_RAG_JUDGE_MODEL or --judge-model.")
        generator_model = options["generator_model"] or os.environ.get("CAREER_RAG_GENERATOR_MODEL", DEFAULT_ANSWER_MODEL)
        report = run_rag_eval(
            split=options["split"],
            output_dir=output_dir,
            generator_model=generator_model,
            judge_model=judge_model,
            retriever_system=options["retriever"],
            allow_test=options["allow_test"],
        )
        self.stdout.write(self.style.SUCCESS(f"RAG {options['split']} evaluation complete."))
        for system, data in report["systems"].items():
            f1 = data["macro"]["weighted_nugget_f1"]["mean"]
            faith = data["macro"]["faithfulness"]["mean"]
            self.stdout.write(f"{system}: weighted_nugget_f1={f1:.4f} faithfulness={faith:.4f}")
