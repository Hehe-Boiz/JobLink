from datetime import timedelta

from rest_framework import generics, status, viewsets, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from oauth2_provider.models import Application, AccessToken, RefreshToken
from oauthlib.common import generate_token
from .models import User, VerificationStatus, UserRole, CandidateProfile
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

class EmployerMeView(generics.RetrieveUpdateAPIView):
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


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Chưa nhận thấy token'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            GOOGLE_WEB_CLIENT_ID = "665244573266-77l5gm6jcvsimql5jntqc6g102geoh09.apps.googleusercontent.com"

            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_WEB_CLIENT_ID)

            email = idinfo['email']
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': UserRole.CANDIDATE,
                    'is_active': True
                }
            )

            if created:
                user.set_unusable_password()
                user.save()
                CandidateProfile.objects.create(user=user)

            app_oauth = Application.objects.first()
            if not app_oauth:
                return Response({'error': 'OAuth App chưa được cấu hình'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            expires = timezone.now() + timedelta(seconds=36000)
            access_token = AccessToken.objects.create(
                user=user, application=app_oauth, token=generate_token(),
                expires=expires, scope="read write"
            )
            refresh_token = RefreshToken.objects.create(
                user=user, application=app_oauth, token=generate_token(),
                access_token=access_token
            )
            return Response({
                'access_token': access_token.token,
                'refresh_token': refresh_token.token,
                'role': user.role,
                'token_type': 'Bearer',
            }, status=200)

        except ValueError as e:
            return Response({'error': 'Invalid Google Token', 'details': str(e)}, status=400)


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