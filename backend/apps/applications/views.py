from rest_framework import viewsets
from .models import Application
from .serializers import EmployerApplicationSerializer
from apps.users.permissions import IsEmployerApproved


class EmployerApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = EmployerApplicationSerializer
    permission_classes = [IsEmployerApproved]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Application.objects.none()
        qs = Application.objects.filter(job__posted_by=user).select_related("job", "user")
        job_id = self.request.query_params.get("job_id")
        st = self.request.query_params.get("status")
        if job_id:
            qs = qs.filter(job_id=job_id)
        if st:
            qs = qs.filter(status=st)
        return qs
