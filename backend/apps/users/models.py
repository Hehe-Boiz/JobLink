from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from cloudinary.models import CloudinaryField
from ..core.models import BaseModel
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    EMPLOYER = "EMPLOYER", "Employer"
    CANDIDATE = "CANDIDATE", "Candidate"


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


class EducationStatus(models.TextChoices):
    STUDYING = "STUDYING", "Đang học"
    GRADUATED = "GRADUATED", "Đã tốt nghiệp"
    DROPOUT = "DROPOUT", "Đã nghỉ học / Bảo lưu"

class Gender(models.TextChoices):
    MALE = "MALE", "Male"
    FEMALE = "FEMALE", "Female"


class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", UserRole.ADMIN)

        return super().create_superuser(username, email=email, password=password, **extra_fields)


class User(AbstractUser, BaseModel):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    avatar = CloudinaryField(resource_type='image', null=True, folder='avatars')
    phone = models.CharField(max_length=30, null=True)

    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CANDIDATE,
    )

    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    @property
    def full_name(self):
        if self.last_name and self.first_name:
            return f"{self.last_name} {self.first_name}"
        return self.first_name or self.last_name or self.username

    def __str__(self):
        return f"{self.first_name} ({self.email})"

    objects = CustomUserManager()

    @property
    def display_name(self):
        return self.first_name or self.username


class Skill(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class CandidateProfile(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="candidate_profile"
    )
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE)
    address = models.CharField(max_length=255, blank=True, default="")
    experience_years = models.IntegerField(default=0)
    dob = models.DateField(null=True, blank=True)
    specialization = models.CharField(max_length=255, blank=True, null=True)
    school_name = models.CharField(max_length=255, blank=True, null=True)

    resume = CloudinaryField(resource_type='raw', null=True, blank=True, folder='resumes')
    resume_name = models.CharField(max_length=255, blank=True, null=True)
    skills = models.ManyToManyField(Skill, related_name="candidates", blank=True)


    education_status = models.CharField(
        max_length=20,
        choices=EducationStatus.choices,
        default=EducationStatus.GRADUATED
    )

    def __str__(self):
        return self.user.get_full_name() if self.user.get_full_name() else self.user.username


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

    description = models.TextField(blank=True, default="")
    address = models.CharField(max_length=500, blank=True, null=True)

    status = models.CharField(max_length=20, choices=VerificationStatus.choices, default=VerificationStatus.PENDING)
    reject_reason = models.TextField(blank=True, default="")
    verified_at = models.DateTimeField(blank=True, null=True)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="verified_employers"
    )

    @property
    def is_verified(self):
        return self.status == VerificationStatus.APPROVED

    def __str__(self):
        return self.company_name

class WorkExperience(BaseModel):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="work_experiences")
    job_title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-start_date']

class Education(BaseModel):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="educations")
    institution = models.CharField(max_length=255)
    level = models.CharField(max_length=100)
    field_of_study = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-start_date']

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Ngày kết thúc không được nhỏ hơn ngày bắt đầu.'})

        if self.is_current and self.end_date:
            self.end_date = None

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.level} - {self.institution}"

class Language(BaseModel):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="languages")
    language = models.CharField(max_length=100)

    oral_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Điểm Nói (0-10)"
    )

    written_level = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name="Điểm Viết (0-10)"
    )

    is_first_language = models.BooleanField(
        default=False,
        verbose_name="Là ngôn ngữ mẹ đẻ"
    )

    def __str__(self):
        type_str = " (Native)" if self.is_first_language else ""
        return f"{self.language}{type_str} - Oral: {self.oral_level}, Written: {self.written_level}"

    class Meta:
        unique_together = ('candidate', 'language')



class Appreciation(BaseModel):
    candidate = models.ForeignKey(CandidateProfile, on_delete=models.CASCADE, related_name="appreciations")
    award_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ['-end_date']