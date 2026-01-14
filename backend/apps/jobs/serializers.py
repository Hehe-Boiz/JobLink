from rest_framework import serializers
from .models import Job, JobCategory, Location, Tag, BookmarkJob
from django.utils import timezone
from ..users.models import EmployerProfile
from ..core.serializers import MediaURLSerializer


class JobCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobCategory
        fields = ['id', 'name']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CandidateJobSerializer(serializers.ModelSerializer):
    category = JobCategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    employer_logo = serializers.SerializerMethodField()
    bookmark_id = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company_name', 'employer_logo',
            'category', 'location', 'employment_type',
            'experience_level', 'salary_min', 'salary_max',
            'deadline', 'tags', 'updated_date', 'active', 'bookmark_id'
        ]

    def get_employer_logo(self, obj):
        try:
            if hasattr(obj.posted_by, 'employer_profile') and obj.posted_by.employer_profile.logo:
                return obj.posted_by.employer_profile.logo.url
        except Exception:
            return None
        return None

    def get_bookmark_id(self, obj):
        user = self.context.get('request').user

        if not user.is_authenticated:
            return None
        try:
            bookmark = obj.bookmarked_by.filter(user=user).first()
            return bookmark.id if bookmark else None
        except:
            return None


class CompanyInfoSerializer(MediaURLSerializer):
    id = serializers.ReadOnlyField(source='pk')
    logo = serializers.SerializerMethodField()

    class Meta:
        model = EmployerProfile
        fields = ['id', 'company_name', 'website', 'logo', 'description', 'address', 'tax_code']

    def get_logo(self, obj):
        try:
            return obj.user.avatar.url
        except:
            pass
        return None

    def get_address(self, obj):
        return "Việt Nam"


class CandidateJobDetailSerializer(CandidateJobSerializer):
    company = CompanyInfoSerializer(source='posted_by.employer_profile', read_only=True)

    class Meta(CandidateJobSerializer.Meta):
        fields = CandidateJobSerializer.Meta.fields + ['description', 'requirements', 'benefits','company']


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
            "address",
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

    def get_tags_detail(self, job):
        return [{"id": t.id, "name": t.name} for t in job.tags.all()]

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
        validated_data.pop("posted_by", None)
        validated_data.pop("company_name", None)
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


class CandidateBookmarkJobSerializer(serializers.ModelSerializer):
    job = CandidateJobSerializer(read_only=True)  # chỉ dùng cho chiều dữ liệu đi ra

    job_id = serializers.PrimaryKeyRelatedField(
        queryset=Job.objects.filter(active=True),  # giới hạn phạm vi tìm kiếm
        source="job",  # gán vào trường job của Bookmark sau khi tìm thấy
        write_only=True  # dùng cho chiều dữ liệu đi vào
    )

    class Meta:
        model = BookmarkJob
        fields = ['id', 'job_id', 'job', 'created_date']
        read_only_fields = ['created_date']
