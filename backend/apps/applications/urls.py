from django.urls import path, include
from rest_framework.routers import DefaultRouter
from ..applications.views import EmployerApplicationViewSet

router = DefaultRouter()
router.register("employer/application", EmployerApplicationViewSet, basename="employer-application")
urlpatterns = [
    path('', include(router.urls)),
]