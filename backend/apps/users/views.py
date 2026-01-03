from rest_framework import generics, status, viewsets, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User, VerificationStatus
from .models import EmployerProfile
from .permissions import IsAdminRole, IsCandidate, IsEmployer
from .serializers import EmployerProfileSerializer, AdminEmployerSerializer
from . import serializers
from .serializers import CandidateRegisterSerializer, EmployerRegisterSerializer, UserSerializer, CandidateProfileSerializer
from django.utils import timezone


class UserView(viewsets.ViewSet):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
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

class EmployerMeView(viewsets.ViewSet,generics.RetrieveUpdateAPIView):
    permission_classes = [IsEmployer]
    serializer_class = EmployerProfileSerializer

    def get_object(self):
        return self.request.user.employer_profile


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
        return Response({"message": "Approved", "data": serializers.EmployerProfileSerializer(emp).data}, status=status.HTTP_200_OK)

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