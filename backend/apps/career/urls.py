from django.urls import path

from .views import CareerAskView


urlpatterns = [
    path("career/ask/", CareerAskView.as_view(), name="career-ask"),
]