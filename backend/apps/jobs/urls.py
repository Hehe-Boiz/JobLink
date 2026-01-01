from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewCandidate, EmployerJobViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewCandidate, basename='job-public')
router.register("employer/jobs", EmployerJobViewSet, basename="employer-jobs")
urlpatterns = [
    path('', include(router.urls)),
]