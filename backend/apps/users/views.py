from rest_framework import generics, status, viewsets, parsers, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import User, VerificationStatus
from .models import EmployerProfile, WorkExperience, Education, Skill
from .permissions import IsAdminRole, IsCandidate, IsEmployer
from .serializers import EmployerProfileSerializer, AdminEmployerSerializer, Language, LanguageSerializer, Appreciation
from . import serializers
from .serializers import CandidateRegisterSerializer, EmployerRegisterSerializer, UserSerializer, \
    CandidateProfileSerializer, WorkExperienceSerializer, EducationSerializer, AppreciationSerializer, SkillSerializer
from django.utils import timezone
from .paginators import StandardResultsSetPagination


class UserView(viewsets.ViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        u = request.user
        if request.method.__eq__('PATCH'):
            serializer = serializers.UserSerializer(u, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializers.UserSerializer(u).data, status=status.HTTP_200_OK)


class CandidateMeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsCandidate]
    serializer_class = CandidateProfileSerializer

    def get_object(self):
        return self.request.user.candidate_profile

class SkillViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Skill.objects.all().order_by('name')
    serializer_class = SkillSerializer
    permission_classes = [IsCandidate]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    pagination_class = StandardResultsSetPagination

class BaseCandidateItemViewSet(viewsets.ViewSet, generics.CreateAPIView, generics.UpdateAPIView,
                               generics.DestroyAPIView):
    permission_classes = [IsCandidate]

    def get_queryset(self):
        return self.model.objects.filter(candidate=self.request.user.candidate_profile)

    def perform_create(self, serializer):
        serializer.save(candidate=self.request.user.candidate_profile)


class WorkExperienceViewSet(BaseCandidateItemViewSet):
    model = WorkExperience
    serializer_class = WorkExperienceSerializer


class EducationViewSet(BaseCandidateItemViewSet):
    model = Education
    serializer_class = EducationSerializer


class LanguageViewSet(BaseCandidateItemViewSet, generics.ListAPIView):
    model = Language
    serializer_class = LanguageSerializer


class AppreciationViewSet(BaseCandidateItemViewSet):
    model = Appreciation
    serializer_class = AppreciationSerializer


class EmployerMeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsEmployer]
    serializer_class = EmployerProfileSerializer

    def get_object(self):
        return self.request.user.employer_profile


class ResumeActionView(APIView):
    permission_classes = [IsCandidate]

    def delete(self, request):
        try:
            profile = request.user.candidate_profile
            profile.resume = None
            profile.resume_name = None
            profile.save()

            return Response({"message": "Resume deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class AdminEmployerViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAdminRole]
    queryset = EmployerProfile.objects.select_related("user").all()
    serializer_class = AdminEmployerSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        st = self.request.query_params.get("status")
        if st:
            qs = qs.filter(status=st)
        return qs

    @action(methods=["post"], detail=True)
    def approve(self, request, pk=None):
        emp = self.get_object()
        emp.status = VerificationStatus.APPROVED
        emp.reject_reason = ""
        emp.verified_at = timezone.now()
        emp.verified_by = request.user
        emp.save()
        return Response({"message": "Approved", "data": serializers.EmployerProfileSerializer(emp).data},
                        status=status.HTTP_200_OK)

    @action(methods=["post"], detail=True)
    def reject(self, request, pk=None):
        emp = self.get_object()
        emp.status = VerificationStatus.REJECTED
        emp.reject_reason = request.data.get("reason", "")
        emp.verified_at = timezone.now()
        emp.verified_by = request.user
        emp.save()
        return Response({"message": "Rejected"}, status=status.HTTP_200_OK)


class RegisterCandidateView(viewsets.ViewSet, generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = CandidateRegisterSerializer
    parser_classes = [parsers.MultiPartParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class RegisterEmployerView(viewsets.ViewSet, generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmployerRegisterSerializer
    parser_classes = [parsers.MultiPartParser]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            return Response(
                {
                    "message": "Đăng ký thành công. Vui lòng chờ Admin phê duyệt trước khi đăng tin.",
                    "user": UserSerializer(user).data
                },
                status=status.HTTP_201_CREATED
            )
        except TypeError as ex:
            return Response(
                {
                    "message": f"Không có trường {ex}",
                },
                status=status.HTTP_400_BAD_REQUEST
            )
