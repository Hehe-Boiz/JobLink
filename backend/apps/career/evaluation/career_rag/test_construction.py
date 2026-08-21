from __future__ import annotations

import re
import json
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from . import audit as audit_module
from .audit import (
    audit_derived_label_leakage,
    audit_evidence_truncation,
    audit_split,
    embedding_provenance_expected_contract,
    embedding_provenance_contract,
    embedding_provenance_is_freeze_safe,
    sha256_tree,
)
from .judges import judge_candidates
from .nuggets import (
    NUGGET_IMPORTANCE_POLICY_VERSION,
    NUGGET_PROMPT_VERSION,
    NUGGET_WEIGHT_POLICY,
    PREVALENCE_UNAVAILABLE,
    _judge_importance_batch,
    _validate_importance,
    _verify_support,
    _verify_support_matrix,
    build_nuggets_for_topic,
)
from .pooling import audit_pool_coverage, audit_pool_coverage_offline
from .schema import CareerQuery, CareerTopic, CorpusJob, PooledCandidate, RelevanceJudgment
from .semantics import (
    CANONICAL_INFORMATION_FACETS,
    CANONICAL_INFORMATION_NEED_VERSION,
    canonical_information_need,
)
from .topics import BASE_QUERY_VARIANTS, discover_topics, generate_query_variants


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
            max_in_flight=1,
            refill_size=1,
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

    def test_string_boolean_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            _verify_support(FakeJudgeClient({"J1": "false"}), "REST API", _jobs()[:1])

    def test_missing_verifier_key_is_rejected(self) -> None:
        class MissingKeyClient(FakeJudgeClient):
            def json_call(self, *, system: str, user: str) -> dict:
                return {"support": {"J1": True}}

        with self.assertRaises(ValueError):
            _verify_support(MissingKeyClient({}), "REST API", _jobs()[:2])

    def test_extra_verifier_key_is_rejected(self) -> None:
        class ExtraKeyClient(FakeJudgeClient):
            def json_call(self, *, system: str, user: str) -> dict:
                return {"support": {"J1": False, "J2": False}}

        with self.assertRaises(ValueError):
            _verify_support(ExtraKeyClient({}), "REST API", _jobs()[:1])

    def test_invalid_support_shape_is_rejected(self) -> None:
        class InvalidShapeClient(FakeJudgeClient):
            def json_call(self, *, system: str, user: str) -> dict:
                return {"support": []}

        with self.assertRaises(ValueError):
            _verify_support(InvalidShapeClient({}), "REST API", _jobs()[:1])

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
        underclaimed = self._build(
            support,
            client=FakeJudgeClient(support, extractor_support_keys=("vietjobs::J1",)),
        )
        overclaimed = self._build(
            support,
            client=FakeJudgeClient(
                support,
                extractor_support_keys=tuple(f"vietjobs::J{i}" for i in range(1, 5)),
            ),
        )
        self.assertEqual(underclaimed, overclaimed)


class StaticMatrixClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls = 0

    def json_call(self, *, system: str, user: str, retries: int = 2) -> object:
        self.calls += 1
        return self.payload


