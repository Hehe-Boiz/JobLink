from rest_framework import serializers

from .models import ApplicationMatchAnalysis


class ApplicationMatchAnalysisSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = ApplicationMatchAnalysis

        fields = [
            "id",
            "application",
            "status",
            "final_score",
            "matched_skills",
            "partial_skills",
            "missing_skills",
            "evidence",
            "breakdown",
            "explanation",
            "cv_hash",
            "job_fingerprint",
            "parser_version",
            "matcher_version",
            "scoring_version",
            "embedding_version",
            "prompt_version",
            "processing_ms",
            "error_code",
            "error_message",
            "created_date",
            "updated_date",
        ]

        read_only_fields = fields # Tất cả đều read-only vì client không được tự gửi