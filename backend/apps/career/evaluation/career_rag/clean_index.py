from __future__ import annotations

"""Immutable, benchmark-only dense index for CareerRAGBench-Auto-V3.

This module deliberately reads the existing frozen chunks but never reads or
writes ``CareerJobChunk.embedding``.  The sidecar is a new provenance-bearing
matrix, not a claim about the historical production vectors.
"""

import hashlib
import importlib.metadata
import json
import os
import platform
import re
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import numpy as np

from apps.career.embedding import CareerEmbeddingService
from apps.career.models import CareerJobChunk

from .audit import FORBIDDEN_DERIVED_KEYS, sha256_file

BACKEND_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_CLEAN_INDEX_DIR = BACKEND_ROOT / "data" / "career_eval" / "career_rag_clean_index_v3"
CLEAN_EMBEDDING_INPUT_POLICY_VERSION = "career-rag-clean-sidecar-input-v1"
CLEAN_EMBEDDING_INPUT_FIELD_POLICY = "raw-job-fields-only-no-forbidden-derived-fields-v1"
CLEAN_INDEX_TYPE = "career-rag-benchmark-sidecar-npy-v1"
CLEAN_INDEX_PROVENANCE_SCHEMA_VERSION = "career-rag-clean-index-provenance-v2"
CLEAN_INDEXING_POLICY_VERSION = "career-rag-clean-sidecar-build-v1"
CLEAN_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"
CLEAN_EMBEDDING_DIMENSION = 384
V3_SNAPSHOT_INDEXED_JOB_COUNT = 47_097
V3_SNAPSHOT_ACTIVE_CHUNK_COUNT = 152_379
VECTORS_FILENAME = "vectors.npy"
CHUNK_MAP_FILENAME = "chunk_map.jsonl"
PROVENANCE_FILENAME = "embedding_provenance.json"
DEPENDENCY_DISTRIBUTIONS = {
    "numpy_version": "numpy",
    "sentence_transformers_version": "sentence-transformers",
    "transformers_version": "transformers",
    "torch_version": "torch",
    "rank_bm25_version": "rank-bm25",
}
QUERY_ENCODER_DEPENDENCY_FIELDS = (
    "numpy_version",
    "sentence_transformers_version",
    "transformers_version",
    "torch_version",
)


def configured_clean_index_dir() -> Path:
    value = os.environ.get("CAREER_RAG_CLEAN_INDEX_DIR")
    if not value:
        return DEFAULT_CLEAN_INDEX_DIR
    path = Path(value)
    return path if path.is_absolute() else BACKEND_ROOT / path


def clean_embedding_input(row: dict) -> str:
    """Build the sole permitted embedding input from an existing chunk row."""

    # Do not use ``metadata`` here.  Keeping the input as a narrow mapping is
    # intentional: it makes forbidden derived fields unavailable by design.
    headers = [f"passage: Job title: {row.get('job_title') or ''}"]
    for field, label in (
        ("location_key", "Location"),
        ("category_key", "Category"),
        ("experience_level", "Experience level"),
        ("employment_type", "Employment type"),
        ("section", "Section"),
    ):
        value = row.get(field)
        if value:
            headers.append(f"{label}: {value}")
    return "\n".join(headers) + "\n\n" + (row.get("content") or "")


def _chunk_rows() -> Iterable[dict]:
    return (
        CareerJobChunk.objects.filter(active=True, source="vietjobs")
        .order_by("source_job_id", "chunk_index", "chunk_id")
        .values(
            "chunk_id",
            "source",
            "source_job_id",
            "chunk_index",
            "job_title",
            "location_key",
            "category_key",
            "experience_level",
            "employment_type",
            "section",
            "content",
        )
    )


