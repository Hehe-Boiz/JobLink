from django.urls import path
from .views import EmployerStatsView
urlpatterns = [
    path('employer-stats/', EmployerStatsView.as_view(), name='employer-stats'),
]