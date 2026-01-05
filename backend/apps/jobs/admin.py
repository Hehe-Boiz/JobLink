from django.contrib import admin
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from .models import Job, JobCategory, Tag, Location


class JobForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget())
    benefits = forms.CharField(widget=CKEditorUploadingWidget())
    requirements = forms.CharField(widget=CKEditorUploadingWidget())
    class Meta:
        model = Job
        fields = '__all__'


@admin.register(JobCategory)
class JobCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'salary_min', 'deadline', 'active', 'created_date')
    list_filter = ('active', 'employment_type', 'experience_level', 'location', 'category')
    search_fields = ('title', 'company_name')
    readonly_fields = ('created_date', 'updated_date')

    # Fieldsets để group các trường trong admin cho đẹp (tùy chọn)
    fieldsets = (
        ('Thông tin cơ bản', {
            'fields': ('title', 'company_name', 'employer_website', 'category', 'location', 'active')
        }),
        ('Chi tiết công việc', {
            'fields': ('employment_type', 'experience_level', 'salary_min', 'salary_max', 'deadline', 'tags')
        }),
        ('Nội dung', {
            'fields': ('description', 'requirements', 'benefits')
        }),
        ('System Info', {
            'fields': ('created_date', 'updated_date', 'posted_by'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.posted_by_id:
            obj.posted_by = request.user
        super().save_model(request, obj, form, change)