class NuggetMatrixValidationTests(unittest.TestCase):
    def _verify(self, payload: dict) -> list[list[str]]:
        return _verify_support_matrix(
            StaticMatrixClient(payload),
            [{"text": "REST API"}, {"text": "Python"}],
            _jobs(2),
            max_in_flight=1,
            refill_size=1,
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

    def test_matrix_reconstructs_distinct_rows_across_parallel_job_batches(self) -> None:
        client = FakeJudgeClient(
            {},
            support_by_candidate={
                "REST API": {"J1": True, "J2": False, "J3": True, "J4": False},
                "Python": {"J1": False, "J2": True, "J3": False, "J4": True},
            },
        )
        result = _verify_support_matrix(
            client,
            [{"text": "REST API"}, {"text": "Python"}],
            _jobs(4),
            nugget_batch_size=2,
            job_batch_size=2,
            max_in_flight=2,
            refill_size=2,
        )
        self.assertEqual(
            result,
            [
                ["vietjobs::J1", "vietjobs::J3"],
                ["vietjobs::J2", "vietjobs::J4"],
            ],
        )


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


class NuggetMatrixRetryTests(unittest.TestCase):
    def _verify(self, client: object) -> list[list[str]]:
        return _verify_support_matrix(
            client,
            [{"text": "REST API"}],
            _jobs(2),
            max_in_flight=1,
            refill_size=1,
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
        self.assertEqual([call[2] for call in client.calls], [0, 0, 0])
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
        self.assertEqual([call[2] for call in client.calls], [0, 0, 0])
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
        self.assertEqual([call[2] for call in client.calls], [0, 0, 0])
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
        self.assertEqual([call[2] for call in client.calls], [0] * 5)
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


class TopicSemanticsTests(unittest.TestCase):
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


class OfflineDiagnosticTests(unittest.TestCase):
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
            self.assertIn("resulting_candidate_count", detail)
            self.assertIn("max_pool_dropped_count", detail)
            self.assertEqual(detail["rrf_new_candidates"], [])
        self.assertTrue(report["reports"]["20"]["topics"]["topic-1"]["max_pool_truncates_system_unique"])

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

    def test_embedding_provenance_is_explicitly_unverified_without_history(self) -> None:
        backend_root = Path(__file__).resolve().parents[4]
        contract = embedding_provenance_contract(
            backend_root=backend_root,
            corpus_membership_sha256="m" * 64,
            corpus_chunks_sha256="c" * 64,
            forbidden_derived_metadata_present=False,
        )
        self.assertEqual(contract["status"], "UNVERIFIED")
        self.assertIsNone(contract["forbidden_derived_fields_excluded"])
        self.assertEqual(len(contract["chunking_source_sha256"]), 64)
        self.assertEqual(len(contract["embedding_source_sha256"]), 64)
        self.assertTrue(contract["requires_verified_clean_for_freeze"])

    def test_matching_clean_embedding_provenance_artifact_is_verified(self) -> None:
        backend_root = Path(__file__).resolve().parents[4]
        membership = "m" * 64
        chunks = "c" * 64
        artifact = embedding_provenance_expected_contract(
            backend_root=backend_root,
            corpus_membership_sha256=membership,
            corpus_chunks_sha256=chunks,
        )
        artifact.update({"status": "VERIFIED_CLEAN", "indexing_timestamp": "2026-08-21T00:00:00Z"})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "embedding-provenance.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")
            contract = embedding_provenance_contract(
                backend_root=backend_root,
                corpus_membership_sha256=membership,
                corpus_chunks_sha256=chunks,
                forbidden_derived_metadata_present=False,
                provenance_path=path,
            )
        self.assertEqual(contract["status"], "VERIFIED_CLEAN")
        self.assertTrue(embedding_provenance_is_freeze_safe(contract))

    def test_explicitly_leaked_embedding_provenance_is_not_freeze_safe(self) -> None:
        backend_root = Path(__file__).resolve().parents[4]
        artifact = embedding_provenance_expected_contract(
            backend_root=backend_root,
            corpus_membership_sha256="m" * 64,
            corpus_chunks_sha256="c" * 64,
        )
        artifact.update({
            "status": "VERIFIED_LEAKED",
            "indexing_timestamp": "2026-08-21T00:00:00Z",
            "derived_fields_included": ["technical_skills"],
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "embedding-provenance.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")
            contract = embedding_provenance_contract(
                backend_root=backend_root,
                corpus_membership_sha256="m" * 64,
                corpus_chunks_sha256="c" * 64,
                forbidden_derived_metadata_present=False,
                provenance_path=path,
            )
        self.assertEqual(contract["status"], "VERIFIED_LEAKED")
        self.assertFalse(embedding_provenance_is_freeze_safe(contract))

    def test_mismatched_embedding_provenance_is_unverified_and_blocks_freeze(self) -> None:
        backend_root = Path(__file__).resolve().parents[4]
        artifact = embedding_provenance_expected_contract(
            backend_root=backend_root,
            corpus_membership_sha256="m" * 64,
            corpus_chunks_sha256="c" * 64,
        )
        artifact.update({
            "status": "VERIFIED_CLEAN",
            "indexing_timestamp": "2026-08-21T00:00:00Z",
            "embedding_model": "wrong-model",
        })
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "embedding-provenance.json"
            path.write_text(json.dumps(artifact), encoding="utf-8")
            contract = embedding_provenance_contract(
                backend_root=backend_root,
                corpus_membership_sha256="m" * 64,
                corpus_chunks_sha256="c" * 64,
                forbidden_derived_metadata_present=False,
                provenance_path=path,
            )
        self.assertEqual(contract["status"], "UNVERIFIED")
        self.assertFalse(embedding_provenance_is_freeze_safe(contract))

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
