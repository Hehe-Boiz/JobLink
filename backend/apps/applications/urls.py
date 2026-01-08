from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..applications.views import EmployerApplicationViewSet, CandidateApplicationViewSet

router = DefaultRouter()
router.register("employer/applications", EmployerApplicationViewSet, basename="employer-application")
router.register("candidate/applications", CandidateApplicationViewSet, basename="candidate-application")
urlpatterns = [
    path('', include(router.urls)),
]