from rest_framework import viewsets, filters
from .models import Job
from ..core.paginators import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .serializers import CandidateJobSerializer, CandidateJobDetailSerializer, EmployerJobSerializer
from ..users.permissions import IsEmployerApproved


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
            return CandidateJobDetailSerializer
        return CandidateJobSerializer


class EmployerJobViewSet(viewsets.ModelViewSet):
    serializer_class = EmployerJobSerializer
    permission_classes = [IsEmployerApproved]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Job.objects.none()
        return Job.objects.filter(posted_by=user).select_related("category", "location")

    def perform_create(self, serializer):
        ep = self.request.user.employer_profile
        serializer.save(
            posted_by=self.request.user,
            company_name=ep.company_name,
        )
