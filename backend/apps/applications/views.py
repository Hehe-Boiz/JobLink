from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import action
from apps.users.models import CandidateProfile
from apps.users.serializers import CandidateProfileSerializer
from .models import Application
from .serializers import EmployerApplicationSerializer, CandidateApplicationListSerializer, \
    CandidateApplicationWriteSerializer, CandidateApplicationDetailSerializer
from ..users.permissions import IsEmployerApproved, IsCandidate
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied


class EmployerApplicationViewSet(viewsets.ViewSet, generics.ListAPIView, generics.RetrieveUpdateAPIView):
    serializer_class = EmployerApplicationSerializer
    permission_classes = [IsEmployerApproved]

    def get_queryset(self):
        user = self.request.user
        ep = user.employer_profile

        if not user.is_authenticated:
            return Application.objects.none()
        qs = Application.objects.filter(job__posted_by=ep).select_related("job", "candidate")
        job_id = self.request.query_params.get("job_id")
        st = self.request.query_params.get("status")
        if job_id:
            qs = qs.filter(job_id=job_id)
        if st:
            qs = qs.filter(status=st)
        return qs

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
        return Application.objects.filter(user=user).select_related('job')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except Exception as e:
            if "uniq_user_job_application" in str(e):
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
