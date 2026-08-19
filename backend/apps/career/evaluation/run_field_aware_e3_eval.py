from __future__ import annotations

import ast
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
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

OUTPUT_PATH = BENCHMARK_DIR / "field_aware_e3_results.json"

MAX_RANK = 20
RRF_K = 60

CATEGORY_PREFIX = "tìm việc trong lĩnh vực "
LOCATION_PREFIX = "tìm việc tại "
AT_CUE = " tại "
SKILL_CUE = " cần kỹ năng "


@dataclass(frozen=True, slots=True)
class ParsedCareerQuery:
    raw_query: str
    category_key: str | None
    location_key: str | None
    skill_query: str | None


def _normalize_text(value: str) -> str:
    return unicodedata.normalize("NFKC", value).casefold().strip()


def _normalize_key(value: str | None) -> str | None:
    if value is None:
        return None

    text = _normalize_text(value)
    text = re.sub(r"\s+", " ", text)

    return text or None


def _humanize_category(value: str) -> str:
    return value.replace("_", " ")


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


def _parse_locations(value: str | None) -> list[str]:
    if not value:
        return []

    result: list[str] = []

    for part in value.split(","):
        normalized = _normalize_key(part)

        if normalized:
            result.append(normalized)

    return list(dict.fromkeys(result))


def _tokenize(text: str) -> list[str]:
    normalized = _normalize_text(text)

    normalized = re.sub(
        r"[^\w+#./-]+",
        " ",
        normalized,
        flags=re.UNICODE,
    )

    return [token for token in normalized.split() if token]


def _rrf_fuse(
    first: list[str],
    second: list[str],
    *,
    top_k: int,
    rrf_k: int = RRF_K,
) -> list[str]:
    scores: dict[str, float] = defaultdict(float)

    for rank, doc_id in enumerate(first, start=1):
        scores[doc_id] += 1.0 / (rrf_k + rank)

    for rank, doc_id in enumerate(second, start=1):
        scores[doc_id] += 1.0 / (rrf_k + rank)

    ranked = sorted(
        scores,
        key=lambda doc_id: (
            -scores[doc_id],
            doc_id,
        ),
    )

    return ranked[:top_k]


