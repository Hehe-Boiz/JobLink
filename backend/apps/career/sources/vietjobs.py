from __future__ import annotations

import csv
from collections.abc import Iterator
from pathlib import Path
from apps.career.domain import RawJobRecord

BACKEND_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_DATASET_DIR = BACKEND_ROOT / "data" / "career_eval" / "vietjobs"

REQUIRED_COLUMNS = {
    "job_title",
    "description",
    "requirements_text",
    "category",
}


class VietJobsSource:
    SOURCE_NAME = "vietjobs"
    def __init__(self, dataset_dir: Path = DEFAULT_DATASET_DIR) -> None:
        self.dataset_dir = Path(dataset_dir)

    def iter_records(self, limit: int | None = None) -> Iterator[RawJobRecord]:
        csv_path = self._find_dataset_csv()
        produced = 0
        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            self._validate_columns(reader.fieldnames)

            for row_number, row in enumerate(reader, start=1):
                title = self._value(row, "job_title")
                if not title:
                    continue

                yield self._to_record(row=row, row_number=row_number, csv_path=csv_path)
                produced += 1
                if limit is not None and produced >= limit:
                    break

    def _to_record(self, *, row: dict[str, str], row_number: int, csv_path: Path) -> RawJobRecord:
        return RawJobRecord(
            source=self.SOURCE_NAME,
            source_job_id=(f"{csv_path.stem}:{row_number}"),
            title=self._value(row, "job_title"),
            company_name="",
            description=self._value(row, "description"),
            requirements=self._value(row, "requirements_text"),
            benefits=self._value(row, "benefits"),
            location_key=self._optional_value(row, "location"),
            experience_level=self._optional_value(row, "experience_required"),
            employment_type=self._optional_value(row, "contract_type"),
            category_key=self._optional_value(row, "category"),
            is_active=True,
            metadata={
                "country": self._optional_value(row, "country"),
                "qualifications": self._optional_value(row, "qualifications"),
                "technical_skills": self._optional_value(row, "technical_skills"),
                "soft_skills": self._optional_value(row, "soft_skills"),
                "languages_required": self._optional_value(row, "languages_required"),
                "salary": self._optional_value(row, "salary"),
                "working_hours": self._optional_value(row, "working_hours"),
            },
        )

    def _find_dataset_csv(self) -> Path:
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"VietJobs dataset directory does not exist: {self.dataset_dir}")
        candidates = sorted(self.dataset_dir.rglob("*.csv"))
        if not candidates:
            raise FileNotFoundError(f"No CSV file found inside {self.dataset_dir}")

        for path in candidates:
            with path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.reader(file)

                try:
                    header = next(reader)
                except StopIteration:
                    continue

            if REQUIRED_COLUMNS.issubset(set(header)):
                return path

        raise FileNotFoundError(f"Could not find VietJobs CSV containing required columns: {sorted(REQUIRED_COLUMNS)}")

    @staticmethod
    def _validate_columns(fieldnames: list[str] | None) -> None:
        if fieldnames is None:
            raise ValueError("VietJobs CSV has no header.")

        missing = REQUIRED_COLUMNS - set(fieldnames)
        if missing:
            raise ValueError(f"VietJobs CSV is missing columns: {sorted(missing)}")

    @staticmethod
    def _value(row: dict[str, str], key: str) -> str:
        value = row.get(key)

        if value is None:
            return ""

        return value.strip()

    @classmethod
    def _optional_value(cls, row: dict[str, str], key: str) -> str | None:
        value = cls._value(row, key)

        return value or None