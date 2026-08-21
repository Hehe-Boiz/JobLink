from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from .audit import sha256_tree
from .nuggets import (
    DEFAULT_VITAL_PREVALENCE,
    NUGGET_PROMPT_VERSION,
    _verify_support,
    _verify_support_matrix,
    build_nuggets_for_topic,
)
from .schema import CareerTopic, CorpusJob, RelevanceJudgment


class FakeJudgeClient:
    def __init__(
        self,
        support: dict[str, bool] | dict[str, object],
        *,
        candidate_texts: tuple[str, ...] = ("REST API",),
        extractor_support_keys: tuple[str, ...] = ("vietjobs::J1",),
        support_by_candidate: dict[str, dict[str, bool]] | None = None,
    ) -> None:
        self.support = support
        self.candidate_texts = candidate_texts
        self.extractor_support_keys = extractor_support_keys
        self.support_by_candidate = support_by_candidate or {}
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
    def test_nugget_protocol_version_is_v3(self) -> None:
        self.assertEqual(NUGGET_PROMPT_VERSION, "career-rag-silver-nuggets-v3")

    def _build(
        self,
        support: dict[str, bool],
        *,
        min_support_jobs: int = 2,
        job_count: int = 4,
        client: FakeJudgeClient | None = None,
        nugget_batch_size: int = 8,
        job_batch_size: int = 8,
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
            max_in_flight=1,
            refill_size=1,
        )

    def test_extractor_underclaim_does_not_bias_prevalence(self) -> None:
        nuggets = self._build({"J1": True, "J2": True, "J3": True, "J4": False})
        self.assertEqual(len(nuggets), 1)
        nugget = nuggets[0]
        self.assertEqual(set(nugget.support_job_keys), {"vietjobs::J1", "vietjobs::J2", "vietjobs::J3"})
        self.assertEqual(nugget.support_count, 3)
        self.assertEqual(nugget.support_count, len(set(nugget.support_job_keys)))
        self.assertTrue(set(nugget.support_job_keys).issubset({job.job_key for job in _jobs()}))
        self.assertEqual(nugget.prevalence, 0.75)

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

    def test_prevalence_boundary_keeps_default_importance_threshold(self) -> None:
        vital = self._build(
            {f"J{i}": i <= 7 for i in range(1, 21)},
            min_support_jobs=1,
            job_count=20,
        )[0]
        okay = self._build(
            {f"J{i}": i <= 6 for i in range(1, 21)},
            min_support_jobs=1,
            job_count=20,
        )[0]
        self.assertEqual(DEFAULT_VITAL_PREVALENCE, 0.35)
        self.assertEqual(vital.prevalence, 0.35)
        self.assertEqual(vital.importance, "VITAL")
        self.assertEqual(okay.prevalence, 0.3)
        self.assertEqual(okay.importance, "OKAY")

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
        client = SequencedMatrixClient([self._malformed_payload(), self._valid_payload()])
        self.assertEqual(self._verify(client), [["vietjobs::J1"]])
        self.assertEqual(len(client.calls), 2)
        self.assertEqual([call[2] for call in client.calls], [0, 0])
        self.assertNotEqual(client.calls[0][1], client.calls[1][1])
        self.assertIn("all and only these nugget IDs: N1", client.calls[1][1])
        self.assertIn("all and only these job IDs: J1, J2", client.calls[1][1])
        self.assertIn("literal JSON true or false", client.calls[1][1])

    def test_schema_retry_budget_is_exact_when_every_response_is_malformed(self) -> None:
        client = SequencedMatrixClient(
            [self._malformed_payload(), self._malformed_payload(), self._malformed_payload()]
        )
        with self.assertRaisesRegex(RuntimeError, "after 2 retries"):
            self._verify(client)
        self.assertEqual(len(client.calls), 3)
        self.assertEqual([call[2] for call in client.calls], [0, 0, 0])

    def test_cached_malformed_response_cannot_block_corrective_prompt(self) -> None:
        client = CacheLikeSequencedMatrixClient([self._malformed_payload(), self._valid_payload()])
        self.assertEqual(self._verify(client), [["vietjobs::J1"]])
        self.assertEqual(len(client.calls), 2)
        self.assertNotEqual(client.calls[0][1], client.calls[1][1])
        self.assertEqual(len(client.cache), 2)


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
