from django.urls import path

from .views import CandidateApplicationMatchView, CandidateApplicationMatchHistoryView, CandidateApplicationMatchDetailView


urlpatterns = [
    path(
        "candidate/applications/<int:application_id>/analysis/",
        CandidateApplicationMatchView.as_view(),
        name="candidate-application-match",
    ),

    path(
        "candidate/applications/<int:application_id>/analyses/",
        CandidateApplicationMatchHistoryView.as_view(),
        name="candidate-application-match-history",
    ),

    path(
        "candidate/applications/<int:application_id>/analyses/<int:analysis_id>/",
        CandidateApplicationMatchDetailView.as_view(),
        name="candidate-application-match-detail",
    ),
]