from __future__ import annotations

import json

from django.conf import settings
from openai import OpenAI
from apps.matching.domain import ApplicationScoreResult, RequirementDecision

DEFAULT_EXPLAINER_MODEL = "deepseek-v4-flash-0731"
PROMPT_VERSION = "application-match-explainer-v1"


class LLMExplainer:
    def __init__(self, model_name: str = DEFAULT_EXPLAINER_MODEL, client: OpenAI | None = None) -> None:
        self._model_name = model_name or settings.APPLICATION_MATCH_EXPLAINER_MODEL
        self._client = client

    @property
    def prompt_version(self) -> str:
        return PROMPT_VERSION

    def _get_client(self) -> OpenAI:
        if self._client is None:
            api_key = getattr(settings, "CKEY_API_KEY", "")
            if not api_key:
                raise RuntimeError("CKEY_API_KEY chưa được cấu hình.")

            self._client = OpenAI(
                api_key=settings.CKEY_API_KEY,
                base_url=settings.CKEY_BASE_URL,
            )

        return self._client

    @staticmethod
    def _serialize_decision(decision: RequirementDecision) -> dict:
        evidence_text = None
        if decision.candidate_skill is not None:
            evidence_text = decision.candidate_skill.evidence_text

        elif decision.selected_evidence_text is not None:
            evidence_text = decision.selected_evidence_text

        return {
            "requirement": decision.requirement.original_text,
            "priority": decision.requirement.priority.value,
            "level": decision.level.value,
            "match_type": decision.match_type.value,
            "credit": float(decision.credit),
            "reason": decision.reason,
            "evidence": evidence_text,
        }

    def _build_input(self, result: ApplicationScoreResult) -> str:
        payload = {
            "final_score": float(result.final_score),
            "breakdown": result.breakdown,
            "matched": [
                self._serialize_decision(decision)
                for decision in result.matched
            ],
            "partial": [
                self._serialize_decision(decision)
                for decision in result.partial
            ],
            "missing": [
                self._serialize_decision(decision)
                for decision in result.missing
            ],
        }

        return json.dumps(payload, ensure_ascii=False, indent=2)

    def explain(self, result: ApplicationScoreResult) -> str:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self._model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là hệ thống giải thích kết quả CV–Job Matching cho ứng viên. "

                        "Chỉ được sử dụng dữ liệu matching được cung cấp. Không được suy diễn "
                        "thêm kỹ năng, kinh nghiệm hoặc thành tích không có trong dữ liệu. "

                        "Giải thích ngắn gọn bằng tiếng Việt. Nêu điểm mạnh chính, các yêu cầu chỉ "
                        "match một phần và các yêu cầu còn thiếu. "

                        "Nếu evidence không đủ rõ thì phải nói rằng CV chưa thể hiện rõ, không được "
                        "tự khẳng định ứng viên có kỹ năng đó. "

                        "Final score là điểm tương thích heuristic, không phải xác suất được tuyển. "

                        "Không tự tính lại hoặc thay đổi final score."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_input(result),
                },
            ],
        )
        content = response.choices[0].message.content

        return content.strip() if content else ""