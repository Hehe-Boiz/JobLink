from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action

from ..core.paginators import StandardResultsSetPagination
from ..users.models import CandidateProfile
from ..users.serializers import CandidateProfileSerializer
from .models import Application
from .serializers import EmployerApplicationSerializer, CandidateApplicationListSerializer, \
    CandidateApplicationWriteSerializer, CandidateApplicationDetailSerializer
from ..users.permissions import IsEmployerApproved, IsCandidate
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


class EmployerApplicationViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveUpdateAPIView):
    serializer_class = EmployerApplicationSerializer
    permission_classes = [IsEmployerApproved]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()
        qs = Application.objects.filter(job__posted_by=user.employer_profile).select_related("job", "candidate",
                                                                                             "candidate__user")
        job_id = self.request.query_params.get("job_id")
        if job_id:
            qs = qs.filter(job_id=job_id)
        st = self.request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)

        # 3. Tìm kiếm (Thay thế logic q lúc nãy)
        q = self.request.query_params.get('q')
        if q:
            from django.db.models import Q
            qs = qs.filter(
                Q(candidate__user__first_name__icontains=q) |
                Q(candidate__user__last_name__icontains=q) |
                Q(candidate__user__email__icontains=q)
            )

        return qs.order_by('-created_date')

    @action(methods=['get'], url_path='candidate-profile', detail=True)
    def get_candidate_profile(self, request, pk):
        application = self.get_object()
        return Response(CandidateProfileSerializer(application.candidate).data, status=status.HTTP_200_OK)


class CandidateApplicationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsCandidate]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()
        return Application.objects.filter(candidate=user.candidate_profile).select_related(
            'job',
            'job__category',
            'job__location',
            'job__posted_by'
        ).prefetch_related(
            'job__tags'
        )

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user.candidate_profile)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            if "uniq_candidate_job_application" in str(e):
                return Response(
                    {"detail": "Bạn đã ứng tuyển công việc này rồi."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            raise e

    def perform_update(self, serializer):
        instance = serializer.instance

        if instance.status != 'SUBMITTED':
            raise PermissionDenied("Hồ sơ đã được Nhà tuyển dụng xử lý, bạn không thể chỉnh sửa nữa.")

        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != 'SUBMITTED':
            raise PermissionDenied("Bạn không thể hủy ứng tuyển khi hồ sơ đang được xử lý hoặc đã có kết quả.")

        instance.delete()

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateApplicationListSerializer
        if self.action == "retrieve":
            return CandidateApplicationDetailSerializer
        return CandidateApplicationWriteSerializer