def current_clean_corpus_identity() -> dict:
    """Return the deterministic identity of the exact rows sidecar indexes."""

    rows = _chunk_rows()
    chunks_digest = hashlib.sha256()
    context_digest = hashlib.sha256()
    membership = hashlib.sha256()
    source_job_ids: list[str] = []
    chunk_count = 0
    last_job_id: str | None = None
    for row in rows.iterator(chunk_size=4000):
        source_job_id = str(row["source_job_id"])
        if source_job_id != last_job_id:
            source_job_ids.append(source_job_id)
            last_job_id = source_job_id
        context = {
            "source": row["source"],
            "source_job_id": source_job_id,
            "chunk_id": row["chunk_id"],
            "chunk_index": row["chunk_index"],
            "job_title": row["job_title"],
            "location_key": row["location_key"],
            "category_key": row["category_key"],
            "experience_level": row["experience_level"],
            "employment_type": row["employment_type"],
            "section": row["section"],
            "content": row["content"],
        }
        chunks_digest.update(json.dumps(context, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        chunks_digest.update(b"\n")
        context_digest.update(str(row["chunk_id"]).encode("utf-8"))
        context_digest.update(b"\0")
        context_digest.update(clean_embedding_input(row).encode("utf-8"))
        context_digest.update(b"\n")
        chunk_count += 1
    for source_job_id in source_job_ids:
        membership.update(source_job_id.encode("utf-8"))
        membership.update(b"\n")
    return {
        "indexed_job_count": len(source_job_ids),
        "indexed_chunk_count": chunk_count,
        "corpus_membership_sha256": membership.hexdigest(),
        "corpus_chunks_sha256": chunks_digest.hexdigest(),
        "chunk_context_sha256": context_digest.hexdigest(),
    }


def _source_hashes() -> dict[str, str]:
    return {
        "embedding_source_sha256": sha256_file(BACKEND_ROOT / "apps" / "career" / "embedding.py"),
        "clean_index_source_sha256": sha256_file(Path(__file__)),
    }


def _resolved_local_model_revision(embedder: CareerEmbeddingService) -> tuple[str | None, str]:
    """Read a cached Hugging Face commit SHA without network resolution."""

    model = getattr(embedder, "model", None)
    candidates: list[object] = []
    try:
        first_module = model._first_module()
    except (AttributeError, TypeError):
        first_module = None
    if first_module is not None:
        auto_model = getattr(first_module, "auto_model", None)
        candidates.append(getattr(getattr(auto_model, "config", None), "_commit_hash", None))
        tokenizer = getattr(first_module, "tokenizer", None)
        candidates.append(getattr(tokenizer, "init_kwargs", {}).get("_commit_hash"))
    candidates.append(getattr(getattr(model, "config", None), "_commit_hash", None))
    for value in candidates:
        if isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{40,64}", value):
            return value.lower(), "VERIFIED_FROM_LOCAL_MODEL_CONFIG"
    return None, "UNVERIFIED"


def _runtime_provenance(
    embedder: CareerEmbeddingService,
    *,
    dependency_fields: Iterable[str] | None = None,
) -> dict:
    versions: dict[str, str] = {}
    selected_fields = tuple(dependency_fields or DEPENDENCY_DISTRIBUTIONS)
    for field in selected_fields:
        distribution = DEPENDENCY_DISTRIBUTIONS[field]
        try:
            versions[field] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(
                f"Cannot record clean-index dependency provenance: {distribution} is unavailable"
            ) from exc
    revision, revision_status = _resolved_local_model_revision(embedder)
    return {
        "python_version": platform.python_version(),
        **versions,
        "embedding_model_revision": revision,
        "embedding_model_revision_status": revision_status,
    }


def _assert_runtime_query_encoder_compatible(
    embedder: CareerEmbeddingService,
    frozen_provenance: dict,
) -> dict:
    """Fail if the live query encoder differs from the document encoder contract."""

    current = _runtime_provenance(
        embedder,
        dependency_fields=QUERY_ENCODER_DEPENDENCY_FIELDS,
    )
    for field in QUERY_ENCODER_DEPENDENCY_FIELDS:
        if current[field] != frozen_provenance.get(field):
            raise RuntimeError(
                "Clean benchmark query encoder dependency does not match sidecar "
                f"provenance: {field}"
            )

    frozen_status = frozen_provenance.get("embedding_model_revision_status")
    frozen_revision = frozen_provenance.get("embedding_model_revision")
    if frozen_status == "VERIFIED_FROM_LOCAL_MODEL_CONFIG":
        if (
            current["embedding_model_revision_status"]
            != "VERIFIED_FROM_LOCAL_MODEL_CONFIG"
            or current["embedding_model_revision"] != frozen_revision
        ):
            raise RuntimeError(
                "Clean benchmark query encoder model revision does not match sidecar provenance"
            )

    # Preserve the frozen status when a cached model cannot expose a durable
    # revision. Matching package/model/dimension contracts do not upgrade an
    # UNVERIFIED revision into a verified claim.
    return {
        **current,
        "embedding_model_revision": frozen_revision,
        "embedding_model_revision_status": frozen_status,
    }


@contextmanager
def _offline_huggingface():
    keys = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    previous = {key: os.environ.get(key) for key in keys}
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _new_sibling_directory(output_dir: Path) -> Path:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(20):
        candidate = output_dir.parent / f"{output_dir.name}.building-{os.getpid()}-{secrets.token_hex(8)}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError("Could not allocate a temporary clean-index directory")


def _assert_expected_corpus(identity: dict) -> None:
    if identity["indexed_job_count"] != V3_SNAPSHOT_INDEXED_JOB_COUNT:
        raise RuntimeError(
            "Clean sidecar corpus drift: expected "
            f"{V3_SNAPSHOT_INDEXED_JOB_COUNT} jobs, got {identity['indexed_job_count']}"
        )
    if identity["indexed_chunk_count"] != V3_SNAPSHOT_ACTIVE_CHUNK_COUNT:
        raise RuntimeError(
            "Clean sidecar corpus drift: expected "
            f"{V3_SNAPSHOT_ACTIVE_CHUNK_COUNT} chunks, got {identity['indexed_chunk_count']}"
        )


def build_clean_embedding_index(
    *,
    output_dir: Path = DEFAULT_CLEAN_INDEX_DIR,
    batch_size: int = 32,
    device: str | None = None,
) -> dict:
    """Create one sidecar in a sibling directory and atomically publish it."""

    output_dir = Path(output_dir)
    if output_dir.exists():
        raise RuntimeError(f"Refusing to overwrite existing clean index: {output_dir}")
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")

    identity_before = current_clean_corpus_identity()
    _assert_expected_corpus(identity_before)
    candidate = _new_sibling_directory(output_dir)
    try:
        with _offline_huggingface():
            try:
                embedder = CareerEmbeddingService(
                    model_name=CLEAN_EMBEDDING_MODEL,
                    batch_size=batch_size,
                    device=device,
                )
            except Exception as exc:  # model must be local; never download here
                raise RuntimeError(
                    "Clean sidecar requires cached intfloat/multilingual-e5-small; "
                    "offline model load failed. Populate the approved model cache before building."
                ) from exc
            if embedder.model_name != CLEAN_EMBEDDING_MODEL or embedder.dimension != CLEAN_EMBEDDING_DIMENSION:
                raise RuntimeError("Clean sidecar embedder model/dimension does not match the frozen V3 contract")
            runtime_provenance = _runtime_provenance(embedder)

            vectors_path = candidate / VECTORS_FILENAME
            vectors = np.lib.format.open_memmap(
                vectors_path,
                mode="w+",
                dtype=np.float32,
                shape=(identity_before["indexed_chunk_count"], CLEAN_EMBEDDING_DIMENSION),
            )
            map_path = candidate / CHUNK_MAP_FILENAME
            rows = _chunk_rows()
            row_index = 0
            with map_path.open("w", encoding="utf-8") as map_handle:
                pending: list[dict] = []

                def flush() -> None:
                    nonlocal row_index, pending
                    if not pending:
                        return
                    texts = [clean_embedding_input(item) for item in pending]
                    encoded = embedder.model.encode(
                        texts,
                        batch_size=batch_size,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                        show_progress_bar=False,
                    )
                    encoded = np.asarray(encoded, dtype=np.float32)
                    if encoded.shape != (len(pending), CLEAN_EMBEDDING_DIMENSION):
                        raise RuntimeError(f"Clean embedder returned invalid vector shape {encoded.shape!r}")
                    if not np.isfinite(encoded).all():
                        raise RuntimeError("Clean embedder returned NaN or Inf")
                    norms = np.linalg.norm(encoded, axis=1)
                    if not np.allclose(norms, 1.0, rtol=1e-4, atol=1e-4):
                        raise RuntimeError("Clean embedder returned non-normalized vectors")
                    vectors[row_index : row_index + len(pending)] = encoded
                    for offset, item in enumerate(pending):
                        map_handle.write(json.dumps({
                            "row_index": row_index + offset,
                            "chunk_id": item["chunk_id"],
                            "source": "vietjobs",
                            "source_job_id": str(item["source_job_id"]),
                            "job_key": f"vietjobs::{item['source_job_id']}",
                        }, ensure_ascii=False, sort_keys=True) + "\n")
                    row_index += len(pending)
                    pending = []

                for item in rows.iterator(chunk_size=4000):
                    pending.append(item)
                    if len(pending) >= batch_size:
                        flush()
                flush()
            vectors.flush()
            del vectors

        if row_index != identity_before["indexed_chunk_count"]:
            raise RuntimeError("Clean sidecar vector/map row count does not match its corpus snapshot")
        identity_after = current_clean_corpus_identity()
        _assert_expected_corpus(identity_after)
        if identity_after != identity_before:
            raise RuntimeError("CareerJobChunk corpus changed while clean sidecar was being built")

        provenance = {
            "status": "VERIFIED_CLEAN",
            "provenance_schema_version": CLEAN_INDEX_PROVENANCE_SCHEMA_VERSION,
            "indexing_timestamp": datetime.now(timezone.utc).isoformat(),
            "index_type": CLEAN_INDEX_TYPE,
            "embedding_model": CLEAN_EMBEDDING_MODEL,
            "embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
            "input_field_policy": CLEAN_EMBEDDING_INPUT_FIELD_POLICY,
            "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
            "forbidden_derived_fields": sorted(FORBIDDEN_DERIVED_KEYS),
            "forbidden_derived_fields_excluded": True,
            "derived_fields_included": [],
            "indexing_policy_version": CLEAN_INDEXING_POLICY_VERSION,
            **runtime_provenance,
            **identity_before,
            "vectors_filename": VECTORS_FILENAME,
            "vectors_sha256": sha256_file(vectors_path),
            "vectors_dtype": "float32",
            "vectors_shape": [identity_before["indexed_chunk_count"], CLEAN_EMBEDDING_DIMENSION],
            "chunk_map_filename": CHUNK_MAP_FILENAME,
            "chunk_map_sha256": sha256_file(map_path),
            **_source_hashes(),
        }
        provenance_path = candidate / PROVENANCE_FILENAME
        provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        verification = verify_clean_embedding_index(candidate)
        if not verification["passed"]:
            raise RuntimeError("Fresh clean sidecar failed verification: " + "; ".join(verification["blockers"]))
        if output_dir.exists():
            raise RuntimeError("Clean-index destination appeared during build; refusing to replace it")
        candidate.replace(output_dir)
        return {"output_dir": str(output_dir), "provenance": provenance, "verification": verification}
    except Exception:
        if candidate.exists():
            import shutil

            shutil.rmtree(candidate)
        raise


def _read_chunk_map(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"chunk map has a blank row at line {line_number}")
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"chunk map row {line_number} is not an object")
            rows.append(row)
    return rows


def verify_clean_embedding_index(index_dir: Path = DEFAULT_CLEAN_INDEX_DIR) -> dict:
    """Verify bytes, schema, source code, and current frozen corpus identity."""

    index_dir = Path(index_dir)
    blockers: list[str] = []
    checks: dict[str, bool] = {}
    provenance: dict = {}
    try:
        raw = json.loads((index_dir / PROVENANCE_FILENAME).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("provenance must be an object")
        provenance = raw
        checks["provenance_readable"] = True
    except Exception as exc:  # noqa: BLE001 - report all offline blockers
        checks["provenance_readable"] = False
        blockers.append(f"provenance unreadable: {exc}")

    expected_scalars = {
        "status": "VERIFIED_CLEAN",
        "provenance_schema_version": CLEAN_INDEX_PROVENANCE_SCHEMA_VERSION,
        "index_type": CLEAN_INDEX_TYPE,
        "embedding_model": CLEAN_EMBEDDING_MODEL,
        "embedding_dimension": CLEAN_EMBEDDING_DIMENSION,
        "input_field_policy": CLEAN_EMBEDDING_INPUT_FIELD_POLICY,
        "clean_embedding_input_policy_version": CLEAN_EMBEDDING_INPUT_POLICY_VERSION,
        "indexing_policy_version": CLEAN_INDEXING_POLICY_VERSION,
        "vectors_filename": VECTORS_FILENAME,
        "vectors_dtype": "float32",
        "chunk_map_filename": CHUNK_MAP_FILENAME,
    }
    for field, expected in expected_scalars.items():
        ok = provenance.get(field) == expected
        checks[f"provenance_{field}"] = ok
        if not ok:
            blockers.append(f"clean index provenance mismatch: {field}")
    fields_ok = (
        provenance.get("forbidden_derived_fields") == sorted(FORBIDDEN_DERIVED_KEYS)
        and provenance.get("forbidden_derived_fields_excluded") is True
        and provenance.get("derived_fields_included") == []
    )
    checks["raw_only_input_policy"] = fields_ok
    if not fields_ok:
        blockers.append("clean index does not prove forbidden derived fields were excluded")
    dependency_fields_ok = all(
        isinstance(provenance.get(field), str) and bool(provenance[field])
        for field in ("python_version", *DEPENDENCY_DISTRIBUTIONS)
    )
    revision = provenance.get("embedding_model_revision")
    revision_status = provenance.get("embedding_model_revision_status")
    revision_ok = (
        revision is None
        and revision_status == "UNVERIFIED"
    ) or (
        isinstance(revision, str)
        and re.fullmatch(r"[0-9a-f]{40,64}", revision) is not None
        and revision_status == "VERIFIED_FROM_LOCAL_MODEL_CONFIG"
    )
    checks["dependency_provenance"] = dependency_fields_ok
    checks["embedding_model_revision"] = revision_ok
    if not dependency_fields_ok:
        blockers.append("clean index dependency version provenance is incomplete")
    if not revision_ok:
        blockers.append("clean index embedding model revision provenance is inconsistent")
    timestamp = provenance.get("indexing_timestamp")
    try:
        parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        timestamp_ok = parsed_timestamp.utcoffset() == timezone.utc.utcoffset(parsed_timestamp)
    except (AttributeError, TypeError, ValueError):
        timestamp_ok = False
    checks["timestamp"] = timestamp_ok
    if not checks["timestamp"]:
        blockers.append("clean index provenance has no timezone-aware UTC timestamp")

    vectors_path = index_dir / VECTORS_FILENAME
    map_path = index_dir / CHUNK_MAP_FILENAME
    try:
        checks["vectors_hash"] = sha256_file(vectors_path) == provenance.get("vectors_sha256")
        if not checks["vectors_hash"]:
            blockers.append("vectors.npy SHA256 mismatch")
        vectors = np.load(vectors_path, mmap_mode="r", allow_pickle=False)
        checks["vectors_dtype"] = vectors.dtype == np.float32
        shape = [int(value) for value in vectors.shape]
        checks["vectors_shape"] = shape == provenance.get("vectors_shape") and len(shape) == 2 and shape[1] == CLEAN_EMBEDDING_DIMENSION
        checks["vectors_finite"] = bool(np.isfinite(vectors).all())
        checks["vectors_normalized"] = (
            checks["vectors_shape"]
            and checks["vectors_finite"]
            and bool(np.allclose(np.linalg.norm(vectors, axis=1), 1.0, rtol=1e-4, atol=1e-4))
        )
        if not checks["vectors_dtype"]:
            blockers.append("vectors.npy dtype is not float32")
        if not checks["vectors_shape"]:
            blockers.append("vectors.npy shape/dimension mismatch")
        if not checks["vectors_finite"]:
            blockers.append("vectors.npy contains NaN or Inf")
        if not checks["vectors_normalized"]:
            blockers.append("vectors.npy is not L2-normalized")
    except Exception as exc:  # noqa: BLE001
        vectors = None
        checks["vectors_readable"] = False
        blockers.append(f"vectors.npy unreadable: {exc}")
    else:
        checks["vectors_readable"] = True

    try:
        checks["chunk_map_hash"] = sha256_file(map_path) == provenance.get("chunk_map_sha256")
        if not checks["chunk_map_hash"]:
            blockers.append("chunk_map.jsonl SHA256 mismatch")
        map_rows = _read_chunk_map(map_path)
        indices = [row.get("row_index") for row in map_rows]
        chunks = [row.get("chunk_id") for row in map_rows]
        required_map_keys = {"row_index", "chunk_id", "source", "source_job_id", "job_key"}
        map_ok = (
            indices == list(range(len(map_rows)))
            and len(chunks) == len(set(chunks))
            and all(
                set(row) == required_map_keys
                and isinstance(row.get("chunk_id"), str)
                and row.get("source") == "vietjobs"
                and isinstance(row.get("source_job_id"), str)
                and row.get("job_key") == f"vietjobs::{row.get('source_job_id')}"
                for row in map_rows
            )
            and (vectors is None or len(map_rows) == vectors.shape[0])
        )
        checks["chunk_map_alignment"] = map_ok
        if not map_ok:
            blockers.append("chunk map rows are not contiguous, unique, deterministic, or aligned to vectors")
        if map_ok:
            current_map_ok = True
            for expected_index, (mapped, current) in enumerate(
                zip(map_rows, _chunk_rows().iterator(chunk_size=4000), strict=True)
            ):
                if (
                    mapped["row_index"] != expected_index
                    or mapped["chunk_id"] != current["chunk_id"]
                    or mapped["source"] != current["source"]
                    or mapped["source_job_id"] != str(current["source_job_id"])
                    or mapped["job_key"] != f"{current['source']}::{current['source_job_id']}"
                ):
                    current_map_ok = False
                    break
            checks["current_chunk_map_alignment"] = current_map_ok
            if not current_map_ok:
                blockers.append("chunk map does not map vectors to the current deterministic CareerJobChunk order")
    except Exception as exc:  # noqa: BLE001
        checks["chunk_map_readable"] = False
        blockers.append(f"chunk map unreadable: {exc}")
    else:
        checks["chunk_map_readable"] = True

    try:
        identity = current_clean_corpus_identity()
        _assert_expected_corpus(identity)
        identity_ok = all(provenance.get(field) == value for field, value in identity.items())
        checks["current_corpus_identity"] = identity_ok
        if not identity_ok:
            blockers.append("clean index does not match the current frozen CareerJobChunk corpus")
    except Exception as exc:  # noqa: BLE001
        checks["current_corpus_identity"] = False
        blockers.append(f"current corpus identity unavailable: {exc}")

    try:
        expected_sources = _source_hashes()
        source_ok = all(provenance.get(field) == value for field, value in expected_sources.items())
        checks["source_hashes"] = source_ok
        if not source_ok:
            blockers.append("clean index source hashes do not match the local clean-index implementation")
    except Exception as exc:  # noqa: BLE001
        checks["source_hashes"] = False
        blockers.append(f"clean index source hash verification failed: {exc}")
    return {
        "passed": not blockers,
        "status": "PASS" if not blockers else "FAIL",
        "index_dir": str(index_dir),
        "provenance": provenance,
        "checks": checks,
        "blockers": blockers,
    }


class CleanBenchmarkDenseRanker:
    """Exact NumPy dense ranker that can only use a verified clean sidecar."""

    candidate_multiplier = 20

    def __init__(
        self,
        index_dir: Path = DEFAULT_CLEAN_INDEX_DIR,
    ) -> None:
        self.index_dir = Path(index_dir)
        verification = verify_clean_embedding_index(self.index_dir)
        if not verification["passed"]:
            raise RuntimeError("Clean benchmark dense index is invalid: " + "; ".join(verification["blockers"]))
        self.provenance = verification["provenance"]
        self.vectors = np.load(self.index_dir / VECTORS_FILENAME, mmap_mode="r", allow_pickle=False)
        self.map_rows = _read_chunk_map(self.index_dir / CHUNK_MAP_FILENAME)
        self._job_keys = np.asarray([row["job_key"] for row in self.map_rows], dtype=str)
        self._chunk_ids = np.asarray([row["chunk_id"] for row in self.map_rows], dtype=str)
        self._row_indices = np.arange(len(self.map_rows))
        with _offline_huggingface():
            try:
                self.embedder = CareerEmbeddingService(model_name=CLEAN_EMBEDDING_MODEL)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError("Clean benchmark dense ranker requires the cached approved embedding model") from exc
        if self.embedder.model_name != CLEAN_EMBEDDING_MODEL or self.embedder.dimension != CLEAN_EMBEDDING_DIMENSION:
            raise RuntimeError("Clean benchmark dense ranker embedder does not match sidecar contract")
        self.query_encoder_provenance = _assert_runtime_query_encoder_compatible(
            self.embedder,
            self.provenance,
        )

    def rank_job_keys(self, query: str, depth: int) -> list[str]:
        if depth <= 0:
            raise ValueError("depth must be positive")
        vector = np.asarray(self.embedder.embed_query(query), dtype=np.float32)
        if vector.shape != (CLEAN_EMBEDDING_DIMENSION,) or not np.isfinite(vector).all():
            raise RuntimeError("Clean benchmark query encoder returned an invalid vector")
        norm = float(np.linalg.norm(vector))
        if not np.isclose(norm, 1.0, rtol=1e-4, atol=1e-4):
            raise RuntimeError("Clean benchmark query encoder returned a non-normalized vector")
        scores = np.asarray(self.vectors @ vector, dtype=np.float32)
        # lexsort's last key is primary: score DESC, then job key, chunk ID,
        # then original row index.  It makes every exact-score tie reproducible.
        order = np.lexsort((self._row_indices, self._chunk_ids, self._job_keys, -scores))
        candidate_limit = min(len(order), max(depth * self.candidate_multiplier, depth))
        keys: list[str] = []
        seen: set[str] = set()
        for index in order[:candidate_limit]:
            key = str(self._job_keys[index])
            if key not in seen:
                seen.add(key)
                keys.append(key)
                if len(keys) == depth:
                    return keys
        # Candidate multiplier is the primary retrieval window.  Continuing
        # deterministically only when chunks collapse heavily guarantees the
        # requested unique-job depth without changing the first-window order.
        for index in order[candidate_limit:]:
            key = str(self._job_keys[index])
            if key not in seen:
                seen.add(key)
                keys.append(key)
                if len(keys) == depth:
                    break
        return keys
