from rest_framework import serializers
from .models import Application
from ..jobs.models import Job  # để lấy job.title (nếu cần)
from ..core.serializers import MediaURLSerializer
from ..jobs.serializers import CandidateJobSerializer, CandidateJobDetailSerializer
from django.utils import timezone
from cloudinary.models import CloudinaryField
from apps.users.serializers import CandidateProfileSerializer
from apps.jobs.serializers import EmployerJobSerializer
class EmployerApplicationSerializer(serializers.ModelSerializer):
    candidate_id = serializers.IntegerField(source="candidate.user.id", read_only=True)
    candidate_email = serializers.EmailField(source="candidate.user.email", read_only=True)
    candidate_name = serializers.CharField(source="candidate.user.full_name", read_only=True)
    candidate_avatar = serializers.SerializerMethodField()
    job_id = serializers.IntegerField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)

    def get_candidate_avatar(self, obj):
        user = obj.candidate.user
        if user.avatar:
            return user.avatar.url
        return MediaURLSerializer().get_default_avatar(user)

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
        ]

    def validate_rating(self, value):
        if value is None:
            return value
        if not (1 <= value <= 5):
            raise serializers.ValidationError("rating must be between 1 and 5")
        return value


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
        fields = ['id', 'job', 'cv', 'cover_letter', 'status', 'employer_note', 'created_date', 'updated_date']
        read_only_fields = ['status', 'created_date', 'updated_date', 'employer_note']


class CandidateApplicationWriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        fields = ['job', 'cv', 'cover_letter']

    def validate_job(self, value):
        if not value.active:
            raise serializers.ValidationError("Công việc này đã đóng, bạn không thể ứng tuyển.")

        if value.deadline and value.deadline < timezone.now().date():
            raise serializers.ValidationError("Công việc này đã hết hạn nộp hồ sơ.")

        return value

    def validate_cv(self, value):
        valid_extensions = ['.pdf', '.doc', '.docx']
        if not any(value.name.lower().endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError("Chỉ chấp nhận file định dạng PDF hoặc Word (.doc, .docx).")

        return value
