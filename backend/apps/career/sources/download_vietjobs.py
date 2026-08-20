from __future__ import annotations

from pathlib import Path
from huggingface_hub import snapshot_download


DATASET_REPO_ID = "dinhieufam/VietJobs"
BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "career_eval" / "vietjobs"


def download_vietjobs(output_dir: Path = DEFAULT_OUTPUT_DIR) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {DATASET_REPO_ID}...")

    snapshot_path = snapshot_download(
        repo_id=DATASET_REPO_ID,
        repo_type="dataset",
        local_dir=str(output_dir),
    )

    resolved_path = Path(snapshot_path).resolve()

    print("VietJobs download completed.")
    print(f"Dataset directory: {resolved_path}")
    return resolved_path


def main() -> None:
    download_vietjobs()


if __name__ == "__main__":
    main()