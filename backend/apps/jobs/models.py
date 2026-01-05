from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from ckeditor.fields import RichTextField
from django.db.models import Q, F
from ..core.models import BaseModel
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class JobCategory(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=120, unique=True, db_index=True)

    def __str__(self):
        return self.name


class EmploymentType(models.TextChoices):
    FULL_TIME = "FULL_TIME", "Full-time"
    PART_TIME = "PART_TIME", "Part-time"
    INTERN = "INTERN", "Intern"
    REMOTE = "REMOTE", "Remote"


class ExperienceLevel(models.TextChoices):
    INTERN = "INTERN", "Intern"
    JUNIOR = "JUNIOR", "Junior"
    MIDDLE = "MIDDLE", "Middle"
    SENIOR = "SENIOR", "Senior"
    EXPERT = "EXPERT", "Expert"


class Tag(BaseModel):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Job(BaseModel):
    posted_by = models.ForeignKey(User, related_name='posted_jobs', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, db_index=True)
    description = RichTextField()
    requirements = RichTextField()
    benefits = RichTextField()

    company_name = models.CharField(max_length=255)

    category = models.ForeignKey(JobCategory, on_delete=models.PROTECT, related_name="jobs")
    location = models.ForeignKey(Location, on_delete=models.PROTECT, related_name="jobs")
    address = models.TextField(blank=True, default="")
    employment_type = models.CharField(
        max_length=20, choices=EmploymentType.choices, default=EmploymentType.FULL_TIME
    )
    experience_level = models.CharField(
        max_length=20, choices=ExperienceLevel.choices, default=ExperienceLevel.JUNIOR
    )

    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="jobs")

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                        Q(salary_min__isnull=True) |
                        Q(salary_max__isnull=True) |
                        Q(salary_min__lte=F("salary_max"))
                ),
                name="chk_salary_range_valid",
            )
        ]

    def clean(self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValidationError("salary_min must be <= salary_max")
        if self.deadline is not None and self.deadline < timezone.now().date():
            # optional rule: không bắt buộc, bạn có thể bỏ
            pass

    def __str__(self):
        return f"{self.title} - {self.company_name}"


class BookmarkJob(BaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='bookmarked_jobs', on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='bookmarked_by')

    class Meta:
        ordering = ['-created_date']
        constraints = [
            models.UniqueConstraint(fields=['user', 'job'], name='unique_user_job_bookmark'),
        ]

    def __str__(self):
            return f"{self.user} bookmarked {self.job}"
