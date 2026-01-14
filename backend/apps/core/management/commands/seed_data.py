import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker
from datetime import timedelta

# Import models
from apps.users.models import User, UserRole, VerificationStatus, CandidateProfile, EmployerProfile, EducationStatus
from apps.jobs.models import JobCategory, Location, Job, Tag, EmploymentType, ExperienceLevel
from apps.applications.models import Application, ApplicationStatus


class Command(BaseCommand):
    help = "Tạo dữ liệu giả (Mock Data) chuẩn theo models.py mới"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Đang khởi tạo dữ liệu giả...")
        fake = Faker(['vi_VN'])

        # Dùng transaction để đảm bảo tạo dữ liệu nhanh và an toàn
        with transaction.atomic():
            # ==========================================
            # 1. TẠO ADMIN
            # ==========================================
            self.stdout.write("- Đang tạo Admin...")
            admin_email = 'admin@gmail.com'
            if not User.objects.filter(email=admin_email).exists():
                User.objects.create_superuser(
                    username='admin',
                    email=admin_email,
                    password='123456',
                    first_name='Super',
                    last_name='Admin'
                )
            admin_user = User.objects.get(email=admin_email)

            # ==========================================
            # 2. TẠO NHÀ TUYỂN DỤNG (EMPLOYER + PROFILE)
            # ==========================================
            self.stdout.write("- Đang tạo Nhà tuyển dụng...")

            for i in range(10):  # Tạo 10 nhà tuyển dụng
                email = f"recruiter_{i}@company.com"

                # Check user tồn tại chưa
                if not User.objects.filter(email=email).exists():
                    # Tạo User
                    user = User.objects.create_user(
                        username=f"recruiter_{i}",
                        email=email,
                        password='123456',
                        role=UserRole.EMPLOYER,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        phone=fake.phone_number(),
                        bio=fake.catch_phrase()
                    )

                    # [FIX] Force 5 ông đầu tiên luôn APPROVED để chắc chắn có job
                    if i < 5:
                        status = VerificationStatus.APPROVED
                    else:
                        status = random.choice(VerificationStatus.choices)[0]

                    verified_at = timezone.now() if status == VerificationStatus.APPROVED else None
                    verified_by = admin_user if status == VerificationStatus.APPROVED else None

                    # Tạo EmployerProfile
                    EmployerProfile.objects.create(
                        user=user,
                        company_name=fake.company(),
                        tax_code=fake.unique.ean13(),
                        website=fake.url(),
                        description=fake.paragraph(nb_sentences=3),
                        address=fake.address(),
                        status=status,
                        verified_at=verified_at,
                        verified_by=verified_by,
                        reject_reason="Thiếu giấy phép kinh doanh" if status == VerificationStatus.REJECTED else ""
                    )

            # [QUAN TRỌNG] Lấy lại danh sách từ DB để bao gồm cả user cũ và mới
            recruiters = User.objects.filter(role=UserRole.EMPLOYER,
                                             employer_profile__status=VerificationStatus.APPROVED)

            # ==========================================
            # 3. TẠO ỨNG VIÊN (CANDIDATE + PROFILE)
            # ==========================================
            self.stdout.write("- Đang tạo Ứng viên...")
            for i in range(20):  # Tạo 20 ứng viên
                email = f"candidate_{i}@gmail.com"
                if not User.objects.filter(email=email).exists():
                    user = User.objects.create_user(
                        username=f"candidate_{i}",
                        email=email,
                        password='123456',
                        role=UserRole.CANDIDATE,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        phone=fake.phone_number()
                    )
                    dob = fake.date_of_birth(minimum_age=18, maximum_age=40)

                    specializations = ["React Native Dev", "Python Backend", "Digital Marketing", "Business Analyst",
                                       "Tester", "Designer"]
                    schools = ["Đại học Bách Khoa", "Đại học CNTT", "Đại học Kinh Tế", "FPT University",
                               "Đại học Mở TPHCM"]

                    CandidateProfile.objects.create(
                        user=user,
                        address=fake.address(),
                        experience_years=random.randint(0, 10),
                        dob=dob,
                        specialization=random.choice(specializations),
                        school_name=random.choice(schools),
                        education_status=random.choice(EducationStatus.choices)[0]
                    )

            # ==========================================
            # 4. TẠO JOBS
            # ==========================================
            self.stdout.write("- Đang tạo Job Categories & Locations...")

            categories = [JobCategory.objects.get_or_create(name=n)[0] for n in
                          ["IT Phần mềm", "Marketing", "Sales", "Kế toán", "Design"]]
            locations = [Location.objects.get_or_create(name=n)[0] for n in
                         ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Cần Thơ"]]
            tags = [Tag.objects.get_or_create(name=n)[0] for n in
                    ["Python", "Java", "React", "English", "Fullstack", "NodeJS"]]

            self.stdout.write(f"- Đang tạo Jobs cho {recruiters.count()} nhà tuyển dụng được duyệt...")

            # Xóa job cũ
            Job.objects.all().delete()

            if recruiters.exists():
                for _ in range(50):
                    recruiter = random.choice(recruiters)
                    employer_profile = recruiter.employer_profile

                    base_salary = random.randint(5, 50) * 1000000

                    job = Job.objects.create(
                        posted_by=recruiter,
                        title=f"{fake.job()} ({random.choice(['Senior', 'Junior', 'Fresher', 'Intern'])})",
                        description=f"<p>{fake.paragraph(nb_sentences=3)}</p><p><strong>Mô tả chi tiết:</strong></p><ul><li>{fake.sentence()}</li><li>{fake.sentence()}</li></ul>",
                        requirements=f"<ul><li>{fake.sentence()}</li><li>Kinh nghiệm {random.randint(1, 5)} năm</li></ul>",
                        benefits=f"<ul><li>Lương tháng 13</li><li>Bảo hiểm đầy đủ</li><li>Du lịch hàng năm</li></ul>",

                        company_name=employer_profile.company_name,
                        category=random.choice(categories),
                        location=random.choice(locations),
                        address=employer_profile.address,
                        employment_type=random.choice(EmploymentType.choices)[0],
                        experience_level=random.choice(ExperienceLevel.choices)[0],
                        salary_min=base_salary,
                        salary_max=base_salary + 5000000,
                        deadline=timezone.now().date() + timedelta(days=random.randint(5, 60))
                    )
                    job.tags.set(random.sample(tags, k=random.randint(2, 4)))
            else:
                self.stdout.write(self.style.WARNING("⚠️ Vẫn không tìm thấy nhà tuyển dụng nào được duyệt!"))

            # ==========================================
            # 5. TẠO APPLICATIONS
            # ==========================================
            all_jobs = Job.objects.all()
            candidates = User.objects.filter(role=UserRole.CANDIDATE)

            if not all_jobs.exists() or not candidates.exists():
                self.stdout.write(self.style.WARNING("⚠️ Cần có Job và Candidate để tạo Application."))
                return

            self.stdout.write("- Đang tạo Hồ sơ ứng tuyển (Applications)...")
            Application.objects.all().delete()

            app_count = 0
            for candidate in candidates:
                # Random 3-8 jobs để nộp
                random_jobs = random.sample(list(all_jobs), k=min(len(all_jobs), random.randint(3, 8)))

                for job in random_jobs:
                    status = random.choice(ApplicationStatus.choices)[0]
                    rating = None
                    employer_note = ""

                    if status != ApplicationStatus.SUBMITTED:
                        rating = random.randint(1, 5) if random.random() > 0.3 else None
                        employer_note = fake.sentence() if random.random() > 0.5 else ""

                    cover_letter = f"Kính gửi {job.company_name},\n\nTôi tên là {candidate.full_name}. Tôi rất quan tâm đến vị trí {job.title}...\n\nTrân trọng."

                    Application.objects.create(
                        user=candidate,
                        job=job,
                        status=status,
                        cover_letter=cover_letter,
                        employer_note=employer_note,
                        rating=rating,
                    )
                    app_count += 1

            self.stdout.write(f"- Đã tạo {app_count} hồ sơ ứng tuyển.")

        self.stdout.write(self.style.SUCCESS('✅ Đã tạo dữ liệu giả thành công!'))