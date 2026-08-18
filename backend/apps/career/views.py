from __future__ import annotations

from functools import lru_cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.permissions import IsCandidate
from .answering import CareerAnswerService
from .retrieval import CareerRetriever
from .serializers import CareerAnswerResponseSerializer, CareerAskRequestSerializer


@lru_cache(maxsize=1)
def get_career_retriever() -> CareerRetriever:
    return CareerRetriever()


@lru_cache(maxsize=1)
def get_career_answer_service() -> CareerAnswerService:
    return CareerAnswerService()


class CareerAskView(APIView):
    permission_classes = [IsCandidate]

    def post(self, request) -> Response:
        request_serializer = CareerAskRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        data = request_serializer.validated_data
        retriever = get_career_retriever()

        jobs = retriever.search(
            query=data["query"],
            top_k=data["top_k"],
            source=data.get("source"),
            location_key=data.get("location_key"),
            experience_level=data.get("experience_level"),
            employment_type=data.get("employment_type"),
            category_key=data.get("category_key"),
        )

        answer_service = get_career_answer_service()
        result = answer_service.answer(query=data["query"], jobs=jobs)
        response_serializer = CareerAnswerResponseSerializer(result)

        return Response(response_serializer.data, status=status.HTTP_200_OK)