from rest_framework import serializers
from .models import Application
from ..core.serializers import MediaURLSerializer
from ..jobs.serializers import CandidateJobSerializer, CandidateJobDetailSerializer
from django.utils import timezone
from apps.users.serializers import UserSerializer, SkillSerializer, WorkExperienceSerializer, EducationSerializer
from apps.users.models import CandidateProfile
from pathlib import Path

ALLOWED_CV_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_CV_SIZE_BYTES = 5 * 1024 * 1024

class EmployerApplicationSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(source="candidate.user.id", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.user.email", read_only=True)
    candidate_name = serializers.CharField(source="candidate.user.full_name", read_only=True)
    candidate_avatar = serializers.SerializerMethodField()
    job_id = serializers.IntegerField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)
    submitted_cv = serializers.SerializerMethodField()

    def get_candidate_avatar(self, obj):
        user = obj.candidate.user
        if user.avatar:
            return user.avatar.url
        return MediaURLSerializer().get_default_avatar(user)

    def get_submitted_cv(self, obj):
        if not obj.cv:
            return None

        return obj.cv.url


    class Meta:
        model = Application
        fields = [
            "id",
            "job_id",
            "job_title",
            "company_name",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "candidate_avatar",

            "submitted_cv",
            "cover_letter",
            "created_date",

            "status",
            "employer_note",
            "rating",
        ]
        read_only_fields = [
            "id",
            "job_id",
            "job_title",
            "company_name",
            "candidate_id",
            "candidate_email",
            "candidate_name",
            "candidate_avatar",
            "submitted_cv",
            "cover_letter",
            "created_date",
        ]

    def validate_rating(self, value):
        if value is None:
            return value
        if not (1 <= value <= 5):
            raise serializers.ValidationError("rating must be between 1 and 5")
        return value

class EmployerCandidateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skill_list = SkillSerializer(source="skills",many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True,read_only=True)

    class Meta:
        model = CandidateProfile
        fields = [
            "user",
            "specialization",
            "school_name",
            "education_status",
            "skill_list",
            "work_experiences",
            "educations",
        ]

        read_only_fields = fields

class CandidateApplicationListSerializer(serializers.ModelSerializer):
    job = CandidateJobSerializer(read_only=True)

    class Meta:
        model = Application
        fields = ['id', 'job', 'status', 'created_date']
        read_only_fields = ['status', 'created_date']


class CandidateApplicationDetailSerializer(MediaURLSerializer):
    job = CandidateJobDetailSerializer(read_only=True)
    media_fields = ["cv"]

    class Meta:
        model = Application
        fields = ['id', 'job', 'cv', 'cover_letter', 'status', 'created_date', 'updated_date']
        read_only_fields = ['status', 'created_date', 'updated_date']


def validate_cv_file(file):
    extension = Path(file.name).suffix.lower()

    if extension not in ALLOWED_CV_EXTENSIONS:
        raise serializers.ValidationError("Chỉ chấp nhận PDF hoặc Word (.pdf, .doc, .docx).")

    if file.size > MAX_CV_SIZE_BYTES:
        raise serializers.ValidationError("Kích thước CV không được vượt quá 5 MB.")

    return file

class CandidateApplicationCreateSerializer (serializers.ModelSerializer):
    cv = serializers.FileField (required=True, allow_null=False, write_only=True)

    class Meta:
        model = Application
        fields = ["job", "cv", "cover_letter",]

    def validate_job(self, job):
        if not job.active: 
            raise serializers.ValidationError(
                "Công việc này đã đóng, bạn không thể ứng tuyển."
            )

        if job.deadline and job.deadline < timezone.localdate():
            raise serializers.ValidationError(
                "Công việc này đã hết hạn nộp hồ sơ."
            )

        return job

    def validate_cv(self, cv):
        return validate_cv_file(cv)

    def validate(self, attrs):
        request = self.context["request"]
        candidate = request.user.candidate_profile
        # attrs là những dữ liệu sau khi parse từ json sang object python
        job = attrs["job"]

        if Application.objects.filter(candidate=candidate, job=job,).exists():
            raise serializers.ValidationError(
                {
                    "job": "Bạn đã ứng tuyển công việc này rồi."
                }
            )

        return attrs

class CandidateApplicationUpdateSerializer(serializers.ModelSerializer):
    cv = serializers.FileField(
        required=False,
        allow_null=False,
    )

    IMMUTABLE_FIELDS = frozenset({
        "candidate",
        "candidate_id",
        "job",
        "job_id",
    })

    class Meta:
        model = Application
        fields = [
            "cover_letter",
            "cv",
        ]

    def validate_cv(self, cv):
        return validate_cv_file(cv)

    def validate(self, attrs):
        # thực hiện phép giao
        attempted_fields = self.IMMUTABLE_FIELDS.intersection(
            # intitial_data là dữ liệu thô mà client thực sự gửi lên.
            self.initial_data.keys()
        )

        if attempted_fields:
            errors = {
                field: "Field này không thể thay đổi sau khi đã ứng tuyển."
                for field in sorted(attempted_fields)
            }
            raise serializers.ValidationError(errors)

        return attrs