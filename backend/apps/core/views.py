from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from apps.jobs.models import Job
from apps.users.models import EmployerProfile, CandidateProfile
from apps.applications.models import Application

def is_admin(user):
    return user.is_authenticated and (user.is_superuser or user.is_staff)

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_jobs = Job.objects.count()
    total_candidates = CandidateProfile.objects.count()
    total_employers = EmployerProfile.objects.count()
    total_applications = Application.objects.count()

    total_revenue = Job.objects.count() * 500000
    current_year = timezone.now().year
    jobs_chart = Job.objects.filter(created_date__year=current_year) \
        .annotate(month=TruncMonth('created_date')) \
        .values('month') \
        .annotate(count=Count('id')) \
        .order_by('month')

    labels = [item['month'].strftime('%T%m') for item in jobs_chart]
    data = [item['count'] for item in jobs_chart]

    recent_jobs = Job.objects.select_related('posted_by').order_by('-created_date')[:5]

    context = {
        'stats': {
            'jobs': total_jobs,
            'candidates': total_candidates,
            'employers': total_employers,
            'apps': total_applications,
            'revenue': total_revenue
        },
        'chart': {
            'labels': labels,
            'data': data
        },
        'recent_jobs': recent_jobs
    }

    return render(request, 'custom_admin/dashboard.html', context)
