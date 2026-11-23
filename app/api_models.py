"""Request/response models of the web API. Mirror `src.schemas.Answer`."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Provider = Literal["auto", "gemini", "groq", "grok"]


class AskRequest(BaseModel):
    question: str
    use_hybrid: bool = True
    use_reranker: bool = True
    use_routing: bool = True
    final_top_k: int = Field(6, ge=3, le=10)
    provider: Provider = "auto"

    @field_validator("question")
    @classmethod
    def _check_question(cls, v: str) -> str:
        v = v.strip()
        if not 3 <= len(v) <= 1000:
            raise ValueError("question must be 3 to 1000 characters")
        return v


class CitationOut(BaseModel):
    spec: str
    section: str
    valid: bool


class RemovedCitation(BaseModel):
    spec: str
    section: str


class RouteOut(BaseModel):
    specs: list[str]
    reason: str


class GateOut(BaseModel):
    score: float | None
    threshold: float
    passed: bool
    kind: Literal["reranker", "dense"]


class LLMOut(BaseModel):
    called: bool
    provider: str | None
    model: str | None
    fallback_used: bool


class SourceOut(BaseModel):
    chunk_id: str
    spec: str
    section: str
    title: str
    content_type: str
    text: str
    final_rank: int | None
    rerank_score: float | None
    dense_rank: int | None
    dense_score: float | None
    bm25_rank: int | None
    bm25_score: float | None
    rrf_score: float | None
    cited: bool
    below_gate: bool


class ConfigOut(BaseModel):
    use_hybrid: bool
    use_reranker: bool
    use_routing: bool
    final_top_k: int
    provider: Provider


class AskResponse(BaseModel):
    id: str
    question: str
    text: str
    refused: bool
    citations: list[CitationOut]
    removed_citations: list[RemovedCitation]
    warnings: list[str]
    route: RouteOut
    gate: GateOut
    llm: LLMOut
    sources: list[SourceOut]
    config: ConfigOut
    timings_ms: dict[str, int]


class ErrorBody(BaseModel):
    code: str
    message: str
    fix: str | None = None
