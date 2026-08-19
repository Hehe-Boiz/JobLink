from __future__ import annotations

import argparse
import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "joblink.settings")

import django
django.setup()

from apps.career.evaluation.vietjobs import VietJobsSource
from apps.career.models import CareerJobChunk
from apps.career.normalization import normalize_key


ZERO_EMBEDDING = [0.0] * 384
BATCH_SIZE = 2000


def run(dataset_dir: Path) -> None:
    source = VietJobsSource(dataset_dir)

    CareerJobChunk.objects.filter(source="vietjobs").delete()

    buffer: list[CareerJobChunk] = []
    jobs = 0

    for record in source.iter_records():
        metadata = dict(record.metadata)

        row = CareerJobChunk(
            chunk_id=f"vietjobs-market-{record.source_job_id}",
            chunk_index=0,
            source="vietjobs",
            source_job_id=record.source_job_id,
            job_title=record.title[:255],
            company_name=record.company_name[:255],
            section="market_record",
            content=record.requirements or record.description or record.title,
            location_key=normalize_key(record.location_key),
            experience_level=normalize_key(record.experience_level),
            employment_type=normalize_key(record.employment_type),
            category_key=normalize_key(record.category_key),
            active=record.is_active,
            published_at=record.published_at,
            source_url=record.source_url,
            metadata=metadata,
            embedding=ZERO_EMBEDDING,
        )

        buffer.append(row)
        jobs += 1

        if len(buffer) >= BATCH_SIZE:
            CareerJobChunk.objects.bulk_create(buffer, batch_size=BATCH_SIZE)
            buffer.clear()
            print(f"loaded {jobs} jobs")

    if buffer:
        CareerJobChunk.objects.bulk_create(buffer, batch_size=BATCH_SIZE)

    print(f"DONE: {jobs} VietJobs loaded")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, required=True)
    args = parser.parse_args()

    run(args.dataset_dir)


if __name__ == "__main__":
    main()
