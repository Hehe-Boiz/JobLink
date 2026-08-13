from django.db import models

from apps.applications.models import Application
from apps.core.models import BaseModel

class ApplicationMatchStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PARSING = "PARSING", "Parsing"
    MATCHING = "MATCHING", "Matching"
    EXPLAINING = "EXPLAINING", "Explaining"
    COMPLETED = "COMPLETED", "Completed"
    FAILED = "FAILED", "Failed"

class ApplicationMatchAnalysis(BaseModel):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="match_analyses")
    status = models.CharField(max_length=20, choices=ApplicationMatchStatus.choices, default=ApplicationMatchStatus.PENDING, db_index=True)
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    matched_skills = models.JSONField(default=list, blank=True)
    partial_skills = models.JSONField(default=list, blank=True)
    missing_skills = models.JSONField(default=list, blank=True)
    evidence = models.JSONField(default=list, blank=True)
    # Lưu cách score được cấu thành
    breakdown = models.JSONField(default=dict, blank=True)
    explanation = models.TextField(blank=True, default="")
    cv_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    job_fingerprint = models.CharField(max_length=64, blank=True, default="", db_index=True)
    job_snapshot = models.JSONField(default=dict, blank=True)

    parser_version = models.CharField(max_length=50, default="document-text-v1")
    matcher_version = models.CharField(max_length=50, default="exact-alias-v1")
    scoring_version = models.CharField(max_length=50, default="required-skill-ratio-v1")
    embedding_version = models.CharField(max_length=100, blank=True, default="")
    prompt_version = models.CharField(max_length=50, blank=True, default="")

    processing_ms = models.PositiveIntegerField(null=True, blank=True)
    error_code = models.CharField(max_length=100, blank=True, default="")
    error_message = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_date"]
        indexes = [
            models.Index(
                fields=["application", "status"],
                name="app_match_status_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Application {self.application_id} - "
            f"{self.status} - {self.final_score}"
        )