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

# Important:
# Use the saved E1-small result, not dense_results.json, because later
# encoder ablations may overwrite the default dense result file.
DENSE_RESULTS_PATH = BENCHMARK_DIR / "dense_results_e1_small.json"

OUTPUT_PATH = BENCHMARK_DIR / "skill_hybrid_results.json"

MAX_RANK = 20
RRF_K = 60

# E2 is intentionally skill-aware:
# the lexical branch is only allowed to influence queries that explicitly
# express skill intent in the natural-language query itself.
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


def _tokenize(text: str) -> list[str]:
    """
    Lightweight multilingual lexical tokenizer.

    - Unicode NFKC normalization
    - case-insensitive via casefold()
    - preserves useful technical punctuation in tokens:
      C++, C#, ASP.NET, HTTP/2, CI/CD, etc.
    """
    normalized = unicodedata.normalize(
        "NFKC",
        text,
    ).casefold()

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


def _has_skill_intent(query: str) -> bool:
    normalized = unicodedata.normalize(
        "NFKC",
        query,
    ).casefold()

    return SKILL_QUERY_CUE in normalized


def _rrf_fuse(
    dense_ranked: list[str],
    lexical_ranked: list[str],
    *,
    top_k: int,
    rrf_k: int = RRF_K,
) -> list[str]:
    """
    Reciprocal Rank Fusion.

    score(doc) =
        1 / (rrf_k + dense_rank)
        +
        1 / (rrf_k + lexical_rank)

    Equal branch weights are deliberate for the first E2 ablation.
    Do not tune weights on the same 300-query benchmark yet.
    """
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


