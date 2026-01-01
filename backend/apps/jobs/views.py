from rest_framework import viewsets, filters
from .models import Job
from ..core.paginators import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .serializers import JobSerializer, JobDetailSerializer


# danh sách và chi tiết job
class JobViewCandidate(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.all()
    pagination_class = StandardResultsSetPagination

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'company_name']  # cấu hình cho SearchFilter
    filterset_fields = ['category', 'location', 'employment_type',
                        'experience_level']  # cấu hình cho DjangoFilterBackend dành cho tìm kiếm chính xác
    ordering_fields = ['salary_min', 'salary_max', 'created_date']  # các trường người dùng được sắp xếp
    ordering = ['-created_date']  # sắp xếp mặc định

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(deadline__gte=timezone.now().date())

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return JobDetailSerializer
        return JobSerializer
