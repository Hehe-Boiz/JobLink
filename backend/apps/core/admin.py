from django.contrib import admin
from django.db.models import Count, Sum
from django.utils.html import format_html
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.admin import AdminSite
from apps.users.models import EmployerProfile, VerificationStatus, CandidateProfile
from apps.jobs.models import Job, JobCategory
from apps.applications.models import Application

User = get_user_model()

class JobLinkAdminSite(AdminSite):
    site_header = "HỆ THỐNG QUẢN TRỊ JOBLINK"
    site_title = "JobLink Admin"
    index_title = "Dashboard Tổng Quan"

admin_site = JobLinkAdminSite(name='joblink_admin')


class BaseAdminView(admin.ModelAdmin):
    list_per_page = 20

class EmployerProfileAdmin(admin.ModelAdmin):
    list_per_page = 10
    list_display = ('company_name', 'user_email', 'tax_code', 'status_badge', 'verified_at')
    list_filter = ('status', 'verified_at')
    search_fields = ('company_name', 'tax_code', 'user__email')
    actions = ['approve_employers', 'reject_employers']
    readonly_fields = ('user', 'company_name', 'tax_code','website','verified_by', 'verified_at')
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email Đăng Nhập"

    def has_change_permission(self, request, obj=None):
        return False
    def status_badge(self, obj):
        colors = {
            'PENDING': '#FFC107',
            'APPROVED': '#28A745',
            'REJECTED': '#DC3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    status_badge.short_description = "Trạng thái"

    @admin.action(description='✅ DUYỆT các tài khoản đã chọn')
    def approve_employers(self, request, queryset):
        rows_updated = queryset.update(
            status=VerificationStatus.APPROVED,
            verified_at=timezone.now(),
            verified_by=request.user,
            reject_reason="",
        )
        self.message_user(request, f"Đã duyệt thành công {rows_updated} nhà tuyển dụng.")

    @admin.action(description='❌ TỪ CHỐI các tài khoản đã chọn')
    def reject_employers(self, request, queryset):
        rows_updated = queryset.update(status=VerificationStatus.REJECTED,
        verified_at = timezone.now(),
        verified_by = request.user,
        reject_reason="Thông tin cung cấp không đủ tính xác thực"
        )
        self.message_user(request, f"Đã từ chối {rows_updated} nhà tuyển dụng.")

admin_site.register(EmployerProfile, EmployerProfileAdmin)
admin_site.register(Job, BaseAdminView)
admin_site.register(JobCategory, BaseAdminView)
admin_site.register(User, BaseAdminView)
admin_site.register(Application, BaseAdminView)

