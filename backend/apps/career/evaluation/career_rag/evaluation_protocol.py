from __future__ import annotations

"""Explicit DEV-selected protocol freeze required before one-shot TEST."""

import hashlib
import json
from pathlib import Path

from apps.career.answering import PROMPT_VERSION as ANSWER_PROMPT_VERSION

from .audit import (
    V3_BENCHMARK_NAME,
    V3_BENCHMARK_VERSION,
    sha256_file,
    sha256_tree,
    verify_frozen_benchmark,
)
from .evidence import EVIDENCE_PACKING_POLICY_VERSION
from .metrics import UNCERTAIN_CONDENSING_POLICY_VERSION

EVALUATION_PROTOCOL_SCHEMA_VERSION = "career-rag-evaluation-protocol-v2"
RETRIEVAL_EVALUATION_PROTOCOL_VERSION = "career-rag-retrieval-eval-v1"
RAG_EVALUATION_PROTOCOL_VERSION = "career-rag-rag-eval-v2"
RAG_JUDGE_PROTOCOL_VERSION = "career-rag-answer-judge-strict-v1"
GENERATION_TEMPERATURE = 0
PAIRED_SIGN_FLIP_POLICY_VERSION = "paired-family-sign-flip-exact-or-seeded-mc-v1"
BOOTSTRAP_UNIT = "family"
RETRIEVAL_SYSTEMS = ("bm25", "clean_dense", "title", "hybrid")
RETRIEVAL_HEADLINE_METRICS = (
    "ndcg@5",
    "ndcg@10",
    "strong_precision@5",
    "strong_precision@10",
)
PROTOCOL_RELATIVE_PATH = Path("reports") / "evaluation_protocol.json"
PROTOCOL_HASH_RELATIVE_PATH = Path("reports") / "evaluation_protocol.sha256"

PACKAGE_DIR = Path(__file__).resolve().parent
CAREER_DIR = PACKAGE_DIR.parents[1]
SEMANTIC_SOURCE_FILES = {
    "retrieval": (
        PACKAGE_DIR / "audit.py",
        PACKAGE_DIR / "metrics.py",
        PACKAGE_DIR / "run_retrieval_eval.py",
        PACKAGE_DIR / "clean_index.py",
        PACKAGE_DIR / "pooling.py",
        PACKAGE_DIR / "schema.py",
        PACKAGE_DIR / "evaluation_integrity.py",
        PACKAGE_DIR / "evaluation_protocol.py",
        CAREER_DIR / "embedding.py",
    ),
    "rag": (
        PACKAGE_DIR / "audit.py",
        PACKAGE_DIR / "run_rag_eval.py",
        PACKAGE_DIR / "metrics.py",
        PACKAGE_DIR / "evidence.py",
        PACKAGE_DIR / "clean_index.py",
        PACKAGE_DIR / "pooling.py",
        PACKAGE_DIR / "schema.py",
        PACKAGE_DIR / "evaluation_integrity.py",
        PACKAGE_DIR / "evaluation_protocol.py",
        PACKAGE_DIR / "judges.py",
        CAREER_DIR / "answering.py",
        CAREER_DIR / "embedding.py",
        CAREER_DIR / "retrieval.py",
    ),
}

TOP_LEVEL_KEYS = frozenset({
    "status",
    "protocol_schema_version",
    "benchmark",
    "retrieval",
    "rag",
    "statistics",
    "implementation",
    "protocol_sha256",
})
BENCHMARK_KEYS = frozenset({
    "benchmark_name",
    "benchmark_version",
    "benchmark_manifest_sha256",
})
RETRIEVAL_KEYS = frozenset({
    "protocol_version",
    "systems",
    "top_k",
    "headline_metric_names",
    "qrel_uncertainty_policy",
})
RAG_KEYS = frozenset({
    "protocol_version",
    "retriever_system",
    "top_k",
    "generator_model_requested",
    "judge_model_requested",
    "generation_temperature",
    "answer_prompt_version",
    "rag_judge_protocol_version",
    "evidence_packing_policy_version",
})
STATISTICS_KEYS = frozenset({
    "bootstrap_unit",
    "bootstrap_seed",
    "bootstrap_samples",
    "alpha",
    "sign_flip_policy_version",
})
IMPLEMENTATION_KEYS = frozenset({
    "retrieval_source_files",
    "retrieval_source_sha256",
    "rag_source_files",
    "rag_source_sha256",
})


