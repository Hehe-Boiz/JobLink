from rest_framework import viewsets, generics, mixins
from .models import Job
from .serializers import EmployerJobSerializer
from apps.users.permissions import IsEmployerApproved

class EmployerJobViewSet(viewsets.ModelViewSet):
    serializer_class = EmployerJobSerializer
    permission_classes = [IsEmployerApproved]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Job.objects.none()
        return Job.objects.filter(posted_by=user).select_related("category", "location")

    def perform_create(self, serializer):
        ep = self.request.user.employer_profile
        serializer.save(
            posted_by=self.request.user,
            company_name=ep.company_name,
        )
