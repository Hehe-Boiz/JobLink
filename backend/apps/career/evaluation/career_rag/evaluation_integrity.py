from __future__ import annotations

import json
from pathlib import Path

from .audit import sha256_file, verify_frozen_benchmark
from .clean_index import configured_clean_index_dir, verify_clean_embedding_index


def verify_evaluation_integrity(output_dir: Path, *, clean_index_dir: Path | None = None) -> dict:
    """Fail closed before any evaluator model/API work or TEST lock use."""

    output_dir = Path(output_dir)
    frozen = verify_frozen_benchmark(output_dir)
    blockers = list(frozen["blockers"])
    clean_dir = Path(clean_index_dir or configured_clean_index_dir())
    clean = verify_clean_embedding_index(clean_dir)
    if not clean["passed"]:
        blockers.append("clean sidecar invalid: " + "; ".join(clean["blockers"]))
    try:
        configuration = json.loads((output_dir / "benchmark_manifest.json").read_text(encoding="utf-8")).get("configuration", {})
        provenance = clean.get("provenance", {})
        expected = {
            "clean_embedding_vectors_sha256": provenance.get("vectors_sha256"),
            "clean_embedding_chunk_map_sha256": provenance.get("chunk_map_sha256"),
            "clean_embedding_provenance_sha256": sha256_file(clean_dir / "embedding_provenance.json"),
            "clean_embedding_corpus_membership_sha256": provenance.get("corpus_membership_sha256"),
            "clean_embedding_chunk_context_sha256": provenance.get("chunk_context_sha256"),
        }
        mismatched = [field for field, value in expected.items() if configuration.get(field) != value]
        if mismatched:
            blockers.append("clean sidecar does not match frozen benchmark manifest: " + ", ".join(mismatched))
    except Exception as exc:  # noqa: BLE001
        blockers.append(f"could not compare clean sidecar to frozen manifest: {exc}")
    return {
        "passed": not blockers,
        "frozen": frozen,
        "clean_index": clean,
        "clean_index_dir": str(clean_dir),
        "blockers": blockers,
    }


def assert_evaluation_integrity(output_dir: Path, *, clean_index_dir: Path | None = None) -> dict:
    result = verify_evaluation_integrity(output_dir, clean_index_dir=clean_index_dir)
    if not result["passed"]:
        raise RuntimeError("Frozen benchmark/clean sidecar integrity verification failed: " + "; ".join(result["blockers"]))
    return result


def consume_test_lock(output_dir: Path, *, evaluator: str, allow_test: bool) -> Path:
    if not allow_test:
        raise RuntimeError("TEST is locked. Re-run explicitly with --allow-test only after DEV choices are frozen.")
    lock = Path(output_dir) / "reports" / f"TEST_{evaluator}_ALREADY_RUN.lock"
    try:
        with lock.open("x", encoding="utf-8") as handle:
            handle.write("TEST evaluation consumed before execution. This conservative lock is intentionally permanent.\n")
    except FileExistsError as exc:
        raise RuntimeError(f"TEST {evaluator.lower()} evaluation has already been run for this frozen benchmark. Refusing a second run.") from exc
    return lock
