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
    # This benchmark command validates its own corpus/index invariants.  It
    # must remain runnable offline without importing unrelated API views.
    requires_system_checks: list = []

    def add_arguments(self, parser) -> None:
        parser.add_argument("--output-dir", default=str(DEFAULT_PREFLIGHT_OUTPUT_DIR))
        parser.add_argument("--seed", type=int, default=20260819)
        parser.add_argument("--max-pool", type=int, default=80)
        parser.add_argument("--json", action="store_true", help="Print the complete machine-readable report.")

    def handle(self, *args, **options) -> None:
        report = run_construction_preflight(
            output_dir=Path(options["output_dir"]),
            seed=options["seed"],
            max_pool=options["max_pool"],
        )
        if options["json"]:
            self.stdout.write(json.dumps(report["report"], ensure_ascii=False, indent=2, sort_keys=True))
        else:
            payload = report["report"]
            corpus = payload.get("corpus", {})
            topics = payload.get("topics", {})
            clean = payload.get("clean_index", {})
            pooling = payload.get("pooling", {})
            aggregate = pooling.get("reports", {}).get("20", {}).get("aggregate", {})
            size = aggregate.get("direct_union_size", {})
            self.stdout.write(f"Corpus      : {corpus.get('indexed_vietjobs_jobs', 0)} jobs / {corpus.get('indexed_vietjobs_chunks', 0)} chunks")
            self.stdout.write(f"Topics      : {topics.get('topic_count', 0)}")
            self.stdout.write(f"Queries     : {topics.get('query_count', 0)}")
            clean_status = "PASS" if clean.get("passed") else ("MISSING" if not Path(clean.get("index_dir", "")).exists() else "INVALID")
            self.stdout.write(f"Clean index : {clean_status}")
            self.stdout.write(f"Provenance  : {payload.get('embedding_provenance', {}).get('status', 'UNVERIFIED')}")
            self.stdout.write(f"Pool policy : {pooling.get('pooling_policy', 'FULL_DIRECT_UNION_V1')}")
            self.stdout.write(f"Pool size   : p50={size.get('p50', 0)} / p95={size.get('p95', 0)} / max={size.get('max', 0)}")
            self.stdout.write(f"Leakage     : {'PASS' if payload.get('leakage', {}).get('passed') else 'FAIL'}")
            self.stdout.write(f"LLM calls   : {payload.get('external_llm_calls', 0)}")
            self.stdout.write(f"STATUS: {payload.get('readiness', {}).get('status', 'BLOCKED')}")
        if report["readiness"]["status"] != "READY_FOR_PAID_BUILD":
            raise CommandError("CareerRAGBench-Auto-V3 preflight BLOCKED; see preflight_report.json.")
