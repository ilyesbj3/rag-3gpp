"""Data models shared across ingestion, retrieval, generation and evaluation."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ContentType = Literal["text", "table", "definitions", "references"]


class Chunk(BaseModel):
    """One retrievable unit of a spec (see CLAUDE.md §5.4)."""

    chunk_id: str  # "24.501:5.5.1.2.4:0"
    spec: str  # "TS 24.501"
    spec_short: str  # "24.501"
    version: str
    release: str
    section: str  # "5.5.1.2.4" or "A.1"
    title: str
    breadcrumb: list[str] = Field(default_factory=list)
    parent_titles: list[str] = Field(default_factory=list)
    content_type: ContentType = "text"
    part: int = 0
    n_tokens: int = 0
    text: str  # starts with the contextual header line

    @property
    def label(self) -> str:
        """Citation label, identical to the format the LLM must use."""
        return f"[{self.spec} §{self.section}]"

    @property
    def body(self) -> str:
        """Text without the contextual header line."""
        if self.text.startswith("[") and "\n" in self.text:
            return self.text.split("\n", 1)[1]
        return self.text


class RetrievedChunk(BaseModel):
    """A chunk plus its retrieval provenance."""

    chunk: Chunk
    dense_rank: int | None = None
    dense_score: float | None = None
    bm25_rank: int | None = None
    bm25_score: float | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    final_rank: int | None = None


class RouteDecision(BaseModel):
    specs: set[str]  # e.g. {"TS 24.501"}
    reason: str
    scores: dict[str, float] = Field(default_factory=dict)


class Citation(BaseModel):
    spec: str  # "TS 24.501"
    section: str
    valid: bool
    loose: bool = False  # cited section is an ancestor of a provided section


class Answer(BaseModel):
    question: str
    text: str
    refused: bool = False
    citations: list[Citation] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[RetrievedChunk] = Field(default_factory=list)
    below_gate: list[RetrievedChunk] = Field(default_factory=list)  # gate refusals only
    route: RouteDecision | None = None
    gate_score: float | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    fallback_used: bool = False
    config_snapshot: dict[str, Any] = Field(default_factory=dict)
    timings: dict[str, float] = Field(default_factory=dict)
