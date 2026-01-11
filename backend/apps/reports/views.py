# backend/joblink/views.py

from django.db.models import Count, Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.jobs.models import Job, JobCategory
from apps.applications.models import Application
from apps.users.permissions import IsEmployerApproved
import random


class EmployerStatsView(APIView):
    permission_classes = [IsEmployerApproved]

    def get(self, request):
        ep = request.user.employer_profile
        current_year = timezone.now().year

        # 1. LẤY THAM SỐ TỪ CLIENT
        # period: 'year' (xem các năm), 'quarter' (xem 4 quý), 'month' (xem 12 tháng)
        period = request.query_params.get('period', 'month')
        # category_id: Lọc theo ngành
        category_id = request.query_params.get('category_id', 'all')
        # selected_year: Năm cần xem (dùng cho lọc quý và tháng)
        selected_year = int(request.query_params.get('year', current_year))

        # 2. LỌC JOB THEO USER & CATEGORY
        jobs_query = Job.objects.filter(posted_by=ep)
        if category_id and category_id != 'all':
            jobs_query = jobs_query.filter(category_id=category_id)

        job_ids = jobs_query.values_list('id', flat=True)

        # 3. HÀM TÍNH TOÁN %
        def get_efficiency(app_count):
            # Giả lập View (Thực tế bạn thay bằng query ViewLog)
            # Logic: View gấp 10-20 lần App.
            if app_count == 0:
                view_count = random.randint(10, 50)  # Vẫn có view dù ko có app
                return 0.0

            view_count = int(app_count * random.uniform(8, 15) + random.randint(5, 20))
            return round((app_count / view_count) * 100, 1)

        labels = []
        data_points = []

        if period == 'year':
            years_range = range(current_year - 2, current_year + 3)

            for y in years_range:
                labels.append(str(y))

                # Đếm App trong năm y
                app_count = Application.objects.filter(
                    job_id__in=job_ids,
                    created_date__year=y
                ).count()

                data_points.append(get_efficiency(app_count))

        elif period == 'quarter':
            quarters = [
                (1, 3, "Quý 1"),
                (4, 6, "Quý 2"),
                (7, 9, "Quý 3"),
                (10, 12, "Quý 4"),
            ]

            for start_m, end_m, label in quarters:
                labels.append(label)

                app_count = Application.objects.filter(
                    job_id__in=job_ids,
                    created_date__year=selected_year,
                    created_date__month__gte=start_m,
                    created_date__month__lte=end_m
                ).count()

                data_points.append(get_efficiency(app_count))

        else:
            # --- LỌC THEO THÁNG (T1 -> T12 của selected_year) ---
            for m in range(1, 13):
                labels.append(f"T{m}")

                app_count = Application.objects.filter(
                    job_id__in=job_ids,
                    created_date__year=selected_year,
                    created_date__month=m
                ).count()

                data_points.append(get_efficiency(app_count))

        # 5. Lấy danh sách Category
        categories = JobCategory.objects.values('id', 'name')

        return Response({
            "chart_data": {
                "labels": labels,
                "data": data_points
            },
            "categories": list(categories),
            "selected_year": selected_year
        })