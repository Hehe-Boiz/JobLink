from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from apps.career.embedding import CareerEmbeddingService

from .metrics import evaluate_ranking, mean_metrics
from .vietjobs import VietJobsSource


BACKEND_ROOT = Path(__file__).resolve().parents[3]

BENCHMARK_DIR = (
    BACKEND_ROOT
    / "data"
    / "career_eval"
    / "benchmark_freeform_v2"
)

CACHE_DIR = (
    BACKEND_ROOT
    / "data"
    / "career_eval"
    / "cache"
)

DEFAULT_EMBEDDINGS_PATH = (
    CACHE_DIR
    / "vietjobs_embeddings_e1_small.npy"
)

DEFAULT_CHUNK_DOC_INDICES_PATH = (
    CACHE_DIR
    / "vietjobs_chunk_doc_indices_e1_small.npy"
)

DEFAULT_DOC_IDS_PATH = (
    CACHE_DIR
    / "vietjobs_doc_ids_e1_small.json"
)

MAX_RANK = 20
DENSE_DOC_CANDIDATES = 100


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def _load_json(path: Path) -> dict:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def _load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                items.append(
                    json.loads(line)
                )

    return items


class FreeFormV2DenseEvaluator:
    def __init__(
        self,
        *,
        split: str,
        embeddings_path: Path,
        chunk_doc_indices_path: Path,
        doc_ids_path: Path,
    ) -> None:
        if split not in {
            "dev",
            "test",
        }:
            raise ValueError(
                "split must be dev or test"
            )

        self.split = split

        self.embeddings_path = Path(
            embeddings_path
        )

        self.chunk_doc_indices_path = Path(
            chunk_doc_indices_path
        )

        self.doc_ids_path = Path(
            doc_ids_path
        )

        self.embedder = (
            CareerEmbeddingService()
        )

        self.split_dir = (
            BENCHMARK_DIR
            / split
        )

        self.queries_path = (
            self.split_dir
            / "queries.jsonl"
        )

        self.qrels_path = (
            self.split_dir
            / "qrels.clusters.jsonl"
        )

        self.audit_path = (
            self.split_dir
            / "intents.audit.jsonl"
        )

        self.doc_to_cluster_path = (
            BENCHMARK_DIR
            / "doc_to_cluster.json"
        )

        self.manifest_path = (
            BENCHMARK_DIR
            / "manifest.json"
        )

        self.test_lock_path = (
            BENCHMARK_DIR
            / "test_lock.json"
        )

        self.results_path = (
            self.split_dir
            / "dense_e1_small_results.json"
        )

    def run(self) -> dict:
        self._verify_benchmark_files()
        self._verify_corpus_fingerprint()

        if self.split == "test":
            self._verify_test_lock()

        (
            embeddings,
            chunk_doc_indices,
            doc_ids,
        ) = self._load_dense_cache()

        doc_to_cluster = _load_json(
            self.doc_to_cluster_path
        )

        self._verify_doc_alignment(
            doc_ids=doc_ids,
            doc_to_cluster=doc_to_cluster,
        )

        queries = _load_jsonl(
            self.queries_path
        )

        qrels = (
            self._load_cluster_qrels()
        )

        audit_by_query = (
            self._load_audit_for_reporting()
        )

        all_metrics: list[
            dict[str, float]
        ] = []

        family_metrics: dict[
            str,
            list[dict[str, float]],
        ] = defaultdict(list)

        result_rows: list[dict] = []

        for index, query_item in enumerate(
            queries,
            start=1,
        ):
            query_id = (
                query_item["query_id"]
            )

            query_text = (
                query_item["query"]
            )

            relevant_clusters = (
                qrels.get(
                    query_id,
                    set(),
                )
            )

            ranked_doc_ids = (
                self._search_dense_docs(
                    query=query_text,
                    embeddings=embeddings,
                    chunk_doc_indices=(
                        chunk_doc_indices
                    ),
                    doc_ids=doc_ids,
                    top_k_docs=(
                        DENSE_DOC_CANDIDATES
                    ),
                )
            )

            ranked_clusters = (
                self._collapse_to_clusters(
                    ranked_doc_ids=(
                        ranked_doc_ids
                    ),
                    doc_to_cluster=(
                        doc_to_cluster
                    ),
                    top_k=MAX_RANK,
                )
            )

            metrics = evaluate_ranking(
                ranked_clusters,
                relevant_clusters,
            )

            all_metrics.append(
                metrics
            )

            audit = audit_by_query.get(
                query_id,
                {},
            )

            family = audit.get(
                "family",
                "unknown",
            )

            family_metrics[
                family
            ].append(
                metrics
            )

            result_rows.append(
                {
                    "query_id": query_id,
                    "query": query_text,
                    "num_relevant_clusters": (
                        len(
                            relevant_clusters
                        )
                    ),
                    "retrieved_clusters": (
                        ranked_clusters
                    ),
                    "metrics": metrics,
                }
            )

            if index % 25 == 0:
                print(
                    f"Evaluated {index}/"
                    f"{len(queries)} queries"
                )

        summary = {
            "split": self.split,
            "retrieval_system": (
                "E1 dense-small"
            ),
            "evaluation_unit": (
                "exact-duplicate cluster"
            ),
            "overall": (
                mean_metrics(
                    all_metrics
                )
            ),
            "by_family": {
                family: (
                    mean_metrics(
                        values
                    )
                )
                for family, values
                in family_metrics.items()
            },
            "num_queries": (
                len(
                    result_rows
                )
            ),
        }

        payload = {
            "summary": summary,
            "queries": result_rows,
        }

        with self.results_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                payload,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return payload

    def _verify_benchmark_files(
        self,
    ) -> None:
        required = (
            self.queries_path,
            self.qrels_path,
            self.audit_path,
            self.doc_to_cluster_path,
            self.manifest_path,
        )

        missing = [
            str(path)
            for path in required
            if not path.exists()
        ]

        if missing:
            raise FileNotFoundError(
                "Missing benchmark files. "
                "Build free-form v2 first:\n"
                + "\n".join(
                    missing
                )
            )

    def _verify_corpus_fingerprint(
        self,
    ) -> None:
        manifest = _load_json(
            self.manifest_path
        )

        expected_sha = (
            manifest[
                "dataset_fingerprint"
            ]["sha256"]
        )

        source = VietJobsSource()

        csv_path = (
            source._find_dataset_csv()
        )

        actual_sha = _sha256_file(
            csv_path
        )

        if actual_sha != expected_sha:
            raise RuntimeError(
                "VietJobs corpus SHA-256 "
                "does not match benchmark "
                "manifest. Refusing to compare "
                "against stale qrels.\n"
                f"Expected: {expected_sha}\n"
                f"Actual:   {actual_sha}"
            )

    def _verify_test_lock(
        self,
    ) -> None:
        if not self.test_lock_path.exists():
            raise FileNotFoundError(
                "Missing test_lock.json"
            )

        lock = _load_json(
            self.test_lock_path
        )

        checks = {
            "queries_sha256": (
                self.queries_path
            ),
            "qrels_clusters_sha256": (
                self.qrels_path
            ),
            "audit_sha256": (
                self.audit_path
            ),
            "doc_to_cluster_sha256": (
                self.doc_to_cluster_path
            ),
        }

        for key, path in checks.items():
            expected = lock[
                key
            ]

            actual = _sha256_file(
                path
            )

            if actual != expected:
                raise RuntimeError(
                    "Frozen TEST artifact "
                    f"changed: {path}\n"
                    f"Expected: {expected}\n"
                    f"Actual:   {actual}"
                )

    def _load_dense_cache(
        self,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        list[str],
    ]:
        required = (
            self.embeddings_path,
            self.chunk_doc_indices_path,
            self.doc_ids_path,
        )

        missing = [
            str(path)
            for path in required
            if not path.exists()
        ]

        if missing:
            raise FileNotFoundError(
                "Missing E1-small dense cache. "
                "This evaluator intentionally "
                "does not fall back to the "
                "default cache because that cache "
                "may have been overwritten by "
                "another model experiment.\n"
                "Missing:\n"
                + "\n".join(
                    missing
                )
            )

        print(
            "Loading frozen E1-small "
            "dense cache..."
        )

        embeddings = np.load(
            self.embeddings_path,
            mmap_mode="r",
        )

        chunk_doc_indices = np.load(
            self.chunk_doc_indices_path
        )

        with self.doc_ids_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            doc_ids = json.load(
                file
            )

        if embeddings.ndim != 2:
            raise RuntimeError(
                "Embeddings must be 2D."
            )

        if (
            len(
                chunk_doc_indices
            )
            != embeddings.shape[0]
        ):
            raise RuntimeError(
                "Chunk-index count does not "
                "match embedding rows."
            )

        if not doc_ids:
            raise RuntimeError(
                "Dense doc-id cache is empty."
            )

        if (
            int(
                chunk_doc_indices.max()
            )
            >= len(
                doc_ids
            )
        ):
            raise RuntimeError(
                "Chunk document index is "
                "out of bounds."
            )

        if (
            self.embedder.dimension
            != embeddings.shape[1]
        ):
            raise RuntimeError(
                "Embedding dimension does not "
                "match current E5-small query "
                "encoder.\n"
                f"Cache dim: {embeddings.shape[1]}\n"
                f"Query dim: {self.embedder.dimension}"
            )

        return (
            embeddings,
            chunk_doc_indices,
            doc_ids,
        )

    @staticmethod
    def _verify_doc_alignment(
        *,
        doc_ids: list[str],
        doc_to_cluster: dict[
            str,
            str,
        ],
    ) -> None:
        missing = [
            doc_id
            for doc_id in doc_ids
            if doc_id
            not in doc_to_cluster
        ]

        if missing:
            raise RuntimeError(
                "Dense-cache document IDs "
                "do not align with benchmark "
                "corpus. Example missing IDs: "
                f"{missing[:5]}"
            )

    def _search_dense_docs(
        self,
        *,
        query: str,
        embeddings: np.ndarray,
        chunk_doc_indices: np.ndarray,
        doc_ids: list[str],
        top_k_docs: int,
    ) -> list[str]:
        query_embedding = (
            self.embedder.embed_query(
                query
            )
        )

        chunk_scores = (
            embeddings
            @ query_embedding
        )

        job_scores = np.full(
            len(
                doc_ids
            ),
            -np.inf,
            dtype=np.float32,
        )

        np.maximum.at(
            job_scores,
            chunk_doc_indices,
            chunk_scores,
        )

        limit = min(
            top_k_docs,
            len(
                doc_ids
            ),
        )

        if limit == 0:
            return []

        candidate_indices = (
            np.argpartition(
                -job_scores,
                limit - 1,
            )[:limit]
        )

        ranked_indices = (
            candidate_indices[
                np.argsort(
                    -job_scores[
                        candidate_indices
                    ],
                    kind="stable",
                )
            ]
        )

        return [
            doc_ids[
                int(index)
            ]
            for index in ranked_indices
        ]

    @staticmethod
    def _collapse_to_clusters(
        *,
        ranked_doc_ids: list[str],
        doc_to_cluster: dict[
            str,
            str,
        ],
        top_k: int,
    ) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()

        for doc_id in ranked_doc_ids:
            cluster_id = (
                doc_to_cluster.get(
                    doc_id
                )
            )

            if cluster_id is None:
                continue

            if cluster_id in seen:
                continue

            seen.add(
                cluster_id
            )

            result.append(
                cluster_id
            )

            if len(
                result
            ) >= top_k:
                break

        return result

    def _load_cluster_qrels(
        self,
    ) -> dict[
        str,
        set[str],
    ]:
        qrels: dict[
            str,
            set[str],
        ] = defaultdict(set)

        for item in _load_jsonl(
            self.qrels_path
        ):
            if item.get(
                "relevance",
                0,
            ) > 0:
                qrels[
                    item["query_id"]
                ].add(
                    item[
                        "cluster_id"
                    ]
                )

        return dict(
            qrels
        )

    def _load_audit_for_reporting(
        self,
    ) -> dict[str, dict]:
        # IMPORTANT:
        # This file is used only AFTER ranking,
        # for stratified reporting. It is never
        # passed to the retrieval function.
        return {
            item["query_id"]: item
            for item in _load_jsonl(
                self.audit_path
            )
        }


