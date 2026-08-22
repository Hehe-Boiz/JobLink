from __future__ import annotations

from dataclasses import dataclass
from django.conf import settings
from openai import OpenAI
from .retrieval import CareerRetrievedJob

DEFAULT_ANSWER_MODEL = "deepseek-v4-flash-0731"
PROMPT_VERSION = "career-rag-answer-v1"


@dataclass(frozen=True, slots=True)
class CareerCitation:
    citation_id: str

    source: str
    source_job_id: str

    job_title: str
    company_name: str

    source_url: str | None


@dataclass(frozen=True, slots=True)
class CareerAnswer:
    answer: str
    citations: tuple[CareerCitation, ...]


class CareerAnswerService:
    def __init__(
        self,
        model_name: str = DEFAULT_ANSWER_MODEL,
        client: OpenAI | None = None,
        temperature: float | None = None,
    ) -> None:
        self._model_name = model_name
        self._client = client
        self._temperature = temperature

    @property
    def prompt_version(self) -> str:
        return PROMPT_VERSION

    def answer(self, query: str, jobs: list[CareerRetrievedJob]) -> CareerAnswer:
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("Query must not be empty")

        if not jobs:
            return CareerAnswer(
                answer=(
                    "Không tìm thấy đủ bằng chứng từ các công việc "
                    "hiện có để trả lời câu hỏi này."
                ),
                citations=(),
            )

        citations = self._build_citations(jobs)
        context = self._build_context(jobs)
        client = self._get_client()

        request = {
            "model": self._model_name,
            "messages": [
                {
                    "role": "system",
                    "content": self._system_prompt(),
                },
                {
                    "role": "user",
                    "content": (
                        f"Câu hỏi của người dùng:\n"
                        f"{normalized_query}\n\n"
                        f"Evidence đã retrieval:\n"
                        f"{context}"
                    ),
                },
            ],
        }
        if self._temperature is not None:
            request["temperature"] = self._temperature
        response = client.chat.completions.create(
            **request,
        )

        content = response.choices[0].message.content

        return CareerAnswer(
            answer=content.strip() if content else "",
            citations=citations,
        )

    def _get_client(self) -> OpenAI:
        if self._client is not None:
            return self._client

        api_key = getattr(settings, "CKEY_API_KEY", "")
        if not api_key:
            raise RuntimeError("CKEY_API_KEY chưa được cấu hình.")

        base_url = getattr(settings, "CKEY_BASE_URL", "")
        self._client = OpenAI(api_key=api_key, base_url=base_url)

        return self._client

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Bạn là Career Intelligence Assistant của JobLink. "

            "Bạn chỉ được trả lời dựa trên evidence của các job "
            "được cung cấp trong prompt. "

            "Không được tự tạo thêm công việc, công ty, kỹ năng, "
            "mức lương, yêu cầu tuyển dụng hoặc thông tin không xuất "
            "hiện trong evidence. "

            "Nếu evidence không đủ để kết luận một điều, phải nói rõ "
            "rằng dữ liệu hiện tại chưa đủ để kết luận. "

            "Khi đề cập đến một job cụ thể, phải trích citation ID "
            "tương ứng, ví dụ [J1] hoặc [J2]. "

            "Không được tạo citation ID không tồn tại trong evidence. "

            "Retrieval similarity chỉ biểu diễn độ gần semantic giữa "
            "query và evidence. Không được diễn giải similarity thành "
            "phần trăm phù hợp, xác suất được tuyển hoặc Application "
            "Match score. "

            "Ưu tiên trả lời trực tiếp câu hỏi của người dùng bằng "
            "tiếng Việt, ngắn gọn nhưng đủ thông tin. "
        )

    @staticmethod
    def _build_context(jobs: list[CareerRetrievedJob]) -> str:
        job_blocks: list[str] = []
        for index, job in enumerate(jobs, start=1):
            citation_id = f"J{index}"
            evidence_blocks: list[str] = []
            for evidence in job.evidence:
                evidence_blocks.append(
                    (
                        f"[{evidence.section}]\n"
                        f"{evidence.content}"
                    )
                )

            evidence_text = "\n\n".join(evidence_blocks)
            job_blocks.append(
                "\n".join(
                    [
                        f"Citation: [{citation_id}]",
                        f"Job title: {job.job_title}",
                        f"Company: {job.company_name}",
                        f"Location: {job.location_key or 'unknown'}",
                        (
                            "Experience level: "
                            f"{job.experience_level or 'unknown'}"
                        ),
                        (
                            "Employment type: "
                            f"{job.employment_type or 'unknown'}"
                        ),
                        (
                            "Category: "
                            f"{job.category_key or 'unknown'}"
                        ),
                        "Evidence:",
                        evidence_text,
                    ]
                )
            )

        return "\n\n---\n\n".join(job_blocks)

    @staticmethod
    def _build_citations(jobs: list[CareerRetrievedJob]) -> tuple[CareerCitation, ...]:
        return tuple(
            CareerCitation(
                citation_id=f"J{index}",
                source=job.source,
                source_job_id=job.source_job_id,
                job_title=job.job_title,
                company_name=job.company_name,
                source_url=job.source_url,
            )
            for index, job in enumerate(jobs, start=1)
        )
