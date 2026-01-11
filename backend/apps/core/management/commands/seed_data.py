import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from faker import Faker
from datetime import timedelta

# Import Models
# Đảm bảo đường dẫn import đúng với cấu trúc dự án của bạn
from apps.users.models import User, UserRole, VerificationStatus, CandidateProfile, EmployerProfile, EducationStatus
from apps.jobs.models import JobCategory, Location, Job, Tag, EmploymentType, ExperienceLevel
from apps.applications.models import Application, ApplicationStatus


class Command(BaseCommand):
    help = "Tạo dữ liệu giả: Job (có views), EmployerProfile, Application (CandidateProfile)"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Đang khởi tạo dữ liệu giả...")
        fake = Faker(['vi_VN'])

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

            # Lấy instance admin để làm người duyệt hồ sơ
            admin_user = User.objects.get(email=admin_email)

            # ==========================================
            # 2. TẠO NHÀ TUYỂN DỤNG (EMPLOYER + PROFILE)
            # ==========================================
            self.stdout.write("- Đang tạo Nhà tuyển dụng...")
            recruiters = []  # Danh sách User recruiter

            for i in range(10):
                email = f"recruiter_{i}@company.com"
                if not User.objects.filter(email=email).exists():
                    user = User.objects.create_user(
                        username=f"recruiter_{i}",
                        email=email,
                        password='123456',
                        role=UserRole.EMPLOYER,
                        first_name=fake.first_name(),
                        last_name=fake.last_name(),
                        phone=fake.phone_number()
                    )

                    # Random trạng thái
                    status = random.choice(VerificationStatus.choices)[0]
                    # Nếu Approved thì phải có người duyệt + ngày duyệt
                    verified_at = timezone.now() if status == VerificationStatus.APPROVED else None
                    verified_by = admin_user if status == VerificationStatus.APPROVED else None

                    EmployerProfile.objects.create(
                        user=user,
                        company_name=fake.company(),
                        tax_code=fake.unique.ean13(),
                        website=fake.url(),
                        status=status,
                        verified_at=verified_at,
                        verified_by=verified_by
                    )

                    if status == VerificationStatus.APPROVED:
                        recruiters.append(user)
                else:
                    # Nếu user đã có, kiểm tra xem có được duyệt không để add vào list
                    u = User.objects.get(email=email)
                    if hasattr(u, 'employer_profile') and u.employer_profile.status == VerificationStatus.APPROVED:
                        recruiters.append(u)

            # ==========================================
            # 3. TẠO ỨNG VIÊN (CANDIDATE + PROFILE)
            # ==========================================
            self.stdout.write("- Đang tạo Ứng viên...")
            candidates_profiles = []  # Lưu list CandidateProfile để dùng tạo Application

            for i in range(20):
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

                    # Dữ liệu ngẫu nhiên
                    specializations = ["React Native", "Python Backend", "Digital Marketing", "Business Analyst"]
                    schools = ["Đại học Bách Khoa", "Đại học CNTT", "RMIT", "FPT University"]

                    profile = CandidateProfile.objects.create(
                        user=user,
                        address=fake.address(),
                        experience_years=random.randint(0, 10),
                        dob=fake.date_of_birth(minimum_age=18, maximum_age=40),
                        specialization=random.choice(specializations),
                        school_name=random.choice(schools),
                        education_status="GRADUATED"
                    )
                    candidates_profiles.append(profile)
                else:
                    u = User.objects.get(email=email)
                    if hasattr(u, 'candidate_profile'):
                        candidates_profiles.append(u.candidate_profile)

            # ==========================================
            # 4. TẠO JOBS (Job -> EmployerProfile)
            # ==========================================
            self.stdout.write("- Đang tạo Job Categories & Locations...")

            categories = [JobCategory.objects.get_or_create(name=n)[0] for n in
                          ["IT Phần mềm", "Marketing", "Sales", "Kế toán"]]
            locations = [Location.objects.get_or_create(name=n)[0] for n in ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng"]]
            tags = [Tag.objects.get_or_create(name=n)[0] for n in ["Python", "Java", "React", "English"]]

            self.stdout.write(f"- Đang tạo Jobs cho {len(recruiters)} nhà tuyển dụng...")

            # Xóa hết Job cũ để tránh rác
            Job.objects.all().delete()

            all_created_jobs = []

            for _ in range(50):
                if not recruiters: break

                # Lấy ngẫu nhiên user recruiter, sau đó lấy profile
                recruiter_user = random.choice(recruiters)
                employer_profile = recruiter_user.employer_profile

                base_salary = random.randint(5, 50) * 1000000

                # --- [NEW] Tạo số view ảo ---
                random_views = random.randint(50, 5000)

                job = Job.objects.create(
                    posted_by=employer_profile,  # <--- SỬA: Trỏ vào EmployerProfile

                    title=f"{fake.job()} ({random.choice(['Senior', 'Junior', 'Fresher'])})",
                    company_name=employer_profile.company_name,
                    category=random.choice(categories),
                    location=random.choice(locations),

                    salary_min=base_salary,
                    salary_max=base_salary + 5000000,
                    deadline=timezone.now().date() + timedelta(days=random.randint(5, 60)),

                    description=f"<p>{fake.paragraph(nb_sentences=5)}</p>",
                    requirements=f"<ul><li>{fake.sentence()}</li></ul>",
                    benefits=f"<ul><li>Lương tháng 13</li></ul>",

                    views=random_views  # <--- SỬA: Thêm Views
                )
                job.tags.set(random.sample(tags, k=2))
                all_created_jobs.append(job)

            # ==========================================
            # 5. TẠO APPLICATIONS (App -> CandidateProfile)
            # ==========================================
            if not all_created_jobs or not candidates_profiles:
                self.stdout.write(self.style.WARNING("⚠️ Thiếu Job hoặc Candidate để tạo Application."))
                return

            self.stdout.write("- Đang tạo Hồ sơ ứng tuyển (Applications)...")
            Application.objects.all().delete()

            app_count = 0

            for profile in candidates_profiles:
                # Logic: Nếu Job ít thì lấy hết, nhiều thì random 3-8 cái
                k = random.randint(3, 8)
                if k > len(all_created_jobs):
                    k = len(all_created_jobs)

                random_jobs = random.sample(all_created_jobs, k=k)

                for job in random_jobs:
                    status = random.choice(ApplicationStatus.choices)[0]
                    rating = None
                    employer_note = ""

                    if status != ApplicationStatus.SUBMITTED:
                        rating = random.randint(1, 5) if random.random() > 0.3 else None
                        employer_note = fake.sentence() if random.random() > 0.5 else ""

                    Application.objects.create(
                        candidate=profile,  # <--- SỬA: Trỏ vào CandidateProfile
                        job=job,
                        status=status,
                        cover_letter=f"Kính gửi {job.company_name},\n\nTôi rất thích vị trí {job.title}. {fake.paragraph()}",
                        employer_note=employer_note,
                        rating=rating
                    )
                    app_count += 1

            self.stdout.write(
                self.style.SUCCESS(f'✅ Đã tạo dữ liệu thành công! (Jobs: {len(all_created_jobs)}, Apps: {app_count})'))