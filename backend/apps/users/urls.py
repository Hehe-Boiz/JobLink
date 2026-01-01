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
    # Path dành cho Generic View
    path('register/candidate/', views.RegisterCandidateView.as_view(), name='register-candidate'),
    path('register/employer/', views.RegisterEmployerView.as_view(), name='register-employer'),

    # Include router vào
    path('', include(router.urls)),
]