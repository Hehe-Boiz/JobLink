from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import Application
from apps.users.permissions import IsCandidate

from .serializers import (
    ApplicationMatchAnalysisSerializer,
)
from .services.application_matching import (
    ApplicationMatchingService,
)


class CandidateApplicationMatchView(APIView):
    permission_classes = [IsCandidate]

    def get_application(self, request, application_id: int) -> Application:
        # tìm được thì trả ra obj không thì trả ra lỗi 
        return get_object_or_404(
            Application.objects
            .select_related("job", "candidate") # Yêu cầu Django lấy luôn hai object liên quan
            .prefetch_related("job__tags"), # Yêu cầu Django lấy trước các tag của job (chạy 1 query riêng)
            id=application_id,
            candidate=request.user.candidate_profile,
        )

    def post(self, request, application_id: int) -> Response:
        application = self.get_application(request=request, application_id=application_id)
        analysis = ApplicationMatchingService().run(application)
        serializer = ApplicationMatchAnalysisSerializer(analysis)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request, application_id: int) -> Response:
        application = self.get_application(request=request, application_id=application_id)
        analysis = application.match_analyses.order_by("-created_date").first()

        if analysis is None:
            return Response(
                {
                    "detail": "Application này chưa được phân tích."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = ApplicationMatchAnalysisSerializer(analysis)

        return Response(serializer.data,status=status.HTTP_200_OK)

class CandidateApplicationMatchHistoryView(APIView):
    permission_classes = [IsCandidate]

    def get_application(self, request, application_id: int) -> Application:
        return get_object_or_404(
            Application.objects.select_related("job", "candidate"),
            id=application_id,
            candidate=request.user.candidate_profile,
        )

    def get(self, request, application_id: int) -> Response:
        application = self.get_application(request=request, application_id=application_id,)
        analyses = application.match_analyses.order_by("-created_date")
        serializer = ApplicationMatchAnalysisSerializer(analyses, many=True,)

        return Response(serializer.data, status=status.HTTP_200_OK,)


class CandidateApplicationMatchDetailView(APIView):
    permission_classes = [IsCandidate]

    def get(self, request, application_id: int, analysis_id: int) -> Response:
        application = get_object_or_404(Application, id=application_id, candidate=request.user.candidate_profile)
        analysis = get_object_or_404(application.match_analyses, id=analysis_id)
        serializer = ApplicationMatchAnalysisSerializer(analysis)

        return Response(serializer.data, status=status.HTTP_200_OK)