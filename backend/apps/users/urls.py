from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router dành cho ViewSet
router = DefaultRouter()
router.register('users', views.UserView, basename='user')

urlpatterns = [
    path('register/candidate/', views.RegisterCandidateView.as_view(), name='register-candidate'),
    path('register/employer/', views.RegisterEmployerView.as_view(), name='register-employer'),
    path('', include(router.urls)),
]