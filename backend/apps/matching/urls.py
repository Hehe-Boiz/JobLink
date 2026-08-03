from django.urls import path

from .views import CandidateApplicationMatchView


urlpatterns = [
    path(
        "candidate/applications/<int:application_id>/analysis/",
        CandidateApplicationMatchView.as_view(),
        name="candidate-application-match",
    ),
]