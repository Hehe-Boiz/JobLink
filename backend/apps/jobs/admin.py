from django.contrib import admin
from django.db.models import Count
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path
from .models import Job, JobCategory, Tag, Location, BookmarkJob


class JobForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())

    class Meta:
        model = Job
        fields = '__all__'

class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active", "created_date")
    search_fields = ("name",)
    list_filter = ("active",)
    ordering = ("name",)


class JobAdmin(admin.ModelAdmin):
    form = JobForm
    list_display = (
        "id", "title", "company_name", "category", "location",
        "salary_min", "salary_max", "active", "created_date"
    )
    list_filter = ("active", "category", "location", "employment_type", "experience_level")
    search_fields = ("title", "company_name")
    ordering = ("-created_date",)
    autocomplete_fields = ("category", "location")
    filter_horizontal = ("tags",)

class BookmarkJobAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "job", "created_date", "active")
    search_fields = ("user__email", "job__title")
    list_filter = ("active",)
    ordering = ("-created_date",)


