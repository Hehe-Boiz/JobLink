from __future__ import annotations

import re
import json
import os
import tempfile
import unittest
import hashlib
import numpy as np
from collections import Counter
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
from django.test import override_settings
from apps.career.answering import CareerAnswerService

from . import audit as audit_module
from . import clean_index as clean_index_module
from . import evaluation_integrity as integrity_module
from . import evaluation_protocol as protocol_module
from . import judges as judges_module
from . import run_rag_eval as rag_eval_module
from . import run_retrieval_eval as retrieval_eval_module
from . import build_benchmark as build_benchmark_module
from .audit import (
    V3_REQUIRED_ARTIFACTS,
    artifact_sha256_map,
    audit_controls,
    audit_derived_label_leakage,
    audit_evidence_truncation,
    audit_qrels,
    audit_split,
    sha256_tree,
    verify_frozen_benchmark,
)
from .build_benchmark import (
    _assert_final_output_available,
    _create_building_directory,
    _finalize_candidate,
    build_benchmark,
)
from .clean_index import (
    CLEAN_EMBEDDING_DIMENSION,
    CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
    CLEAN_EMBEDDING_MODEL,
    CLEAN_INDEX_TYPE,
    CLEAN_INDEX_PROVENANCE_SCHEMA_VERSION,
    CleanBenchmarkDenseRanker,
    build_clean_embedding_index,
    clean_embedding_input,
    verify_clean_embedding_index,
)
from .evaluation_protocol import (
    BENCHMARK_KEYS,
    IMPLEMENTATION_KEYS,
    PROTOCOL_HASH_RELATIVE_PATH,
    PROTOCOL_RELATIVE_PATH,
    RAG_KEYS,
    RETRIEVAL_KEYS,
    STATISTICS_KEYS,
    TOP_LEVEL_KEYS,
    GENERATION_TEMPERATURE,
    assert_test_evaluation_protocol,
    freeze_evaluation_protocol,
    load_and_verify_evaluation_protocol,
    rag_runtime_settings,
    retrieval_runtime_settings,
)
from .evidence import (
    DEFAULT_EVIDENCE_CHAR_BUDGET,
    EVIDENCE_PACKING_POLICY_VERSION,
    evidence_sensitivity_diagnostic_input,
    pack_job_evidence,
)
from .judges import JudgeClient, judge_candidates
from .nuggets import (
    NUGGET_IMPORTANCE_POLICY_VERSION,
    NUGGET_PROMPT_VERSION,
    NUGGET_WEIGHT_POLICY,
    PREVALENCE_UNAVAILABLE,
    NUGGET_SUPPORT_SEMANTICS_VERSION,
    _judge_importance_batch,
    _validate_importance,
    _verify_support_matrix_batch,
    build_nuggets_for_topic,
)
from .metrics import (
    aggregate_topic_values_by_family,
    condense_uncertain_ranking,
    family_cluster_bootstrap_ci,
    family_cluster_paired_bootstrap,
    ndcg_at_k,
    observed_support_coverage_at_k,
    paired_family_sign_flip_test,
    strong_precision_at_k,
    weighted_nugget_coverage,
)
from .pooling import (
    PoolingService,
    audit_pool_coverage,
    audit_pool_coverage_offline,
    load_corpus_jobs,
)
from .run_rag_eval import (
    _as_retrieved,
    _certain_gold_context_rows,
    _evaluate_answer,
    _model_identity,
    validate_rag_judge_payload,
)
from .run_retrieval_eval import _load_qrels
from .evaluation_integrity import consume_test_lock
from .schema import CareerQuery, CareerTopic, CorpusJob, Nugget, PooledCandidate, RelevanceJudgment
from .semantics import (
    CANONICAL_INFORMATION_FACETS,
    CANONICAL_INFORMATION_NEED_VERSION,
    canonical_information_need,
)
from .topics import (
    BASE_QUERY_VARIANTS,
    _select_categories,
    discover_topics,
    generate_query_variants,
)


class FakeJudgeClient:
    def __init__(
        self,
        support: dict[str, bool] | dict[str, object],
        *,
        candidate_texts: tuple[str, ...] = ("REST API",),
        extractor_support_keys: tuple[str, ...] = ("vietjobs::J1",),
        support_by_candidate: dict[str, dict[str, bool]] | None = None,
        importance_by_candidate: dict[str, str] | None = None,
    ) -> None:
        self.support = support
        self.candidate_texts = candidate_texts
        self.extractor_support_keys = extractor_support_keys
        self.support_by_candidate = support_by_candidate or {}
        self.importance_by_candidate = importance_by_candidate or {}
        self.calls: list[tuple[str, str, int]] = []

    def json_call(self, *, system: str, user: str, retries: int = 2) -> dict:
        self.calls.append((system, user, retries))
        if "Extract atomic career-information" in system:
            return {
                "nuggets": [
                    {
                        "text": text,
                        "support_job_keys": list(self.extractor_support_keys),
                    }
                    for text in self.candidate_texts
                ]
            }

        if "Judge the importance" in system:
            nugget_rows = re.findall(
                r"(?m)^(N\d+)\nNugget text: (.+)$",
                user,
            )
            return {
                "importance": {
                    nugget_id: self.importance_by_candidate.get(candidate_text, "VITAL")
                    for nugget_id, candidate_text in nugget_rows
                }
            }

        job_pairs = re.findall(
            r"(?m)^(J\d+)\nJob title: Engineer (J\d+)$",
            user,
        )
        if "support matrix" in system:
            nugget_rows = re.findall(
                r"(?m)^(N\d+)\nCandidate nugget: (.+)$",
                user,
            )
            return {
                "support": {
                    nugget_id: {
                        local_job_id: self.support[job_id]
                        for local_job_id, job_id in job_pairs
                    }
                    if candidate_text not in self.support_by_candidate
                    else {
                        local_job_id: self.support_by_candidate[candidate_text][job_id]
                        for local_job_id, job_id in job_pairs
                    }
                    for nugget_id, candidate_text in nugget_rows
                }
            }

        return {
            "support": {
                local_job_id: self.support[job_id]
                for local_job_id, job_id in job_pairs
            }
        }


def _jobs(count: int = 4) -> list[CorpusJob]:
    return [
        CorpusJob(
            source="vietjobs",
            source_job_id=f"J{i}",
            job_title=f"Engineer J{i}",
            category_key="tech",
            location_key=None,
            experience_level=None,
            employment_type=None,
            chunks=(),
        )
        for i in range(1, count + 1)
    ]


def _topic() -> CareerTopic:
    return CareerTopic("topic-1", "family-1", "scope", "label", "tech")


def _qrels(count: int = 4) -> list[RelevanceJudgment]:
    return [RelevanceJudgment("topic-1", "vietjobs", f"J{i}", 2, (2, 2, 2), False) for i in range(1, count + 1)]


class NuggetConstructionTests(unittest.TestCase):
    def test_nugget_protocol_and_importance_policy_versions_are_frozen(self) -> None:
        self.assertEqual(NUGGET_PROMPT_VERSION, "career-rag-silver-nuggets-v4")
        self.assertEqual(NUGGET_IMPORTANCE_POLICY_VERSION, "career-rag-nugget-importance-v1")
        self.assertEqual(
            NUGGET_SUPPORT_SEMANTICS_VERSION,
            "career-rag-nugget-support-observed-before-adaptive-stop-v1",
        )
        self.assertEqual(NUGGET_WEIGHT_POLICY, {"VITAL": 1.0, "OKAY": 0.5})

    def _build(
        self,
        support: dict[str, bool],
        *,
        min_support_jobs: int = 2,
        job_count: int = 4,
        client: FakeJudgeClient | None = None,
        nugget_batch_size: int = 8,
        job_batch_size: int = 8,
        importance_batch_size: int = 8,
        max_in_flight: int = 1,
        refill_size: int = 1,
    ):
        jobs = _jobs(job_count)
        return build_nuggets_for_topic(
            client or FakeJudgeClient(support),
            _topic(),
            _qrels(job_count),
            {job.job_key: job for job in jobs},
            min_support_jobs=min_support_jobs,
            nugget_batch_size=nugget_batch_size,
            job_batch_size=job_batch_size,
            importance_batch_size=importance_batch_size,
            max_in_flight=max_in_flight,
            refill_size=refill_size,
        )

    def test_extractor_underclaim_expands_verified_support_before_threshold(self) -> None:
        nuggets = self._build(
            {"J1": True, "J2": True, "J3": True, "J4": False},
            job_batch_size=1,
        )
        self.assertEqual(len(nuggets), 1)
        nugget = nuggets[0]
        self.assertEqual(set(nugget.support_job_keys), {"vietjobs::J1", "vietjobs::J2"})
        self.assertEqual(nugget.support_count, 2)
        self.assertEqual(nugget.support_count, len(set(nugget.support_job_keys)))
        self.assertTrue(set(nugget.support_job_keys).issubset({job.job_key for job in _jobs()}))
        self.assertEqual(nugget.prevalence, PREVALENCE_UNAVAILABLE)

    def test_unsupported_nugget_is_removed_after_authoritative_verification(self) -> None:
        self.assertEqual(self._build({"J1": True, "J2": False, "J3": False, "J4": False}), [])

    def test_high_prevalence_nugget_can_be_okay(self) -> None:
        nugget = self._build(
            {f"J{i}": True for i in range(1, 5)},
            client=FakeJudgeClient(
                {f"J{i}": True for i in range(1, 5)},
                importance_by_candidate={"REST API": "OKAY"},
            ),
        )[0]
        self.assertEqual(nugget.prevalence, PREVALENCE_UNAVAILABLE)
        self.assertEqual(nugget.importance, "OKAY")
        self.assertEqual(nugget.weight, 0.5)

    def test_low_prevalence_nugget_can_be_vital(self) -> None:
        support = {f"J{i}": i <= 2 for i in range(1, 5)}
        nugget = self._build(
            support,
            client=FakeJudgeClient(
                support,
                importance_by_candidate={"REST API": "VITAL"},
            ),
        )[0]
        self.assertEqual(nugget.prevalence, PREVALENCE_UNAVAILABLE)
        self.assertEqual(nugget.importance, "VITAL")
        self.assertEqual(nugget.weight, 1.0)

    def test_prevalence_change_does_not_change_importance_or_weight(self) -> None:
        first_support = {f"J{i}": i <= 2 for i in range(1, 4)}
        second_support = {f"J{i}": i <= 3 for i in range(1, 4)}
        first = self._build(
            first_support,
            job_count=3,
            min_support_jobs=1,
            client=FakeJudgeClient(
                first_support,
                importance_by_candidate={"REST API": "OKAY"},
            ),
        )[0]
        second = self._build(
            second_support,
            job_count=3,
            min_support_jobs=1,
            client=FakeJudgeClient(
                second_support,
                importance_by_candidate={"REST API": "OKAY"},
            ),
        )[0]
        self.assertEqual(first.prevalence, PREVALENCE_UNAVAILABLE)
        self.assertEqual(second.prevalence, PREVALENCE_UNAVAILABLE)
        self.assertEqual(first.importance, second.importance)
        self.assertEqual(first.weight, second.weight)

    def test_adaptive_verification_stops_after_sufficient_verified_support(self) -> None:
        support = {"J1": True, "J2": True, "J3": True, "J4": True}
        client = FakeJudgeClient(support)
        nuggets = self._build(
            support,
            client=client,
            min_support_jobs=2,
            job_batch_size=1,
        )
        self.assertEqual(len(nuggets), 1)
        self.assertEqual(
            nuggets[0].support_job_keys,
            ("vietjobs::J1", "vietjobs::J2"),
        )
        support_calls = [call for call in client.calls if "support matrix" in call[0]]
        self.assertEqual(len(support_calls), 2)
        self.assertLess(len(support_calls), 4)
        self.assertEqual(nuggets[0].prevalence, PREVALENCE_UNAVAILABLE)

    def test_adaptive_support_is_invariant_to_job_batch_size(self) -> None:
        support = {"J1": True, "J2": True, "J3": True, "J4": False}
        observed = []
        for job_batch_size in (1, 2, 4):
            nuggets = self._build(
                support,
                min_support_jobs=2,
                job_batch_size=job_batch_size,
            )
            observed.append(nuggets[0].support_job_keys)
        self.assertEqual(
            observed,
            [("vietjobs::J1", "vietjobs::J2")] * 3,
        )

    def test_adaptive_support_is_invariant_to_all_transport_batching(self) -> None:
        support_by_candidate = {
            "REST API": {"J1": True, "J2": True, "J3": True, "J4": False},
            "Python": {"J1": False, "J2": True, "J3": True, "J4": True},
        }
        configurations = (
            {"nugget_batch_size": 1, "job_batch_size": 1, "max_in_flight": 1, "refill_size": 1},
            {"nugget_batch_size": 1, "job_batch_size": 2, "max_in_flight": 2, "refill_size": 2},
            {"nugget_batch_size": 2, "job_batch_size": 4, "max_in_flight": 2, "refill_size": 2},
        )
        observed = []
        for configuration in configurations:
            client = FakeJudgeClient(
                {},
                candidate_texts=("REST API", "Python"),
                support_by_candidate=support_by_candidate,
            )
            nuggets = self._build(
                {},
                client=client,
                min_support_jobs=2,
                **configuration,
            )
            observed.append({nugget.text: nugget.support_job_keys for nugget in nuggets})
        expected = {
            "REST API": ("vietjobs::J1", "vietjobs::J2"),
            "Python": ("vietjobs::J2", "vietjobs::J3"),
        }
        self.assertEqual(observed, [expected, expected, expected])

    def test_only_one_verified_support_is_removed_for_minimum_two(self) -> None:
        support = {"J1": True, "J2": False, "J3": False, "J4": False}
        client = FakeJudgeClient(support)
        self.assertEqual(
            self._build(support, client=client, min_support_jobs=2, job_batch_size=1),
            [],
        )
        support_calls = [call for call in client.calls if "support matrix" in call[0]]
        self.assertEqual(len(support_calls), 4)

    def test_partial_verification_never_reports_exact_prevalence(self) -> None:
        support = {"J1": True, "J2": True, "J3": False, "J4": False}
        nugget = self._build(
            support,
            client=FakeJudgeClient(support),
            min_support_jobs=2,
            job_batch_size=1,
        )[0]
        self.assertEqual(nugget.support_count, len(set(nugget.support_job_keys)))
        self.assertEqual(nugget.prevalence, PREVALENCE_UNAVAILABLE)

    def test_malformed_importance_values_are_rejected(self) -> None:
        expected = ("N1", "N2")
        malformed = [
            {"importance": {"N1": "VITAL"}},
            {"importance": {"N1": "VITAL", "N2": "OKAY", "N3": "VITAL"}},
            {"importance": {"N1": "true", "N2": "OKAY"}},
            {"importance": {"N1": 1, "N2": None}},
            {"importance": []},
        ]
        for payload in malformed:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                _validate_importance(payload, nugget_ids=expected)

    def test_importance_prompt_uses_fixed_evidence_preview_without_frequency_signal(self) -> None:
        class CaptureImportanceClient:
            def __init__(self) -> None:
                self.users: list[str] = []

            def json_call(self, *, system: str, user: str, retries: int = 2) -> dict:
                self.users.append(system + "\n" + user)
                return {"importance": {"N1": "OKAY"}}

        jobs = _jobs(20)
        corpus = {job.job_key: job for job in jobs}
        first = {
            "text": "REST API",
            "support_job_keys": tuple(sorted(job.job_key for job in jobs)[:3]),
        }
        second = {
            "text": "REST API",
            "support_job_keys": tuple(job.job_key for job in jobs),
        }
        client = CaptureImportanceClient()
        _judge_importance_batch(client, _topic(), [first], corpus, evidence_chars=5000)
        _judge_importance_batch(client, _topic(), [second], corpus, evidence_chars=5000)

        self.assertEqual(client.users[0], client.users[1])
        for forbidden in (
            "support_count",
            "prevalence",
            "Additional verified supporting jobs",
        ):
            self.assertNotIn(forbidden, client.users[0])
        for job in jobs[3:]:
            self.assertNotIn(job.job_key, client.users[0])

    def test_extractor_hints_do_not_change_authoritative_result(self) -> None:
        support = {"J1": True, "J2": True, "J3": True, "J4": False}
        hints = (
            (),
            ("vietjobs::J1",),
            ("vietjobs::J3",),
            tuple(f"vietjobs::J{i}" for i in range(1, 5)),
        )
        results = []
        importance_prompts = []
        for extractor_hints in hints:
            client = FakeJudgeClient(
                support,
                extractor_support_keys=extractor_hints,
            )
            nuggets = self._build(
                support,
                client=client,
                min_support_jobs=2,
                job_batch_size=4,
            )
            results.append(nuggets)
            importance_prompts.append(
                [user for system, user, _ in client.calls if "Judge the importance" in system]
            )

        self.assertEqual(results, [results[0]] * len(hints))
        self.assertEqual(importance_prompts, [importance_prompts[0]] * len(hints))
        nugget = results[0][0]
        self.assertEqual(nugget.support_job_keys, ("vietjobs::J1", "vietjobs::J2"))
        self.assertEqual(nugget.support_count, 2)
        self.assertEqual(nugget.importance, "VITAL")
        self.assertEqual(nugget.weight, 1.0)


class StaticMatrixClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls = 0

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls += 1
        return self.payload


class NuggetMatrixValidationTests(unittest.TestCase):
    def _verify(self, payload: dict) -> list[list[str]]:
        return _verify_support_matrix_batch(
            StaticMatrixClient(payload),
            [{"text": "REST API"}, {"text": "Python"}],
            _jobs(2),
            evidence_chars=5000,
        )

    def test_missing_nugget_matrix_row_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            self._verify({"support": {"N1": {"J1": True, "J2": False}}})

    def test_missing_matrix_cell_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            self._verify(
                {
                    "support": {
                        "N1": {"J1": True},
                        "N2": {"J1": False, "J2": False},
                    }
                }
            )

    def test_extra_matrix_row_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            self._verify(
                {
                    "support": {
                        "N1": {"J1": True, "J2": False},
                        "N2": {"J1": False, "J2": False},
                        "N3": {"J1": False, "J2": False},
                    }
                }
            )

    def test_extra_matrix_cell_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            self._verify(
                {
                    "support": {
                        "N1": {"J1": True, "J2": False, "J3": False},
                        "N2": {"J1": False, "J2": False},
                    }
                }
            )

    def test_matrix_string_boolean_is_rejected(self) -> None:
        with self.assertRaises(RuntimeError):
            self._verify(
                {
                    "support": {
                        "N1": {"J1": "false", "J2": False},
                        "N2": {"J1": False, "J2": False},
                    }
                }
            )

    def test_matrix_numeric_and_null_booleans_are_rejected(self) -> None:
        for value in (1, 0, None):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                self._verify(
                    {
                        "support": {
                            "N1": {"J1": value, "J2": False},
                            "N2": {"J1": False, "J2": False},
                        }
                    }
                )

    def test_different_batch_sizes_are_semantically_identical(self) -> None:
        support_by_candidate = {
            "REST API": {"J1": True, "J2": False, "J3": True, "J4": False},
            "Python": {"J1": False, "J2": True, "J3": False, "J4": True},
        }
        first = build_nuggets_for_topic(
            FakeJudgeClient(
                {},
                candidate_texts=("REST API", "Python"),
                support_by_candidate=support_by_candidate,
            ),
            _topic(),
            _qrels(),
            {job.job_key: job for job in _jobs()},
            min_support_jobs=2,
            nugget_batch_size=1,
            job_batch_size=1,
            max_in_flight=1,
            refill_size=1,
        )
        second = build_nuggets_for_topic(
            FakeJudgeClient(
                {},
                candidate_texts=("REST API", "Python"),
                support_by_candidate=support_by_candidate,
            ),
            _topic(),
            _qrels(),
            {job.job_key: job for job in _jobs()},
            min_support_jobs=2,
            nugget_batch_size=2,
            job_batch_size=2,
            max_in_flight=1,
            refill_size=1,
        )
        self.assertEqual(first, second)
        support_by_text = {nugget.text: set(nugget.support_job_keys) for nugget in first}
        self.assertEqual(support_by_text["REST API"], {"vietjobs::J1", "vietjobs::J3"})
        self.assertEqual(support_by_text["Python"], {"vietjobs::J2", "vietjobs::J4"})

class SequencedMatrixClient:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = list(payloads)
        self.calls: list[tuple[str, str, int]] = []

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls.append((system, user, retries))
        if not self.payloads:
            raise AssertionError("fake matrix client exhausted its payloads")
        return self.payloads.pop(0)


class CacheLikeSequencedMatrixClient(SequencedMatrixClient):
    def __init__(self, payloads: list[object]) -> None:
        super().__init__(payloads)
        self.cache: dict[tuple[str, str], object] = {}

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls.append((system, user, retries))
        cache_key = (system, user)
        if cache_key in self.cache:
            return self.cache[cache_key]
        if not self.payloads:
            raise AssertionError("fake matrix client exhausted its payloads")
        payload = self.payloads.pop(0)
        self.cache[cache_key] = payload
        return payload


class SequencedImportanceClient:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = list(payloads)
        self.calls: list[tuple[str, str, int]] = []

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls.append((system, user, retries))
        if not self.payloads:
            raise AssertionError("fake importance client exhausted its payloads")
        return self.payloads.pop(0)


class JudgeJsonRetryRegressionTests(unittest.TestCase):
    @staticmethod
    def _judge_client(
        contents: list[str],
        finish_reasons: list[str | None] | None = None,
    ) -> tuple[JudgeClient, list[dict]]:
        requests: list[dict] = []
        remaining = list(contents)
        remaining_finish_reasons = list(finish_reasons or [None] * len(contents))

        def create(**kwargs):
            requests.append(kwargs)
            if not remaining:
                raise AssertionError("fake judge transport exhausted its responses")
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=remaining.pop(0)),
                        finish_reason=remaining_finish_reasons.pop(0),
                    )
                ]
            )

        transport = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        return JudgeClient("offline-json-retry-test", client=transport), requests

    def test_json_call_retries_transient_malformed_json_and_caches_only_success(self) -> None:
        client, requests = self._judge_client([
            '{"broken" true}',
            '{"ok": true}',
        ])
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {
                "CAREER_RAG_LLM_CACHE_DIR": directory,
                "CAREER_RAG_DISABLE_LLM_CACHE": "0",
            }, clear=False),
            patch.object(client, "_save_cache", wraps=client._save_cache) as save_cache,
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
            patch.object(judges_module.time, "sleep"),
        ):
            result = client.json_call(system="system", user="user")
            cache_path = client._cache_path(system="system", user="user")
            cached_payload = json.loads(
                cache_path.read_text(encoding="utf-8")
            )["payload"]

        self.assertEqual(result, {"ok": True})
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]["messages"], requests[1]["messages"])
        self.assertEqual(save_cache.call_count, 1)
        self.assertEqual(save_cache.call_args.kwargs["payload"], {"ok": True})
        self.assertIsNotNone(cache_path)
        self.assertEqual(cached_payload, {"ok": True})

    def test_fenced_json_requires_a_complete_json_object(self) -> None:
        self.assertEqual(
            JudgeClient._parse_json('```json\n{"ok": true}\n```'),
            {"ok": True},
        )
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            JudgeClient._parse_json('```json\n{"ok": true')

    def test_judge_max_tokens_and_truncation_diagnostics(self) -> None:
        truncated = '```json\n{"ok": true'
        client, requests = self._judge_client(
            [truncated, '{"ok": true}'],
            finish_reasons=["length", "stop"],
        )
        with (
            patch.dict(os.environ, {
                "CAREER_RAG_DISABLE_LLM_CACHE": "1",
                "CAREER_RAG_JUDGE_MAX_TOKENS": "1234",
            }, clear=False),
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
            patch.object(judges_module.time, "sleep"),
            patch("builtins.print") as print_mock,
        ):
            result = client.json_call(system="system", user="user")

        self.assertEqual(result, {"ok": True})
        self.assertEqual([request["max_tokens"] for request in requests], [1234, 1234])
        retry_messages = [
            call.args[0]
            for call in print_mock.call_args_list
            if call.args and call.args[0].startswith("[json-retry]")
        ]
        self.assertEqual(len(retry_messages), 1)
        self.assertIn("finish_reason=length", retry_messages[0])
        self.assertIn(f"content_length={len(truncated)}", retry_messages[0])
        self.assertNotIn(truncated, retry_messages[0])

    def test_judge_max_tokens_default_and_invalid_values(self) -> None:
        default_client, default_requests = self._judge_client(['{"ok": true}'])
        with (
            patch.dict(os.environ, {}, clear=False),
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
        ):
            os.environ.pop("CAREER_RAG_JUDGE_MAX_TOKENS", None)
            os.environ["CAREER_RAG_DISABLE_LLM_CACHE"] = "1"
            self.assertEqual(
                default_client.json_call(system="system", user="user"),
                {"ok": True},
            )
        self.assertEqual(default_requests[0]["max_tokens"], 16_384)

        invalid_client, invalid_requests = self._judge_client(['{"ok": true}'])
        for value in ("0", "-1", "1.5", "invalid"):
            with self.subTest(value=value), patch.dict(os.environ, {
                "CAREER_RAG_DISABLE_LLM_CACHE": "1",
                "CAREER_RAG_JUDGE_MAX_TOKENS": value,
            }, clear=False):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    invalid_client.json_call(system="system", user="user")
        self.assertEqual(invalid_requests, [])

    def test_support_matrix_transient_malformed_json_uses_common_retry_policy(self) -> None:
        client, requests = self._judge_client([
            '{"support" {}}',
            '{"support": {"N1": {"J1": true, "J2": false}}}',
        ])
        with (
            patch.dict(os.environ, {"CAREER_RAG_DISABLE_LLM_CACHE": "1"}, clear=False),
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
            patch.object(judges_module.time, "sleep"),
        ):
            result = _verify_support_matrix_batch(
                client,
                [{"text": "REST API"}],
                _jobs(2),
                evidence_chars=5000,
            )
        self.assertEqual(result, [["vietjobs::J1"]])
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]["messages"], requests[1]["messages"])

    def test_candidate_judge_transient_malformed_json_retries_without_schema_change(self) -> None:
        client, requests = self._judge_client([
            '{"grades" {}}',
            '{"grades": {"C1": 2}}',
            '{"grades": {"C1": 2}}',
            '{"grades": {"C1": 2}}',
        ])
        candidate = PooledCandidate(
            topic_id="topic-1",
            source="vietjobs",
            source_job_id="J1",
            job_title="Engineer J1",
            category_key="tech",
            location_key=None,
        )
        job = _jobs(1)[0]
        with (
            patch.dict(os.environ, {"CAREER_RAG_DISABLE_LLM_CACHE": "1"}, clear=False),
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
            patch.object(judges_module.time, "sleep"),
        ):
            judgments = judge_candidates(
                client,
                _topic(),
                [candidate],
                {job.job_key: job},
                max_in_flight=1,
                refill_size=1,
            )
        self.assertEqual(judgments[0].grade, 2)
        self.assertEqual(judgments[0].judge_grades, (2, 2, 2))
        self.assertEqual(len(requests), 4)
        self.assertEqual(requests[0]["messages"], requests[1]["messages"])

    def test_importance_judge_transient_malformed_json_uses_common_retry_policy(self) -> None:
        client, requests = self._judge_client([
            '{"importance" {}}',
            '{"importance": {"N1": "OKAY"}}',
        ])
        with (
            patch.dict(os.environ, {"CAREER_RAG_DISABLE_LLM_CACHE": "1"}, clear=False),
            patch.object(JudgeClient, "_wait_for_request_slot"),
            patch.object(JudgeClient, "_register_success"),
            patch.object(judges_module.time, "sleep"),
        ):
            result = _judge_importance_batch(
                client,
                _topic(),
                [{"text": "REST API", "support_job_keys": ("vietjobs::J1",)}],
                {job.job_key: job for job in _jobs(1)},
                evidence_chars=5000,
            )
        self.assertEqual(result, ["OKAY"])
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]["messages"], requests[1]["messages"])


class NuggetMatrixRetryTests(unittest.TestCase):
    def _verify(self, client: object) -> list[list[str]]:
        return _verify_support_matrix_batch(
            client,
            [{"text": "REST API"}],
            _jobs(2),
            evidence_chars=5000,
        )

    @staticmethod
    def _valid_payload() -> dict:
        return {"support": {"N1": {"J1": True, "J2": False}}}

    @staticmethod
    def _malformed_payload() -> dict:
        return {"support": {"N1": {"J1": True}}}

    def test_schema_retry_recovers_after_first_malformed_response(self) -> None:
        client = SequencedMatrixClient(
            [self._malformed_payload(), self._malformed_payload(), self._valid_payload()]
        )
        self.assertEqual(self._verify(client), [["vietjobs::J1"]])
        self.assertEqual(len(client.calls), 3)
        self.assertEqual([call[2] for call in client.calls], [2, 2, 2])
        prompts = [call[1] for call in client.calls]
        self.assertEqual(len(set(prompts)), 3)
        self.assertIn("SCHEMA_RETRY_ATTEMPT=1", prompts[1])
        self.assertIn("SCHEMA_RETRY_ATTEMPT=2", prompts[2])
        self.assertIn("all and only these nugget IDs: N1", prompts[1])
        self.assertIn("all and only these job IDs: J1, J2", prompts[1])
        self.assertIn("literal JSON true or false", prompts[1])

    def test_schema_retry_budget_is_exact_when_every_response_is_malformed(self) -> None:
        client = SequencedMatrixClient(
            [self._malformed_payload(), self._malformed_payload(), self._malformed_payload()]
        )
        with self.assertRaisesRegex(RuntimeError, "after 2 retries"):
            self._verify(client)
        self.assertEqual(len(client.calls), 3)
        self.assertEqual([call[2] for call in client.calls], [2, 2, 2])
        self.assertEqual(len({call[1] for call in client.calls}), 3)

    def test_cached_malformed_response_cannot_block_corrective_prompt(self) -> None:
        client = CacheLikeSequencedMatrixClient(
            [self._malformed_payload(), self._malformed_payload(), self._valid_payload()]
        )
        self.assertEqual(self._verify(client), [["vietjobs::J1"]])
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(len(client.cache), 3)
        self.assertEqual(len(set(call[1] for call in client.calls)), 3)
        self.assertEqual(client.payloads, [])

    def test_importance_schema_retries_are_strict_and_distinct(self) -> None:
        client = SequencedImportanceClient(
            [
                {"importance": {}},
                {"importance": {}},
                {"importance": {"N1": "OKAY"}},
            ]
        )
        result = _judge_importance_batch(
            client,
            _topic(),
            [{"text": "REST API", "support_job_keys": ("vietjobs::J1",)}],
            {job.job_key: job for job in _jobs(1)},
            evidence_chars=5000,
        )
        self.assertEqual(result, ["OKAY"])
        self.assertEqual(len(client.calls), 3)
        self.assertEqual([call[2] for call in client.calls], [2, 2, 2])
        self.assertEqual(len({call[1] for call in client.calls}), 3)
        self.assertIn("SCHEMA_RETRY_ATTEMPT=1", client.calls[1][1])
        self.assertIn("SCHEMA_RETRY_ATTEMPT=2", client.calls[2][1])