def _canonical_hash(payload: dict) -> str:
    content = dict(payload)
    content.pop("protocol_sha256", None)
    encoded = json.dumps(
        content,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _source_labels(paths: tuple[Path, ...]) -> list[str]:
    backend_root = PACKAGE_DIR.parents[3]
    return [path.relative_to(backend_root).as_posix() for path in paths]


def semantic_source_identity() -> dict:
    return {
        "retrieval_source_files": _source_labels(SEMANTIC_SOURCE_FILES["retrieval"]),
        "retrieval_source_sha256": sha256_tree(SEMANTIC_SOURCE_FILES["retrieval"]),
        "rag_source_files": _source_labels(SEMANTIC_SOURCE_FILES["rag"]),
        "rag_source_sha256": sha256_tree(SEMANTIC_SOURCE_FILES["rag"]),
    }


def retrieval_runtime_settings(
    *,
    top_k: int,
    bootstrap_seed: int,
    bootstrap_samples: int,
    bootstrap_alpha: float,
) -> dict:
    return {
        "retrieval": {
            "protocol_version": RETRIEVAL_EVALUATION_PROTOCOL_VERSION,
            "systems": list(RETRIEVAL_SYSTEMS),
            "top_k": top_k,
            "headline_metric_names": list(RETRIEVAL_HEADLINE_METRICS),
            "qrel_uncertainty_policy": UNCERTAIN_CONDENSING_POLICY_VERSION,
        },
        "statistics": {
            "bootstrap_unit": BOOTSTRAP_UNIT,
            "bootstrap_seed": bootstrap_seed,
            "bootstrap_samples": bootstrap_samples,
            "alpha": bootstrap_alpha,
            "sign_flip_policy_version": PAIRED_SIGN_FLIP_POLICY_VERSION,
        },
    }


def rag_runtime_settings(
    *,
    retriever_system: str,
    top_k: int,
    generator_model: str,
    judge_model: str,
    generation_temperature: int,
    bootstrap_seed: int,
    bootstrap_samples: int,
    bootstrap_alpha: float,
) -> dict:
    return {
        "rag": {
            "protocol_version": RAG_EVALUATION_PROTOCOL_VERSION,
            "retriever_system": retriever_system,
            "top_k": top_k,
            "generator_model_requested": generator_model,
            "judge_model_requested": judge_model,
            "generation_temperature": generation_temperature,
            "answer_prompt_version": ANSWER_PROMPT_VERSION,
            "rag_judge_protocol_version": RAG_JUDGE_PROTOCOL_VERSION,
            "evidence_packing_policy_version": EVIDENCE_PACKING_POLICY_VERSION,
        },
        "statistics": {
            "bootstrap_unit": BOOTSTRAP_UNIT,
            "bootstrap_seed": bootstrap_seed,
            "bootstrap_samples": bootstrap_samples,
            "alpha": bootstrap_alpha,
            "sign_flip_policy_version": PAIRED_SIGN_FLIP_POLICY_VERSION,
        },
    }


def _validate_freeze_arguments(
    *,
    retrieval_top_k: int,
    rag_retriever_system: str,
    rag_top_k: int,
    generator_model: str,
    judge_model: str,
    generation_temperature: int,
    bootstrap_seed: int,
    bootstrap_samples: int,
    alpha: float,
) -> None:
    if retrieval_top_k < 10:
        raise ValueError("retrieval_top_k must be >= 10")
    if rag_retriever_system not in {"dense", "hybrid"}:
        raise ValueError("rag_retriever_system must be dense or hybrid")
    if rag_top_k <= 0:
        raise ValueError("rag_top_k must be positive")
    if not generator_model or not judge_model:
        raise ValueError("generator_model and judge_model are required")
    if type(generation_temperature) is not int or generation_temperature != GENERATION_TEMPERATURE:
        raise ValueError("generation_temperature must be the frozen benchmark value 0")
    if type(bootstrap_seed) is not int:
        raise ValueError("bootstrap_seed must be an integer")
    if type(bootstrap_samples) is not int or bootstrap_samples <= 0:
        raise ValueError("bootstrap_samples must be a positive integer")
    if type(alpha) is not float or not 0 < alpha < 1:
        raise ValueError("alpha must be a float between 0 and 1")


def freeze_evaluation_protocol(
    output_dir: Path,
    *,
    retrieval_top_k: int = 10,
    rag_retriever_system: str = "dense",
    rag_top_k: int = 5,
    generator_model: str,
    judge_model: str,
    generation_temperature: int = GENERATION_TEMPERATURE,
    bootstrap_seed: int = 20260819,
    bootstrap_samples: int = 2000,
    alpha: float = 0.05,
) -> dict:
    """Deliberately freeze final DEV-selected settings; never auto-freeze TEST."""

    _validate_freeze_arguments(
        retrieval_top_k=retrieval_top_k,
        rag_retriever_system=rag_retriever_system,
        rag_top_k=rag_top_k,
        generator_model=generator_model,
        judge_model=judge_model,
        generation_temperature=generation_temperature,
        bootstrap_seed=bootstrap_seed,
        bootstrap_samples=bootstrap_samples,
        alpha=alpha,
    )
    output_dir = Path(output_dir)
    frozen = verify_frozen_benchmark(output_dir)
    if not frozen["passed"]:
        raise RuntimeError(
            "Cannot freeze evaluation protocol for an invalid benchmark: "
            + "; ".join(frozen["blockers"])
        )
    manifest_path = output_dir / "benchmark_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    retrieval = retrieval_runtime_settings(
        top_k=retrieval_top_k,
        bootstrap_seed=bootstrap_seed,
        bootstrap_samples=bootstrap_samples,
        bootstrap_alpha=alpha,
    )
    rag = rag_runtime_settings(
        retriever_system=rag_retriever_system,
        top_k=rag_top_k,
        generator_model=generator_model,
        judge_model=judge_model,
        generation_temperature=generation_temperature,
        bootstrap_seed=bootstrap_seed,
        bootstrap_samples=bootstrap_samples,
        bootstrap_alpha=alpha,
    )
    payload = {
        "status": "FROZEN",
        "protocol_schema_version": EVALUATION_PROTOCOL_SCHEMA_VERSION,
        "benchmark": {
            "benchmark_name": manifest.get("benchmark_name"),
            "benchmark_version": manifest.get("benchmark_version"),
            "benchmark_manifest_sha256": sha256_file(manifest_path),
        },
        "retrieval": retrieval["retrieval"],
        "rag": rag["rag"],
        "statistics": retrieval["statistics"],
        "implementation": semantic_source_identity(),
    }
    payload["protocol_sha256"] = _canonical_hash(payload)
    path = output_dir / PROTOCOL_RELATIVE_PATH
    hash_path = output_dir / PROTOCOL_HASH_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or hash_path.exists():
        existing = path if path.exists() else hash_path
        raise RuntimeError(
            f"Refusing to overwrite frozen evaluation protocol artifact: {existing}"
        )
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n"
            )
    except FileExistsError as exc:
        raise RuntimeError(
            f"Refusing to overwrite frozen evaluation protocol: {path}"
        ) from exc
    try:
        with hash_path.open("x", encoding="utf-8") as handle:
            handle.write(sha256_file(path) + "\n")
    except FileExistsError as exc:
        raise RuntimeError(
            f"Refusing to overwrite frozen evaluation protocol hash: {hash_path}"
        ) from exc
    return payload


