from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewCandidate, EmployerJobViewSet, BookmarkJobViewSet, JobCategoryViewSet, LocationViewSet

router = DefaultRouter()
router.register(r'jobs', JobViewCandidate, basename='job-public')
router.register("employer/jobs", EmployerJobViewSet, basename="employer-jobs")
router.register('bookmarks', BookmarkJobViewSet, basename='job-bookmark')
router.register('categories', JobCategoryViewSet, basename='job-categories')
router.register('locations', LocationViewSet, basename='locations')
urlpatterns = [
    path('', include(router.urls)),
]