class TreeHashTests(unittest.TestCase):
    def test_tree_hash_is_root_independent_and_content_sensitive(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            roots = [Path(first) / "checkout", Path(second) / "checkout"]
            for root in roots:
                (root / "nested").mkdir(parents=True)
                (root / "a.py").write_bytes(b"a")
                (root / "nested" / "b.py").write_bytes(b"b")

            first_paths = [roots[0] / "a.py", roots[0] / "nested" / "b.py"]
            second_paths = [roots[1] / "a.py", roots[1] / "nested" / "b.py"]
            self.assertEqual(sha256_tree(first_paths), sha256_tree(second_paths))

            (roots[1] / "nested" / "b.py").write_bytes(b"changed")
            self.assertNotEqual(sha256_tree(first_paths), sha256_tree(second_paths))

    def test_input_order_does_not_change_tree_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = [root / "a.py", root / "b.py"]
            paths[0].write_bytes(b"a")
            paths[1].write_bytes(b"b")
            self.assertEqual(sha256_tree(paths), sha256_tree(reversed(paths)))

    def test_singleton_filename_is_part_of_tree_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "foo.py"
            second = root / "bar.py"
            first.write_bytes(b"same bytes")
            second.write_bytes(b"same bytes")
            self.assertNotEqual(sha256_tree([first]), sha256_tree([second]))

    def test_filename_change_changes_tree_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "old.py"
            second = root / "new.py"
            first.write_bytes(b"same bytes")
            second.write_bytes(b"same bytes")
            self.assertNotEqual(sha256_tree([first]), sha256_tree([second]))

    def test_content_change_changes_tree_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "source.py"
            path.write_bytes(b"before")
            first = sha256_tree([path])
            path.write_bytes(b"after")
            self.assertNotEqual(first, sha256_tree([path]))

    def test_structural_boundary_collision_is_impossible(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_root = Path(first)
            second_root = Path(second)
            (first_root / "a").write_bytes(b"x")
            (first_root / "bc").write_bytes(b"y")
            (second_root / "a").write_bytes(b"xb")
            (second_root / "c").write_bytes(b"y")

            tree_a = sha256_tree([first_root / "a", first_root / "bc"])
            tree_b = sha256_tree([second_root / "a", second_root / "c"])
            self.assertNotEqual(tree_a, tree_b)


class FreezeIntegrityTests(unittest.TestCase):
    @staticmethod
    def _write_frozen_fixture(root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        clean_provenance = {
            "status": "VERIFIED_CLEAN",
            "index_type": CLEAN_INDEX_TYPE,
            "embedding_model": CLEAN_EMBEDDING_MODEL,
            "embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
            "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
            "vectors_sha256": "v" * 64,
            "chunk_map_sha256": "m" * 64,
            "corpus_membership_sha256": "c" * 64,
            "chunk_context_sha256": "x" * 64,
        }
        clean_fields = {
            "clean_embedding_index_type": clean_provenance["index_type"],
            "clean_embedding_model": clean_provenance["embedding_model"],
            "clean_embedding_dimension": clean_provenance["embedding_dimension"],
            "clean_embedding_input_policy_version": clean_provenance["clean_embedding_input_policy_version"],
            "clean_embedding_vectors_sha256": clean_provenance["vectors_sha256"],
            "clean_embedding_chunk_map_sha256": clean_provenance["chunk_map_sha256"],
            "clean_embedding_corpus_membership_sha256": clean_provenance["corpus_membership_sha256"],
            "clean_embedding_chunk_context_sha256": clean_provenance["chunk_context_sha256"],
        }
        rows = {
            "corpus_manifest.json": {"benchmark": "CareerRAGBench-Auto-V3", "dataset_sha256": "d" * 64, **clean_fields},
            "topics.jsonl": [
                {"topic_id": "topic-1", "family_id": "family-1", "scope": "broad", "label": "Tech", "category_key": "tech", "known_skills": [], "split": "dev"}
            ],
            "queries.jsonl": [
                {"query_id": "q1", "topic_id": "topic-1", "variant": "direct", "text": "Tech", "known_skills": []},
                {"query_id": "q2", "topic_id": "topic-1", "variant": "conversational", "text": "Tech", "known_skills": []},
                {"query_id": "q3", "topic_id": "topic-1", "variant": "noisy", "text": "Tech", "known_skills": []},
            ],
            "pool.jsonl": [],
            "qrels.silver.jsonl": [],
            "qrels.uncertain.jsonl": [],
            "controls.jsonl": [],
            "nuggets.silver.jsonl": [],
            "dev_ids.json": {"family_ids": ["family-1"], "topic_ids": ["topic-1"]},
            "test_ids.json": {"family_ids": ["family-2"], "topic_ids": []},
            "reports/build_audit.json": {"passed": True},
            "reports/preflight_corpus.json": {"indexed_vietjobs_jobs": 1},
            "reports/preflight_leakage.json": {"passed": True},
            "reports/preflight_topics.json": {"topic_count": 1},
            "reports/preflight_report.json": {"readiness": {"status": "READY_FOR_PAID_BUILD"}},
            "reports/preflight_embedding_provenance.json": {"status": "VERIFIED_CLEAN"},
            "reports/clean_embedding_provenance.json": clean_provenance,
            "reports/preflight_evidence_truncation.json": {"cutoff_chars": 5000},
            "reports/preflight_pooling.json": {"mode": "real_offline"},
        }
        for relative, payload in rows.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if relative.endswith(".jsonl"):
                path.write_text(
                    "".join(json.dumps(row, sort_keys=True) + "\n" for row in payload),
                    encoding="utf-8",
                )
            else:
                path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        hashes = artifact_sha256_map(root)
        clean_fields["clean_embedding_provenance_sha256"] = hashes["reports/clean_embedding_provenance.json"]
        corpus_path = root / "corpus_manifest.json"
        corpus_payload = json.loads(corpus_path.read_text(encoding="utf-8"))
        corpus_payload["clean_embedding_provenance_sha256"] = clean_fields["clean_embedding_provenance_sha256"]
        corpus_path.write_text(json.dumps(corpus_payload, sort_keys=True) + "\n", encoding="utf-8")
        hashes = artifact_sha256_map(root)
        manifest = {
            "benchmark_name": "CareerRAGBench-Auto-V3",
            "benchmark_version": "3.0",
            "random_seed": 20260819,
            "dataset_sha256": "d" * 64,
            "corpus_manifest_sha256": hashes["corpus_manifest.json"],
            "topics_sha256": hashes["topics.jsonl"],
            "queries_sha256": hashes["queries.jsonl"],
            "pool_sha256": hashes["pool.jsonl"],
            "qrels_sha256": hashes["qrels.silver.jsonl"],
            "nuggets_sha256": hashes["nuggets.silver.jsonl"],
            "judge_model": "offline-test",
            "judge_prompt_sha256": "p" * 64,
            "builder_source_sha256": "b" * 64,
            "exact_model_id_equal": False,
            "dev_family_ids": ["family-1"],
            "test_family_ids": ["family-2"],
            "configuration": {
                "git_head": "deadbeef",
                "generator_model_requested": "offline-generator",
                "generator_model_reported": None,
                "judge_model_requested": "offline-test",
                "judge_model_reported": None,
                "exact_model_id_equal": False,
                "family_relation": "UNVERIFIED",
                "family_metadata_source": None,
                "relevance_judgment_design": "multi-view consistency judgments from one judge model",
                "qrel_ground_truth_status": "SILVER_LLM_GENERATED_NOT_HUMAN_GOLD",
                "human_calibration_status": "NOT_PERFORMED",
                "embedding_provenance": {"status": "VERIFIED_CLEAN"},
                "embedding_provenance_status": "VERIFIED_CLEAN",
                **clean_fields,
            },
            "artifact_sha256": hashes,
        }
        manifest_path = root / "benchmark_manifest.json"
        manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
        (root / "test_lock.json").write_text(
            json.dumps({
                "status": "LOCKED", "immutable": True, "frozen": True,
                "benchmark_name": "CareerRAGBench-Auto-V3", "benchmark_version": "3.0",
                "benchmark_manifest_sha256": __import__("hashlib").sha256(manifest_path.read_bytes()).hexdigest(),
                "test_ids_sha256": __import__("hashlib").sha256((root / "test_ids.json").read_bytes()).hexdigest(),
            }, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def test_frozen_fixture_verifies_and_any_bound_artifact_tamper_fails(self) -> None:
        for relative in V3_REQUIRED_ARTIFACTS:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                self._write_frozen_fixture(root)
                before = verify_frozen_benchmark(root)
                self.assertTrue(before["passed"], before)
                with (root / relative).open("ab") as handle:
                    handle.write(b"tamper")
                after = verify_frozen_benchmark(root)
                self.assertFalse(after["passed"], after)

    def test_manifest_artifact_path_cannot_escape_benchmark_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_frozen_fixture(root)
            manifest_path = root / "benchmark_manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifact_sha256"]["../outside.json"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
            lock_path = root / "test_lock.json"
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            lock["benchmark_manifest_sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            lock_path.write_text(json.dumps(lock, sort_keys=True) + "\n", encoding="utf-8")

            result = verify_frozen_benchmark(root)
            self.assertFalse(result["passed"])
            self.assertTrue(any("escapes benchmark directory" in blocker for blocker in result["blockers"]))

    def test_existing_frozen_and_partial_directories_are_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "bench"
            root.mkdir()
            (root / "benchmark_manifest.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                _assert_final_output_available(root)
            partial = Path(directory) / "partial"
            partial.mkdir()
            (partial / "topics.jsonl").write_text("partial", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                _assert_final_output_available(partial)

    def test_candidate_finalize_is_atomic_and_failed_build_has_no_final_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            final = Path(directory) / "bench"
            candidate = _create_building_directory(final)
            (candidate / "test_lock.json").write_text("candidate", encoding="utf-8")
            _finalize_candidate(candidate, final)
            self.assertTrue(final.is_dir())
            self.assertFalse(candidate.exists())

            failed = Path(directory) / "failed"
            with patch.object(build_benchmark_module, "_build_benchmark_into", side_effect=RuntimeError("free failure")):
                with self.assertRaisesRegex(RuntimeError, "free failure"):
                    build_benchmark(output_dir=failed, judge_model="offline-test")
            self.assertFalse(failed.exists())

    def test_free_preflight_failure_never_instantiates_paid_judge(self) -> None:
        blocked = {"readiness": {"status": "BLOCKED", "blockers": ["UNVERIFIED"]}}
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            candidate.mkdir()
            with patch.object(build_benchmark_module, "run_construction_preflight", return_value=blocked), \
                    patch.object(build_benchmark_module, "JudgeClient", create=True) as judge_client:
                with self.assertRaisesRegex(RuntimeError, "free preflight blocked"):
                    build_benchmark_module._build_benchmark_into(
                        candidate,
                        judge_model="offline-test",
                        seed=20260819,
                        pool_depth=20,
                        max_pool=80,
                    )
            judge_client.assert_not_called()


class LlmCacheAtomicBuildTests(unittest.TestCase):
    @staticmethod
    def _client() -> JudgeClient:
        client = object.__new__(JudgeClient)
        client.model_name = "offline-cache-test"
        return client

    def test_default_cache_never_creates_final_benchmark_and_survives_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            final = root / "career_rag_bench_auto_v3"
            cache_root = root / "career_rag_llm_cache_v3"
            candidate = _create_building_directory(final)
            (candidate / "candidate.txt").write_text("complete", encoding="utf-8")
            client = self._client()
            with patch.object(judges_module, "DEFAULT_LLM_CACHE_DIR", cache_root), \
                    patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CAREER_RAG_LLM_CACHE_DIR", None)
                cache_path = client._cache_path(system="system", user="user")
                client._save_cache(system="system", user="user", payload={"ok": True})

            self.assertIsNotNone(cache_path)
            self.assertTrue(cache_path.is_file())
            self.assertTrue(cache_path.is_relative_to(cache_root))
            self.assertFalse(final.exists())

            # A failed candidate can disappear without deleting paid-call cache.
            for child in candidate.iterdir():
                child.unlink()
            candidate.rmdir()
            self.assertTrue(cache_path.is_file())

            retry_candidate = _create_building_directory(final)
            (retry_candidate / "candidate.txt").write_text("complete", encoding="utf-8")
            _finalize_candidate(retry_candidate, final)
            self.assertTrue(final.is_dir())
            self.assertTrue(cache_path.is_file())

    def test_explicit_llm_cache_directory_override_is_honored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            override = Path(directory) / "explicit-cache"
            client = self._client()
            with patch.dict(
                os.environ,
                {"CAREER_RAG_LLM_CACHE_DIR": str(override)},
                clear=False,
            ):
                path = client._cache_path(system="system", user="user")
                client._save_cache(system="system", user="user", payload={"ok": True})
            self.assertIsNotNone(path)
            self.assertTrue(path.is_file())
            self.assertTrue(path.is_relative_to(override))

    def test_current_model_cache_hit_takes_precedence_over_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "CAREER_RAG_LLM_CACHE_DIR": directory,
                "CAREER_RAG_CACHE_FALLBACK_MODEL": "old-model",
            },
            clear=False,
        ):
            client = self._client()
            client.model_name = "old-model"
            client._save_cache(system="system", user="user", payload={"source": "fallback"})
            client.model_name = "current-model"
            client._save_cache(system="system", user="user", payload={"source": "current"})

            self.assertEqual(
                client._load_cache(system="system", user="user"),
                {"source": "current"},
            )

    def test_fallback_model_cache_hit_is_promoted_to_current_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "CAREER_RAG_LLM_CACHE_DIR": directory,
                "CAREER_RAG_CACHE_FALLBACK_MODEL": "old-model",
            },
            clear=False,
        ):
            client = self._client()
            client.model_name = "old-model"
            client._save_cache(system="system", user="user", payload={"ok": True})
            client.model_name = "current-model"
            current_path = client._cache_path(system="system", user="user")
            self.assertFalse(current_path.exists())

            self.assertEqual(
                client._load_cache(system="system", user="user"),
                {"ok": True},
            )
            self.assertTrue(current_path.is_file())
            promoted = json.loads(current_path.read_text(encoding="utf-8"))
            self.assertEqual(promoted["model"], "current-model")
            self.assertEqual(promoted["payload"], {"ok": True})

    def test_fallback_model_does_not_match_a_different_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {
                "CAREER_RAG_LLM_CACHE_DIR": directory,
                "CAREER_RAG_CACHE_FALLBACK_MODEL": "old-model",
            },
            clear=False,
        ):
            client = self._client()
            client.model_name = "old-model"
            client._save_cache(
                system="system-old",
                user="user-old",
                payload={"unexpected": True},
            )
            client.model_name = "current-model"
            self.assertIsNone(
                client._load_cache(system="system-new", user="user-new")
            )
            self.assertFalse(
                client._cache_path(system="system-new", user="user-new").exists()
            )

    def test_no_fallback_environment_keeps_current_model_only_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {"CAREER_RAG_LLM_CACHE_DIR": directory},
            clear=False,
        ):
            os.environ.pop("CAREER_RAG_CACHE_FALLBACK_MODEL", None)
            client = self._client()
            client.model_name = "old-model"
            client._save_cache(system="system", user="user", payload={"old": True})
            client.model_name = "current-model"

            self.assertIsNone(client._load_cache(system="system", user="user"))
            self.assertFalse(
                client._cache_path(system="system", user="user").exists()
            )


class CandidateJudgeSchemaRetryClient:
    def __init__(self, payloads: list[object]) -> None:
        self.payloads = list(payloads)
        self.cache: dict[tuple[str, str], object] = {}
        self.calls: list[tuple[str, str, int]] = []

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls.append((system, user, retries))
        cache_key = (system, user)
        if cache_key in self.cache:
            return self.cache[cache_key]
        if not self.payloads:
            raise AssertionError("fake candidate judge exhausted its payloads")
        payload = self.payloads.pop(0)
        self.cache[cache_key] = payload
        return payload


class CandidateJudgeSchemaRetryTests(unittest.TestCase):
    @staticmethod
    def _candidate() -> PooledCandidate:
        return PooledCandidate(
            topic_id="topic-1",
            source="vietjobs",
            source_job_id="J1",
            job_title="Engineer J1",
            category_key="tech",
            location_key=None,
        )

    def test_candidate_judge_retries_use_distinct_cache_keys(self) -> None:
        malformed = {"grades": {}}
        valid = {"grades": {"C1": 2}}
        client = CandidateJudgeSchemaRetryClient(
            [malformed, malformed, valid, valid, valid]
        )
        job = _jobs(1)[0]
        result = judge_candidates(
            client,
            _topic(),
            [self._candidate()],
            {job.job_key: job},
            max_in_flight=1,
            refill_size=1,
        )
        self.assertEqual(result[0].grade, 2)
        self.assertEqual(len(client.calls), 5)
        self.assertEqual([call[2] for call in client.calls], [2] * 5)
        first_view_prompts = [call[1] for call in client.calls[:3]]
        self.assertEqual(len(set(first_view_prompts)), 3)
        self.assertIn("SCHEMA_RETRY_ATTEMPT=1", first_view_prompts[1])
        self.assertIn("SCHEMA_RETRY_ATTEMPT=2", first_view_prompts[2])
        self.assertEqual(len(client.cache), 5)

    def test_candidate_judge_schema_retry_budget_is_exact(self) -> None:
        client = CandidateJudgeSchemaRetryClient([{"grades": {}}] * 3)
        job = _jobs(1)[0]
        with self.assertRaisesRegex(RuntimeError, "strict schema"):
            judge_candidates(
                client,
                _topic(),
                [self._candidate()],
                {job.job_key: job},
                max_in_flight=1,
                refill_size=1,
            )
        self.assertEqual(len(client.calls), 3)
        self.assertEqual(len(client.cache), 3)

    def test_candidate_judge_rejects_coerced_grade_types(self) -> None:
        for value in ("3", 3.0, True):
            with self.subTest(value=value):
                client = CandidateJudgeSchemaRetryClient(
                    [{"grades": {"C1": value}}] * 3
                )
                with self.assertRaisesRegex(RuntimeError, "strict schema"):
                    judge_candidates(
                        client,
                        _topic(),
                        [self._candidate()],
                        {_jobs(1)[0].job_key: _jobs(1)[0]},
                        max_in_flight=1,
                        refill_size=1,
                    )
                self.assertEqual(len(client.calls), 3)

    def test_judge_cache_identity_binds_model_base_url_and_full_prompts(self) -> None:
        client = object.__new__(JudgeClient)
        client.model_name = "judge-a"
        with override_settings(CKEY_BASE_URL="https://provider-a.invalid/v1"):
            baseline = client._cache_key(system="system-v1", user="user-v1")
            self.assertNotEqual(baseline, client._cache_key(system="system-v2", user="user-v1"))
            self.assertNotEqual(baseline, client._cache_key(system="system-v1", user="user-v2"))
            client.model_name = "judge-b"
            self.assertNotEqual(baseline, client._cache_key(system="system-v1", user="user-v1"))
            client.model_name = "judge-a"
        with override_settings(CKEY_BASE_URL="https://provider-b.invalid/v1"):
            self.assertNotEqual(baseline, client._cache_key(system="system-v1", user="user-v1"))


class TopicSemanticsTests(unittest.TestCase):
    def test_min_family_jobs_is_a_hard_eligibility_floor(self) -> None:
        title_jobs = {"tech": Counter({"backend engineer": 100})}
        with self.assertRaisesRegex(RuntimeError, "No career family"):
            _select_categories(
                Counter({"tech": 99}),
                title_jobs,
                min_family_jobs=100,
                preferred_specific_support=8,
                hard_min_specific_support=8,
            )
        selected, _, _ = _select_categories(
            Counter({"tech": 100}),
            title_jobs,
            min_family_jobs=100,
            preferred_specific_support=8,
            hard_min_specific_support=8,
        )
        self.assertEqual(selected, ["tech"])

    def test_base_topic_emits_exactly_three_shared_need_variants(self) -> None:
        topic = CareerTopic(
            "topic-1",
            "family-1",
            "broad",
            "Software Engineering",
            "tech",
            known_skills=("Python",),
        )
        queries = generate_query_variants(topic)
        self.assertEqual(len(queries), 3)
        self.assertEqual({query.variant for query in queries}, set(BASE_QUERY_VARIANTS))
        self.assertNotIn("personalized", {query.variant for query in queries})
        self.assertEqual({query.topic_id for query in queries}, {topic.topic_id})
        self.assertTrue(all(query.known_skills == () for query in queries))
        self.assertTrue(all("skill" in query.text.casefold() or "kỹ năng" in query.text.casefold() for query in queries))
        self.assertTrue(all("bổ sung" not in query.text for query in queries))

    def test_canonical_information_need_is_deterministic_and_facet_conditioned(self) -> None:
        broad = CareerTopic("broad", "family-1", "broad", "Software Engineering", "tech")
        specific = CareerTopic(
            "specific",
            "family-1",
            "specific",
            "Backend Developer",
            "tech",
        )
        broad_need = canonical_information_need(broad)
        specific_need = canonical_information_need(specific)
        self.assertEqual(broad_need, canonical_information_need(broad))
        self.assertEqual(
            CANONICAL_INFORMATION_NEED_VERSION,
            "career-rag-canonical-information-need-v1",
        )
        for facet in CANONICAL_INFORMATION_FACETS.split(", "):
            self.assertIn(facet.split(" and ")[0], broad_need)
        self.assertIn("Backend Developer", specific_need)
        self.assertIn("tech", specific_need)
        self.assertIn("what employers expect", specific_need)

    def test_family_split_audit_remains_disjoint(self) -> None:
        topics = [
            CareerTopic("dev", "family-dev", "broad", "Dev", "tech", split="dev"),
            CareerTopic("test", "family-test", "broad", "Test", "tech", split="test"),
        ]
        report = audit_split(topics)
        self.assertTrue(report["passed"])
        self.assertEqual(report["overlap"], [])

    def test_discover_topics_keeps_three_queries_and_disjoint_families(self) -> None:
        jobs = [
            CorpusJob(
                source="vietjobs",
                source_job_id=f"{category}-{index}",
                job_title=f"{category} Engineer",
                category_key=category,
                location_key=None,
                experience_level=None,
                employment_type=None,
                chunks=(),
            )
            for category in ("tech_a", "tech_b")
            for index in range(1, 9)
        ]
        topics, queries, dev_families, test_families = discover_topics(
            jobs,
            min_family_jobs=1,
            min_specific_title_jobs=8,
        )
        self.assertEqual(len(queries), len(topics) * 3)
        self.assertEqual(set(dev_families) & set(test_families), set())
        by_topic = {}
        for query in queries:
            by_topic.setdefault(query.topic_id, []).append(query)
        self.assertTrue(all(len(by_topic[topic.topic_id]) == 3 for topic in topics))
        self.assertTrue(all(set(query.variant for query in by_topic[topic.topic_id]) == set(BASE_QUERY_VARIANTS) for topic in topics))
        self.assertTrue(all(topic.known_skills == () for topic in topics))
        self.assertTrue(all(query.known_skills == () for query in queries))


class OfflineDiagnosticTests(unittest.TestCase):
    def test_control_audit_rejects_string_booleans(self) -> None:
        rows = [
            {"control_type": "positive", "passed": "false"},
            {"control_type": "negative", "passed": True},
            {"control_type": "order_invariance", "passed": True},
            {"control_type": "paraphrase_consistency", "passed": True},
        ]
        report = audit_controls(rows)
        self.assertFalse(report["shape_ok"])
        self.assertFalse(report["passed"])

    def test_benchmark_corpus_load_uses_deterministic_chunk_tie_breaker(self) -> None:
        calls: list[tuple[str, object]] = []
        row = {
            "source": "vietjobs",
            "source_job_id": "J1",
            "job_title": "Engineer",
            "category_key": "tech",
            "location_key": None,
            "experience_level": None,
            "employment_type": None,
            "section": "description",
            "content": "evidence",
        }

        class Rows:
            def order_by(self, *fields):
                calls.append(("order_by", fields))
                return self

            def values(self, *fields):
                calls.append(("values", fields))
                return self

            def iterator(self, *, chunk_size: int):
                return iter((row,))

        class Manager:
            def filter(self, **filters):
                calls.append(("filter", filters))
                return Rows()

        with patch("apps.career.evaluation.career_rag.pooling.CareerJobChunk.objects", Manager()):
            jobs = load_corpus_jobs(source="vietjobs")
        self.assertEqual(len(jobs), 1)
        self.assertIn(("order_by", ("source_job_id", "chunk_index", "chunk_id")), calls)

    @staticmethod
    def _rankings() -> dict[str, dict[str, dict[str, list[str]]]]:
        return {
            "topic-1": {
                "direct": {
                    "bm25": [f"B{i}" for i in range(1, 26)],
                    "dense": [f"D{i}" for i in range(1, 26)],
                    "title": [f"T{i}" for i in range(1, 26)],
                },
                "conversational": {
                    "bm25": ["B1", "B2", "B26", "B27"],
                    "dense": ["D1", "D2", "D26", "D27"],
                    "title": ["T1", "T2", "T26", "T27"],
                },
                "noisy": {
                    "bm25": ["B1", "B3", "B28"],
                    "dense": ["D1", "D3", "D28"],
                    "title": ["T1", "T3", "T28"],
                },
            }
        }

    def test_pool_coverage_diagnostic_reports_all_required_depths(self) -> None:
        report = audit_pool_coverage(
            self._rankings(),
            depths=(5, 10, 15, 20),
            max_pool=3,
        )
        self.assertEqual(report["depths"], [5, 10, 15, 20])
        for depth in (5, 10, 15, 20):
            detail = report["reports"][str(depth)]["topics"]["topic-1"]
            self.assertIn("direct_union_size", detail)
            self.assertIn("unique_contribution_counts", detail)
            self.assertIn("judged_candidate_count", detail)
            self.assertIn("legacy_max_pool_dropped_count", detail)
        self.assertGreater(report["reports"]["20"]["aggregate"]["total_candidates_that_old_max_pool_would_drop"], 0)

    def test_pool_unique_contribution_is_unique_against_all_other_systems(self) -> None:
        rankings = {
            "topic-1": {
                "direct": {
                    "bm25": ["A", "B", "C"],
                    "dense": ["B", "C", "D"],
                    "title": ["C", "E"],
                }
            }
        }
        detail = audit_pool_coverage(
            rankings,
            depths=(5,),
            max_pool=10,
        )["reports"]["5"]["topics"]["topic-1"]
        self.assertEqual(
            {system: set(values) for system, values in detail["unique_contribution"].items()},
            {"bm25": {"A"}, "dense": {"D"}, "title": {"E"}},
        )

    def test_pool_aggregate_is_a_summary_of_topics_not_a_global_repool(self) -> None:
        rankings = {
            "topic-a": {
                "direct": {
                    "bm25": ["A"],
                    "dense": ["A"],
                    "title": ["A"],
                }
            },
            "topic-b": {
                "direct": {
                    "bm25": ["B1", "B2", "B3"],
                    "dense": ["D1", "D2", "D3"],
                    "title": ["T1", "T2", "T3"],
                }
            },
        }
        report = audit_pool_coverage(rankings, depths=(5,), max_pool=2)
        aggregate = report["reports"]["5"]["aggregate"]
        self.assertEqual(aggregate["topic_count"], 2)
        self.assertEqual(aggregate["total_candidates_that_old_max_pool_would_drop"], 7)
        self.assertEqual(
            aggregate["total_system_unique_candidates"],
            {"bm25": 3, "dense": 3, "title": 3},
        )

    def test_offline_pool_audit_runs_local_rankings_without_llm(self) -> None:
        class StubPooler:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str, int]] = []

            def _ranking(self, system: str, query: str, depth: int) -> list[str]:
                self.calls.append((system, query, depth))
                return [f"{system}-{index}" for index in range(1, depth + 1)]

            def bm25(self, query: str, depth: int) -> list[str]:
                return self._ranking("bm25", query, depth)

            def dense(self, query: str, depth: int) -> list[str]:
                return self._ranking("dense", query, depth)

            def title_lexical(self, query: str, depth: int) -> list[str]:
                return self._ranking("title", query, depth)

        pooler = StubPooler()
        topic = CareerTopic("topic-1", "family-1", "broad", "Tech", "tech")
        query = CareerQuery("q1", "topic-1", "direct", "Tech jobs")
        report = audit_pool_coverage_offline(
            pooler,
            [topic],
            {topic.topic_id: [query]},
            depths=(5, 10, 15, 20),
            max_pool=3,
        )
        self.assertEqual(report["mode"], "real_offline")
        self.assertEqual(report["query_count"], 1)
        self.assertEqual(sorted(set(pooler.calls)), [
            ("bm25", "Tech jobs", 20),
            ("dense", "Tech jobs", 20),
            ("title", "Tech jobs", 20),
        ])

    def test_truncation_audit_is_deterministic_and_detects_late_qualifications(self) -> None:
        jobs = [
            CorpusJob(
                source="vietjobs",
                source_job_id="J1",
                job_title="Engineer J1",
                category_key="tech",
                location_key=None,
                experience_level=None,
                employment_type=None,
                chunks=(
                    {"section": "description", "content": "x" * 5100},
                    {"section": "required qualifications", "content": "Python"},
                ),
            ),
            CorpusJob(
                source="vietjobs",
                source_job_id="J2",
                job_title="Engineer J2",
                category_key="tech",
                location_key=None,
                experience_level=None,
                employment_type=None,
                chunks=({"section": "description", "content": "short"},),
            ),
            CorpusJob(
                source="vietjobs",
                source_job_id="J3",
                job_title="Engineer J3",
                category_key="tech",
                location_key=None,
                experience_level=None,
                employment_type=None,
                chunks=(
                    {"section": "description", "content": "x" * 4800},
                    {"section": "required qualifications", "content": "Python " * 200},
                ),
            ),
        ]
        first = audit_evidence_truncation(jobs, cutoff=5000)
        second = audit_evidence_truncation(jobs, cutoff=5000)
        self.assertEqual(first, second)
        self.assertEqual(first["job_count"], 3)
        self.assertEqual(first["over_cutoff_count"], 2)
        self.assertEqual(first["late_qualification_section_job_count"], 1)
        self.assertIn("required qualifications", first["late_qualification_sections"])
        self.assertEqual(first["qualification_section_after_cutoff_job_count"], 1)
        self.assertEqual(first["qualification_section_crossing_cutoff_job_count"], 1)
        self.assertEqual(first["qualification_content_lost_job_count"], 2)
        self.assertGreater(first["qualification_content_chars_lost_total"], 0)

    def test_section_aware_evidence_packing_preserves_late_required_qualifications(self) -> None:
        job = CorpusJob(
            source="vietjobs",
            source_job_id="J-pack",
            job_title="Engineer",
            category_key="tech",
            location_key="Hanoi",
            experience_level="mid",
            employment_type="full-time",
            chunks=(
                {"section": "description", "content": "d" * 4800},
                {"section": "required qualifications", "content": "Python Docker Kubernetes"},
                {"section": "benefits", "content": "b" * 1000},
            ),
        )
        first = pack_job_evidence(job, char_budget=5000)
        second = pack_job_evidence(job, char_budget=5000)
        self.assertEqual(first, second)
        self.assertLessEqual(len(first), 5000)
        self.assertIn("[required qualifications]", first)
        self.assertIn("Python Docker Kubernetes", first)
        self.assertEqual(EVIDENCE_PACKING_POLICY_VERSION, "career-rag-evidence-packing-v1")

        duplicate_job = CorpusJob(
            source="vietjobs",
            source_job_id="J-duplicate",
            job_title="Engineer",
            category_key="tech",
            location_key=None,
            experience_level=None,
            employment_type=None,
            chunks=(
                {"section": "description", "content": "Same evidence"},
                {"section": "required qualifications", "content": "Same evidence"},
            ),
        )
        deduplicated = pack_job_evidence(duplicate_job, char_budget=5000)
        self.assertEqual(deduplicated.count("Same evidence"), 1)
        self.assertIn("[required qualifications]", deduplicated)

        sensitivity = evidence_sensitivity_diagnostic_input(job, char_budget=5000)
        self.assertEqual(sensitivity["packed_evidence"], first)
        self.assertEqual(sensitivity["expanded_evidence"], job.raw_evidence)
        self.assertEqual(sensitivity["judgment_status"], "UNPROVEN_NOT_RUN")

    def test_vietjobs_leakage_audit_ignores_unrelated_sources(self) -> None:
        class FakeQuery:
            def __init__(self, rows: list[dict]) -> None:
                self.rows = rows

            def values(self, *fields: str) -> "FakeQuery":
                return self

            def iterator(self, *, chunk_size: int):
                return iter(self.rows)

        class FakeManager:
            def __init__(self) -> None:
                self.filters: dict[str, object] = {}
                self.rows = [
                    {"chunk_id": "viet-clean", "source": "vietjobs", "active": True, "metadata": {}},
                    {
                        "chunk_id": "other-leaked",
                        "source": "other-source",
                        "active": True,
                        "metadata": {"technical_skills": ["Python"]},
                    },
                ]

            def filter(self, **filters: object) -> FakeQuery:
                self.filters = filters
                return FakeQuery([
                    row
                    for row in self.rows
                    if all(row.get(key) == value for key, value in filters.items())
                ])

        manager = FakeManager()
        with patch.object(audit_module, "CareerJobChunk", SimpleNamespace(objects=manager)):
            report = audit_derived_label_leakage(source="vietjobs")
        self.assertTrue(report["passed"])
        self.assertEqual(manager.filters, {"active": True, "source": "vietjobs"})


