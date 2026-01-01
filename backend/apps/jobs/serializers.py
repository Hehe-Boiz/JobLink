from rest_framework import serializers
from .models import Job, JobCategory, Location, Tag


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


class JobSerializer(serializers.ModelSerializer):
    category = JobCategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    employer_logo = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company_name', 'employer_logo',
            'category', 'location', 'employment_type',
            'experience_level', 'salary_min', 'salary_max',
            'deadline', 'tags', 'updated_date', 'active'
        ]

    def get_employer_logo(self, obj):
        try:
            if hasattr(obj.posted_by, 'employer_profile') and obj.posted_by.employer_profile.logo:
                return obj.posted_by.employer_profile.logo.url
        except Exception:
            return None
        return None


class JobDetailSerializer(JobSerializer):
    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ['description', 'requirements', 'benefits']