class VietJobsSkillHybridEvaluator:
    """
    E2 evaluation-only retriever.

    Dense branch:
        frozen E1-small rankings already saved in
        dense_results_e1_small.json.

    Lexical branch:
        one BM25 document per job containing ONLY
        metadata["technical_skills"].

    Fusion:
        equal-weight RRF, k=60.

    This intentionally does not modify production CareerRetriever yet.
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
        hybrid_metrics: list[
            dict[str, float]
        ] = []

        hybrid_family_metrics: dict[
            str,
            list[dict[str, float]],
        ] = defaultdict(list)

        dense_metrics: list[
            dict[str, float]
        ] = []

        dense_family_metrics: dict[
            str,
            list[dict[str, float]],
        ] = defaultdict(list)

        lexical_metrics: list[
            dict[str, float]
        ] = []

        lexical_family_metrics: dict[
            str,
            list[dict[str, float]],
        ] = defaultdict(list)

        query_results: list[dict] = []

        skill_query_count = 0

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
            dense_family_metrics[
                family
            ].append(
                dense_metric
            )

            skill_intent = _has_skill_intent(
                query
            )

            if skill_intent:
                skill_query_count += 1

                lexical_ranked = (
                    self._search_bm25(
                        query=query,
                        top_k=MAX_RANK,
                    )
                )

                hybrid_ranked = _rrf_fuse(
                    dense_ranked,
                    lexical_ranked,
                    top_k=MAX_RANK,
                )
            else:
                # Important control:
                # category_location has no explicit skill intent,
                # so E2 must preserve the E1 dense ranking exactly.
                lexical_ranked = []
                hybrid_ranked = dense_ranked

            lexical_metric = evaluate_ranking(
                lexical_ranked,
                relevant_doc_ids,
            )

            hybrid_metric = evaluate_ranking(
                hybrid_ranked,
                relevant_doc_ids,
            )

            lexical_metrics.append(
                lexical_metric
            )
            lexical_family_metrics[
                family
            ].append(
                lexical_metric
            )

            hybrid_metrics.append(
                hybrid_metric
            )
            hybrid_family_metrics[
                family
            ].append(
                hybrid_metric
            )

            query_results.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "family": family,
                    "skill_intent": (
                        skill_intent
                    ),
                    "num_relevant": len(
                        relevant_doc_ids
                    ),
                    "dense_retrieved": (
                        dense_ranked
                    ),
                    "bm25_skill_retrieved": (
                        lexical_ranked
                    ),
                    "hybrid_retrieved": (
                        hybrid_ranked
                    ),
                    "dense_metrics": (
                        dense_metric
                    ),
                    "bm25_skill_metrics": (
                        lexical_metric
                    ),
                    "hybrid_metrics": (
                        hybrid_metric
                    ),
                }
            )

            if index % 25 == 0:
                print(
                    "Evaluated "
                    f"{index}/"
                    f"{len(self.queries)} "
                    "queries"
                )

        dense_summary = {
            "overall": mean_metrics(
                dense_metrics
            ),
            "by_family": {
                family: mean_metrics(
                    values
                )
                for family, values
                in dense_family_metrics.items()
            },
        }

        lexical_summary = {
            "overall": mean_metrics(
                lexical_metrics
            ),
            "by_family": {
                family: mean_metrics(
                    values
                )
                for family, values
                in lexical_family_metrics.items()
            },
        }

        hybrid_summary = {
            "overall": mean_metrics(
                hybrid_metrics
            ),
            "by_family": {
                family: mean_metrics(
                    values
                )
                for family, values
                in hybrid_family_metrics.items()
            },
        }

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
                "skill_query_count": (
                    skill_query_count
                ),
                "bm25_job_count": len(
                    self.bm25_doc_ids
                ),
                "note": (
                    "Dense candidate depth is "
                    "limited to the saved E1-small "
                    "top-20 rankings. This is an "
                    "initial E2 ablation, not the "
                    "final production hybrid."
                ),
            },
            "dense": dense_summary,
            "bm25_skill": lexical_summary,
            "hybrid": hybrid_summary,
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
        tokenized_corpus: list[
            list[str]
        ] = []

        doc_ids: list[str] = []

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

            doc_ids.append(doc_id)
            tokenized_corpus.append(
                tokens
            )

        if not tokenized_corpus:
            raise RuntimeError(
                "Could not build BM25 skill "
                "corpus: no technical skills "
                "were found."
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
        query: str,
        top_k: int,
    ) -> list[str]:
        query_tokens = _tokenize(
            query
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
    def _load_queries() -> list[dict]:
        if not QUERIES_PATH.exists():
            raise FileNotFoundError(
                "Benchmark queries not found: "
                f"{QUERIES_PATH}"
            )

        items: list[dict] = []

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
        if not QRELS_PATH.exists():
            raise FileNotFoundError(
                "Benchmark qrels not found: "
                f"{QRELS_PATH}"
            )

        qrels: dict[
            str,
            set[str],
        ] = defaultdict(set)

        with QRELS_PATH.open(
            encoding="utf-8",
        ) as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                item = json.loads(line)

                if (
                    item.get(
                        "relevance",
                        0,
                    )
                    > 0
                ):
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
                "Saved E1-small dense results "
                "not found: "
                f"{DENSE_RESULTS_PATH}"
            )

        with DENSE_RESULTS_PATH.open(
            encoding="utf-8",
        ) as file:
            payload = json.load(file)

        results = {
            item["query_id"]: item
            for item in payload["queries"]
        }

        if not results:
            raise RuntimeError(
                "E1-small dense result file "
                "contains no query results."
            )

        return results


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
    dense: dict,
    hybrid: dict,
) -> None:
    print()
    print(
        "=== HYBRID - DENSE DELTA ==="
    )

    for metric in dense[
        "overall"
    ]:
        delta = (
            hybrid["overall"][metric]
            - dense["overall"][metric]
        )

        print(
            f"{metric}: "
            f"{delta:+.4f}"
        )

    print()
    print(
        "=== Delta by family ==="
    )

    for family in dense[
        "by_family"
    ]:
        print()
        print(family)

        for metric in dense[
            "by_family"
        ][family]:
            delta = (
                hybrid["by_family"][
                    family
                ][metric]
                - dense["by_family"][
                    family
                ][metric]
            )

            print(
                f"  {metric}: "
                f"{delta:+.4f}"
            )


def main() -> None:
    evaluator = (
        VietJobsSkillHybridEvaluator()
    )

    result = evaluator.run()

    _print_summary(
        "E1 DENSE-SMALL CONTROL",
        result["dense"],
    )

    _print_summary(
        "BM25 TECHNICAL_SKILLS ONLY",
        result["bm25_skill"],
    )

    _print_summary(
        "E2 SKILL-AWARE HYBRID RRF",
        result["hybrid"],
    )

    _print_delta(
        result["dense"],
        result["hybrid"],
    )

    print()
    print(
        "Saved results to: "
        f"{OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()