class CleanInputAndPoolRegressionTests(unittest.TestCase):
    @staticmethod
    def _write_clean_sidecar(root: Path) -> dict:
        vectors = np.asarray([[1.0] + [0.0] * 383, [0.0, 1.0] + [0.0] * 382], dtype=np.float32)
        np.save(root / "vectors.npy", vectors)
        rows = [
            {"row_index": 0, "chunk_id": "c1", "source": "vietjobs", "source_job_id": "J1", "job_key": "vietjobs::J1"},
            {"row_index": 1, "chunk_id": "c2", "source": "vietjobs", "source_job_id": "J2", "job_key": "vietjobs::J2"},
        ]
        map_path = root / "chunk_map.jsonl"
        map_path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
        identity = {
            "indexed_job_count": 2, "indexed_chunk_count": 2,
            "corpus_membership_sha256": "a" * 64, "corpus_chunks_sha256": "b" * 64,
            "chunk_context_sha256": "b" * 64,
        }
        provenance = {
            "status": "VERIFIED_CLEAN", "provenance_schema_version": CLEAN_INDEX_PROVENANCE_SCHEMA_VERSION,
            "indexing_timestamp": "2026-08-22T00:00:00+00:00", "index_type": CLEAN_INDEX_TYPE,
            "embedding_model": CLEAN_EMBEDDING_MODEL, "embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
            "input_field_policy": "raw-job-fields-only-no-forbidden-derived-fields-v1",
            "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
            "forbidden_derived_fields": ["derived_role_labels", "gold_nuggets", "judge_labels", "soft_skills", "technical_skills"],
            "forbidden_derived_fields_excluded": True, "derived_fields_included": [],
            "indexing_policy_version": "career-rag-clean-sidecar-build-v1", **identity,
            "python_version": "3.12.13", "numpy_version": "2.5.2",
            "sentence_transformers_version": "5.7.0", "transformers_version": "5.15.0",
            "torch_version": "2.13.0", "rank_bm25_version": "0.2.2",
            "embedding_model_revision": None, "embedding_model_revision_status": "UNVERIFIED",
            "vectors_filename": "vectors.npy", "vectors_sha256": hashlib.sha256((root / "vectors.npy").read_bytes()).hexdigest(),
            "vectors_dtype": "float32", "vectors_shape": [2, 384], "chunk_map_filename": "chunk_map.jsonl",
            "chunk_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest(),
            "embedding_source_sha256": "e" * 64, "clean_index_source_sha256": "s" * 64,
        }
        (root / "embedding_provenance.json").write_text(json.dumps(provenance), encoding="utf-8")
        return identity

    def _verify_fixture(self, root: Path, identity: dict) -> dict:
        class FakeRows:
            def iterator(self, *, chunk_size: int):
                return iter([
                    {"chunk_id": "c1", "source": "vietjobs", "source_job_id": "J1"},
                    {"chunk_id": "c2", "source": "vietjobs", "source_job_id": "J2"},
                ])

        with patch.object(clean_index_module, "V3_SNAPSHOT_INDEXED_JOB_COUNT", 2), \
                patch.object(clean_index_module, "V3_SNAPSHOT_ACTIVE_CHUNK_COUNT", 2), \
                patch.object(clean_index_module, "current_clean_corpus_identity", return_value=identity), \
                patch.object(clean_index_module, "_chunk_rows", return_value=FakeRows()), \
                patch.object(clean_index_module, "_source_hashes", return_value={"embedding_source_sha256": "e" * 64, "clean_index_source_sha256": "s" * 64}):
            return verify_clean_embedding_index(root)

    @staticmethod
    def _rehash_provenance(root: Path) -> None:
        path = root / "embedding_provenance.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["vectors_sha256"] = hashlib.sha256((root / "vectors.npy").read_bytes()).hexdigest()
        payload["chunk_map_sha256"] = hashlib.sha256((root / "chunk_map.jsonl").read_bytes()).hexdigest()
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_clean_embedding_input_is_deterministic_and_has_no_metadata_channel(self) -> None:
        row = {
            "job_title": "Backend Engineer", "location_key": "hanoi", "category_key": "software",
            "experience_level": "mid", "employment_type": "full-time", "section": "requirements",
            "content": "Python and PostgreSQL", "metadata": {"technical_skills": ["LEAK"]},
        }
        expected = (
            "passage: Job title: Backend Engineer\nLocation: hanoi\nCategory: software\n"
            "Experience level: mid\nEmployment type: full-time\nSection: requirements\n\nPython and PostgreSQL"
        )
        self.assertEqual(clean_embedding_input(row), expected)
        self.assertNotIn("LEAK", clean_embedding_input(row))
        self.assertNotIn("metadata", clean_embedding_input(row))

    def test_clean_builder_writes_aligned_vectors_map_and_real_provenance(self) -> None:
        rows = [
            {
                "chunk_id": f"c{index}",
                "source": "vietjobs",
                "source_job_id": f"J{index}",
                "chunk_index": 0,
                "job_title": f"Engineer {index}",
                "location_key": None,
                "category_key": "tech",
                "experience_level": None,
                "employment_type": None,
                "section": "description",
                "content": f"content {index}",
            }
            for index in (1, 2)
        ]

        class FakeRows:
            def iterator(self, *, chunk_size: int):
                return iter(rows)

        class FakeModel:
            def encode(self, texts, **kwargs):
                vectors = np.zeros((len(texts), CLEAN_EMBEDDING_DIMENSION), dtype=np.float32)
                vectors[:, 0] = 1.0
                return vectors

        embedder = SimpleNamespace(
            model_name=CLEAN_EMBEDDING_MODEL,
            dimension=CLEAN_EMBEDDING_DIMENSION,
            model=FakeModel(),
        )
        identity = {
            "indexed_job_count": 2,
            "indexed_chunk_count": 2,
            "corpus_membership_sha256": "a" * 64,
            "corpus_chunks_sha256": "b" * 64,
            "chunk_context_sha256": "c" * 64,
        }
        source_hashes = {
            "embedding_source_sha256": "e" * 64,
            "clean_index_source_sha256": "s" * 64,
        }
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(clean_index_module, "V3_SNAPSHOT_INDEXED_JOB_COUNT", 2), \
                patch.object(clean_index_module, "V3_SNAPSHOT_ACTIVE_CHUNK_COUNT", 2), \
                patch.object(clean_index_module, "current_clean_corpus_identity", return_value=identity), \
                patch.object(clean_index_module, "_chunk_rows", return_value=FakeRows()), \
                patch.object(clean_index_module, "_source_hashes", return_value=source_hashes), \
                patch.object(clean_index_module, "_runtime_provenance", return_value={
                    "python_version": "3.12.13", "numpy_version": "2.5.2",
                    "sentence_transformers_version": "5.7.0", "transformers_version": "5.15.0",
                    "torch_version": "2.13.0", "rank_bm25_version": "0.2.2",
                    "embedding_model_revision": None,
                    "embedding_model_revision_status": "UNVERIFIED",
                }), \
                patch.object(clean_index_module, "CareerEmbeddingService", return_value=embedder):
            output = Path(directory) / "index"
            result = build_clean_embedding_index(
                output_dir=output,
                batch_size=1,
            )
            self.assertEqual(result["verification"]["status"], "PASS")
            vectors = np.load(output / "vectors.npy")
            mapping = [json.loads(line) for line in (output / "chunk_map.jsonl").read_text(encoding="utf-8").splitlines()]
            provenance = json.loads((output / "embedding_provenance.json").read_text(encoding="utf-8"))
            self.assertEqual(vectors.shape, (2, CLEAN_EMBEDDING_DIMENSION))
            self.assertEqual([row["row_index"] for row in mapping], [0, 1])
            self.assertEqual([row["chunk_id"] for row in mapping], ["c1", "c2"])
            self.assertEqual(provenance["status"], "VERIFIED_CLEAN")
            self.assertEqual(provenance["sentence_transformers_version"], "5.7.0")
            self.assertIsNone(provenance["embedding_model_revision"])
            self.assertEqual(provenance["embedding_model_revision_status"], "UNVERIFIED")
            self.assertEqual(provenance["vectors_sha256"], hashlib.sha256((output / "vectors.npy").read_bytes()).hexdigest())
            with self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                build_clean_embedding_index(output_dir=output)

    def test_clean_runtime_provenance_records_versions_and_never_guesses_revision(self) -> None:
        versions = {
            "numpy": "2.5.2",
            "sentence-transformers": "5.7.0",
            "transformers": "5.15.0",
            "torch": "2.13.0",
            "rank-bm25": "0.2.2",
        }
        no_revision = SimpleNamespace(model=SimpleNamespace())
        with patch.object(
            clean_index_module.importlib.metadata,
            "version",
            side_effect=lambda distribution: versions[distribution],
        ), patch.object(clean_index_module.platform, "python_version", return_value="3.12.13"):
            provenance = clean_index_module._runtime_provenance(no_revision)
        self.assertEqual(provenance["python_version"], "3.12.13")
        self.assertEqual(provenance["rank_bm25_version"], "0.2.2")
        self.assertIsNone(provenance["embedding_model_revision"])
        self.assertEqual(provenance["embedding_model_revision_status"], "UNVERIFIED")

        commit = "a" * 40
        first_module = SimpleNamespace(
            auto_model=SimpleNamespace(config=SimpleNamespace(_commit_hash=commit)),
            tokenizer=SimpleNamespace(init_kwargs={}),
        )
        local_model = SimpleNamespace(_first_module=lambda: first_module)
        with patch.object(
            clean_index_module.importlib.metadata,
            "version",
            side_effect=lambda distribution: versions[distribution],
        ):
            verified = clean_index_module._runtime_provenance(
                SimpleNamespace(model=local_model)
            )
        self.assertEqual(verified["embedding_model_revision"], commit)
        self.assertEqual(
            verified["embedding_model_revision_status"],
            "VERIFIED_FROM_LOCAL_MODEL_CONFIG",
        )

    def test_runtime_query_encoder_must_match_frozen_dependencies_and_revision(self) -> None:
        frozen = {
            "numpy_version": "2.5.2",
            "sentence_transformers_version": "5.7.0",
            "transformers_version": "5.15.0",
            "torch_version": "2.13.0",
            "embedding_model_revision": "a" * 40,
            "embedding_model_revision_status": "VERIFIED_FROM_LOCAL_MODEL_CONFIG",
        }
        current = {**frozen, "python_version": "3.12.13"}
        embedder = SimpleNamespace()
        with patch.object(clean_index_module, "_runtime_provenance", return_value=current):
            observed = clean_index_module._assert_runtime_query_encoder_compatible(
                embedder,
                frozen,
            )
        self.assertEqual(observed["embedding_model_revision"], "a" * 40)

        for field in clean_index_module.QUERY_ENCODER_DEPENDENCY_FIELDS:
            mismatch = {**current, field: "different"}
            with self.subTest(field=field), \
                    patch.object(clean_index_module, "_runtime_provenance", return_value=mismatch), \
                    self.assertRaisesRegex(RuntimeError, field):
                clean_index_module._assert_runtime_query_encoder_compatible(
                    embedder,
                    frozen,
                )

        revision_mismatch = {
            **current,
            "embedding_model_revision": "b" * 40,
        }
        with patch.object(
            clean_index_module,
            "_runtime_provenance",
            return_value=revision_mismatch,
        ), self.assertRaisesRegex(RuntimeError, "model revision"):
            clean_index_module._assert_runtime_query_encoder_compatible(
                embedder,
                frozen,
            )

    def test_unverified_frozen_revision_remains_unverified_at_runtime(self) -> None:
        frozen = {
            "numpy_version": "2.5.2",
            "sentence_transformers_version": "5.7.0",
            "transformers_version": "5.15.0",
            "torch_version": "2.13.0",
            "embedding_model_revision": None,
            "embedding_model_revision_status": "UNVERIFIED",
        }
        current = {
            **frozen,
            "python_version": "3.12.13",
            "embedding_model_revision": "a" * 40,
            "embedding_model_revision_status": "VERIFIED_FROM_LOCAL_MODEL_CONFIG",
        }
        with patch.object(clean_index_module, "_runtime_provenance", return_value=current):
            observed = clean_index_module._assert_runtime_query_encoder_compatible(
                SimpleNamespace(),
                frozen,
            )
        self.assertIsNone(observed["embedding_model_revision"])
        self.assertEqual(observed["embedding_model_revision_status"], "UNVERIFIED")

    def test_dense_ranker_checks_runtime_query_encoder_contract_on_init(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._write_clean_sidecar(root)
            provenance = json.loads(
                (root / "embedding_provenance.json").read_text(encoding="utf-8")
            )
            embedder = SimpleNamespace(
                model_name=CLEAN_EMBEDDING_MODEL,
                dimension=CLEAN_EMBEDDING_DIMENSION,
            )
            with patch.object(
                clean_index_module,
                "verify_clean_embedding_index",
                return_value={
                    "passed": True,
                    "blockers": [],
                    "provenance": provenance,
                },
            ), patch.object(
                clean_index_module,
                "CareerEmbeddingService",
                return_value=embedder,
            ), patch.object(
                clean_index_module,
                "_assert_runtime_query_encoder_compatible",
                side_effect=RuntimeError("runtime encoder drift"),
            ) as compatible, self.assertRaisesRegex(RuntimeError, "runtime encoder drift"):
                CleanBenchmarkDenseRanker(root)
            compatible.assert_called_once_with(embedder, provenance)

    def test_clean_verifier_rejects_inconsistent_model_revision_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            provenance_path = root / "embedding_provenance.json"
            provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
            provenance["embedding_model_revision_status"] = "VERIFIED_FROM_LOCAL_MODEL_CONFIG"
            provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
            result = self._verify_fixture(root, identity)
        self.assertFalse(result["passed"])
        self.assertTrue(any("revision provenance" in blocker for blocker in result["blockers"]))

    def test_clean_sidecar_detects_vector_map_nan_dimension_and_corpus_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            self.assertTrue(self._verify_fixture(root, identity)["passed"])
            with (root / "vectors.npy").open("ab") as handle:
                handle.write(b"tamper")
            self.assertFalse(self._verify_fixture(root, identity)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            map_path = root / "chunk_map.jsonl"
            map_path.write_text(map_path.read_text(encoding="utf-8").replace('"row_index": 1', '"row_index": 2'), encoding="utf-8")
            self.assertFalse(self._verify_fixture(root, identity)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            map_path = root / "chunk_map.jsonl"
            rows = [json.loads(line) for line in map_path.read_text(encoding="utf-8").splitlines()]
            rows[0]["technical_skills"] = ["forbidden"]
            map_path.write_text(
                "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                encoding="utf-8",
            )
            self._rehash_provenance(root)
            self.assertFalse(self._verify_fixture(root, identity)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            mismatched = {**identity, "corpus_chunks_sha256": "z" * 64, "chunk_context_sha256": "z" * 64}
            self.assertFalse(self._verify_fixture(root, mismatched)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            vectors = np.load(root / "vectors.npy")
            vectors[0, 0] = np.nan
            np.save(root / "vectors.npy", vectors)
            self._rehash_provenance(root)
            self.assertFalse(self._verify_fixture(root, identity)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            vectors = np.load(root / "vectors.npy")
            vectors[0, 0] = np.inf
            np.save(root / "vectors.npy", vectors)
            self._rehash_provenance(root)
            self.assertFalse(self._verify_fixture(root, identity)["passed"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            identity = self._write_clean_sidecar(root)
            np.save(root / "vectors.npy", np.zeros((2, 383), dtype=np.float32))
            self._rehash_provenance(root)
            self.assertFalse(self._verify_fixture(root, identity)["passed"])

    def test_missing_clean_sidecar_fails_and_corpus_identity_query_is_read_only(self) -> None:
        identity = {
            "indexed_job_count": 0,
            "indexed_chunk_count": 0,
            "corpus_membership_sha256": hashlib.sha256().hexdigest(),
            "corpus_chunks_sha256": hashlib.sha256().hexdigest(),
            "chunk_context_sha256": hashlib.sha256().hexdigest(),
        }
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(clean_index_module, "current_clean_corpus_identity", return_value=identity), \
                patch.object(clean_index_module, "_source_hashes", return_value={}):
            result = verify_clean_embedding_index(Path(directory) / "missing")
        self.assertFalse(result["passed"])
        self.assertTrue(any("provenance unreadable" in blocker for blocker in result["blockers"]))

        calls: list[tuple[str, object]] = []

        class ReadOnlyRows:
            def order_by(self, *fields):
                calls.append(("order_by", fields))
                return self

            def values(self, *fields):
                calls.append(("values", fields))
                return self

            def iterator(self, *, chunk_size: int):
                calls.append(("iterator", chunk_size))
                return iter(())

        class ReadOnlyManager:
            def filter(self, **filters):
                calls.append(("filter", filters))
                return ReadOnlyRows()

        with patch.object(clean_index_module.CareerJobChunk, "objects", ReadOnlyManager()):
            observed = clean_index_module.current_clean_corpus_identity()
        self.assertEqual(observed["indexed_job_count"], 0)
        self.assertEqual([name for name, _ in calls], ["filter", "order_by", "values", "iterator"])

    def test_full_direct_union_pool_ignores_max_pool_and_retains_ranks(self) -> None:
        jobs = _jobs(9)
        pooler = object.__new__(PoolingService)
        pooler.by_key = {job.job_key: job for job in jobs}
        pooler.dense_ranker = object()
        pooler.bm25 = lambda query, depth: ["vietjobs::J1", "vietjobs::J2", "vietjobs::J3"]
        pooler.dense = lambda query, depth: ["vietjobs::J4", "vietjobs::J5", "vietjobs::J6"]
        pooler.title_lexical = lambda query, depth: ["vietjobs::J7", "vietjobs::J8", "vietjobs::J9"]
        queries = [
            CareerQuery("q-direct", "topic-1", "direct", "x"),
            CareerQuery("q-conv", "topic-1", "conversational", "x"),
            CareerQuery("q-noisy", "topic-1", "noisy", "x"),
        ]
        candidates = pooler.pool_topic("topic-1", queries, depth=3, max_pool=1)
        self.assertEqual({candidate.job_key for candidate in candidates}, {job.job_key for job in jobs})
        for candidate in candidates:
            self.assertTrue(candidate.ranks)
            self.assertTrue(any(name.startswith(("bm25:", "dense:", "title:")) for name in candidate.ranks))
        again = pooler.pool_topic("topic-1", queries, depth=3, max_pool=999)
        self.assertEqual([item.job_key for item in candidates], [item.job_key for item in again])

    def test_rrf_cannot_remove_direct_union_candidate(self) -> None:
        detail = audit_pool_coverage({
            "topic": {"direct": {
                "bm25": ["A", "B"], "dense": ["C", "D"], "title": ["E", "F"],
            }}
        }, depths=(2,), max_pool=1)["reports"]["2"]["topics"]["topic"]
        self.assertEqual(detail["judged_candidate_count"], 6)
        self.assertEqual(detail["legacy_max_pool_dropped_count"], 5)
        self.assertEqual(
            detail["leave_one_contributor_out"]["title"]["metric_sensitivity_status"],
            "UNPROVEN_WITHOUT_QRELS",
        )

    def test_title_rank_twenty_survives_below_legacy_max_pool_cut(self) -> None:
        job_ids = [f"J{index:03d}" for index in range(1, 141)]
        jobs = [
            CorpusJob("vietjobs", job_id, job_id, "tech", None, None, None, ())
            for job_id in job_ids
        ]
        pooler = object.__new__(PoolingService)
        pooler.by_key = {job.job_key: job for job in jobs}

        variant_offset = {"direct": 0, "conversational": 20, "noisy": 40}

        def ranking(query: str, start: int) -> list[str]:
            offset = variant_offset[query]
            return [f"vietjobs::J{start + offset + index:03d}" for index in range(20)]

        pooler.bm25 = lambda query, depth: ranking(query, 1)[:depth]
        pooler.dense = lambda query, depth: ranking(query, 1)[:depth]
        pooler.title_lexical = lambda query, depth: ranking(query, 81)[:depth]
        queries = [
            CareerQuery(f"q-{variant}", "topic", variant, variant)
            for variant in BASE_QUERY_VARIANTS
        ]
        candidates = pooler.pool_topic("topic", queries, depth=20, max_pool=80)
        by_key = {candidate.job_key: candidate for candidate in candidates}
        self.assertGreater(len(candidates), 80)
        self.assertIn("vietjobs::J140", by_key)
        self.assertEqual(by_key["vietjobs::J140"].ranks["title:noisy"], 20)

    def test_clean_dense_ranker_collapses_unique_jobs_with_deterministic_ties(self) -> None:
        class Embedder:
            def embed_query(self, query: str) -> np.ndarray:
                return np.asarray([1.0] + [0.0] * 383, dtype=np.float32)

        ranker = object.__new__(CleanBenchmarkDenseRanker)
        ranker.vectors = np.asarray([
            [1.0] + [0.0] * 383,
            [1.0] + [0.0] * 383,
            [0.8] + [0.0] * 383,
        ], dtype=np.float32)
        ranker._job_keys = np.asarray(["vietjobs::A", "vietjobs::A", "vietjobs::B"], dtype=str)
        ranker._chunk_ids = np.asarray(["a-2", "a-1", "b-1"], dtype=str)
        ranker._row_indices = np.arange(3)
        ranker.embedder = Embedder()
        self.assertEqual(ranker.rank_job_keys("query", 2), ["vietjobs::A", "vietjobs::B"])

    def test_v3_pooling_refuses_production_dense_fallback(self) -> None:
        with self.assertRaises(TypeError):
            PoolingService(_jobs(2))

        pooler = object.__new__(PoolingService)
        pooler.by_key = {job.job_key: job for job in _jobs(3)}
        pooler.bm25 = lambda query, depth: ["vietjobs::J1"]
        pooler.dense = lambda query, depth: ["vietjobs::J2"]
        pooler.title_lexical = lambda query, depth: ["vietjobs::J3"]
        query = CareerQuery("q", "topic", "direct", "query")
        with patch("apps.career.retrieval.CareerRetriever", side_effect=AssertionError("production fallback")):
            candidates = pooler.pool_topic("topic", [query], depth=1, max_pool=1)
        self.assertEqual({candidate.job_key for candidate in candidates}, {job.job_key for job in _jobs(3)})


class QrelAndBootstrapRegressionTests(unittest.TestCase):
    def test_known_grade_zero_is_not_unjudged(self) -> None:
        self.assertEqual(ndcg_at_k(["zero"], {"zero": 0}, 1), 0.0)

    def test_uncertain_condenses_without_consuming_metric_rank(self) -> None:
        result = condense_uncertain_ranking(
            ["uncertain", "good", "zero"],
            certain_qrels={"good": 3, "zero": 0}, uncertain_job_keys={"uncertain"}, k=2,
        )
        self.assertEqual(result["ranking"], ["good", "zero"])
        self.assertEqual(result["uncertain_skipped"], 1)
        self.assertEqual(result["judged_fraction"], 1.0)
        self.assertEqual(result["certain_fraction"], 2 / 3)

    def test_unjudged_document_is_not_grade_zero(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unjudged document encountered"):
            condense_uncertain_ranking(["unknown"], certain_qrels={"zero": 0}, uncertain_job_keys=set(), k=1)
        with self.assertRaisesRegex(ValueError, "Unjudged document encountered"):
            ndcg_at_k(["unknown"], {"zero": 0}, 1)

    def test_qrels_partition_pool_exactly_once(self) -> None:
        topic = CareerTopic("topic", "family", "broad", "Tech", "tech")
        candidate = PooledCandidate("topic", "vietjobs", "J1", "Engineer", "tech", None)
        certain = RelevanceJudgment("topic", "vietjobs", "J1", 0, (0, 0, 0), False)
        valid = audit_qrels([topic], [candidate], [certain], min_strong_per_topic=0)
        self.assertTrue(valid["passed"], valid)

        missing = audit_qrels([topic], [candidate], [], min_strong_per_topic=0)
        self.assertFalse(missing["passed"])
        self.assertEqual(missing["missing_qrels"], [("topic", "vietjobs::J1")])

        duplicate = audit_qrels(
            [topic], [candidate], [certain, certain], min_strong_per_topic=0,
        )
        self.assertFalse(duplicate["passed"])
        self.assertEqual(duplicate["duplicate_qrel_keys"], [("topic", "vietjobs::J1")])

    def test_missing_certain_or_uncertain_qrels_file_refuses_evaluation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FileNotFoundError):
                _load_qrels(root)
            (root / "qrels.silver.jsonl").write_text("", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                _load_qrels(root)

    def test_strong_precision_uses_requested_k_denominator(self) -> None:
        self.assertEqual(strong_precision_at_k([], {}, 5), 0.0)
        self.assertEqual(
            strong_precision_at_k(["s1", "s2", "zero"], {"s1": 3, "s2": 2, "zero": 0}, 5),
            0.4,
        )
        self.assertEqual(
            strong_precision_at_k(
                ["s1", "s2", "weak", "zero1", "zero2"],
                {"s1": 3, "s2": 2, "weak": 1, "zero1": 0, "zero2": 0},
                5,
            ),
            0.4,
        )

    def test_observed_support_coverage_is_not_exhaustive_recall(self) -> None:
        # True support may be J1..J4, but adaptive storage observed only J1,J2.
        nuggets = [
            Nugget(
                "topic", "N1", "Skill", "skill",
                ("vietjobs::J1", "vietjobs::J2"), 2, -1.0, 1.0, "VITAL",
            )
        ]
        self.assertEqual(observed_support_coverage_at_k(["vietjobs::J1"], nuggets, 5), 1.0)
        self.assertEqual(observed_support_coverage_at_k(["vietjobs::J3"], nuggets, 5), 0.0)
        self.assertIn("neither exhaustive nugget recall", observed_support_coverage_at_k.__doc__)
        self.assertIn("nor a headline metric", observed_support_coverage_at_k.__doc__)

    def test_weighted_nugget_metric_is_coverage_only(self) -> None:
        nuggets = [
            Nugget("topic", "N1", "Vital", "vital", (), 0, -1.0, 1.0, "VITAL"),
            Nugget("topic", "N2", "Okay", "okay", (), 0, -1.0, 0.5, "OKAY"),
        ]
        self.assertEqual(weighted_nugget_coverage({"N2"}, nuggets), 1 / 3)

        class SameObservableJudge:
            def json_call(self, **kwargs):
                return {
                    "matched_nugget_ids": ["N1"],
                    "claim_count": 2,
                    "supported_claim_count": 2,
                    "unsupported_claim_count": 0,
                    "citation_required_claim_count": 0,
                    "cited_claim_count": 0,
                    "citation_supported_count": 0,
                    "context_used_job_keys": [],
                }

        # The schema cannot distinguish "two paraphrases of N1" from "N1 plus
        # another supported claim outside the canonical nugget set". Both
        # therefore identify gold-nugget coverage, not nugget precision/F1.
        context = [_as_retrieved(_jobs(1)[0])]
        first = _evaluate_answer(
            SameObservableJudge(), query="q", answer="A + paraphrase(A)",
            nuggets=nuggets, context_jobs=context,
        )
        second = _evaluate_answer(
            SameObservableJudge(), query="q", answer="A + supported non-canonical claim",
            nuggets=nuggets, context_jobs=context,
        )
        self.assertEqual(first["weighted_nugget_coverage"], second["weighted_nugget_coverage"])
        self.assertNotIn("weighted_nugget_precision", first)
        self.assertNotIn("weighted_nugget_f1", first)

    def test_family_cluster_bootstrap_is_deterministic_and_keeps_siblings(self) -> None:
        values = {"broad": 0.0, "specific": 1.0, "other": 0.5}
        families = {"broad": "F1", "specific": "F1", "other": "F2"}
        first = family_cluster_bootstrap_ci(values, families, samples=100, seed=7)
        second = family_cluster_bootstrap_ci(values, families, samples=100, seed=7)
        self.assertEqual(first, second)
        paired = family_cluster_paired_bootstrap(values, families, samples=100, seed=7)
        self.assertEqual(paired["bootstrap_unit"], "family")
        # The two F1 topics are represented together: changing their internal
        # variant count is impossible because this helper accepts topic means.
        self.assertEqual(paired["mean_family_delta"], 0.5)
        self.assertEqual(
            aggregate_topic_values_by_family(values, families),
            {"F1": 0.5, "F2": 0.5},
        )

    def test_paired_family_sign_flip_is_exact_and_deterministic(self) -> None:
        deltas = {"F1-broad": 1.0, "F1-specific": 1.0, "F2-broad": 1.0, "F2-specific": 1.0}
        families = {topic_id: topic_id.split("-")[0] for topic_id in deltas}
        first = paired_family_sign_flip_test(deltas, families, seed=11)
        second = paired_family_sign_flip_test(deltas, families, seed=999)
        self.assertEqual(first, second)
        self.assertEqual(first["test_mode"], "exact")
        self.assertEqual(first["assignments"], 4)
        self.assertEqual(first["paired_sign_flip_p_value"], 0.5)
        self.assertEqual(first["mean_family_delta"], 1.0)


class EvaluationProtocolFreezeTests(unittest.TestCase):
    @staticmethod
    def _manifest(root: Path, *, marker: str = "a") -> Path:
        root.mkdir(parents=True, exist_ok=True)
        path = root / "benchmark_manifest.json"
        path.write_text(
            json.dumps({
                "benchmark_name": "CareerRAGBench-Auto-V3",
                "benchmark_version": "3.0",
                "marker": marker,
            }, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    @staticmethod
    def _freeze(root: Path) -> dict:
        EvaluationProtocolFreezeTests._manifest(root)
        with patch.object(
            protocol_module,
            "verify_frozen_benchmark",
            return_value={"passed": True, "blockers": []},
        ):
            return freeze_evaluation_protocol(
                root,
                retrieval_top_k=10,
                rag_retriever_system="dense",
                rag_top_k=5,
                generator_model="generator-v1",
                judge_model="judge-v1",
                bootstrap_seed=123,
                bootstrap_samples=500,
                alpha=0.05,
            )

    @staticmethod
    def _retrieval_runtime(**updates) -> dict:
        arguments = {
            "top_k": 10,
            "bootstrap_seed": 123,
            "bootstrap_samples": 500,
            "bootstrap_alpha": 0.05,
        }
        arguments.update(updates)
        return retrieval_runtime_settings(**arguments)

    @staticmethod
    def _rag_runtime(**updates) -> dict:
        arguments = {
            "retriever_system": "dense",
            "top_k": 5,
            "generator_model": "generator-v1",
            "judge_model": "judge-v1",
            "generation_temperature": GENERATION_TEMPERATURE,
            "bootstrap_seed": 123,
            "bootstrap_samples": 500,
            "bootstrap_alpha": 0.05,
        }
        arguments.update(updates)
        return rag_runtime_settings(**arguments)

    def test_protocol_has_exact_schema_is_bound_and_cannot_be_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self._freeze(root)
            self.assertEqual(set(payload), TOP_LEVEL_KEYS)
            self.assertEqual(set(payload["benchmark"]), BENCHMARK_KEYS)
            self.assertEqual(set(payload["retrieval"]), RETRIEVAL_KEYS)
            self.assertEqual(set(payload["rag"]), RAG_KEYS)
            self.assertEqual(set(payload["statistics"]), STATISTICS_KEYS)
            self.assertEqual(set(payload["implementation"]), IMPLEMENTATION_KEYS)
            self.assertTrue({
                "apps/career/evaluation/career_rag/metrics.py",
                "apps/career/evaluation/career_rag/run_retrieval_eval.py",
                "apps/career/evaluation/career_rag/clean_index.py",
                "apps/career/evaluation/career_rag/pooling.py",
                "apps/career/evaluation/career_rag/evaluation_integrity.py",
            }.issubset(payload["implementation"]["retrieval_source_files"]))
            self.assertTrue({
                "apps/career/evaluation/career_rag/run_rag_eval.py",
                "apps/career/evaluation/career_rag/metrics.py",
                "apps/career/evaluation/career_rag/evidence.py",
                "apps/career/evaluation/career_rag/judges.py",
                "apps/career/answering.py",
            }.issubset(payload["implementation"]["rag_source_files"]))
            self.assertEqual(
                payload["benchmark"]["benchmark_manifest_sha256"],
                hashlib.sha256((root / "benchmark_manifest.json").read_bytes()).hexdigest(),
            )
            self.assertTrue((root / PROTOCOL_RELATIVE_PATH).is_file())
            self.assertTrue((root / PROTOCOL_HASH_RELATIVE_PATH).is_file())
            self.assertEqual(load_and_verify_evaluation_protocol(root), payload)
            with patch.object(
                protocol_module,
                "verify_frozen_benchmark",
                return_value={"passed": True, "blockers": []},
            ), self.assertRaisesRegex(RuntimeError, "Refusing to overwrite"):
                freeze_evaluation_protocol(
                    root,
                    generator_model="generator-v1",
                    judge_model="judge-v1",
                )

    def test_matching_runtime_is_accepted_and_every_frozen_setting_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._freeze(root)
            assert_test_evaluation_protocol(
                root,
                evaluator="RETRIEVAL",
                runtime_settings=self._retrieval_runtime(),
            )
            assert_test_evaluation_protocol(
                root,
                evaluator="RAG",
                runtime_settings=self._rag_runtime(),
            )
            rag_mismatches = (
                {"generator_model": "generator-v2"},
                {"judge_model": "judge-v2"},
                {"retriever_system": "hybrid"},
                {"top_k": 6},
                {"generation_temperature": 1},
                {"bootstrap_seed": 124},
                {"bootstrap_samples": 501},
                {"bootstrap_alpha": 0.10},
            )
            for updates in rag_mismatches:
                with self.subTest(updates=updates), self.assertRaisesRegex(
                    RuntimeError, "do not match"
                ):
                    assert_test_evaluation_protocol(
                        root,
                        evaluator="RAG",
                        runtime_settings=self._rag_runtime(**updates),
                    )
            with self.assertRaisesRegex(RuntimeError, "do not match"):
                assert_test_evaluation_protocol(
                    root,
                    evaluator="RETRIEVAL",
                    runtime_settings=self._retrieval_runtime(top_k=11),
                )

    def test_tampered_protocol_other_benchmark_and_changed_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._freeze(root)
            with (root / PROTOCOL_RELATIVE_PATH).open("ab") as handle:
                handle.write(b" ")
            with self.assertRaisesRegex(RuntimeError, "SHA256 mismatch"):
                load_and_verify_evaluation_protocol(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._freeze(root)
            self._manifest(root, marker="another-benchmark-manifest")
            with self.assertRaisesRegex(RuntimeError, "another benchmark manifest"):
                load_and_verify_evaluation_protocol(root)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = self._freeze(root)
            changed = dict(payload["implementation"])
            changed["retrieval_source_sha256"] = "0" * 64
            with patch.object(
                protocol_module,
                "semantic_source_identity",
                return_value=changed,
            ), self.assertRaisesRegex(RuntimeError, "source identity changed"):
                load_and_verify_evaluation_protocol(root)

    def test_test_protocol_mismatch_is_rejected_before_lock_consumption(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._freeze(root)
            base = {
                "generator_model": "generator-v1",
                "judge_model": "judge-v1",
                "retriever_system": "dense",
                "top_k": 5,
                "generation_temperature": GENERATION_TEMPERATURE,
                "bootstrap_seed": 123,
                "bootstrap_samples": 500,
                "bootstrap_alpha": 0.05,
            }
            for updates in (
                {"generator_model": "wrong-generator"},
                {"judge_model": "wrong-judge"},
                {"retriever_system": "hybrid"},
                {"top_k": 6},
                {"generation_temperature": 1},
                {"bootstrap_seed": 124},
                {"bootstrap_samples": 501},
                {"bootstrap_alpha": 0.10},
            ):
                settings = {**base, **updates}
                with self.subTest(updates=updates), \
                        patch.object(rag_eval_module, "assert_evaluation_integrity", return_value={}), \
                        patch.object(rag_eval_module, "consume_test_lock") as consume, \
                        self.assertRaisesRegex(RuntimeError, "do not match"):
                    rag_eval_module.run_rag_eval(
                        split="test",
                        output_dir=root,
                        allow_test=True,
                        **settings,
                    )
                consume.assert_not_called()
            self.assertFalse(
                (root / "reports" / "TEST_RAG_ALREADY_RUN.lock").exists()
            )

            with patch.object(rag_eval_module, "assert_evaluation_integrity", return_value={}), \
                    patch.object(
                        rag_eval_module,
                        "consume_test_lock",
                        side_effect=RuntimeError("reached lock stage"),
                    ) as consume, \
                    self.assertRaisesRegex(RuntimeError, "reached lock stage"):
                rag_eval_module.run_rag_eval(
                    split="test",
                    output_dir=root,
                    allow_test=True,
                    **base,
                )
            consume.assert_called_once()

    def test_dev_evaluation_does_not_require_protocol_or_consume_test_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(
                retrieval_eval_module,
                "assert_evaluation_integrity",
                side_effect=RuntimeError("stop after DEV integrity entry"),
            ), patch.object(retrieval_eval_module, "consume_test_lock") as consume:
                with self.assertRaisesRegex(RuntimeError, "DEV integrity"):
                    retrieval_eval_module.run_retrieval_eval(
                        split="dev", output_dir=root
                    )
            consume.assert_not_called()
            self.assertFalse((root / PROTOCOL_RELATIVE_PATH).exists())

    def test_missing_test_protocol_fails_before_lock(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(retrieval_eval_module, "assert_evaluation_integrity", return_value={}), \
                    patch.object(retrieval_eval_module, "consume_test_lock") as consume, \
                    self.assertRaisesRegex(RuntimeError, "missing or invalid"):
                retrieval_eval_module.run_retrieval_eval(
                    split="test",
                    output_dir=root,
                    allow_test=True,
                )
            consume.assert_not_called()


class EvaluatorTestLockRegressionTests(unittest.TestCase):
    def test_evaluator_rejects_sidecar_identity_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "benchmark"
            sidecar = Path(directory) / "sidecar"
            root.mkdir()
            sidecar.mkdir()
            (root / "benchmark_manifest.json").write_text(
                json.dumps({
                    "configuration": {
                        "clean_embedding_vectors_sha256": "frozen-vectors",
                        "clean_embedding_chunk_map_sha256": "frozen-map",
                        "clean_embedding_provenance_sha256": "frozen-provenance",
                        "clean_embedding_corpus_membership_sha256": "frozen-membership",
                        "clean_embedding_chunk_context_sha256": "frozen-context",
                    }
                }),
                encoding="utf-8",
            )
            (sidecar / "embedding_provenance.json").write_text("{}", encoding="utf-8")
            clean = {
                "passed": True,
                "blockers": [],
                "provenance": {
                    "vectors_sha256": "other-vectors",
                    "chunk_map_sha256": "frozen-map",
                    "corpus_membership_sha256": "frozen-membership",
                    "chunk_context_sha256": "frozen-context",
                },
            }
            with patch.object(
                integrity_module,
                "verify_frozen_benchmark",
                return_value={"passed": True, "blockers": []},
            ), patch.object(
                integrity_module,
                "verify_clean_embedding_index",
                return_value=clean,
            ):
                result = integrity_module.verify_evaluation_integrity(
                    root,
                    clean_index_dir=sidecar,
                )
            self.assertFalse(result["passed"])
            self.assertTrue(any("does not match" in blocker for blocker in result["blockers"]))

    def test_retrieval_and_rag_test_locks_are_evaluator_specific_and_one_shot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "reports").mkdir()
            retrieval_lock = consume_test_lock(root, evaluator="RETRIEVAL", allow_test=True)
            self.assertEqual(retrieval_lock.name, "TEST_RETRIEVAL_ALREADY_RUN.lock")
            with self.assertRaisesRegex(RuntimeError, "already been run"):
                consume_test_lock(root, evaluator="RETRIEVAL", allow_test=True)
            rag_lock = consume_test_lock(root, evaluator="RAG", allow_test=True)
            self.assertEqual(rag_lock.name, "TEST_RAG_ALREADY_RUN.lock")
            with self.assertRaisesRegex(RuntimeError, "already been run"):
                consume_test_lock(root, evaluator="RAG", allow_test=True)
            with self.assertRaisesRegex(RuntimeError, "locked"):
                consume_test_lock(root, evaluator="RAG", allow_test=False)

    def test_dev_path_never_consumes_a_test_lock_before_integrity_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(retrieval_eval_module, "assert_evaluation_integrity", side_effect=RuntimeError("bad freeze")):
                with self.assertRaisesRegex(RuntimeError, "bad freeze"):
                    retrieval_eval_module.run_retrieval_eval(split="dev", output_dir=root)
            self.assertFalse((root / "reports" / "TEST_RETRIEVAL_ALREADY_RUN.lock").exists())


class RagJudgeSchemaRegressionTests(unittest.TestCase):
    @staticmethod
    def _valid_payload() -> dict:
        return {
            "matched_nugget_ids": ["N1"], "claim_count": 3, "supported_claim_count": 2,
            "unsupported_claim_count": 1, "citation_required_claim_count": 2, "cited_claim_count": 2,
            "citation_supported_count": 1, "context_used_job_keys": ["vietjobs::J1"],
        }

    def test_rag_judge_exact_schema_and_all_strict_type_failures(self) -> None:
        valid = self._valid_payload()
        parsed = validate_rag_judge_payload(valid, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        self.assertEqual(parsed["claim_count"], 3)
        for field, invalid in (("claim_count", "3"), ("claim_count", 3.0), ("claim_count", True), ("claim_count", -1)):
            with self.subTest(field=field, invalid=invalid):
                payload = self._valid_payload()
                payload[field] = invalid
                with self.assertRaises(ValueError):
                    validate_rag_judge_payload(payload, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        missing = self._valid_payload()
        del missing["claim_count"]
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(missing, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        extra = self._valid_payload()
        extra["extra"] = 1
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(extra, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        fake_nugget = self._valid_payload()
        fake_nugget["matched_nugget_ids"] = ["FAKE"]
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(fake_nugget, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        fake_context = self._valid_payload()
        fake_context["context_used_job_keys"] = ["vietjobs::FAKE"]
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(fake_context, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        duplicate_nugget = self._valid_payload()
        duplicate_nugget["matched_nugget_ids"] = ["N1", "N1"]
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(
                duplicate_nugget,
                gold_nugget_ids={"N1"},
                context_job_keys={"vietjobs::J1"},
            )

    def test_rag_judge_count_arithmetic_and_no_context_invariants(self) -> None:
        for updates in (
            {"supported_claim_count": 4},
            {"unsupported_claim_count": 2},
            {"citation_supported_count": 3},
            {"cited_claim_count": 3},
        ):
            with self.subTest(updates=updates):
                payload = self._valid_payload()
                payload.update(updates)
                with self.assertRaises(ValueError):
                    validate_rag_judge_payload(payload, gold_nugget_ids={"N1"}, context_job_keys={"vietjobs::J1"})
        no_context = self._valid_payload()
        no_context.update({
            "matched_nugget_ids": [], "claim_count": 1, "supported_claim_count": 1, "unsupported_claim_count": 0,
            "citation_required_claim_count": 0, "cited_claim_count": 0, "citation_supported_count": 0,
            "context_used_job_keys": [],
        })
        with self.assertRaises(ValueError):
            validate_rag_judge_payload(no_context, gold_nugget_ids={"N1"}, context_job_keys=set())

    def test_rag_schema_retry_uses_distinct_cache_prompts_and_exact_budget(self) -> None:
        class FakeJudge:
            def __init__(self, payloads: list[object]) -> None:
                self.payloads, self.calls = list(payloads), []

            def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
                self.calls.append((system, user, retries))
                return self.payloads.pop(0)

        nugget = Nugget("topic", "N1", "Python", "python", ("vietjobs::J1",), 1, -1.0, 1.0, "VITAL")
        job = _as_retrieved(_jobs(1)[0])
        malformed = {"claim_count": 1}
        judge = FakeJudge([malformed, self._valid_payload()])
        _evaluate_answer(judge, query="q", answer="a", nuggets=[nugget], context_jobs=[job])
        self.assertEqual(len(judge.calls), 2)
        self.assertIn("SCHEMA_RETRY_ATTEMPT=1", judge.calls[1][1])
        exhausted = FakeJudge([malformed, malformed, malformed])
        with self.assertRaisesRegex(RuntimeError, "after 2 retries"):
            _evaluate_answer(exhausted, query="q", answer="a", nuggets=[nugget], context_jobs=[job])
        self.assertEqual(len(exhausted.calls), 3)

    def test_context_aliases_normalize_before_strict_validation(self) -> None:
        class FakeJudge:
            def __init__(self, context_used_job_keys: list[str]) -> None:
                self.context_used_job_keys = context_used_job_keys
                self.calls: list[tuple[str, str]] = []

            def json_call(self, *, system: str, user: str, retries: int = 2) -> dict:
                self.calls.append((system, user))
                payload = RagJudgeSchemaRegressionTests._valid_payload()
                payload["context_used_job_keys"] = list(self.context_used_job_keys)
                return payload

        nugget = Nugget(
            "topic", "N1", "Python", "python", ("vietjobs::J1",),
            1, -1.0, 1.0, "VITAL",
        )
        jobs = [_as_retrieved(job) for job in _jobs(2)]

        alias_judge = FakeJudge(["J1", "J2"])
        alias_result = _evaluate_answer(
            alias_judge,
            query="q",
            answer="a",
            nuggets=[nugget],
            context_jobs=jobs,
        )
        self.assertEqual(
            alias_result["context_used_job_keys"],
            ["vietjobs::J1", "vietjobs::J2"],
        )
        self.assertIn("never display aliases such as \"J1\"", alias_judge.calls[0][0])

        canonical_judge = FakeJudge(["vietjobs::J1", "vietjobs::J2"])
        canonical_result = _evaluate_answer(
            canonical_judge,
            query="q",
            answer="a",
            nuggets=[nugget],
            context_jobs=jobs,
        )
        self.assertEqual(
            canonical_result["context_used_job_keys"],
            ["vietjobs::J1", "vietjobs::J2"],
        )

        unknown_judge = FakeJudge(["J999"])
        with self.assertRaisesRegex(RuntimeError, "unsupported IDs"):
            _evaluate_answer(
                unknown_judge,
                query="q",
                answer="a",
                nuggets=[nugget],
                context_jobs=jobs,
            )
        self.assertIn(
            "use exact JOB_KEY values for context_used_job_keys and never aliases",
            unknown_judge.calls[1][1],
        )

        duplicate_judge = FakeJudge(["J1", "vietjobs::J1"])
        with self.assertRaisesRegex(RuntimeError, "unique IDs"):
            _evaluate_answer(
                duplicate_judge,
                query="q",
                answer="a",
                nuggets=[nugget],
                context_jobs=jobs,
            )

    def test_no_rag_grounding_is_not_applicable_and_never_aggregates_as_zero(self) -> None:
        class FakeJudge:
            def json_call(self, *, system: str, user: str, retries: int = 2) -> dict:
                return {
                    "matched_nugget_ids": ["N1"],
                    "claim_count": 5,
                    "supported_claim_count": 0,
                    "unsupported_claim_count": 5,
                    "citation_required_claim_count": 0,
                    "cited_claim_count": 0,
                    "citation_supported_count": 0,
                    "context_used_job_keys": [],
                }

        nugget = Nugget(
            "topic",
            "N1",
            "Python",
            "python",
            ("vietjobs::J1",),
            1,
            -1.0,
            1.0,
            "VITAL",
        )
        result = _evaluate_answer(
            FakeJudge(),
            query="q",
            answer="five claims",
            nuggets=[nugget],
            context_jobs=[],
        )
        self.assertEqual(result["weighted_nugget_coverage"], 1.0)
        self.assertEqual(result["claim_count"], 5)
        self.assertEqual(result["context_used_job_keys"], [])
        self.assertEqual(
            result["grounding_status"],
            "NOT_APPLICABLE_NO_RETRIEVED_CONTEXT",
        )
        for metric in (
            "faithfulness",
            "unsupported_claim_rate",
            "citation_coverage",
            "citation_support_rate",
            "context_utilization",
        ):
            self.assertIsNone(result[metric])
            summary = rag_eval_module._rag_metric_summary(
                {"topic": [result]},
                metric,
                {"topic": "family"},
                bootstrap_samples=10,
                bootstrap_seed=7,
                bootstrap_alpha=0.05,
            )
            self.assertIsNone(summary["mean"])
            self.assertIsNone(summary["ci"])
            self.assertEqual(summary["status"], "NOT_APPLICABLE")

    def test_context_rag_grounding_metrics_remain_numeric(self) -> None:
        class FakeJudge:
            def json_call(self, *, system: str, user: str, retries: int = 2) -> dict:
                return RagJudgeSchemaRegressionTests._valid_payload()

        nugget = Nugget(
            "topic",
            "N1",
            "Python",
            "python",
            ("vietjobs::J1",),
            1,
            -1.0,
            1.0,
            "VITAL",
        )
        result = _evaluate_answer(
            FakeJudge(),
            query="q",
            answer="grounded claims",
            nuggets=[nugget],
            context_jobs=[_as_retrieved(_jobs(1)[0])],
        )
        self.assertEqual(result["grounding_status"], "APPLICABLE_RETRIEVED_CONTEXT")
        self.assertAlmostEqual(result["faithfulness"], 2 / 3)
        self.assertAlmostEqual(result["unsupported_claim_rate"], 1 / 3)
        self.assertEqual(result["citation_coverage"], 1.0)
        self.assertEqual(result["citation_support_rate"], 0.5)
        self.assertEqual(result["context_utilization"], 1.0)

    def test_all_benchmark_generation_paths_send_zero_temperature_and_default_service_does_not(self) -> None:
        calls: list[dict] = []

        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))]
            )

        client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        rag_eval_module._no_rag_answer(client, "generator", "query")
        benchmark_service = CareerAnswerService(
            model_name="generator",
            client=client,
            temperature=GENERATION_TEMPERATURE,
        )
        job = _as_retrieved(_jobs(1)[0])
        benchmark_service.answer("clean query", [job])
        benchmark_service.answer("gold query", [job])
        self.assertEqual([call.get("temperature") for call in calls], [0, 0, 0])

        calls.clear()
        CareerAnswerService(model_name="production", client=client).answer(
            "production query",
            [job],
        )
        self.assertNotIn("temperature", calls[0])

    def test_rag_context_uses_section_aware_evidence_packing(self) -> None:
        job = CorpusJob(
            source="vietjobs",
            source_job_id="J-late",
            job_title="Engineer",
            category_key="tech",
            location_key=None,
            experience_level=None,
            employment_type=None,
            chunks=(
                {"section": "description", "content": "d" * 4800},
                {"section": "required qualifications", "content": "Python Docker Kubernetes"},
            ),
        )
        retrieved = _as_retrieved(job)
        self.assertEqual(len(retrieved.evidence), 1)
        self.assertIn("Python Docker Kubernetes", retrieved.evidence[0].content)
        self.assertLessEqual(len(retrieved.evidence[0].content), DEFAULT_EVIDENCE_CHAR_BUDGET)

    def test_gold_context_is_strong_and_explicitly_certain_only(self) -> None:
        rows = [
            {"topic_id": "topic", "source": "vietjobs", "source_job_id": "strong", "grade": 3, "uncertain": False},
            {"topic_id": "topic", "source": "vietjobs", "source_job_id": "weak", "grade": 1, "uncertain": False},
            {"topic_id": "topic", "source": "vietjobs", "source_job_id": "uncertain", "grade": 3, "uncertain": True},
            {"topic_id": "topic", "source": "vietjobs", "source_job_id": "unknown-state", "grade": 3},
            {"topic_id": "other", "source": "vietjobs", "source_job_id": "other", "grade": 3, "uncertain": False},
        ]
        selected = _certain_gold_context_rows(rows, topic_id="topic", top_k=5)
        self.assertEqual([row["source_job_id"] for row in selected], ["strong"])

    def test_model_identity_never_guesses_family_from_names(self) -> None:
        identity = _model_identity("deepseek-generator", "deepseek-judge")
        self.assertFalse(identity["exact_model_id_equal"])
        self.assertEqual(identity["family_relation"], "UNVERIFIED")
        self.assertIsNone(identity["family_metadata_source"])
        same = _model_identity("exact-id", "exact-id")
        self.assertTrue(same["exact_model_id_equal"])
        self.assertEqual(same["family_relation"], "UNVERIFIED")


class RagEvalQueryConcurrencyTests(unittest.TestCase):
    @staticmethod
    def _query_result(index: int) -> dict:
        return {
            "index": index,
            "results": {
                system: {
                    "query_id": f"query-{index}",
                    "topic_id": f"topic-{index}",
                    "variant": "direct",
                    "answer": f"{system}-{index}",
                }
                for system in rag_eval_module.RAG_SYSTEMS
            },
        }

    def test_query_worker_preserves_retrieval_generation_and_judging_semantics(self) -> None:
        class FakeRanker:
            def __init__(self) -> None:
                self.calls: list[tuple[str, int]] = []

            def rank_job_keys(self, query: str, depth: int) -> list[str]:
                self.calls.append((query, depth))
                return ["vietjobs::J2", "vietjobs::J1"]

        class FakeAnswerService:
            def __init__(self) -> None:
                self.calls: list[tuple[str, list[str]]] = []

            def answer(self, query: str, jobs: list) -> SimpleNamespace:
                keys = [f"{job.source}::{job.source_job_id}" for job in jobs]
                self.calls.append((query, keys))
                return SimpleNamespace(answer="answer:" + ",".join(keys))

        jobs = _jobs(3)
        corpus_by_key = {job.job_key: job for job in jobs}
        qrels = {
            "topic": [
                {
                    "topic_id": "topic", "source": "vietjobs",
                    "source_job_id": "J3", "grade": 3, "uncertain": False,
                },
                {
                    "topic_id": "topic", "source": "vietjobs",
                    "source_job_id": "J2", "grade": 3, "uncertain": True,
                },
                {
                    "topic_id": "topic", "source": "vietjobs",
                    "source_job_id": "J1", "grade": 1, "uncertain": False,
                },
            ],
        }
        nuggets = {"topic": []}
        ranker = FakeRanker()
        answer_service = FakeAnswerService()
        no_rag_calls: list[tuple[str, str, int]] = []
        judge_contexts: list[tuple[str, list[str]]] = []

        def no_rag_answer(client, model, query, *, temperature):
            no_rag_calls.append((model, query, temperature))
            return "no-rag-answer"

        def evaluate_answer(judge, *, query, answer, nuggets, context_jobs):
            keys = [f"{job.source}::{job.source_job_id}" for job in context_jobs]
            judge_contexts.append((answer, keys))
            return {"judged_context_job_keys": keys}

        with patch.object(rag_eval_module, "_no_rag_answer", side_effect=no_rag_answer), \
                patch.object(rag_eval_module, "_evaluate_answer", side_effect=evaluate_answer):
            result = rag_eval_module._evaluate_query(
                7,
                {
                    "query_id": "query-7", "topic_id": "topic",
                    "variant": "noisy", "text": "query text",
                },
                retriever_system="dense",
                top_k=2,
                clean_ranker=ranker,
                pooler=object(),
                retrieval_lock=rag_eval_module.threading.Lock(),
                corpus_by_key=corpus_by_key,
                qrels=qrels,
                nuggets=nuggets,
                generator_model="generator",
                generation_temperature=GENERATION_TEMPERATURE,
                answer_service=answer_service,
                no_rag_client=object(),
                judge=object(),
            )

        self.assertEqual(result["index"], 7)
        self.assertEqual(set(result["results"]), set(rag_eval_module.RAG_SYSTEMS))
        self.assertEqual(ranker.calls, [("query text", 2)])
        self.assertEqual(no_rag_calls, [("generator", "query text", 0)])
        self.assertEqual(
            answer_service.calls,
            [
                ("query text", ["vietjobs::J2", "vietjobs::J1"]),
                ("query text", ["vietjobs::J3"]),
            ],
        )
        self.assertEqual(
            judge_contexts,
            [
                ("no-rag-answer", []),
                ("answer:vietjobs::J2,vietjobs::J1", ["vietjobs::J2", "vietjobs::J1"]),
                ("answer:vietjobs::J3", ["vietjobs::J3"]),
            ],
        )
        for row in result["results"].values():
            self.assertEqual(row["query_id"], "query-7")
            self.assertEqual(row["topic_id"], "topic")
            self.assertEqual(row["variant"], "noisy")

    def test_out_of_order_completion_matches_serial_rows_and_keeps_one_row_per_system(self) -> None:
        completion_order: list[int] = []
        release_first = rag_eval_module.threading.Event()

        def task(index: int):
            def run() -> dict:
                if index == 0:
                    self.assertTrue(release_first.wait(timeout=2))
                if index == 2:
                    completion_order.append(index)
                    release_first.set()
                else:
                    completion_order.append(index)
                return self._query_result(index)

            return run

        rows = rag_eval_module._run_rag_query_tasks(
            [task(index) for index in range(3)],
            split="dev",
            config=rag_eval_module.RefillWindowConfig(
                max_in_flight=3,
                refill_size=1,
            ),
        )
        self.assertNotEqual(completion_order, [0, 1, 2])
        serial_results = [self._query_result(index) for index in range(3)]
        for system in rag_eval_module.RAG_SYSTEMS:
            expected_rows = [item["results"][system] for item in serial_results]
            self.assertEqual(rows[system], expected_rows)
            self.assertEqual(len(rows[system]), 3)

    def test_worker_failure_propagates_and_concurrency_env_is_strict(self) -> None:
        def fail() -> dict:
            raise RuntimeError("query worker failed")

        with self.assertRaisesRegex(RuntimeError, "query worker failed"):
            rag_eval_module._run_rag_query_tasks(
                [fail],
                split="dev",
                config=rag_eval_module.RefillWindowConfig(
                    max_in_flight=1,
                    refill_size=1,
                ),
            )

        env_keys = (
            "CAREER_RAG_RAG_EVAL_MAX_IN_FLIGHT",
            "CAREER_RAG_RAG_EVAL_REFILL_SIZE",
        )
        with patch.dict(os.environ, {}, clear=False):
            for key in env_keys:
                os.environ.pop(key, None)
            default = rag_eval_module._rag_eval_concurrency_config()
            self.assertEqual(default.max_in_flight, 4)
            self.assertEqual(default.refill_size, 2)

        for values in (
            {env_keys[0]: "0", env_keys[1]: "1"},
            {env_keys[0]: "2", env_keys[1]: "3"},
            {env_keys[0]: "four", env_keys[1]: "2"},
        ):
            with self.subTest(values=values), patch.dict(os.environ, values):
                with self.assertRaises(ValueError):
                    rag_eval_module._rag_eval_concurrency_config()
