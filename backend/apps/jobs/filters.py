import django_filters
from .models import Job


class JobFilter(django_filters.FilterSet):
    min_salary = django_filters.NumberFilter(field_name="salary_min", lookup_expr='gte')
    max_salary = django_filters.NumberFilter(field_name="salary_max", lookup_expr='lte')

    location = django_filters.CharFilter(field_name='location__name', lookup_expr='icontains')

    created_after = django_filters.DateFilter(field_name="created_date", lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name="created_date", lookup_expr='lte')

    class Meta:
        model = Job
        fields = ['category', 'location', 'employment_type',
                  'experience_level']  # cấu hình cho DjangoFilterBackend dành cho tìm kiếm chính xác
