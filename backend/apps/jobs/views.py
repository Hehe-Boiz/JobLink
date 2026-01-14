from rest_framework import viewsets, filters, status, generics
from rest_framework.permissions import AllowAny

from .models import Job, BookmarkJob, JobCategory, Location
from ..core.paginators import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from .serializers import CandidateJobSerializer, CandidateJobDetailSerializer, EmployerJobSerializer, \
    CandidateBookmarkJobSerializer, JobCategorySerializer, LocationSerializer
from apps.applications.serializers import EmployerApplicationSerializer
from ..users.permissions import IsEmployerApproved, IsCandidate
from rest_framework.response import Response
from rest_framework.decorators import action
from .filters import JobFilter



class JobViewCandidate(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.filter(deadline__gte=timezone.now())
    pagination_class = StandardResultsSetPagination

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = JobFilter
    search_fields = ['title', 'company_name']
    ordering_fields = ['salary_min', 'salary_max', 'created_date']
    ordering = ['-created_date']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(deadline__gte=timezone.now().date(), active=True)

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


class EmployerJobViewSet(viewsets.ViewSet, generics.ListCreateAPIView, generics.UpdateAPIView,
                         generics.DestroyAPIView):
    serializer_class = EmployerJobSerializer
    permission_classes = [IsEmployerApproved]
    pagination_class = StandardResultsSetPagination
    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Job.objects.none()
        return Job.objects.filter(posted_by=user.employer_profile, active=True).select_related("category", "location").order_by('-created_date')

    def destroy(self, request, *args, **kwargs):
        job = self.get_object()
        job.active = False
        job.save()
        return Response(
            {"detail": "Đã xóa tin tuyển dụng (Soft Delete)"},
            status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        ep = self.request.user.employer_profile
        serializer.save(
            posted_by=ep,
            company_name=ep.company_name,
        )

    @action(methods=['get'], url_path='applications', detail=True)
    def get_applications(self, request, pk):
        applications = self.get_object().applications.filter(active=True)
        return Response(EmployerApplicationSerializer(applications, many=True).data, status=status.HTTP_200_OK)

class BookmarkJobViewSet(viewsets.ModelViewSet):
    serializer_class = CandidateBookmarkJobSerializer
    permission_classes = [IsCandidate]
    http_method_names = ['get', 'post', 'delete']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return BookmarkJob.objects.filter(user=self.request.user).select_related('job')
        return BookmarkJob.objects.none()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
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
