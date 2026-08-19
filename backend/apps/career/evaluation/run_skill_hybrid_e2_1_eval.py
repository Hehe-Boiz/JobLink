from __future__ import annotations

import ast
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

from .metrics import evaluate_ranking, mean_metrics
from .vietjobs import VietJobsSource


BACKEND_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = BACKEND_ROOT / "data" / "career_eval" / "benchmark"

QUERIES_PATH = BENCHMARK_DIR / "queries.jsonl"
QRELS_PATH = BENCHMARK_DIR / "qrels.jsonl"
DENSE_RESULTS_PATH = BENCHMARK_DIR / "dense_results_e1_small.json"

OUTPUT_PATH = (
    BENCHMARK_DIR
    / "skill_hybrid_e2_1_skill_query_results.json"
)

MAX_RANK = 20
RRF_K = 60
SKILL_QUERY_CUE = "cần kỹ năng"


def _parse_list_value(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, (list, tuple, set)):
        raw_items = list(value)

    elif isinstance(value, str):
        text = value.strip()

        if not text:
            return []

        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            parsed = text

        if isinstance(parsed, (list, tuple, set)):
            raw_items = list(parsed)
        else:
            raw_items = [parsed]

    else:
        raw_items = [value]

    result: list[str] = []

    for item in raw_items:
        text = str(item).strip()

        if text:
            result.append(text)

    return list(dict.fromkeys(result))


def _normalize_text(text: str) -> str:
    return unicodedata.normalize(
        "NFKC",
        text,
    ).casefold()


def _tokenize(text: str) -> list[str]:
    """
    Lightweight Unicode tokenizer for lexical retrieval.

    Keeps technical punctuation that can matter for terms such as:
    C++, C#, ASP.NET, HTTP/2, CI/CD.
    """
    normalized = _normalize_text(text)

    normalized = re.sub(
        r"[^\w+#./-]+",
        " ",
        normalized,
        flags=re.UNICODE,
    )

    return [
        token
        for token in normalized.split()
        if token
    ]


def _extract_skill_phrase(query: str) -> str | None:
    """
    Extract the explicit skill clause from the natural-language query.

    Example:
        "Tìm việc trong lĩnh vực logistics ... cần kỹ năng
         proficient in microsoft office."

        ->
        "proficient in microsoft office"

    This uses only the query text. It does NOT read benchmark filters
    or qrels, so it is not oracle leakage.
    """
    normalized = _normalize_text(query)

    cue_index = normalized.find(
        SKILL_QUERY_CUE
    )

    if cue_index < 0:
        return None

    start = (
        cue_index
        + len(SKILL_QUERY_CUE)
    )

    # NFKC + casefold do not change character count for the benchmark
    # cue used here, so the slice maps back to the original query.
    phrase = query[start:].strip()

    phrase = phrase.strip(
        " \t\r\n.,;:!?。！？；："
    )

    return phrase or None


def _rrf_fuse(
    dense_ranked: list[str],
    lexical_ranked: list[str],
    *,
    top_k: int,
    rrf_k: int = RRF_K,
) -> list[str]:
    scores: dict[str, float] = defaultdict(float)

    for rank, doc_id in enumerate(
        dense_ranked,
        start=1,
    ):
        scores[doc_id] += 1.0 / (
            rrf_k + rank
        )

    for rank, doc_id in enumerate(
        lexical_ranked,
        start=1,
    ):
        scores[doc_id] += 1.0 / (
            rrf_k + rank
        )

    ranked = sorted(
        scores,
        key=lambda doc_id: (
            -scores[doc_id],
            doc_id,
        ),
    )

    return ranked[:top_k]


