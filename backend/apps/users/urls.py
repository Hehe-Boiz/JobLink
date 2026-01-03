from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router dành cho ViewSet
router = DefaultRouter()
router.register('users', views.UserView, basename='user')
router.register('register/employer', views.RegisterEmployerView, basename='register-employer')
router.register('register/candidate', views.RegisterCandidateView, basename='register-candidate')
router.register('admin/employers', views.AdminEmployerViewSet, basename='admin-employer')

urlpatterns = [
    path('candidates/me/', views.CandidateMeView.as_view(), name='candidate-me'),
    path('', include(router.urls)),
]
