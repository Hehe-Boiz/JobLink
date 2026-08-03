from django.contrib import admin
from .models import ApplicationMatchAnalysis

@admin.register(ApplicationMatchAnalysis)
class ApplicationMatchAnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "application",
        "status",
        "final_score",
        "matcher_version",
        "processing_ms",
        "created_date",
    ]

    list_filter = [
        "status",
        "matcher_version",
        "parser_version",
        "scoring_version",
    ]

    search_fields = [
        "application__candidate__user__email",
        "application__job__title",
        "cv_hash",
        "job_fingerprint",
    ]

    readonly_fields = [
        "created_date",
        "updated_date",
    ]