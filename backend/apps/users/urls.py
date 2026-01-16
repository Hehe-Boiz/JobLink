from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('users', views.UserView, basename='user')
router.register('register/employer', views.RegisterEmployerView, basename='register-employer')
router.register('register/candidate', views.RegisterCandidateView, basename='register-candidate')
router.register('admin/employers', views.AdminEmployerViewSet, basename='admin-employer')
router.register('work-experience', views.WorkExperienceViewSet, basename='work-experience')
router.register('education', views.EducationViewSet, basename='education')
router.register('languages', views.LanguageViewSet, basename='languages')
router.register('appreciations', views.AppreciationViewSet, basename='appreciations')
router.register('skills', views.SkillViewSet, basename='skills')
urlpatterns = [
    path('candidates/me/resume/', views.ResumeActionView.as_view(), name='candidate-resume-action'),
    path('candidates/me/', views.CandidateMeView.as_view(), name='candidate-me'),
    path('employers/me/', views.EmployerMeView.as_view(), name='employer-me'),
    path('', include(router.urls)),
]
