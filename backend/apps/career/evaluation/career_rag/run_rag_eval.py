from __future__ import annotations

import json
import os
import threading
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from statistics import mean

from django.conf import settings
from openai import OpenAI

from apps.career.answering import CareerAnswerService, DEFAULT_ANSWER_MODEL
from apps.career.retrieval import CareerEvidenceChunk, CareerRetrievedJob

from .build_benchmark import DEFAULT_OUTPUT_DIR
from .clean_index import CleanBenchmarkDenseRanker, configured_clean_index_dir
from .concurrency import RefillWindowConfig, run_refill_window
from .evidence import DEFAULT_EVIDENCE_CHAR_BUDGET, pack_job_evidence
from .evaluation_integrity import assert_evaluation_integrity, consume_test_lock
from .evaluation_protocol import (
    GENERATION_TEMPERATURE,
    assert_test_evaluation_protocol,
    rag_runtime_settings,
)
from .judges import JudgeClient
from .metrics import family_cluster_bootstrap_ci, robustness, weighted_nugget_coverage
from .pooling import PoolingService, load_corpus_jobs
from .schema import CorpusJob, Nugget

RAG_JUDGE_SCHEMA_RETRIES = 2
DEFAULT_RAG_EVAL_MAX_IN_FLIGHT = 4
DEFAULT_RAG_EVAL_REFILL_SIZE = 2
RAG_JUDGE_REQUIRED_KEYS = frozenset({
    "matched_nugget_ids",
    "claim_count",
    "supported_claim_count",
    "unsupported_claim_count",
    "citation_required_claim_count",
    "cited_claim_count",
    "citation_supported_count",
    "context_used_job_keys",
})
RAG_SYSTEMS = ("no_rag", "clean_rag", "gold_context_rag")


def _read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_retrieved(job: CorpusJob, score: float = 1.0) -> CareerRetrievedJob:
    evidence = (CareerEvidenceChunk(
        chunk_id=f"{job.job_key}:packed",
        section="section-aware packed evidence",
        content=pack_job_evidence(job, char_budget=DEFAULT_EVIDENCE_CHAR_BUDGET),
        distance=1.0 - score,
        similarity=score,
    ),)
    return CareerRetrievedJob(
        source=job.source, source_job_id=job.source_job_id, job_title=job.job_title, company_name="",
        location_key=job.location_key, experience_level=job.experience_level, employment_type=job.employment_type,
        category_key=job.category_key, published_at=None, source_url=None, score=score, evidence=evidence,
    )


