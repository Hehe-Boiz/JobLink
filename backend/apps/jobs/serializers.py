# apps/jobs/serializers.py
from django.utils import timezone
from rest_framework import serializers

from .models import Job, JobCategory, Location, Tag


class EmployerJobSerializer(serializers.ModelSerializer):
    # Hiển thị thêm tên category/location cho dễ đọc
    category_name = serializers.CharField(source="category.name", read_only=True)
    location_name = serializers.CharField(source="location.name", read_only=True)

    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all(), required=False
    )
    tags_detail = serializers.SerializerMethodField()

    posted_by = serializers.IntegerField(source="posted_by_id", read_only=True)
    company_name = serializers.CharField(read_only=True)

    category = serializers.PrimaryKeyRelatedField(queryset=JobCategory.objects.all())
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all())

    class Meta:
        model = Job
        fields = [
            "id",
            "posted_by",
            "title",
            "description",
            "requirements",
            "benefits",
            "company_name",
            "category",
            "category_name",
            "location",
            "location_name",
            "employment_type",
            "experience_level",
            "salary_min",
            "salary_max",
            "deadline",
            "tags",
            "tags_detail",
        ]
        read_only_fields = ["id", "posted_by", "company_name", "category_name", "location_name", "tags_detail"]

    def get_tags_detail(self, obj):
        return [{"id": t.id, "name": t.name} for t in obj.tags.all()]

    def validate(self, attrs):
        salary_min = attrs.get("salary_min")
        salary_max = attrs.get("salary_max")
        deadline = attrs.get("deadline")

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError({"salary_min": "salary_min must be <= salary_max"})

        # Optional rule (bạn có thể bỏ nếu không muốn chặn)
        if deadline is not None and deadline < timezone.now().date():
            raise serializers.ValidationError({"deadline": "deadline must be today or in the future"})

        return attrs

    def _require_approved_employer(self, request_user):
        ep = getattr(request_user, "employer_profile", None)
        if not ep:
            raise serializers.ValidationError("Employer profile not found")

        # ep.is_verified có thể là field hoặc @property (tuỳ bạn refactor)
        if not getattr(ep, "is_verified", False):
            raise serializers.ValidationError("Employer is not approved/verified yet")
        return ep

    def create(self, validated_data):
        request = self.context.get("request")
        tags = validated_data.pop("tags", [])

        ep = self._require_approved_employer(request.user)

        job = Job.objects.create(
            posted_by=request.user,
            company_name=ep.company_name,
            **validated_data
        )
        if tags:
            job.tags.set(tags)
        return job

    def update(self, instance, validated_data):
        # Không cho sửa posted_by/company_name bằng API
        validated_data.pop("posted_by", None)
        validated_data.pop("company_name", None)

        tags = validated_data.pop("tags", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if tags is not None:
            instance.tags.set(tags)
        return instance
