from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from django.conf import settings
from openai import OpenAI

from apps.career.answering import CareerAnswerService, DEFAULT_ANSWER_MODEL
from apps.career.retrieval import CareerEvidenceChunk, CareerRetrievedJob, CareerRetriever

from .build_benchmark import DEFAULT_OUTPUT_DIR
from .judges import JudgeClient
from .metrics import bootstrap_ci, robustness, weighted_nugget_scores
from .pooling import PoolingService, load_corpus_jobs
from .schema import CorpusJob, Nugget


def _read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _as_retrieved(job: CorpusJob, score: float = 1.0, evidence_per_job: int = 2) -> CareerRetrievedJob:
    evidence = tuple(
        CareerEvidenceChunk(
            chunk_id=f"{job.job_key}:{index}",
            section=chunk.get("section", ""),
            content=chunk.get("content", ""),
            distance=1.0 - score,
            similarity=score,
        )
        for index, chunk in enumerate(job.chunks[:evidence_per_job], start=1)
    )
    return CareerRetrievedJob(
        source=job.source,
        source_job_id=job.source_job_id,
        job_title=job.job_title,
        company_name="",
        location_key=job.location_key,
        experience_level=job.experience_level,
        employment_type=job.employment_type,
        category_key=job.category_key,
        published_at=None,
        source_url=None,
        score=score,
        evidence=evidence,
    )


def _no_rag_answer(model: str, query: str) -> str:
    api_key = getattr(settings, "CKEY_API_KEY", "")
    base_url = getattr(settings, "CKEY_BASE_URL", "")
    if not api_key:
        raise RuntimeError("CKEY_API_KEY is required")
    client = OpenAI(api_key=api_key, base_url=base_url or None)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": "Answer the Vietnamese career question concisely. Do not claim access to JobLink evidence or citations."},
            {"role": "user", "content": query},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _evaluate_answer(
    judge: JudgeClient,
    *,
    query: str,
    answer: str,
    nuggets: list[Nugget],
    context_jobs: list[CareerRetrievedJob],
) -> dict:
    context_blocks = []
    for index, job in enumerate(context_jobs, start=1):
        evidence = "\n".join(chunk.content for chunk in job.evidence)
        context_blocks.append(f"[J{index}] JOB_KEY={job.source}::{job.source_job_id}\n{evidence[:5000]}")
    nugget_block = "\n".join(f"{n.nugget_id}: {n.text}" for n in nuggets)
    context_text = "\n\n---\n\n".join(context_blocks) if context_blocks else "[NO CONTEXT]"
    data = judge.json_call(
        system=(
            "Evaluate a generated career answer against silver information nuggets and, when supplied, retrieved raw evidence. "
            "Return JSON only with keys: matched_nugget_ids (list), claim_count (int), supported_claim_count (int), "
            "unsupported_claim_count (int), citation_required_claim_count (int), cited_claim_count (int), "
            "citation_supported_count (int), context_used_job_keys (list). A claim is supported only if raw context clearly supports it. "
            "For no-context answers, supported_claim_count must be 0 because this benchmark cannot establish evidence grounding."
        ),
        user=(
            f"Question:\n{query}\n\nGold silver nuggets:\n{nugget_block}\n\n"
            f"Retrieved context:\n{context_text}\n\n"
            f"Generated answer:\n{answer}"
        ),
    )
    matched = set(str(item) for item in data.get("matched_nugget_ids", []))
    claim_count = max(0, int(data.get("claim_count", 0)))
    supported = max(0, int(data.get("supported_claim_count", 0)))
    unsupported = max(0, int(data.get("unsupported_claim_count", max(0, claim_count - supported))))
    citation_required = max(0, int(data.get("citation_required_claim_count", 0)))
    cited = max(0, int(data.get("cited_claim_count", 0)))
    citation_supported = max(0, int(data.get("citation_supported_count", 0)))
    nugget_scores = weighted_nugget_scores(matched, supported, nuggets)
    context_keys = {f"{job.source}::{job.source_job_id}" for job in context_jobs}
    used_keys = set(str(item) for item in data.get("context_used_job_keys", [])) & context_keys
    return {
        "matched_nugget_ids": sorted(matched),
        "weighted_nugget_precision": nugget_scores["precision"],
        "weighted_nugget_recall": nugget_scores["recall"],
        "weighted_nugget_f1": nugget_scores["f1"],
        "faithfulness": (supported / claim_count) if claim_count else 1.0,
        "unsupported_claim_rate": (unsupported / claim_count) if claim_count else 0.0,
        "citation_coverage": (cited / citation_required) if citation_required else (1.0 if not context_jobs else 0.0),
        "citation_support_rate": (citation_supported / cited) if cited else (1.0 if not context_jobs else 0.0),
        "context_utilization": (len(used_keys) / len(context_keys)) if context_keys else 0.0,
        "claim_count": claim_count,
    }


