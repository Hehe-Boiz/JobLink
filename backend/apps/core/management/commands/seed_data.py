import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker
from datetime import timedelta

# Import models của bạn
# Giả sử app tên là 'users' (chứa User) và 'jobs' (chứa Job)
# Bạn hãy đổi tên app 'users', 'jobs' cho đúng với project của bạn
from apps.users.models import User, UserRole, VerificationStatus, CandidateProfile, EmployerProfile
from apps.jobs.models import JobCategory, Location, Job, Tag, EmploymentType, ExperienceLevel
from apps.applications.models import Application, ApplicationStatus


class Command(BaseCommand):
    help = "Tạo dữ liệu giả (Mock Data) chuẩn theo models.py mới"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Đang khởi tạo dữ liệu giả...")
        fake = Faker(['vi_VN'])

        # Dùng transaction để đảm bảo tạo dữ liệu nhanh và an toàn (nếu lỗi thì rollback hết)
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
            recruiters = []

            for i in range(10):  # Tạo 10 nhà tuyển dụng
                email = f"recruiter_{i}@company.com"
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

                    # Random trạng thái xác minh
                    status = random.choice(VerificationStatus.choices)[0]
                    verified_at = timezone.now() if status == VerificationStatus.APPROVED else None
                    verified_by = admin_user if status == VerificationStatus.APPROVED else None

                    # Tạo EmployerProfile
                    EmployerProfile.objects.create(
                        user=user,
                        company_name=fake.company(),
                        tax_code=fake.unique.ean13(),  # Mã số thuế giả (unique)
                        website=fake.url(),
                        status=status,
                        verified_at=verified_at,
                        verified_by=verified_by,
                        reject_reason="Thiếu giấy phép kinh doanh" if status == VerificationStatus.REJECTED else ""
                    )

                    # Chỉ lấy những người ĐÃ DUYỆT để đăng tin tuyển dụng
                    if status == VerificationStatus.APPROVED:
                        recruiters.append(user)

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

                    # Random chuyên môn
                    specializations = ["React Native Dev", "Python Backend", "Digital Marketing", "Business Analyst",
                                       "Tester", "Designer"]
                    schools = ["Đại học Bách Khoa", "Đại học CNTT", "Đại học Kinh Tế", "FPT University", "Đại học Mở TPHCM"]
                    # Tạo CandidateProfile
                    CandidateProfile.objects.create(
                        user=user,
                        address=fake.address(),
                        experience_years=random.randint(0, 10),
                        dob = dob,
                        specialization = random.choice(specializations),
                        school_name=random.choice(schools)
                    )

            # ==========================================
            # 4. TẠO JOBS (Dành cho Employer đã duyệt)
            # ==========================================
            self.stdout.write("- Đang tạo Job Categories & Locations...")

            # Master Data
            categories = [JobCategory.objects.get_or_create(name=n)[0] for n in
                          ["IT Phần mềm", "Marketing", "Sales", "Kế toán"]]
            locations = [Location.objects.get_or_create(name=n)[0] for n in ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng"]]
            tags = [Tag.objects.get_or_create(name=n)[0] for n in ["Python", "Java", "React", "English"]]

            self.stdout.write(f"- Đang tạo Jobs cho {len(recruiters)} nhà tuyển dụng được duyệt...")

            # Xóa job cũ để tránh rác
            Job.objects.all().delete()

            for _ in range(50):  # 50 Job để test phân trang
                if not recruiters: break  # Nếu không có recruiter nào được duyệt thì thôi

                recruiter = random.choice(recruiters)
                employer_profile = recruiter.employer_profile  # Truy cập ngược qua OneToOne

                base_salary = random.randint(5, 50) * 1000000

                job = Job.objects.create(
                    posted_by=recruiter,
                    title=f"{fake.job()} ({random.choice(['Senior', 'Junior', 'Fresher'])})",
                    description=f"<p>{fake.paragraph(nb_sentences=5)}</p>",
                    requirements=f"<ul><li>{fake.sentence()}</li></ul>",
                    benefits=f"<ul><li>Lương tháng 13</li></ul>",

                    # Lấy thông tin công ty từ EmployerProfile
                    company_name=employer_profile.company_name,

                    category=random.choice(categories),
                    location=random.choice(locations),
                    address=fake.address(),
                    employment_type=random.choice(EmploymentType.choices)[0],
                    experience_level=random.choice(ExperienceLevel.choices)[0],
                    salary_min=base_salary,
                    salary_max=base_salary + 5000000,
                    deadline=timezone.now().date() + timedelta(days=random.randint(5, 60))
                )
                job.tags.set(random.sample(tags, k=2))

            recruiters = User.objects.filter(role=UserRole.EMPLOYER,
                                             employer_profile__status=VerificationStatus.APPROVED)
            candidates = User.objects.filter(role=UserRole.CANDIDATE)
            all_jobs = Job.objects.all()

            if not all_jobs.exists() or not candidates.exists():
                self.stdout.write(self.style.WARNING(
                    "⚠️ Cần có Job và Candidate để tạo Application. Hãy chạy seed User/Job trước."))
                return
            self.stdout.write("- Đang tạo Hồ sơ ứng tuyển (Applications)...")

            # Xóa dữ liệu cũ để tránh lỗi Unique Constraint khi chạy lại
            Application.objects.all().delete()

            app_count = 0

            for candidate in candidates:
                # Mỗi ứng viên nộp bừa 3 đến 8 công việc
                random_jobs = random.sample(list(all_jobs), k=random.randint(3, 8))

                for job in random_jobs:
                    # Random trạng thái hồ sơ
                    status = random.choice(ApplicationStatus.choices)[0]

                    # Logic dữ liệu hợp lý:
                    # - Nếu mới nộp (SUBMITTED) -> Chưa có đánh giá, chưa có note
                    # - Nếu đã xem/phỏng vấn -> Có thể có đánh giá và note
                    rating = None
                    employer_note = ""

                    if status != ApplicationStatus.SUBMITTED:
                        rating = random.randint(1, 5) if random.random() > 0.3 else None  # 70% cơ hội có rating
                        employer_note = fake.sentence() if random.random() > 0.5 else ""

                    # Tạo Cover Letter giả
                    cover_letter = f"Kính gửi {job.company_name},\n\nTôi rất thích vị trí {job.title}. {fake.paragraph()} \n\nTrân trọng."

                    Application.objects.create(
                        user=candidate,
                        job=job,
                        status=status,
                        cover_letter=cover_letter,
                        employer_note=employer_note,
                        rating=rating,
                        # cv=None # CloudinaryField khó fake file thật, để null hoặc string url giả nếu model cho phép
                    )
                    app_count += 1

            self.stdout.write(f"- Đã tạo {app_count} hồ sơ ứng tuyển.")

        self.stdout.write(self.style.SUCCESS('✅ Đã tạo dữ liệu thành công!'))