def _require_exact_keys(value: object, expected: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} requires exact keys {sorted(expected)}")
    return value


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_protocol_types(payload: dict) -> None:
    benchmark = payload["benchmark"]
    retrieval = payload["retrieval"]
    rag = payload["rag"]
    statistics = payload["statistics"]
    implementation = payload["implementation"]
    if not all(isinstance(benchmark[field], str) for field in BENCHMARK_KEYS):
        raise ValueError("benchmark binding values must be strings")
    if not _is_sha256(benchmark["benchmark_manifest_sha256"]):
        raise ValueError("benchmark_manifest_sha256 must be a lowercase SHA256")
    if (
        retrieval["protocol_version"] != RETRIEVAL_EVALUATION_PROTOCOL_VERSION
        or retrieval["systems"] != list(RETRIEVAL_SYSTEMS)
        or retrieval["headline_metric_names"] != list(RETRIEVAL_HEADLINE_METRICS)
        or retrieval["qrel_uncertainty_policy"] != UNCERTAIN_CONDENSING_POLICY_VERSION
        or type(retrieval["top_k"]) is not int
        or retrieval["top_k"] < 10
    ):
        raise ValueError("retrieval protocol values violate the frozen V3 schema")
    if (
        rag["protocol_version"] != RAG_EVALUATION_PROTOCOL_VERSION
        or rag["retriever_system"] not in {"dense", "hybrid"}
        or type(rag["top_k"]) is not int
        or rag["top_k"] <= 0
        or not isinstance(rag["generator_model_requested"], str)
        or not rag["generator_model_requested"]
        or not isinstance(rag["judge_model_requested"], str)
        or not rag["judge_model_requested"]
        or type(rag["generation_temperature"]) is not int
        or rag["generation_temperature"] != GENERATION_TEMPERATURE
        or rag["answer_prompt_version"] != ANSWER_PROMPT_VERSION
        or rag["rag_judge_protocol_version"] != RAG_JUDGE_PROTOCOL_VERSION
        or rag["evidence_packing_policy_version"] != EVIDENCE_PACKING_POLICY_VERSION
    ):
        raise ValueError("RAG protocol values violate the frozen V3 schema")
    if (
        statistics["bootstrap_unit"] != BOOTSTRAP_UNIT
        or type(statistics["bootstrap_seed"]) is not int
        or type(statistics["bootstrap_samples"]) is not int
        or statistics["bootstrap_samples"] <= 0
        or type(statistics["alpha"]) is not float
        or not 0 < statistics["alpha"] < 1
        or statistics["sign_flip_policy_version"] != PAIRED_SIGN_FLIP_POLICY_VERSION
    ):
        raise ValueError("statistics protocol values violate the frozen V3 schema")
    if not all(
        isinstance(implementation[field], list)
        and implementation[field]
        and all(isinstance(value, str) and value for value in implementation[field])
        for field in ("retrieval_source_files", "rag_source_files")
    ) or not all(
        _is_sha256(implementation[field])
        for field in ("retrieval_source_sha256", "rag_source_sha256")
    ):
        raise ValueError("implementation source closure is malformed")