def run_rag_eval(
    *,
    split: str = "dev",
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    generator_model: str = DEFAULT_ANSWER_MODEL,
    judge_model: str,
    retriever_system: str = "dense",
    top_k: int = 5,
    allow_test: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    if split == "test" and not allow_test:
        raise RuntimeError("TEST is locked. Pass allow_test only after retrieval/generator/prompt are frozen.")
    if retriever_system not in {"dense", "hybrid"}:
        raise ValueError("retriever_system must be dense or hybrid")

    topic_rows = {row["topic_id"]: row for row in _read_jsonl(output_dir / "topics.jsonl") if row["split"] == split}
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

    corpus = load_corpus_jobs()
    corpus_by_key = {job.job_key: job for job in corpus}
    pooler = PoolingService(corpus)
    dense_retriever = CareerRetriever()
    answer_service = CareerAnswerService(model_name=generator_model)
    judge = JudgeClient(judge_model)
    systems = ("no_rag", "production_rag", "gold_context_rag")
    rows_by_system: dict[str, list[dict]] = {system: [] for system in systems}

    for query in query_rows:
        topic_id = query["topic_id"]
        if retriever_system == "dense":
            production_jobs = dense_retriever.search(query["text"], top_k=top_k, candidate_multiplier=20, evidence_per_job=2, source="vietjobs")
        else:
            bm25 = pooler.bm25(query["text"], max(top_k, 10))
            dense = pooler.dense(query["text"], max(top_k, 10))
            keys = pooler.rrf([bm25, dense], top_k)
            production_jobs = [_as_retrieved(corpus_by_key[key], score=1.0 - index * 0.001) for index, key in enumerate(keys) if key in corpus_by_key]

        gold_rows = sorted((row for row in qrels[topic_id] if int(row["grade"]) >= 2), key=lambda row: (-int(row["grade"]), f"{row['source']}::{row['source_job_id']}"))[:top_k]
        gold_jobs = [
            _as_retrieved(corpus_by_key[key])
            for row in gold_rows
            if (key := f"{row['source']}::{row['source_job_id']}") in corpus_by_key
        ]

        generated = {
            "no_rag": (_no_rag_answer(generator_model, query["text"]), []),
            "production_rag": (answer_service.answer(query["text"], production_jobs).answer, production_jobs),
            "gold_context_rag": (answer_service.answer(query["text"], gold_jobs).answer, gold_jobs),
        }
        for system, (answer, context) in generated.items():
            evaluation = _evaluate_answer(judge, query=query["text"], answer=answer, nuggets=nuggets[topic_id], context_jobs=context)
            rows_by_system[system].append({"query_id": query["query_id"], "topic_id": topic_id, "variant": query["variant"], "answer": answer, **evaluation})

    report = {"split": split, "generator_model": generator_model, "judge_model": judge_model, "retriever_system": retriever_system, "systems": {}}
    metric_names = ("weighted_nugget_precision", "weighted_nugget_recall", "weighted_nugget_f1", "faithfulness", "unsupported_claim_rate", "citation_coverage", "citation_support_rate", "context_utilization")
    for system in systems:
        by_topic: dict[str, list[dict]] = defaultdict(list)
        for row in rows_by_system[system]:
            by_topic[row["topic_id"]].append(row)
        macro = {}
        robustness_report = {}
        for metric in metric_names:
            topic_means = [mean(float(row[metric]) for row in rows) for rows in by_topic.values()]
            ci = bootstrap_ci(topic_means)
            macro[metric] = {"mean": mean(topic_means) if topic_means else 0.0, "ci95": list(ci)}
            if metric == "weighted_nugget_f1":
                robustness_report[metric] = {topic_id: robustness([float(row[metric]) for row in rows]) for topic_id, rows in by_topic.items()}
        report["systems"][system] = {"macro": macro, "robustness": robustness_report, "queries": rows_by_system[system]}

    _write_json(output_dir / "reports" / f"rag_{split}.json", report)
    return report
