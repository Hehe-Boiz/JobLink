from django.contrib.auth.models import AbstractUser
from django.db import models
from cloudinary.models import CloudinaryField
from apps.core.models import BaseModel

class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    EMPLOYER = "EMPLOYER", "Employer"
    CANDIDATE = "CANDIDATE", "Candidate"

class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    avatar = CloudinaryField(null=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
    )

    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.first_name} ({self.email})"

    @property
    def display_name(self):
        return self.first_name or self.username

class CandidateProfile(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="candidate_profile"
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    address = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.full_name

class EmployerProfile(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="employer_profile"
    )
    company_name = models.CharField(max_length=255)
    tax_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    website = models.URLField(blank=True, null=True)
    logo = CloudinaryField(null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="verified_employers"
    )
    def __str__(self):
        return self.company_name