def _print_summary(
    result: dict,
) -> None:
    summary = result[
        "summary"
    ]

    print()
    print(
        "=== FREE-FORM V2 "
        "DENSE E1-SMALL ==="
    )

    print(
        f"split: {summary['split']}"
    )

    for (
        metric,
        value,
    ) in summary[
        "overall"
    ].items():
        print(
            f"{metric}: "
            f"{value:.4f}"
        )

    print()
    print("=== By family ===")

    for (
        family,
        metrics,
    ) in summary[
        "by_family"
    ].items():
        print()
        print(
            family
        )

        for (
            metric,
            value,
        ) in metrics.items():
            print(
                f"  {metric}: "
                f"{value:.4f}"
            )


def parse_args() -> (
    argparse.Namespace
):
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate E1 dense-small on "
            "JobLink Free-Form Benchmark v2"
        )
    )

    parser.add_argument(
        "--split",
        choices=(
            "dev",
            "test",
        ),
        default="dev",
    )

    parser.add_argument(
        "--embeddings",
        type=Path,
        default=(
            DEFAULT_EMBEDDINGS_PATH
        ),
    )

    parser.add_argument(
        "--chunk-doc-indices",
        type=Path,
        default=(
            DEFAULT_CHUNK_DOC_INDICES_PATH
        ),
    )

    parser.add_argument(
        "--doc-ids",
        type=Path,
        default=(
            DEFAULT_DOC_IDS_PATH
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    evaluator = (
        FreeFormV2DenseEvaluator(
            split=args.split,
            embeddings_path=(
                args.embeddings
            ),
            chunk_doc_indices_path=(
                args.chunk_doc_indices
            ),
            doc_ids_path=(
                args.doc_ids
            ),
        )
    )

    result = evaluator.run()

    _print_summary(
        result
    )

    print()
    print(
        "Saved results to: "
        f"{evaluator.results_path}"
    )


if __name__ == "__main__":
    main()
