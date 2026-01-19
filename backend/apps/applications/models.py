from django.db import models
from ..core.models import BaseModel
from ..jobs.models import Job
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField

from ..users.models import CandidateProfile

User = get_user_model()


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "SUBMITTED", "Submitted"
    REVIEWED = "REVIEWED", "Reviewed"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"

class Application(BaseModel):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    status = models.CharField(max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED)
    employer_note = models.TextField(blank=True, default="")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)  # 1..5 (optional)
    cover_letter = models.TextField(blank=True, default="")
    cv = CloudinaryField(resource_type='raw', folder='cvs', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["candidate", "job"], name="uniq_candidate_job_application")
        ]
