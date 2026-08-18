from __future__ import annotations

from rest_framework import serializers


class CareerAskRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=2000, allow_blank=False, trim_whitespace=True)
    top_k = serializers.IntegerField(min_value=1, max_value=20, default=5)
    source = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=False)
    location_key = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=False)
    experience_level = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=False)
    employment_type = serializers.CharField(max_length=50, required=False, allow_null=True, allow_blank=False)
    category_key = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=False)


class CareerCitationSerializer(serializers.Serializer):
    citation_id = serializers.CharField()
    source = serializers.CharField()
    source_job_id = serializers.CharField()

    job_title = serializers.CharField()
    company_name = serializers.CharField()
    source_url = serializers.URLField(allow_null=True,)


class CareerAnswerResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    citations = CareerCitationSerializer(many=True)