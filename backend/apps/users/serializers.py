from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from .models import UserRole, CandidateProfile, EmployerProfile, Language, Skill, WorkExperience, Education, \
    Appreciation
from ..core.serializers import MediaURLSerializer

User = get_user_model()


class UserSerializer(MediaURLSerializer):
    media_fields = ["avatar"]

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
            "full_name",
            "bio",
            "created_date",
            "phone",
            "avatar",
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


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        exclude = ['candidate']


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        exclude = ['candidate']


class AppreciationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appreciation
        exclude = ['candidate']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        exclude = ['candidate']


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']


class CandidateProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    skills = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False
    )
    skill_list = SkillSerializer(source='skills', many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    appreciations = AppreciationSerializer(many=True, read_only=True)
    bio = serializers.CharField(source='user.bio', required=False, allow_blank=True)

    class Meta:
        model = CandidateProfile
        fields = ['user', 'address', 'dob', 'specialization', 'education_status', 'school_name', 'skills', 'skill_list',
                  'work_experiences', 'educations', 'languages', 'appreciations', 'bio', 'resume', 'resume_name', 'gender']
        read_only_fields = ['resume_name']

    def update(self, instance, validated_data):
        skills_data = validated_data.pop('skills', None)
        bio_data = validated_data.pop('user', {}).get('bio')

        if 'resume' in validated_data:
            uploaded_file = validated_data['resume']
            if uploaded_file:
                instance.resume_name = uploaded_file.name

        instance = super().update(instance, validated_data)

        if skills_data is not None:
            instance.skills.clear()
            for skill_name in skills_data:
                skill_obj, created = Skill.objects.get_or_create(name=skill_name.strip())
                instance.skills.add(skill_obj)

        if bio_data is not None:
            instance.user.bio = bio_data
            instance.user.save()

        return instance

    def validate_resume(self, value):
        if value:
            limit_mb = 5
            if value.size > limit_mb * 1024 * 1024:
                raise serializers.ValidationError(f"File too large. Max size is {limit_mb}MB.")

            if value.content_type != 'application/pdf':
                if not value.name.lower().endswith('.pdf'):
                    raise serializers.ValidationError("Only PDF files are allowed.")

        return value


class EmployerProfileSerializer(MediaURLSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = EmployerProfile
        fields = [
            "user",
            "company_name",
            "tax_code",
            "website",
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
    phone = serializers.CharField(required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


class CandidateRegisterSerializer(BaseRegisterSerializer):
    @transaction.atomic
    def create(self, validated_data):

        password = validated_data.pop("password")
        email = validated_data.pop("email")
        user_data = validated_data

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=UserRole.CANDIDATE,
            **user_data
        )

        # Tạo Profile
        CandidateProfile.objects.create(
            user=user,
        )
        return user



class EmployerRegisterSerializer(BaseRegisterSerializer):
    company_name = serializers.CharField(required=True)
    tax_code = serializers.CharField(required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop("password")
        email = validated_data.pop("email")
        company_name = validated_data.pop("company_name")
        tax_code = validated_data.pop("tax_code", None)
        website = validated_data.pop("website", None)
        user_data = validated_data
        print(user_data)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            role=UserRole.EMPLOYER,
            **user_data
        )

        EmployerProfile.objects.create(
            user=user,
            company_name=company_name,
            tax_code=tax_code,
            website=website,
        )
        return user
