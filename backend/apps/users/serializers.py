from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from .models import UserRole, CandidateProfile, EmployerProfile
from ..core.serializers import MediaURLSerializer

User = get_user_model()


class UserSerializer(MediaURLSerializer):
    class Meta:
        model = User
        # bạn có thể bỏ bớt field nếu muốn ngắn hơn
        fields = [
            # "id",
            "username",
            "email",
            "password",
            "role",
            "first_name",
            "last_name",
            "bio",
            "created_date",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "required": False},
            # role không cho đổi lung tung qua API user update (đổi role do admin)
            "role": {"read_only": True},
            "created_date": {"read_only": True},
        }

    def validate_email(self, value):
        qs = User.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        u = User(**validated_data)
        if password:
            u.set_password(password)
        u.save()
        return u

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if password:
            instance.set_password(password)

        instance.save()
        return instance


class CandidateProfileSerializer(MediaURLSerializer):
    media_fields = ["avatar"]
    user = UserSerializer(read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ["user", "full_name", "phone", "address", "avatar"]


class EmployerProfileSerializer(MediaURLSerializer):
    media_fields = ["logo"]

    class Meta:
        model = EmployerProfile
        fields = [
            "user",
            "company_name",
            "tax_code",
            "website",
            "logo",
            "is_verified",
            "verified_at",
            "verified_by",
        ]
        extra_kwargs = {
            "user": {"read_only": True},
            "is_verified": {"read_only": True},
            "verified_at": {"read_only": True},
            "verified_by": {"read_only": True},
        }


class AdminEmployerSerializer(EmployerProfileSerializer):
    # thêm thông tin user đầy đủ để admin xem nhanh
    user_detail = UserSerializer(source="user", read_only=True)
    verified_by_detail = UserSerializer(source="verified_by", read_only=True)

    class Meta(EmployerProfileSerializer.Meta):
        fields = EmployerProfileSerializer.Meta.fields + [
            "user_detail",
            "verified_by_detail",
        ]
        read_only_fields = fields


class BaseRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


# --- 1. Candidate Register ---
class CandidateRegisterSerializer(BaseRegisterSerializer):
    full_name = serializers.CharField(required=True)
    phone = serializers.CharField(required=True)
    address = serializers.CharField(required=False, allow_blank=True)
    avatar = serializers.ImageField(required=True)

    @transaction.atomic
    def create(self, validated_data):
        # Tách data
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        # Profile data
        full_name = validated_data.pop("full_name")
        phone = validated_data.pop("phone")
        address = validated_data.pop("address", "")
        avatar = validated_data.pop("avatar")

        # User basic data (first_name, last_name...)
        user_data = validated_data

        # Tạo User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=UserRole.CANDIDATE,
            avatar=avatar,
            **user_data
        )

        # Tạo Profile
        CandidateProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            address=address
        )
        return user


# --- 2. Employer Register ---
class EmployerRegisterSerializer(BaseRegisterSerializer):
    company_name = serializers.CharField(required=True)
    tax_code = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=True)  # Bắt buộc logo

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")

        # Profile data
        company_name = validated_data.pop("company_name")
        tax_code = validated_data.pop("tax_code", None)
        website = validated_data.pop("website", None)
        logo = validated_data.pop("logo")
        user_data = validated_data

        # Tạo User
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=UserRole.EMPLOYER,
            **user_data
        )

        # Tạo Profile
        EmployerProfile.objects.create(
            user=user,
            company_name=company_name,
            tax_code=tax_code,
            website=website,
            logo=logo,
        )
        return user
