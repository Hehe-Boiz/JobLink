from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.jobs.views import EmployerJobViewSet

router = DefaultRouter()
router.register("employer/jobs", EmployerJobViewSet, basename="employer-jobs")
urlpatterns = [
    path('', include(router.urls)),
]