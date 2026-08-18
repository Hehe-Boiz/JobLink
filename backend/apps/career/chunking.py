from __future__ import annotations

from transformers import AutoTokenizer, PreTrainedTokenizerBase
from .domain import JobKnowledgeChunk, JobKnowledgeDocument, JobKnowledgeSection


DEFAULT_EMBEDDING_MODEL = "intfloat/multilingual-e5-small"

TARGET_CHUNK_TOKENS = 220
MAX_CHUNK_TOKENS = 320
FORCED_SPLIT_OVERLAP_TOKENS = 40


class JobKnowledgeChunker:
    def __init__(self, tokenizer: PreTrainedTokenizerBase | None = None, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.tokenizer = tokenizer or AutoTokenizer.from_pretrained(model_name)

    def chunk(self, document: JobKnowledgeDocument) -> list[JobKnowledgeChunk]:
        chunks: list[JobKnowledgeChunk] = []
        global_chunk_index = 0

        for section, content in document.sections.items():
            section_contents = self._chunk_section(title=document.title, section=section, content=content,)

            for section_chunk_index, chunk_content in enumerate(section_contents):
                chunk_id = self._build_chunk_id(
                    document=document,
                    section=section,
                    section_chunk_index=section_chunk_index,
                )

                embedding_text = self._build_embedding_text(
                    title=document.title,
                    section=section,
                    content=chunk_content,
                )

                chunks.append(
                    JobKnowledgeChunk(
                        chunk_id=chunk_id,
                        chunk_index=global_chunk_index,
                        source=document.source,
                        source_job_id=document.source_job_id,
                        title=document.title,
                        company_name=document.company_name,
                        section=section,
                        content=chunk_content,
                        embedding_text=embedding_text,
                        location_key=document.location_key,
                        experience_level=document.experience_level,
                        employment_type=document.employment_type,
                        category_key=document.category_key,
                        is_active=document.is_active,
                        published_at=document.published_at,
                        source_url=document.source_url,
                        metadata=dict(document.metadata),
                    )
                )

                global_chunk_index += 1

        return chunks

    def _chunk_section(self, title: str, section: JobKnowledgeSection, content: str) -> list[str]:
        blocks = self._split_blocks(content)

        if not blocks:
            return []

        chunks: list[str] = []
        current_blocks: list[str] = []

        for block in blocks:
            block_text = block.strip()

            if not block_text:
                continue

            block_token_count = self._embedding_token_count(
                title=title,
                section=section,
                content=block_text,
            )

            if block_token_count > MAX_CHUNK_TOKENS:
                if current_blocks:
                    chunks.append(self._join_blocks(current_blocks))
                    current_blocks = []

                chunks.extend(
                    self._split_long_block(
                        title=title,
                        section=section,
                        block=block_text,
                    )
                )

                continue

            # Chunk hiện tại đang rỗng.
            if not current_blocks:
                current_blocks.append(block_text)
                continue

            current_content = self._join_blocks(current_blocks)
            candidate_content = self._join_blocks([*current_blocks, block_text])
            current_tokens = self._embedding_token_count(
                title=title,
                section=section,
                content=current_content,
            )

            candidate_tokens = self._embedding_token_count(
                title=title,
                section=section,
                content=candidate_content,
            )

            if self._should_add_block(current_tokens=current_tokens, candidate_tokens=candidate_tokens):
                current_blocks.append(block_text)
            else:
                chunks.append(current_content)
                current_blocks = [block_text]

        if current_blocks:
            chunks.append(self._join_blocks(current_blocks))

        return chunks

    @staticmethod
    def _split_blocks(content: str) -> list[str]:
        return [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

    @staticmethod
    def _should_add_block(current_tokens: int, candidate_tokens: int) -> bool:
        if candidate_tokens > MAX_CHUNK_TOKENS:
            return False

        if candidate_tokens <= TARGET_CHUNK_TOKENS:
            return True

        current_distance = abs(TARGET_CHUNK_TOKENS - current_tokens)
        candidate_distance = abs(candidate_tokens - TARGET_CHUNK_TOKENS)

        return candidate_distance < current_distance

    def _split_long_block(self, title: str, section: JobKnowledgeSection, block: str) -> list[str]:
        prefix = self._build_embedding_prefix(title=title, section=section,)
        prefix_tokens = len(self.tokenizer.encode(prefix, add_special_tokens=True))
        content_budget = MAX_CHUNK_TOKENS - prefix_tokens

        if content_budget <= FORCED_SPLIT_OVERLAP_TOKENS:
            raise ValueError(
                "Embedding prefix is too long for the configured "
                "chunk token budget"
            )

        token_ids = self.tokenizer.encode(block, add_special_tokens=False)
        step = content_budget - FORCED_SPLIT_OVERLAP_TOKENS
        pieces: list[str] = []
        start = 0

        while start < len(token_ids):
            end = min(start + content_budget, len(token_ids))
            piece_ids = token_ids[start:end]
            piece = self.tokenizer.decode(piece_ids, skip_special_tokens=True).strip()

            if piece:
                pieces.append(piece)

            if end >= len(token_ids):
                break

            start += step

        return pieces

    def _embedding_token_count(self, title: str, section: JobKnowledgeSection, content: str) -> int:
        embedding_text = self._build_embedding_text(
            title=title,
            section=section,
            content=content,
        )

        return len(self.tokenizer.encode(embedding_text, add_special_tokens=True))

    @staticmethod
    def _join_blocks(blocks: list[str]) -> str:
        return "\n".join(blocks).strip()

    @staticmethod
    def _build_embedding_prefix(title: str, section: JobKnowledgeSection) -> str:
        return (
            "passage: "
            f"Job title: {title}\n"
            f"Section: {section.value}\n\n"
        )

    def _build_embedding_text(self, title: str, section: JobKnowledgeSection, content: str) -> str:
        return self._build_embedding_prefix(title=title, section=section) + content.strip()

    @staticmethod
    def _build_chunk_id(document: JobKnowledgeDocument, section: JobKnowledgeSection, section_chunk_index: int) -> str:
        return (
            f"{document.source}:"
            f"{document.source_job_id}:"
            f"{section.value.lower()}:"
            f"{section_chunk_index}"
        )