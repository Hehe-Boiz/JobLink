from django.db import models
from ..core.models import BaseModel
from ..jobs.models import Job
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.core.exceptions import ValidationError

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

    @staticmethod
    def _get_cloudinary_identity(value) -> str:
        if not value:
            return ""

        public_id = getattr(value, "public_id", None)
        return str(public_id or value)

    def _validate_update_rules(self) -> None:
        # khi tạo mới sẽ không có primary key nên được bỏ qua
        if not self.pk:
            return

        original = (
            Application.objects
            .only(
                "candidate_id",
                "job_id",
                "status",
                "cv",
                "cover_letter",
            )
            .get(pk=self.pk)
        )

        errors = {}

        if self.candidate_id != original.candidate_id:
            errors["candidate"] = (
                "Candidate không thể thay đổi "
                "sau khi Application được tạo."
            )

        if self.job_id != original.job_id:
            errors["job"] = (
                "Job không thể thay đổi "
                "sau khi Application được tạo."
            )

        if original.status != ApplicationStatus.SUBMITTED:
            old_cv = self._get_cloudinary_identity(original.cv)
            new_cv = self._get_cloudinary_identity(self.cv)

            if old_cv != new_cv:
                errors["cv"] = (
                    "CV không thể thay đổi sau khi "
                    "hồ sơ đã được xử lý."
                )

            if self.cover_letter != original.cover_letter:
                errors["cover_letter"] = (
                    "Thư ứng tuyển không thể thay đổi sau khi "
                    "hồ sơ đã được xử lý."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self._validate_update_rules()
        return super().save(*args, **kwargs)