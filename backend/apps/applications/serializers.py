# apps/applications/serializers.py
from rest_framework import serializers

from .models import Application
from apps.jobs.models import Job  # để lấy job.title (nếu cần)


class EmployerApplicationSerializer(serializers.ModelSerializer):
    # Đổi cách hiển thị candidate rõ ràng hơn
    candidate_id = serializers.IntegerField(source="user.id", read_only=True)
    candidate_email = serializers.EmailField(source="user.email", read_only=True)
    candidate_name = serializers.CharField(source="user.display_name", read_only=True)

    job_id = serializers.IntegerField(source="job.id", read_only=True)
    job_title = serializers.CharField(source="job.title", read_only=True)
    company_name = serializers.CharField(source="job.company_name", read_only=True)

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
        # Bạn có thể đổi range theo ý (vd 0-100). Model đang integer nên MVP: 1..5
        if not (1 <= value <= 5):
            raise serializers.ValidationError("rating must be between 1 and 5")
        return value
