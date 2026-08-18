from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from apps.career.chunking import JobKnowledgeChunker
from apps.career.embedding import CareerEmbeddingService
from apps.career.knowledge import JobKnowledgeBuilder

from .metrics import evaluate_ranking, mean_metrics
from .vietjobs import VietJobsSource


BACKEND_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = BACKEND_ROOT / "data" / "career_eval" / "benchmark"
CACHE_DIR = BACKEND_ROOT / "data" / "career_eval" / "cache"
QUERIES_PATH = BENCHMARK_DIR / "queries.jsonl"
QRELS_PATH = BENCHMARK_DIR / "qrels.jsonl"
RESULTS_PATH = BENCHMARK_DIR / "dense_results.json"
EMBEDDINGS_PATH = CACHE_DIR / "vietjobs_embeddings.npy"
CHUNK_DOC_INDICES_PATH = CACHE_DIR / "vietjobs_chunk_doc_indices.npy"
DOC_IDS_PATH = CACHE_DIR / "vietjobs_doc_ids.json"
MAX_RANK = 20


class VietJobsDenseEvaluator:
    def __init__(self) -> None:
        self.source = VietJobsSource()
        self.builder = JobKnowledgeBuilder()
        self.chunker = JobKnowledgeChunker()
        self.embedder = CareerEmbeddingService()

    def run(self, *, rebuild_index: bool = False) -> dict:
        embeddings, chunk_doc_indices, doc_ids = self._load_or_build_index(rebuild=rebuild_index)

        queries = self._load_queries()
        qrels = self._load_qrels()
        all_results: list[dict] = []
        metrics_only: list[dict[str, float]] = []
        family_metrics: dict[str, list[dict[str, float]]] = defaultdict(list)

        for index, query_item in enumerate(queries, start=1):
            query_id = query_item["query_id"]
            query_text = query_item["query"]
            relevant_doc_ids = qrels.get(query_id, set())

            ranked_doc_ids = self._search(query=query_text, embeddings=embeddings, chunk_doc_indices=chunk_doc_indices, doc_ids=doc_ids, top_k=MAX_RANK)

            metrics = evaluate_ranking(ranked_doc_ids, relevant_doc_ids)
            metrics_only.append(metrics)
            family = query_item["family"]
            family_metrics[family].append(metrics)

            all_results.append(
                {
                    "query_id": query_id,
                    "query": query_text,
                    "family": family,
                    "num_relevant": len(relevant_doc_ids),
                    "retrieved": ranked_doc_ids,
                    "metrics": metrics,
                }
            )

            if index % 25 == 0:
                print(f"Evaluated {index}/{len(queries)} queries")

        summary = {
            "overall": mean_metrics(metrics_only),
            "by_family": {family: mean_metrics(values) for family, values in family_metrics.items()},
            "num_queries": len(all_results),
        }

        payload = {
            "summary": summary,
            "queries": all_results,
        }

        RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

        with RESULTS_PATH.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

        return payload

    def _load_or_build_index(self, *, rebuild: bool) -> tuple[np.ndarray, np.ndarray, list[str]]:
        if not rebuild and EMBEDDINGS_PATH.exists() and CHUNK_DOC_INDICES_PATH.exists() and DOC_IDS_PATH.exists():
            print("Loading cached VietJobs dense index...")

            embeddings = np.load(EMBEDDINGS_PATH, mmap_mode="r")
            chunk_doc_indices = np.load(CHUNK_DOC_INDICES_PATH)

            with DOC_IDS_PATH.open("r", encoding="utf-8") as file:
                doc_ids = json.load(file)

            return embeddings, chunk_doc_indices, doc_ids

        print("Building VietJobs dense index...")

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        chunks = []
        chunk_doc_indices: list[int] = []
        doc_ids: list[str] = []

        for job_index, record in enumerate(self.source.iter_records()):
            document = self.builder.build(record)
            job_chunks = self.chunker.chunk(document)

            if not job_chunks:
                continue

            doc_id = f"{record.source}:{record.source_job_id}"

            current_doc_index = len(doc_ids)
            doc_ids.append(doc_id)
            chunks.extend(job_chunks)
            chunk_doc_indices.extend([current_doc_index] * len(job_chunks))

            if (job_index + 1) % 5000 == 0:
                print(f"Prepared {job_index + 1} jobs, {len(chunks)} chunks")

        print(f"Embedding {len(chunks)} chunks...")

        embeddings = self.embedder.embed_chunks(chunks)

        chunk_doc_indices_array = np.asarray(chunk_doc_indices, dtype=np.int32)

        np.save(EMBEDDINGS_PATH, embeddings)
        np.save(CHUNK_DOC_INDICES_PATH, chunk_doc_indices_array)

        with DOC_IDS_PATH.open("w", encoding="utf-8") as file:
            json.dump(doc_ids, file, ensure_ascii=False)

        print("Dense index cached.")

        return embeddings, chunk_doc_indices_array, doc_ids

    def _search(self, *, query: str, embeddings: np.ndarray, chunk_doc_indices: np.ndarray, doc_ids: list[str], top_k: int) -> list[str]:
        query_embedding = self.embedder.embed_query(query)
        chunk_scores = embeddings @ query_embedding
        job_scores = np.full(len(doc_ids), -np.inf, dtype=np.float32)

        np.maximum.at(job_scores, chunk_doc_indices, chunk_scores)
        limit = min(top_k, len(doc_ids))

        if limit == 0:
            return []

        candidate_indices = np.argpartition(-job_scores, limit - 1)[:limit]

        ranked_indices = candidate_indices[np.argsort(-job_scores[candidate_indices])]

        return [doc_ids[index] for index in ranked_indices]

    @staticmethod
    def _load_queries() -> list[dict]:
        if not QUERIES_PATH.exists():
            raise FileNotFoundError("Benchmark queries not found. Run build_benchmark first.")

        queries = []

        with QUERIES_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line:
                    queries.append(json.loads(line))

        return queries

    @staticmethod
    def _load_qrels() -> dict[str, set[str]]:
        if not QRELS_PATH.exists():
            raise FileNotFoundError("Benchmark qrels not found. Run build_benchmark first.")

        qrels: dict[str, set[str]] = defaultdict(set)

        with QRELS_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                item = json.loads(line)
                if item.get("relevance", 0) > 0:
                    qrels[item["query_id"]].add(item["doc_id"])

        return dict(qrels)


def main() -> None:
    evaluator = VietJobsDenseEvaluator()
    result = evaluator.run()
    print()
    print("=== Dense Retrieval Eval ===")

    for metric, value in result["summary"]["overall"].items():
        print(f"{metric}: {value:.4f}")

    print()
    print(f"Saved results to: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
