from rest_framework import viewsets, filters, status, generics
from rest_framework.permissions import AllowAny

from .models import Job, BookmarkJob, JobCategory, Location
from ..core.paginators import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .serializers import CandidateJobSerializer, CandidateJobDetailSerializer, EmployerJobSerializer, \
    CandidateBookmarkJobSerializer, JobCategorySerializer, LocationSerializer
from ..users.permissions import IsEmployerApproved, IsCandidate
from rest_framework.response import Response
from rest_framework.decorators import action
from .filters import JobFilter


# danh sách và chi tiết job
class JobViewCandidate(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.filter(deadline__gte=timezone.now())
    pagination_class = StandardResultsSetPagination

    filter_backends = [
        DjangoFilterBackend, # Lọc theo các trường cố định
        filters.SearchFilter, # hỗ trợ tìm kiếm theo từ khóa
        filters.OrderingFilter, # sắp xếp kết quả
    ]
    filterset_class = JobFilter
    search_fields = ['title', 'company_name']  # cấu hình cho SearchFilter
    ordering_fields = ['salary_min', 'salary_max', 'created_date']  # các trường người dùng được sắp xếp
    ordering = ['-created_date']  # sắp xếp mặc định

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(deadline__gte=timezone.now().date())

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CandidateJobDetailSerializer
        return CandidateJobSerializer

    @action(detail=False, methods=['get'], url_path='compare')
    def compare(self, request):
        ids_param = request.query_params.get('ids')
        if not ids_param:
            return Response(
                {"detail": "Vui lòng cung cấp danh sách ID công việc (ví dụ: ?ids=1,2)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job_ids = [int(x.strip()) for x in ids_param.split(',') if x.strip().isdigit()]
        except ValueError:
            return Response(
                {"detail": "ID công việc không hợp lệ."},
                status=status.HTTP_400_BAD_REQUEST
            )

        jobs = Job.objects.filter(id__in=job_ids, active=True).select_related('category', 'location')

        if not jobs.exists():
            return Response(
                {"detail": "Không tìm thấy công việc nào hợp lệ."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CandidateJobDetailSerializer(jobs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


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


class BookmarkJobViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateBookmarkJobSerializer
    permission_classes = [IsCandidate]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return BookmarkJob.objects.filter(user=self.request.user).select_related('job')
        return BookmarkJob.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)  # gán vào giai đoạn này vì backend chỉ tin chính nó

    def create(self, request, *args, **kwargs):
        # Bắt lỗi nếu đã lưu rồi mà bấm lưu tiếp
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            if "unique_user_job_bookmark" in str(e):
                return Response(
                    {"detail": "Bạn đã lưu công việc này rồi."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise e
class JobCategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = JobCategorySerializer
    queryset = JobCategory.objects.all()
    permission_classes = [AllowAny]


class LocationViewSet(viewsets.ViewSet, generics.ListAPIView):
    serializer_class = LocationSerializer
    queryset = Location.objects.all()
    permission_classes = [AllowAny]