def _no_rag_answer(
    client: OpenAI,
    model: str,
    query: str,
    *,
    temperature: int = GENERATION_TEMPERATURE,
) -> str:
    response = client.chat.completions.create(
        model=model, temperature=temperature,
        messages=[
            {"role": "system", "content": "Answer the Vietnamese career question concisely. Do not claim access to JobLink evidence or citations."},
            {"role": "user", "content": query},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _certain_gold_context_rows(qrel_rows: list[dict], *, topic_id: str, top_k: int) -> list[dict]:
    """Select oracle context only from strong, explicitly certain judgments."""

    return sorted(
        (
            row
            for row in qrel_rows
            if row.get("topic_id") == topic_id
            and row.get("uncertain") is False
            and type(row.get("grade")) is int
            and row["grade"] >= 2
        ),
        key=lambda row: (-row["grade"], f"{row['source']}::{row['source_job_id']}"),
    )[:top_k]


def _model_identity(generator_model: str, judge_model: str) -> dict:
    """Report exact requested IDs without guessing provider model families."""

    return {
        "generator_model_requested": generator_model,
        "generator_model_reported": None,
        "judge_model_requested": judge_model,
        "judge_model_reported": None,
        "exact_model_id_equal": generator_model == judge_model,
        "exact_model_id_equal_basis": "requested model IDs; runtime-reported IDs unavailable",
        "generator_model_family": None,
        "judge_model_family": None,
        "family_metadata_source": None,
        "family_relation": "UNVERIFIED",
    }


def validate_rag_judge_payload(
    data: object,
    *,
    gold_nugget_ids: set[str],
    context_job_keys: set[str],
) -> dict:
    """Strictly validate RAG judge JSON before calculating any metric."""

    if not isinstance(data, dict) or set(data) != RAG_JUDGE_REQUIRED_KEYS:
        missing = sorted(RAG_JUDGE_REQUIRED_KEYS - set(data) if isinstance(data, dict) else RAG_JUDGE_REQUIRED_KEYS)
        extra = sorted(set(data) - RAG_JUDGE_REQUIRED_KEYS) if isinstance(data, dict) else []
        raise ValueError(f"RAG judge requires exact top-level keys; missing={missing}; extra={extra}")

    def validate_ids(field: str, allowed: set[str]) -> list[str]:
        value = data[field]
        if not isinstance(value, list) or any(type(item) is not str for item in value):
            raise ValueError(f"RAG judge {field} must be list[str]")
        if len(value) != len(set(value)):
            raise ValueError(f"RAG judge {field} must contain unique IDs")
        invalid = sorted(set(value) - allowed)
        if invalid:
            raise ValueError(f"RAG judge {field} contains unsupported IDs: {invalid}")
        return value

    matched = validate_ids("matched_nugget_ids", gold_nugget_ids)
    used_context = validate_ids("context_used_job_keys", context_job_keys)
    counts: dict[str, int] = {}
    for field in RAG_JUDGE_REQUIRED_KEYS - {"matched_nugget_ids", "context_used_job_keys"}:
        value = data[field]
        if type(value) is not int or value < 0:
            raise ValueError(f"RAG judge {field} must be a non-negative JSON integer (not bool/float/string)")
        counts[field] = value
    if counts["supported_claim_count"] > counts["claim_count"]:
        raise ValueError("RAG judge supported_claim_count exceeds claim_count")
    if counts["unsupported_claim_count"] > counts["claim_count"]:
        raise ValueError("RAG judge unsupported_claim_count exceeds claim_count")
    if counts["supported_claim_count"] + counts["unsupported_claim_count"] != counts["claim_count"]:
        raise ValueError("RAG judge supported + unsupported claims must equal claim_count")
    if counts["citation_required_claim_count"] > counts["claim_count"]:
        raise ValueError("RAG judge citation_required_claim_count exceeds claim_count")
    if counts["cited_claim_count"] > counts["citation_required_claim_count"]:
        raise ValueError("RAG judge cited_claim_count exceeds citation_required_claim_count")
    if counts["citation_supported_count"] > counts["cited_claim_count"]:
        raise ValueError("RAG judge citation_supported_count exceeds cited_claim_count")
    if not context_job_keys and (
        counts["supported_claim_count"] != 0
        or used_context
        or counts["cited_claim_count"] != 0
        or counts["citation_supported_count"] != 0
    ):
        raise ValueError("RAG judge violates required no-context grounding invariants")
    return {"matched_nugget_ids": matched, "context_used_job_keys": used_context, **counts}


def _evaluate_answer(
    judge: JudgeClient,
    *,
    query: str,
    answer: str,
    nuggets: list[Nugget],
    context_jobs: list[CareerRetrievedJob],
    schema_retries: int = RAG_JUDGE_SCHEMA_RETRIES,
) -> dict:
    if schema_retries < 0:
        raise ValueError("schema_retries must be >= 0")
    context_blocks = []
    alias_to_job_key: dict[str, str] = {}
    for index, job in enumerate(context_jobs, start=1):
        alias = f"J{index}"
        job_key = f"{job.source}::{job.source_job_id}"
        alias_to_job_key[alias] = job_key
        evidence = "\n".join(chunk.content for chunk in job.evidence)
        context_blocks.append(f"[{alias}] JOB_KEY={job_key}\n{evidence[:5000]}")
    nugget_block = "\n".join(f"{n.nugget_id}: {n.text}" for n in nuggets)
    context_text = "\n\n---\n\n".join(context_blocks) if context_blocks else "[NO CONTEXT]"
    system_prompt = (
        "Evaluate a generated career answer against silver information nuggets and, when supplied, retrieved raw evidence. "
        "matched_nugget_ids measures answer coverage of the supplied gold nuggets. All supported/unsupported and citation "
        "counts measure grounding only against the supplied retrieved context, not general world knowledge. "
        "Return JSON only with exactly these keys: matched_nugget_ids (list[str]), claim_count (int), "
        "supported_claim_count (int), unsupported_claim_count (int), citation_required_claim_count (int), "
        "cited_claim_count (int), citation_supported_count (int), context_used_job_keys (list[str]). "
        "context_used_job_keys must contain the exact values shown after JOB_KEY= (for example "
        "\"vietjobs::VietJobs:123\"), never display aliases such as \"J1\". "
        "All counts must be non-negative JSON integers. supported_claim_count + unsupported_claim_count must equal claim_count. "
        "For no-context answers, supported_claim_count, cited_claim_count, and citation_supported_count must be 0, "
        "and context_used_job_keys must be []."
    )
    base_user_prompt = (
        f"Question:\n{query}\n\nGold silver nuggets:\n{nugget_block}\n\n"
        f"Retrieved context:\n{context_text}\n\nGenerated answer:\n{answer}"
    )
    nugget_ids = {nugget.nugget_id for nugget in nuggets}
    context_keys = {f"{job.source}::{job.source_job_id}" for job in context_jobs}
    validated: dict | None = None
    last_error: Exception | None = None
    for attempt in range(schema_retries + 1):
        user_prompt = base_user_prompt
        if attempt:
            user_prompt += (
                f"\n\nSCHEMA_RETRY_ATTEMPT={attempt}\n"
                "IMPORTANT CORRECTION: The previous result failed strict validation. Return exactly the required keys, "
                "literal JSON integers (not strings/floats/booleans), IDs only from the supplied nugget/context IDs, "
                "use exact JOB_KEY values for context_used_job_keys and never aliases such as \"J1\", "
                "and satisfy every count arithmetic invariant."
            )
        data = judge.json_call(system=system_prompt, user=user_prompt)
        if isinstance(data, dict):
            context_used_job_keys = data.get("context_used_job_keys")
            if isinstance(context_used_job_keys, list) and all(
                type(value) is str for value in context_used_job_keys
            ):
                data = {
                    **data,
                    "context_used_job_keys": [
                        alias_to_job_key.get(value, value)
                        for value in context_used_job_keys
                    ],
                }
        try:
            validated = validate_rag_judge_payload(
                data, gold_nugget_ids=nugget_ids, context_job_keys=context_keys,
            )
            break
        except Exception as exc:  # schema correction uses a distinct prompt/cache key
            last_error = exc
    if validated is None:
        raise RuntimeError(
            f"RAG answer judge failed strict schema validation after {schema_retries} retries: {last_error}"
        ) from last_error

    matched = set(validated["matched_nugget_ids"])
    claim_count = validated["claim_count"]
    cited = validated["cited_claim_count"]
    citation_required = validated["citation_required_claim_count"]
    has_context = bool(context_keys)
    return {
        "matched_nugget_ids": sorted(matched),
        "weighted_nugget_coverage": weighted_nugget_coverage(matched, nuggets),
        "faithfulness": ((validated["supported_claim_count"] / claim_count) if claim_count else 1.0) if has_context else None,
        "unsupported_claim_rate": ((validated["unsupported_claim_count"] / claim_count) if claim_count else 0.0) if has_context else None,
        "citation_coverage": ((cited / citation_required) if citation_required else 1.0) if has_context else None,
        "citation_support_rate": ((validated["citation_supported_count"] / cited) if cited else 1.0) if has_context else None,
        "context_utilization": (len(validated["context_used_job_keys"]) / len(context_keys)) if has_context else None,
        "grounding_status": (
            "APPLICABLE_RETRIEVED_CONTEXT"
            if has_context
            else "NOT_APPLICABLE_NO_RETRIEVED_CONTEXT"
        ),
        "claim_count": claim_count,
        "supported_claim_count": validated["supported_claim_count"],
        "unsupported_claim_count": validated["unsupported_claim_count"],
        "citation_required_claim_count": citation_required,
        "cited_claim_count": cited,
        "citation_supported_count": validated["citation_supported_count"],
        "context_used_job_keys": validated["context_used_job_keys"],
    }


def _rag_metric_summary(
    by_topic: dict[str, list[dict]],
    metric: str,
    topic_family_ids: dict[str, str],
    *,
    bootstrap_samples: int,
    bootstrap_seed: int,
    bootstrap_alpha: float,
) -> dict:
    topic_values: dict[str, float] = {}
    for topic_id, rows in by_topic.items():
        available = [float(row[metric]) for row in rows if row[metric] is not None]
        if available:
            topic_values[topic_id] = mean(available)
    if not topic_values:
        return {
            "mean": None,
            "ci": None,
            "alpha": bootstrap_alpha,
            "bootstrap_unit": "family",
            "status": "NOT_APPLICABLE",
        }
    ci = family_cluster_bootstrap_ci(
        topic_values,
        topic_family_ids,
        samples=bootstrap_samples,
        seed=bootstrap_seed,
        alpha=bootstrap_alpha,
    )
    return {
        "mean": mean(topic_values.values()),
        "ci": list(ci),
        "alpha": bootstrap_alpha,
        "bootstrap_unit": "family",
        "status": "AVAILABLE",
    }


def _rag_eval_concurrency_config() -> RefillWindowConfig:
    try:
        max_in_flight = int(os.environ.get(
            "CAREER_RAG_RAG_EVAL_MAX_IN_FLIGHT",
            str(DEFAULT_RAG_EVAL_MAX_IN_FLIGHT),
        ))
        refill_size = int(os.environ.get(
            "CAREER_RAG_RAG_EVAL_REFILL_SIZE",
            str(DEFAULT_RAG_EVAL_REFILL_SIZE),
        ))
    except ValueError as exc:
        raise ValueError("RAG evaluation concurrency settings must be integers") from exc
    config = RefillWindowConfig(
        max_in_flight=max_in_flight,
        refill_size=refill_size,
    )
    config.validate()
    return config


def _evaluate_query(
    index: int,
    query: dict,
    *,
    retriever_system: str,
    top_k: int,
    clean_ranker: CleanBenchmarkDenseRanker,
    pooler: PoolingService,
    retrieval_lock: threading.Lock,
    corpus_by_key: dict[str, CorpusJob],
    qrels: dict[str, list[dict]],
    nuggets: dict[str, list[Nugget]],
    generator_model: str,
    generation_temperature: int,
    answer_service: CareerAnswerService,
    no_rag_client: OpenAI,
    judge: JudgeClient,
) -> dict:
    """Evaluate all three RAG systems for one query without nested concurrency."""

    topic_id = query["topic_id"]
    # Sentence-transformer/OpenAI service instances do not declare concurrent
    # method safety. Keep the shared ranker read-only and serialize only the
    # comparatively short retrieval section; LLM work remains query-parallel.
    with retrieval_lock:
        if retriever_system == "dense":
            keys = clean_ranker.rank_job_keys(query["text"], top_k)
        else:
            bm25 = pooler.bm25(query["text"], max(top_k, 10))
            dense = pooler.dense(query["text"], max(top_k, 10))
            keys = pooler.rrf([bm25, dense], top_k)
    clean_jobs = [
        _as_retrieved(corpus_by_key[key], score=1.0 - key_index * 0.001)
        for key_index, key in enumerate(keys)
        if key in corpus_by_key
    ]
    gold_rows = _certain_gold_context_rows(
        qrels[topic_id],
        topic_id=topic_id,
        top_k=top_k,
    )
    gold_jobs = [
        _as_retrieved(corpus_by_key[key])
        for row in gold_rows
        if (key := f"{row['source']}::{row['source_job_id']}") in corpus_by_key
    ]
    generated = {
        "no_rag": (
            _no_rag_answer(
                no_rag_client,
                generator_model,
                query["text"],
                temperature=generation_temperature,
            ),
            [],
        ),
        "clean_rag": (
            answer_service.answer(query["text"], clean_jobs).answer,
            clean_jobs,
        ),
        "gold_context_rag": (
            answer_service.answer(query["text"], gold_jobs).answer,
            gold_jobs,
        ),
    }
    results: dict[str, dict] = {}
    for system, (answer, context) in generated.items():
        evaluation = _evaluate_answer(
            judge,
            query=query["text"],
            answer=answer,
            nuggets=nuggets[topic_id],
            context_jobs=context,
        )
        results[system] = {
            "query_id": query["query_id"],
            "topic_id": topic_id,
            "variant": query["variant"],
            "answer": answer,
            **evaluation,
        }
    return {"index": index, "results": results}


def _run_rag_query_tasks(
    tasks: list[Callable[[], dict]],
    *,
    split: str,
    config: RefillWindowConfig,
) -> dict[str, list[dict]]:
    query_results = run_refill_window(
        tasks,
        config=config,
        label=f"rag-eval:{split}",
    )
    ordered = sorted(query_results, key=lambda item: item["index"])
    if [item["index"] for item in ordered] != list(range(len(tasks))):
        raise RuntimeError("RAG query evaluation returned missing or duplicate indices")
    rows_by_system: dict[str, list[dict]] = {
        system: [] for system in RAG_SYSTEMS
    }
    for item in ordered:
        if set(item["results"]) != set(RAG_SYSTEMS):
            raise RuntimeError("RAG query evaluation returned an incomplete system result")
        for system in RAG_SYSTEMS:
            rows_by_system[system].append(item["results"][system])
    print(f"[rag-eval] completed={len(ordered)}/{len(tasks)}")
    return rows_by_system


def run_rag_eval(
    *,
    split: str = "dev",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    generator_model: str = DEFAULT_ANSWER_MODEL,
    judge_model: str,
    retriever_system: str = "dense",
    top_k: int = 5,
    allow_test: bool = False,
    bootstrap_samples: int = 2000,
    bootstrap_seed: int = 20260819,
    bootstrap_alpha: float = 0.05,
    generation_temperature: int = GENERATION_TEMPERATURE,
    clean_index_dir: Path | None = None,
) -> dict:
    output_dir = Path(output_dir)
    if split not in {"dev", "test"}:
        raise ValueError("split must be dev or test")
    if retriever_system not in {"dense", "hybrid"}:
        raise ValueError("retriever_system must be dense or hybrid")
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    if (
        split != "test"
        and (
            type(generation_temperature) is not int
            or generation_temperature != GENERATION_TEMPERATURE
        )
    ):
        raise ValueError("generation_temperature must be the frozen benchmark value 0")

    integrity = assert_evaluation_integrity(output_dir, clean_index_dir=clean_index_dir)
    if split == "test":
        test_protocol = assert_test_evaluation_protocol(
            output_dir,
            evaluator="RAG",
            runtime_settings=rag_runtime_settings(
                retriever_system=retriever_system,
                top_k=top_k,
                generator_model=generator_model,
                judge_model=judge_model,
                generation_temperature=generation_temperature,
                bootstrap_seed=bootstrap_seed,
                bootstrap_samples=bootstrap_samples,
                bootstrap_alpha=bootstrap_alpha,
            ),
        )
        consume_test_lock(output_dir, evaluator="RAG", allow_test=allow_test)
    else:
        test_protocol = None

    topic_rows = {row["topic_id"]: row for row in _read_jsonl(output_dir / "topics.jsonl") if row["split"] == split}
    topic_family_ids = {topic_id: row["family_id"] for topic_id, row in topic_rows.items()}
    query_rows = [row for row in _read_jsonl(output_dir / "queries.jsonl") if row["topic_id"] in topic_rows]
    qrel_rows = _read_jsonl(output_dir / "qrels.silver.jsonl")
    nugget_rows = _read_jsonl(output_dir / "nuggets.silver.jsonl")

    qrels: dict[str, list[dict]] = defaultdict(list)
    for row in qrel_rows:
        qrels[row["topic_id"]].append(row)
    nuggets: dict[str, list[Nugget]] = defaultdict(list)
    for row in nugget_rows:
        nuggets[row["topic_id"]].append(Nugget(
            topic_id=row["topic_id"], nugget_id=row["nugget_id"], text=row["text"], normalized_text=row["normalized_text"],
            support_job_keys=tuple(row["support_job_keys"]), support_count=int(row["support_count"]),
            prevalence=float(row["prevalence"]), weight=float(row["weight"]), importance=row["importance"],
        ))

    corpus = load_corpus_jobs(source="vietjobs")
    corpus_by_key = {job.job_key: job for job in corpus}
    sidecar_dir = Path(clean_index_dir or configured_clean_index_dir())
    clean_ranker = CleanBenchmarkDenseRanker(sidecar_dir)
    pooler = PoolingService(corpus, dense_ranker=clean_ranker)
    api_key = getattr(settings, "CKEY_API_KEY", "")
    if not api_key:
        raise RuntimeError("CKEY_API_KEY is required")
    concurrency_config = _rag_eval_concurrency_config()
    retrieval_lock = threading.Lock()
    worker_local = threading.local()

    def worker_services() -> tuple[CareerAnswerService, OpenAI, JudgeClient]:
        services = getattr(worker_local, "services", None)
        if services is None:
            services = (
                CareerAnswerService(
                    model_name=generator_model,
                    temperature=generation_temperature,
                ),
                OpenAI(
                    api_key=api_key,
                    base_url=getattr(settings, "CKEY_BASE_URL", "") or None,
                ),
                JudgeClient(judge_model),
            )
            worker_local.services = services
        return services

    tasks: list[Callable[[], dict]] = []
    for index, query in enumerate(query_rows):
        def evaluate(index: int = index, query: dict = query) -> dict:
            answer_service, no_rag_client, judge = worker_services()
            return _evaluate_query(
                index,
                query,
                retriever_system=retriever_system,
                top_k=top_k,
                clean_ranker=clean_ranker,
                pooler=pooler,
                retrieval_lock=retrieval_lock,
                corpus_by_key=corpus_by_key,
                qrels=qrels,
                nuggets=nuggets,
                generator_model=generator_model,
                generation_temperature=generation_temperature,
                answer_service=answer_service,
                no_rag_client=no_rag_client,
                judge=judge,
            )

        tasks.append(evaluate)
    rows_by_system = _run_rag_query_tasks(
        tasks,
        split=split,
        config=concurrency_config,
    )

    report = {
        "split": split, "generator_model": generator_model, "judge_model": judge_model,
        "retriever_system": retriever_system, "bootstrap_unit": "family", "bootstrap_seed": bootstrap_seed,
        "generation_temperature": generation_temperature,
        "bootstrap_samples": bootstrap_samples, "bootstrap_alpha": bootstrap_alpha,
        "family_count": len(set(topic_family_ids.values())),
        "clean_index_dir": str(sidecar_dir), "integrity": integrity,
        "frozen_test_protocol": test_protocol,
        "comparison_interpretation": "system-level; no_rag and context-RAG prompts are not a causal retrieval-only ablation",
        "model_identity": _model_identity(generator_model, judge_model),
        "qrel_ground_truth_status": "SILVER_LLM_GENERATED_NOT_HUMAN_GOLD",
        "human_calibration_status": "NOT_PERFORMED",
        "systems": {},
    }
    metric_names = ("weighted_nugget_coverage", "faithfulness", "unsupported_claim_rate", "citation_coverage", "citation_support_rate", "context_utilization")
    for system in RAG_SYSTEMS:
        by_topic: dict[str, list[dict]] = defaultdict(list)
        for row in rows_by_system[system]:
            by_topic[row["topic_id"]].append(row)
        macro, robustness_report = {}, {}
        for metric in metric_names:
            macro[metric] = _rag_metric_summary(
                by_topic,
                metric,
                topic_family_ids,
                bootstrap_samples=bootstrap_samples,
                bootstrap_seed=bootstrap_seed,
                bootstrap_alpha=bootstrap_alpha,
            )
            if metric == "weighted_nugget_coverage":
                robustness_report[metric] = {topic_id: robustness([float(row[metric]) for row in rows]) for topic_id, rows in by_topic.items()}
        report["systems"][system] = {"macro": macro, "robustness": robustness_report, "queries": rows_by_system[system]}

    _write_json(output_dir / "reports" / f"rag_{split}.json", report)
    return report
