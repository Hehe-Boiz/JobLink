from django.db import models
from ..core.models import BaseModel
from ..jobs.models import Job
from django.contrib.auth import get_user_model

User = get_user_model()

class ApplicationStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    REVIEWING = "REVIEWING", "Reviewing"
    SHORTLISTED = "SHORTLISTED", "Shortlisted"
    REJECTED = "REJECTED", "Rejected"
    HIRED = "HIRED", "Hired"

class Application(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED)
    employer_note = models.TextField(blank=True, default="")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1..5 (optional)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "job"], name="uniq_user_job_application")
        ]
