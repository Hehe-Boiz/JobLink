import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker

from apps.payments.models import ServicePack
# Import models
from apps.users.models import (
    User, UserRole, VerificationStatus, CandidateProfile,
    EmployerProfile, EducationStatus, Skill, Gender,
    WorkExperience, Education, Language
)
from apps.jobs.models import (
    JobCategory, Location, Job, Tag, EmploymentType, ExperienceLevel
)
from apps.applications.models import Application, ApplicationStatus


class Command(BaseCommand):
    help = "Tạo dữ liệu giả (Mock Data) chuẩn theo models.py mới"

    def __init__(self):
        super().__init__()
        self.fake = Faker(['vi_VN'])

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Đang khởi tạo dữ liệu giả...")

        # [White Box Explanation] Transaction.atomic:
        # Cơ chế này đảm bảo tính toàn vẹn dữ liệu (ACID).
        # Nếu bất kỳ dòng code nào bên trong block này bị lỗi,
        # toàn bộ dữ liệu đã tạo trước đó trong block sẽ bị rollback (hủy bỏ).
        # Giúp tránh tình trạng database bị "rác" do tạo dở dang.
        with transaction.atomic():
            self._clean_data()

            admin = self._create_admin()
            skills = self._create_skills()
            recruiters = self._create_employers(admin)
            candidates = self._create_candidates(skills)
            jobs = self._create_jobs(recruiters)
            self._create_applications(candidates, jobs)

        self.stdout.write(self.style.SUCCESS('✅ Đã tạo dữ liệu giả thành công!'))

    def _clean_data(self):
        """Xóa dữ liệu cũ để tránh trùng lặp khi chạy lại nhiều lần"""
        self.stdout.write("🗑️  Đang xóa dữ liệu cũ...")
        # Lưu ý: Xóa User sẽ cascade xóa Profile, Application, v.v.
        User.objects.exclude(is_superuser=True).delete()
        Job.objects.all().delete()
        Skill.objects.all().delete()
        Tag.objects.all().delete()

    def _create_admin(self):
        self.stdout.write("👤 Đang tạo Admin...")
        admin_email = 'admin@gmail.com'
        user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'username': 'admin',
                'password': 'password123',  # Nên dùng set_password ngoài đời thực, nhưng seed data thì tạm chấp nhận
                'first_name': 'Super',
                'last_name': 'Admin',
                'is_staff': True,
                'is_superuser': True,
                'role': UserRole.ADMIN
            }
        )
        if created:
            user.set_password('123456')
            user.save()
        return user

    def _create_skills(self):
        self.stdout.write("🛠️  Đang tạo Skills...")
        skill_names = [
            'Leadership', 'Teamwork', 'Communication', 'Problem Solving',
            'Critical Thinking', 'Time Management', 'Creativity', 'Adaptability',
            'Graphic Design', 'Graphic Thinking', 'UI/UX Design', 'Adobe Indesign',
            'Web Design', 'InDesign', 'Canva Design', 'User Interface Design',
            'Product Design', 'User Experience Design', 'Figma', 'Sketch',
            'JavaScript', 'React', 'React Native', 'Python', 'Java', 'Node.js',
            'Project Management', 'Agile', 'Scrum', 'Data Analysis',
            'Marketing', 'SEO', 'Content Writing', 'Public Speaking',
            'English', 'Vietnamese', 'Japanese', 'Chinese',
            'Responsibility', 'Target oriented', 'Consistent', 'Visioner',
            'Good communication skills', 'Negotiation', 'Decision Making',
        ]
        skills = []
        for name in skill_names:
            skill, _ = Skill.objects.get_or_create(name=name)
            skills.append(skill)
        return skills

    def _create_employers(self, admin_user):
        self.stdout.write("🏢 Đang tạo Nhà tuyển dụng...")
        created_recruiters = []

        for i in range(10):
            email = f"recruiter_{i}@company.com"
            user = User.objects.create_user(
                username=f"recruiter_{i}",
                email=email,
                password='123456',
                role=UserRole.EMPLOYER,
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                phone=self.fake.phone_number(),
                bio=self.fake.catch_phrase()
            )

            # Logic xác thực: 5 người đầu auto duyệt
            is_verified = i < 5
            status = VerificationStatus.APPROVED if is_verified else VerificationStatus.PENDING
            verified_at = timezone.now() if is_verified else None
            verified_by = admin_user if is_verified else None

            EmployerProfile.objects.create(
                user=user,
                company_name=self.fake.company(),
                tax_code=self.fake.unique.ean13(),
                website=self.fake.url(),
                description=self.fake.paragraph(nb_sentences=3),
                address=self.fake.address(),
                status=status,
                verified_at=verified_at,
                verified_by=verified_by
            )

            if is_verified:
                created_recruiters.append(user)

        return created_recruiters

    def _create_candidates(self, skills):
        self.stdout.write("👨‍🎓 Đang tạo Ứng viên & Profile chi tiết...")
        candidates = []

        for i in range(20):
            email = f"candidate_{i}@gmail.com"
            user = User.objects.create_user(
                username=f"candidate_{i}",
                email=email,
                password='123456',
                role=UserRole.CANDIDATE,
                first_name=self.fake.first_name(),
                last_name=self.fake.last_name(),
                phone=self.fake.phone_number()
            )

            # Tạo Candidate Profile
            profile = CandidateProfile.objects.create(
                user=user,
                gender=random.choice(Gender.choices)[0],  # [NEW] Random giới tính
                address=self.fake.address(),
                experience_years=random.randint(0, 10),
                dob=self.fake.date_of_birth(minimum_age=18, maximum_age=35),
                specialization=self.fake.job(),
                school_name="Đại học Công Nghệ Thông Tin",
                education_status=random.choice(EducationStatus.choices)[0]
            )

            # [NEW] Gán Skill (ManyToMany)
            # Random chọn 3-5 skill từ danh sách đã tạo
            random_skills = random.sample(skills, k=random.randint(3, 5))
            profile.skills.set(random_skills)

            # [NEW] Tạo dữ liệu phụ: Education & WorkExperience
            self._create_candidate_details(profile)

            candidates.append(profile)

        return candidates

    def _create_candidate_details(self, profile):
        """Hàm phụ để tạo kinh nghiệm làm việc và học vấn cho ứng viên"""

        # Tạo 1-2 Học vấn
        for _ in range(random.randint(1, 2)):
            Education.objects.create(
                candidate=profile,
                institution=self.fake.company(),  # Giả lập tên trường
                level="Đại học",
                field_of_study="Công nghệ thông tin",
                start_date=self.fake.date_between(start_date='-5y', end_date='-4y'),
                end_date=self.fake.date_between(start_date='-4y', end_date='-1y'),
                description=self.fake.sentence()
            )

        # Tạo 1-3 Kinh nghiệm làm việc (nếu có kinh nghiệm)
        if profile.experience_years > 0:
            for _ in range(random.randint(1, 3)):
                start = self.fake.date_between(start_date='-3y', end_date='-1y')
                WorkExperience.objects.create(
                    candidate=profile,
                    job_title=self.fake.job(),
                    company=self.fake.company(),
                    start_date=start,
                    end_date=start + timedelta(days=365),
                    description=self.fake.paragraph(nb_sentences=2)
                )

    def _create_service_packs(self):
        self.stdout.write("📦 Đang tạo Service Packs...")
        data_packs = [
            {"name": "Tin Cơ Bản (1 ngày)", "price": 20000, "duration_days": 1, "pack_type": "JOB_PUSH"},
            {"name": "Tin Nổi Bật (7 ngày)", "price": 500000, "duration_days": 7, "pack_type": "JOB_PUSH"},
            {"name": "Tin VIP (30 ngày)", "price": 1500000, "duration_days": 30, "pack_type": "JOB_PUSH"},
        ]
        for p in data_packs:
            ServicePack.objects.get_or_create(
                name=p["name"],
                defaults={"price": p["price"], "duration_days": p["duration_days"], "pack_type": p["pack_type"]}
            )

    def _create_jobs(self, recruiters):
        self.stdout.write("💼 Đang tạo Jobs (kèm views & featured)...")
        if not recruiters: return []

        categories = [JobCategory.objects.get_or_create(name=n)[0] for n in ["IT Phần mềm", "Marketing", "Sales"]]
        locations = [Location.objects.get_or_create(name=n)[0] for n in ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng"]]
        tags = [Tag.objects.get_or_create(name=n)[0] for n in ["Java", "Python", "React", "NodeJS"]]

        created_jobs = []
        for _ in range(50):
            recruiter = random.choice(recruiters)
            base_salary = random.randint(10, 50) * 1000000

            # [LOGIC MỚI] Random Featured: 20% cơ hội là tin nổi bật
            is_featured = random.choices([True, False], weights=[20, 80], k=1)[0]

            job = Job.objects.create(
                posted_by=recruiter.employer_profile,
                title=f"{self.fake.job()} ({random.choice(['Junior', 'Senior'])})",
                description=f"<p>{self.fake.paragraph()}</p>",
                requirements=f"<ul><li>{self.fake.sentence()}</li></ul>",
                benefits=f"<ul><li>Lương tháng 13</li></ul>",
                company_name=recruiter.employer_profile.company_name,
                category=random.choice(categories),
                location=random.choice(locations),
                address=recruiter.employer_profile.address,
                employment_type=random.choice(EmploymentType.choices)[0],
                experience_level=random.choice(ExperienceLevel.choices)[0],
                salary_min=base_salary,
                salary_max=base_salary + 5000000,
                deadline=timezone.now().date() + timedelta(days=30),

                # Random views và featured trực tiếp tại đây
                views=random.randint(10, 5000),
                is_featured=is_featured
            )
            job.tags.set(random.sample(tags, k=2))
            created_jobs.append(job)

        return created_jobs

    def _create_applications(self, candidates, jobs):
        self.stdout.write("📄 Đang tạo Applications...")
        if not candidates or not jobs:
            return

        for candidate in candidates:
            # Mỗi ứng viên nộp bừa 3-5 job
            random_jobs = random.sample(jobs, k=random.randint(3, 5))
            for job in random_jobs:
                Application.objects.create(
                    candidate=candidate,
                    job=job,
                    status=random.choice(ApplicationStatus.choices)[0],
                    cover_letter=self.fake.paragraph(),
                    employer_note=self.fake.sentence() if random.random() > 0.7 else ""
                )