class VietJobsSkillQueryHybridEvaluator:
    """
    Compare:

    E2:
        dense E1-small
        + BM25(technical_skills-only corpus, FULL natural query)
        + RRF

    E2.1:
        dense E1-small
        + BM25(technical_skills-only corpus, EXTRACTED skill phrase)
        + RRF

    Everything else stays fixed.
    """

    def __init__(self) -> None:
        self.source = VietJobsSource()

        self.queries = self._load_queries()
        self.qrels = self._load_qrels()
        self.dense_results = (
            self._load_dense_results()
        )

        (
            self.bm25,
            self.bm25_doc_ids,
        ) = self._build_skill_bm25()

    def run(self) -> dict:
        dense_metrics = []
        old_hybrid_metrics = []
        new_hybrid_metrics = []
        old_bm25_metrics = []
        new_bm25_metrics = []

        dense_family = defaultdict(list)
        old_hybrid_family = defaultdict(list)
        new_hybrid_family = defaultdict(list)
        old_bm25_family = defaultdict(list)
        new_bm25_family = defaultdict(list)

        query_results = []

        num_skill_queries = 0
        extraction_failures = 0

        for index, query_item in enumerate(
            self.queries,
            start=1,
        ):
            query_id = query_item["query_id"]
            query = query_item["query"]
            family = query_item["family"]

            relevant_doc_ids = self.qrels.get(
                query_id,
                set(),
            )

            dense_ranked = list(
                self.dense_results[
                    query_id
                ]["retrieved"][:MAX_RANK]
            )

            dense_metric = evaluate_ranking(
                dense_ranked,
                relevant_doc_ids,
            )

            dense_metrics.append(
                dense_metric
            )
            dense_family[
                family
            ].append(
                dense_metric
            )

            skill_phrase = _extract_skill_phrase(
                query
            )

            if skill_phrase is None:
                # No explicit skill clause:
                # preserve dense ranking exactly.
                old_bm25_ranked = []
                new_bm25_ranked = []
                old_hybrid_ranked = dense_ranked
                new_hybrid_ranked = dense_ranked

            else:
                num_skill_queries += 1

                old_bm25_ranked = (
                    self._search_bm25(
                        query_text=query,
                        top_k=MAX_RANK,
                    )
                )

                new_bm25_ranked = (
                    self._search_bm25(
                        query_text=skill_phrase,
                        top_k=MAX_RANK,
                    )
                )

                if not new_bm25_ranked:
                    extraction_failures += 1

                old_hybrid_ranked = _rrf_fuse(
                    dense_ranked,
                    old_bm25_ranked,
                    top_k=MAX_RANK,
                )

                new_hybrid_ranked = _rrf_fuse(
                    dense_ranked,
                    new_bm25_ranked,
                    top_k=MAX_RANK,
                )

            old_bm25_metric = evaluate_ranking(
                old_bm25_ranked,
                relevant_doc_ids,
            )

            new_bm25_metric = evaluate_ranking(
                new_bm25_ranked,
                relevant_doc_ids,
            )

            old_hybrid_metric = evaluate_ranking(
                old_hybrid_ranked,
                relevant_doc_ids,
            )

            new_hybrid_metric = evaluate_ranking(
                new_hybrid_ranked,
                relevant_doc_ids,
            )

            old_bm25_metrics.append(
                old_bm25_metric
            )
            new_bm25_metrics.append(
                new_bm25_metric
            )
            old_hybrid_metrics.append(
                old_hybrid_metric
            )
            new_hybrid_metrics.append(
                new_hybrid_metric
            )

            old_bm25_family[
                family
            ].append(
                old_bm25_metric
            )
            new_bm25_family[
                family
            ].append(
                new_bm25_metric
            )
            old_hybrid_family[
                family
            ].append(
                old_hybrid_metric
            )
            new_hybrid_family[
                family
            ].append(
                new_hybrid_metric
            )

            query_results.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "family": family,
                    "skill_phrase": skill_phrase,
                    "num_relevant": len(
                        relevant_doc_ids
                    ),
                    "dense_retrieved": dense_ranked,
                    "e2_bm25_full_query_retrieved": (
                        old_bm25_ranked
                    ),
                    "e2_1_bm25_skill_query_retrieved": (
                        new_bm25_ranked
                    ),
                    "e2_hybrid_retrieved": (
                        old_hybrid_ranked
                    ),
                    "e2_1_hybrid_retrieved": (
                        new_hybrid_ranked
                    ),
                    "dense_metrics": dense_metric,
                    "e2_bm25_metrics": (
                        old_bm25_metric
                    ),
                    "e2_1_bm25_metrics": (
                        new_bm25_metric
                    ),
                    "e2_hybrid_metrics": (
                        old_hybrid_metric
                    ),
                    "e2_1_hybrid_metrics": (
                        new_hybrid_metric
                    ),
                }
            )

            if index % 25 == 0:
                print(
                    f"Evaluated {index}/"
                    f"{len(self.queries)} queries"
                )

        payload = {
            "config": {
                "dense_source": str(
                    DENSE_RESULTS_PATH
                ),
                "bm25_field": (
                    "technical_skills"
                ),
                "fusion": "RRF",
                "rrf_k": RRF_K,
                "max_rank": MAX_RANK,
                "skill_query_cue": (
                    SKILL_QUERY_CUE
                ),
                "num_skill_queries": (
                    num_skill_queries
                ),
                "empty_skill_bm25_results": (
                    extraction_failures
                ),
                "bm25_job_count": len(
                    self.bm25_doc_ids
                ),
                "e2": (
                    "BM25 receives full natural query"
                ),
                "e2_1": (
                    "BM25 receives only skill phrase "
                    "extracted after 'cần kỹ năng'"
                ),
            },
            "dense": self._summary(
                dense_metrics,
                dense_family,
            ),
            "e2_bm25_full_query": self._summary(
                old_bm25_metrics,
                old_bm25_family,
            ),
            "e2_1_bm25_skill_query": self._summary(
                new_bm25_metrics,
                new_bm25_family,
            ),
            "e2_hybrid": self._summary(
                old_hybrid_metrics,
                old_hybrid_family,
            ),
            "e2_1_hybrid": self._summary(
                new_hybrid_metrics,
                new_hybrid_family,
            ),
            "queries": query_results,
        }

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_PATH.open(
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

    def _build_skill_bm25(
        self,
    ) -> tuple[BM25Okapi, list[str]]:
        tokenized_corpus = []
        doc_ids = []

        for record in self.source.iter_records():
            skills = _parse_list_value(
                record.metadata.get(
                    "technical_skills"
                )
            )

            if not skills:
                continue

            skill_text = " ; ".join(
                skills
            )

            tokens = _tokenize(
                skill_text
            )

            if not tokens:
                continue

            doc_id = (
                f"{record.source}:"
                f"{record.source_job_id}"
            )

            doc_ids.append(
                doc_id
            )
            tokenized_corpus.append(
                tokens
            )

        if not tokenized_corpus:
            raise RuntimeError(
                "No technical skills found "
                "for BM25 corpus."
            )

        print(
            "Built skill-only BM25 index: "
            f"{len(doc_ids)} jobs"
        )

        return (
            BM25Okapi(
                tokenized_corpus
            ),
            doc_ids,
        )

    def _search_bm25(
        self,
        *,
        query_text: str,
        top_k: int,
    ) -> list[str]:
        query_tokens = _tokenize(
            query_text
        )

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(
            query_tokens
        )

        positive_indices = np.flatnonzero(
            scores > 0
        )

        if len(positive_indices) == 0:
            return []

        limit = min(
            top_k,
            len(positive_indices),
        )

        if limit == len(
            positive_indices
        ):
            candidate_indices = (
                positive_indices
            )

        else:
            local_scores = scores[
                positive_indices
            ]

            selected_local = np.argpartition(
                -local_scores,
                limit - 1,
            )[:limit]

            candidate_indices = (
                positive_indices[
                    selected_local
                ]
            )

        ranked_indices = (
            candidate_indices[
                np.argsort(
                    -scores[
                        candidate_indices
                    ],
                    kind="stable",
                )
            ]
        )

        return [
            self.bm25_doc_ids[
                int(index)
            ]
            for index in ranked_indices
        ]

    @staticmethod
    def _summary(
        metrics,
        family_metrics,
    ) -> dict:
        return {
            "overall": mean_metrics(
                metrics
            ),
            "by_family": {
                family: mean_metrics(
                    values
                )
                for family, values
                in family_metrics.items()
            },
        }

    @staticmethod
    def _load_queries() -> list[dict]:
        items = []

        with QUERIES_PATH.open(
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if line:
                    items.append(
                        json.loads(line)
                    )

        return items

    @staticmethod
    def _load_qrels() -> dict[
        str,
        set[str],
    ]:
        qrels = defaultdict(set)

        with QRELS_PATH.open(
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                item = json.loads(line)

                if item.get(
                    "relevance",
                    0,
                ) > 0:
                    qrels[
                        item["query_id"]
                    ].add(
                        item["doc_id"]
                    )

        return dict(qrels)

    @staticmethod
    def _load_dense_results() -> dict[
        str,
        dict,
    ]:
        if not DENSE_RESULTS_PATH.exists():
            raise FileNotFoundError(
                "Missing saved E1-small results: "
                f"{DENSE_RESULTS_PATH}"
            )

        with DENSE_RESULTS_PATH.open(
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        return {
            item["query_id"]: item
            for item in payload["queries"]
        }


def _print_summary(
    name: str,
    summary: dict,
) -> None:
    print()
    print(
        f"=== {name} ==="
    )

    for metric, value in (
        summary["overall"].items()
    ):
        print(
            f"{metric}: {value:.4f}"
        )

    print()
    print("=== By family ===")

    for family, metrics in (
        summary["by_family"].items()
    ):
        print()
        print(family)

        for metric, value in (
            metrics.items()
        ):
            print(
                f"  {metric}: "
                f"{value:.4f}"
            )


def _print_delta(
    old_summary: dict,
    new_summary: dict,
) -> None:
    print()
    print(
        "=== E2.1 - E2 HYBRID DELTA ==="
    )

    for metric in old_summary[
        "overall"
    ]:
        delta = (
            new_summary["overall"][metric]
            - old_summary["overall"][metric]
        )

        print(
            f"{metric}: {delta:+.4f}"
        )

    print()
    print(
        "=== Delta by family ==="
    )

    for family in old_summary[
        "by_family"
    ]:
        print()
        print(family)

        for metric in old_summary[
            "by_family"
        ][family]:
            delta = (
                new_summary[
                    "by_family"
                ][family][metric]
                - old_summary[
                    "by_family"
                ][family][metric]
            )

            print(
                f"  {metric}: "
                f"{delta:+.4f}"
            )


def main() -> None:
    evaluator = (
        VietJobsSkillQueryHybridEvaluator()
    )

    result = evaluator.run()

    _print_summary(
        "E1 DENSE-SMALL CONTROL",
        result["dense"],
    )

    _print_summary(
        "E2 BM25 — FULL QUERY",
        result[
            "e2_bm25_full_query"
        ],
    )

    _print_summary(
        "E2.1 BM25 — SKILL PHRASE ONLY",
        result[
            "e2_1_bm25_skill_query"
        ],
    )

    _print_summary(
        "E2 HYBRID — FULL QUERY BM25",
        result["e2_hybrid"],
    )

    _print_summary(
        "E2.1 HYBRID — SKILL PHRASE BM25",
        result["e2_1_hybrid"],
    )

    _print_delta(
        result["e2_hybrid"],
        result["e2_1_hybrid"],
    )

    print()
    print(
        "Saved results to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()