def load_and_verify_evaluation_protocol(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    path = output_dir / PROTOCOL_RELATIVE_PATH
    hash_path = output_dir / PROTOCOL_HASH_RELATIVE_PATH
    try:
        expected_file_hash = hash_path.read_text(encoding="utf-8").strip()
        if expected_file_hash != sha256_file(path):
            raise ValueError("evaluation protocol file SHA256 mismatch")
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload = _require_exact_keys(payload, TOP_LEVEL_KEYS, "evaluation protocol")
        benchmark = _require_exact_keys(payload["benchmark"], BENCHMARK_KEYS, "benchmark binding")
        _require_exact_keys(payload["retrieval"], RETRIEVAL_KEYS, "retrieval protocol")
        _require_exact_keys(payload["rag"], RAG_KEYS, "RAG protocol")
        _require_exact_keys(payload["statistics"], STATISTICS_KEYS, "statistics protocol")
        implementation = _require_exact_keys(
            payload["implementation"], IMPLEMENTATION_KEYS, "implementation binding"
        )
        _validate_protocol_types(payload)
    except Exception as exc:
        raise RuntimeError(f"Frozen evaluation protocol is missing or invalid: {exc}") from exc

    if payload["status"] != "FROZEN":
        raise RuntimeError("Evaluation protocol status is not FROZEN")
    if payload["protocol_schema_version"] != EVALUATION_PROTOCOL_SCHEMA_VERSION:
        raise RuntimeError("Evaluation protocol schema version mismatch")
    if payload["protocol_sha256"] != _canonical_hash(payload):
        raise RuntimeError("Evaluation protocol content hash mismatch")

    manifest_path = output_dir / "benchmark_manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Cannot read bound benchmark manifest: {exc}") from exc
    expected_benchmark = {
        "benchmark_name": manifest.get("benchmark_name"),
        "benchmark_version": manifest.get("benchmark_version"),
        "benchmark_manifest_sha256": sha256_file(manifest_path),
    }
    if benchmark != expected_benchmark:
        raise RuntimeError("Evaluation protocol is bound to another benchmark manifest")
    if (
        benchmark["benchmark_name"] != V3_BENCHMARK_NAME
        or benchmark["benchmark_version"] != V3_BENCHMARK_VERSION
    ):
        raise RuntimeError("Evaluation protocol benchmark identity is not CareerRAGBench-Auto-V3")

    current_sources = semantic_source_identity()
    if implementation != current_sources:
        raise RuntimeError(
            "Evaluator semantic source identity changed after protocol freeze"
        )
    return payload


def assert_test_evaluation_protocol(
    output_dir: Path,
    *,
    evaluator: str,
    runtime_settings: dict,
) -> dict:
    protocol = load_and_verify_evaluation_protocol(output_dir)
    if evaluator not in {"RETRIEVAL", "RAG"}:
        raise ValueError("evaluator must be RETRIEVAL or RAG")
    section = evaluator.lower()
    expected = {
        section: protocol[section],
        "statistics": protocol["statistics"],
    }
    if runtime_settings != expected:
        raise RuntimeError(
            f"TEST {section} settings do not match the frozen DEV-selected evaluation protocol"
        )
    return protocol