class VietJobsFieldAwareE3Evaluator:
    """
    E3 diagnostic evaluator.

    IMPORTANT:
    - Retrieval uses only natural-language query text + corpus metadata.
    - It never reads query_item["filters"] for retrieval.
    - It never reads qrels until metric calculation.
    - Benchmark qrels are themselves constructed from exact metadata pairs,
      so metadata-aware filtering is highly aligned with benchmark design.
      Treat E3 as a field-aware ablation, not proof of generalization.
    """

    def __init__(self) -> None:
        self.source = VietJobsSource()

        self.queries = self._load_queries()
        self.qrels = self._load_qrels()
        self.dense_results = self._load_dense_results()

        self.records: dict[str, Any] = {}
        self.category_to_docs: dict[str, set[str]] = defaultdict(set)
        self.location_to_docs: dict[str, set[str]] = defaultdict(set)
        self.category_phrase_to_key: dict[str, str] = {}

        (
            self.bm25,
            self.bm25_doc_ids,
            self.bm25_doc_id_to_index,
        ) = self._build_corpus_indexes()

    def run(self) -> dict:
        e2_1_metrics = []
        e3_metrics = []
        e2_1_family = defaultdict(list)
        e3_family = defaultdict(list)
        parse_stats = defaultdict(int)
        query_results = []

        for index, query_item in enumerate(self.queries, start=1):
            query_id = query_item["query_id"]
            query = query_item["query"]
            family = query_item["family"]
            relevant_doc_ids = self.qrels.get(query_id, set())
            dense_ranked = list(self.dense_results[query_id]["retrieved"][:MAX_RANK])
            parsed = self._parse_query(query)

            if parsed.category_key:
                parse_stats["category_parsed"] += 1

            if parsed.location_key:
                parse_stats["location_parsed"] += 1

            if parsed.skill_query:
                parse_stats["skill_parsed"] += 1

            e2_1_ranked = self._e2_1_rank(dense_ranked=dense_ranked, parsed=parsed)
            e3_ranked, route = self._e3_rank(dense_ranked=dense_ranked, parsed=parsed)
            parse_stats[f"route:{route}"] += 1
            e2_1_metric = evaluate_ranking(e2_1_ranked, relevant_doc_ids)
            e3_metric = evaluate_ranking(e3_ranked, relevant_doc_ids)
            e2_1_metrics.append(e2_1_metric)
            e3_metrics.append(e3_metric)
            e2_1_family[family].append(e2_1_metric)
            e3_family[family].append(e3_metric)

            query_results.append(
                {
                    "query_id": query_id,
                    "query": query,
                    "family": family,
                    "parsed": {
                        "category_key": (parsed.category_key),
                        "location_key": (parsed.location_key),
                        "skill_query": (parsed.skill_query),
                    },
                    "route": route,
                    "num_relevant": len(relevant_doc_ids),
                    "e2_1_retrieved": (e2_1_ranked),
                    "e3_retrieved": (e3_ranked),
                    "e2_1_metrics": (e2_1_metric),
                    "e3_metrics": e3_metric,
                }
            )

            if index % 25 == 0:
                print(f"Evaluated {index}/{len(self.queries)} queries")

        payload = {
            "config": {
                "max_rank": MAX_RANK,
                "rrf_k": RRF_K,
                "dense_source": str(DENSE_RESULTS_PATH),
                "retrieval_inputs": ("natural-language query + corpus metadata only"),
                "uses_query_filters_for_retrieval": (False),
                "uses_qrels_for_retrieval": False,
                "benchmark_alignment_warning": (
                    "Benchmark qrels are generated "
                    "from exact category/location/"
                    "technical_skill metadata pairs. "
                    "E3 explicitly exploits those "
                    "same field types after parsing "
                    "the natural-language query, so "
                    "large gains may partly reflect "
                    "benchmark/task alignment."
                ),
                "parse_stats": dict(parse_stats),
            },
            "e2_1_control": self._summary(
                e2_1_metrics,
                e2_1_family,
            ),
            "e3_field_aware": self._summary(
                e3_metrics,
                e3_family,
            ),
            "queries": query_results,
        }

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with OUTPUT_PATH.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

        return payload

    def _build_corpus_indexes(self) -> tuple[BM25Okapi, list[str], dict[str, int]]:
        tokenized_corpus = []
        bm25_doc_ids = []

        for record in self.source.iter_records():
            doc_id = f"{record.source}:{record.source_job_id}"
            self.records[doc_id] = record
            category = _normalize_key(record.category_key)

            if category:
                self.category_to_docs[category].add(doc_id)
                self.category_phrase_to_key[_humanize_category(category)] = category

            for location in _parse_locations(record.location_key):
                self.location_to_docs[location].add(doc_id)

            skills = _parse_list_value(record.metadata.get("technical_skills"))
            if not skills:
                continue

            tokens = _tokenize(" ; ".join(skills))
            if not tokens:
                continue

            bm25_doc_ids.append(doc_id)
            tokenized_corpus.append(tokens)

        if not tokenized_corpus:
            raise RuntimeError("No skill corpus available.")

        bm25_doc_id_to_index = {doc_id: index for index, doc_id in enumerate(bm25_doc_ids)}

        print(
            "Built E3 indexes: "
            f"{len(self.records)} jobs, "
            f"{len(bm25_doc_ids)} "
            "skill-bearing jobs, "
            f"{len(self.category_to_docs)} "
            "categories, "
            f"{len(self.location_to_docs)} "
            "locations"
        )

        return (BM25Okapi(tokenized_corpus), bm25_doc_ids, bm25_doc_id_to_index)

    def _parse_query(self, query: str) -> ParsedCareerQuery:
        normalized = _normalize_text(query)

        normalized = normalized.rstrip(" \t\r\n.")

        category_key = None
        location_key = None
        skill_query = None

        if normalized.startswith(CATEGORY_PREFIX):
            body = normalized[len(CATEGORY_PREFIX) :]

            if SKILL_CUE in body:
                category_phrase, skill = body.split(SKILL_CUE, 1)
                category_phrase = category_phrase.strip()
                category_key = self.category_phrase_to_key.get(category_phrase)
                skill_query = skill.strip() or None

            elif AT_CUE in body:
                category_phrase, location = body.split(AT_CUE, 1)
                category_phrase = category_phrase.strip()
                category_key = self.category_phrase_to_key.get(category_phrase)
                location_key = _normalize_key(location)

        elif normalized.startswith(LOCATION_PREFIX):
            body = normalized[len(LOCATION_PREFIX) :]
            if SKILL_CUE in body:
                location, skill = body.split(SKILL_CUE, 1)
                location_key = _normalize_key(location)
                skill_query = skill.strip() or None

        return ParsedCareerQuery(
            raw_query=query,
            category_key=category_key,
            location_key=location_key,
            skill_query=skill_query,
        )

    def _e2_1_rank(self, *, dense_ranked: list[str], parsed: ParsedCareerQuery) -> list[str]:
        if not parsed.skill_query:
            return dense_ranked

        bm25_ranked = self._search_bm25(skill_query=parsed.skill_query, allowed_doc_ids=None, top_k=MAX_RANK)
        return _rrf_fuse(dense_ranked, bm25_ranked, top_k=MAX_RANK)

    def _e3_rank(self, *, dense_ranked: list[str], parsed: ParsedCareerQuery) -> tuple[list[str], str]:
        if parsed.category_key and parsed.location_key and not parsed.skill_query:
            allowed = self.category_to_docs.get(parsed.category_key, set()) & self.location_to_docs.get(parsed.location_key, set())
            return (
                self._metadata_filtered_dense(
                    dense_ranked=dense_ranked,
                    allowed_doc_ids=allowed,
                    top_k=MAX_RANK,
                ),
                "category_location_filter+dense",
            )

        if parsed.category_key and parsed.skill_query:
            allowed = self.category_to_docs.get(parsed.category_key, set())
            bm25_ranked = self._search_bm25(skill_query=parsed.skill_query, allowed_doc_ids=allowed, top_k=MAX_RANK)

            return (bm25_ranked, "category_filter+skill_bm25")

        if parsed.location_key and parsed.skill_query:
            allowed = self.location_to_docs.get(parsed.location_key, set())
            dense_filtered = [doc_id for doc_id in dense_ranked if doc_id in allowed]
            bm25_ranked = self._search_bm25(skill_query=parsed.skill_query, allowed_doc_ids=allowed, top_k=MAX_RANK,)
            fused = _rrf_fuse(dense_filtered, bm25_ranked, top_k=MAX_RANK)
            return (fused, "location_filter+dense+skill_bm25")

        return (dense_ranked, "dense_fallback")

    def _metadata_filtered_dense(
        self,
        *,
        dense_ranked: list[str],
        allowed_doc_ids: set[str],
        top_k: int,
    ) -> list[str]:
        if not allowed_doc_ids:
            return []

        ranked = [doc_id for doc_id in dense_ranked if doc_id in allowed_doc_ids]

        seen = set(ranked)

        for doc_id in sorted(allowed_doc_ids):
            if doc_id in seen:
                continue

            ranked.append(doc_id)
            seen.add(doc_id)

            if len(ranked) >= top_k:
                break

        return ranked[:top_k]

    def _search_bm25(
        self,
        *,
        skill_query: str,
        allowed_doc_ids: set[str] | None,
        top_k: int,
    ) -> list[str]:
        query_tokens = _tokenize(skill_query)

        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        if allowed_doc_ids is None:
            candidate_indices = np.flatnonzero(scores > 0)
        else:
            indices = [
                self.bm25_doc_id_to_index[doc_id] for doc_id in allowed_doc_ids if doc_id in self.bm25_doc_id_to_index
            ]

            if not indices:
                return []

            candidate_indices = np.asarray(
                indices,
                dtype=np.int64,
            )

            candidate_indices = candidate_indices[scores[candidate_indices] > 0]

        if len(candidate_indices) == 0:
            return []

        limit = min(top_k, len(candidate_indices))
        candidate_scores = scores[candidate_indices]
        if limit < len(candidate_indices):
            local = np.argpartition(-candidate_scores, limit - 1)[:limit]
            candidate_indices = candidate_indices[local]

        ranked_indices = candidate_indices[np.argsort(-scores[candidate_indices], kind="stable")]
        return [self.bm25_doc_ids[int(index)] for index in ranked_indices[:top_k]]

    @staticmethod
    def _summary(metrics, family_metrics) -> dict:
        return {
            "overall": mean_metrics(metrics),
            "by_family": {family: mean_metrics(values) for family, values in family_metrics.items()},
        }

    @staticmethod
    def _load_queries() -> list[dict]:
        items = []

        with QUERIES_PATH.open(encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if line:
                    items.append(json.loads(line))

        return items

    @staticmethod
    def _load_qrels() -> dict[str, set[str]]:
        qrels = defaultdict(set)
        with QRELS_PATH.open(encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                item = json.loads(line)
                if item.get("relevance", 0) > 0:
                    qrels[item["query_id"]].add(item["doc_id"])

        return dict(qrels)

    @staticmethod
    def _load_dense_results() -> dict[str, dict]:
        if not DENSE_RESULTS_PATH.exists():
            raise FileNotFoundError(f"Missing E1-small results: {DENSE_RESULTS_PATH}")

        with DENSE_RESULTS_PATH.open(encoding="utf-8") as file:
            payload = json.load(file)

        return {item["query_id"]: item for item in payload["queries"]}


def _print_summary(name: str, summary: dict) -> None:
    print()
    print(f"=== {name} ===")

    for metric, value in summary["overall"].items():
        print(f"{metric}: {value:.4f}")

    print()
    print("=== By family ===")

    for family, metrics in summary["by_family"].items():
        print()
        print(family)

        for metric, value in metrics.items():
            print(f"  {metric}: {value:.4f}")


def _print_delta(old: dict, new: dict) -> None:
    print()
    print("=== E3 - E2.1 DELTA ===")

    for metric in old["overall"]:
        delta = new["overall"][metric] - old["overall"][metric]

        print(f"{metric}: {delta:+.4f}")

    print()
    print("=== Delta by family ===")

    for family in old["by_family"]:
        print()
        print(family)

        for metric in old["by_family"][family]:
            delta = new["by_family"][family][metric] - old["by_family"][family][metric]

            print(f"  {metric}: {delta:+.4f}")


def main() -> None:
    evaluator = VietJobsFieldAwareE3Evaluator()

    result = evaluator.run()

    print()
    print("=== PARSE STATS ===")

    for key, value in sorted(result["config"]["parse_stats"].items()):
        print(f"{key}: {value}")

    _print_summary("E2.1 CONTROL", result["e2_1_control"])
    _print_summary("E3 FIELD-AWARE", result["e3_field_aware"])
    _print_delta(result["e2_1_control"], result["e3_field_aware"])
    print()
    print(
        "WARNING: benchmark qrels are "
        "constructed from the same metadata "
        "field pairs exploited by E3. Treat "
        "large gains as a field-aware "
        "diagnostic until validated on "
        "free-form held-out queries."
    )

    print()
    print(f"Saved results to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
