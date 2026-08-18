from __future__ import annotations

from collections.abc import Iterator
from apps.jobs.models import Job
from ..domain import RawJobRecord


class JobLinkJobSource:
    SOURCE_NAME = "joblink"
    def iter_records(self, active_only: bool = True) -> Iterator[RawJobRecord]:
        queryset = Job.objects.select_related("category", "location")
        if active_only:
            queryset = queryset.filter(active=True)

        for job in queryset.iterator():
            yield self.to_record(job)

    def to_record(self, job: Job) -> RawJobRecord:

        return RawJobRecord(
            source=self.SOURCE_NAME,
            source_job_id=str(job.pk),

            title=job.title,
            company_name=job.company_name,

            description=job.description or "",
            requirements=job.requirements or "",
            benefits=job.benefits or "",

            location_key=(
                job.location.name
                if job.location_id
                else None
            ),

            experience_level=job.experience_level,
            employment_type=job.employment_type,

            category_key=(
                job.category.name
                if job.category_id
                else None
            ),

            is_active=job.active,
            published_at=job.created_date,
        )