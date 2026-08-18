from __future__ import annotations

from django.db import models
from pgvector.django import VectorField

from apps.core.models import BaseModel


class CareerJobChunk(BaseModel):
    chunk_id = models.CharField(max_length=255, unique=True)
    chunk_index = models.PositiveIntegerField()
    source = models.CharField(max_length=50, db_index=True)
    source_job_id = models.CharField(max_length=255, db_index=True)
    job_title = models.CharField(max_length=255,)
    company_name = models.CharField(max_length=255, blank=True, default="")
    section = models.CharField(max_length=50, db_index=True)
    content = models.TextField()
    location_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    experience_level = models.CharField(max_length=50, null=True,blank=True, db_index=True)
    employment_type = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    category_key = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    published_at = models.DateTimeField(null=True, blank=True,)
    source_url = models.URLField(max_length=1000, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    embedding = VectorField(dimensions=384,)

    class Meta:
        ordering = ["source", "source_job_id", "chunk_index"]

        indexes = [
            models.Index(
                fields=["source", "source_job_id"],
                name="career_source_job_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.job_title} "
            f"[{self.section}] "
            f"#{self.chunk_index}"
        )