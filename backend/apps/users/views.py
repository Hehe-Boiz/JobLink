from rest_framework import generics, status, viewsets, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import User

from . import serializers
from .serializers import CandidateRegisterSerializer, EmployerRegisterSerializer, UserSerializer


class UserView(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer
    parser_classes = [parsers.MultiPartParser]

    @action(methods=['get', 'patch'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        u = request.user
        if request.method.__eq__('PATCH'):
            for k, v in request.data.items():
                if k in ['first_name', 'last_name', 'email']:
                    setattr(u, k, v)
            u.save()
        return Response(serializers.UserSerializer(u).data, status=status.HTTP_200_OK)


class RegisterCandidateView(generics.CreateAPIView):
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


class RegisterEmployerView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmployerRegisterSerializer
    parser_classes = [parsers.MultiPartParser]
    def create(self, request, *args, **kwargs):
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