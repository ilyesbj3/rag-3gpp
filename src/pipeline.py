"""RAGPipeline: route -> dense (+BM25) -> RRF -> rerank -> gate -> final selection -> LLM.

Every component is injectable so that tests run offline with fixture chunks and a fake LLM,
and every ablation is reachable through `overrides` (CLAUDE.md §4, §16.11).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np

from src.config import Settings, load_settings
from src.generation.citation_check import check_citations
from src.generation.llm import REFUSAL, build_llm
from src.generation.prompts import build_user_prompt, system_prompt_for
from src.retrieval.hybrid import fuse, select_final
from src.retrieval.router import route
from src.schemas import Answer, Chunk, RetrievedChunk, RouteDecision

log = logging.getLogger(__name__)
TRANSLATE_PROMPT = (
    "Translate the user's question into English. Keep 3GPP terms, message names, timers and "
    "cause numbers unchanged. Output only the translation."
)


class DenseSearcher(Protocol):
    def search(
        self, query_vec: np.ndarray, top_n: int, specs: set[str] | None = None
    ) -> list[tuple[Chunk, float]]: ...


class SparseSearcher(Protocol):
    def search(
        self, query: str, top_n: int, specs: set[str] | None = None
    ) -> list[tuple[Chunk, float]]: ...


class LLM(Protocol):
    def generate(self, system: str, user: str) -> Any: ...


RerankFn = Callable[[str, list[RetrievedChunk]], list[RetrievedChunk]]
EmbedFn = Callable[[str], np.ndarray]


@dataclass
class RetrievalResult:
    route: RouteDecision
    candidates: list[RetrievedChunk]  # ranked after rerank/fusion, before final_top_k
    final: list[RetrievedChunk]  # what the LLM sees
    gate_score: float | None
    gate_passed: bool
    timings: dict[str, float] = field(default_factory=dict)


class RAGPipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        llm: LLM | None = None,
        overrides: dict[str, Any] | None = None,
        *,
        dense: DenseSearcher | None = None,
        sparse: SparseSearcher | None = None,
        embed_fn: EmbedFn | None = None,
        rerank_fn: RerankFn | None = None,
    ):
        base = settings or load_settings()
        if overrides:
            from src.config import _deep_merge

            base = Settings.model_validate(_deep_merge(base.model_dump(), overrides))
        self.settings = base
        self._llm = llm
        self._dense = dense
        self._sparse = sparse
        self._embed_fn = embed_fn
        self._rerank_fn = rerank_fn
        self._translations: dict[str, str] = {}

    # ------------------------------------------------------------------ lazy components
    @property
    def dense(self) -> DenseSearcher:
        if self._dense is None:
            from src.index.qdrant_store import QdrantStore

            self._dense = QdrantStore(self.settings)
        return self._dense

    @property
    def sparse(self) -> SparseSearcher:
        if self._sparse is None:
            from src.index.bm25_store import BM25Store
            from src.ingest.chunker import load_chunks

            self._sparse = BM25Store.load({c.chunk_id: c for c in load_chunks()})
        return self._sparse

    def embed(self, text: str) -> np.ndarray:
        if self._embed_fn is not None:
            return self._embed_fn(text)
        from src.index.embed import embed_query

        e = self.settings.embedding
        return embed_query(text, e.model, e.max_seq_length)

    def rerank(self, query: str, cands: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if self._rerank_fn is not None:
            return self._rerank_fn(query, cands)
        from src.retrieval.reranker import rerank

        r = self.settings.reranker
        return rerank(query, cands, r.model, r.max_length)

    @property
    def llm(self) -> LLM:
        if self._llm is None:
            prov = self.settings.llm.provider
            self._llm = build_llm(
                force=None if prov == "auto" else prov,
                temperature=self.settings.llm.temperature,
                max_tokens=self.settings.llm.max_tokens,
            )
        return self._llm

    def config_snapshot(self) -> dict[str, Any]:
        s = self.settings
        return {
            "use_hybrid": s.retrieval.use_hybrid,
            "use_reranker": s.retrieval.use_reranker,
            "use_routing": s.retrieval.use_routing,
            "translate_query_for_bm25": s.retrieval.translate_query_for_bm25,
            "final_top_k": s.retrieval.final_top_k,
            "fused_top_n": s.retrieval.fused_top_n,
            "embedding_model": s.embedding.model,
            "reranker_model": s.reranker.model,
            "reranker_threshold": s.gate.reranker_threshold,
            "dense_threshold": s.gate.dense_threshold,
            "llm_provider": s.llm.provider,
        }

    # ------------------------------------------------------------------ retrieval
    def retrieve_full(self, question: str) -> RetrievalResult:
        r = self.settings.retrieval
        t: dict[str, float] = {}
        t0 = time.perf_counter()
        decision = route(question, use_routing=r.use_routing)
        specs = decision.specs if r.use_routing else None
        t["route"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        dense_hits = self.dense.search(self.embed(question), r.dense_top_n, specs)
        t["dense"] = time.perf_counter() - t0

        sparse_hits = None
        if r.use_hybrid:
            t0 = time.perf_counter()
            bm25_query = self.to_english(question) if r.translate_query_for_bm25 else question
            sparse_hits = self.sparse.search(bm25_query, r.sparse_top_n, specs)
            t["sparse"] = time.perf_counter() - t0

        cands = fuse(dense_hits, sparse_hits, r.rrf_k, r.fused_top_n)
        if r.use_reranker:
            t0 = time.perf_counter()
            cands = self.rerank(question, cands)
            t["rerank"] = time.perf_counter() - t0

        gate_score, passed = self._gate(cands)
        final = (
            select_final(list(cands), r.final_top_k, decision.specs, r.min_per_spec_when_both)
            if passed
            else []
        )
        return RetrievalResult(decision, cands, final, gate_score, passed, t)

    def to_english(self, question: str) -> str:
        """Translate a question to English with the LLM (used only for BM25, cached)."""
        if question.isascii():
            return question
        if question not in self._translations:
            resp = self.llm.generate(TRANSLATE_PROMPT, question)
            self._translations[question] = resp.text.strip() or question
        return self._translations[question]

    def _gate(self, cands: list[RetrievedChunk]) -> tuple[float | None, bool]:
        """Anti-hallucination gate on the best retrieval score (§8.5)."""
        if not cands:
            return None, False
        g = self.settings.gate
        if self.settings.retrieval.use_reranker:
            score = max(c.rerank_score or 0.0 for c in cands)
            return score, score >= g.reranker_threshold
        dense_scores = [c.dense_score for c in cands if c.dense_score is not None]
        score = max(dense_scores) if dense_scores else 0.0
        return score, score >= g.dense_threshold

    def retrieve(self, question: str) -> list[RetrievedChunk]:
        """Final chunks given to the LLM (empty when the gate refuses)."""
        return self.retrieve_full(question).final

    # ------------------------------------------------------------------ generation
    def answer(self, question: str) -> Answer:
        t_start = time.perf_counter()
        res = self.retrieve_full(question)
        base = dict(
            question=question,
            sources=res.final,
            route=res.route,
            gate_score=res.gate_score,
            config_snapshot=self.config_snapshot(),
        )
        if not res.gate_passed:
            timings = {**res.timings, "llm": 0.0, "total": time.perf_counter() - t_start}
            return Answer(
                text=REFUSAL,
                refused=True,
                timings=timings,
                warnings=["Refused by retrieval score gate (LLM not called)"],
                **base,
            )

        t0 = time.perf_counter()
        resp = self.llm.generate(
            system_prompt_for(self.settings.corpus.specs), build_user_prompt(question, res.final)
        )
        t_llm = time.perf_counter() - t0

        labels = {(rc.chunk.spec, rc.chunk.section) for rc in res.final}
        checked = check_citations(resp.text, labels)
        timings = {**res.timings, "llm": t_llm, "total": time.perf_counter() - t_start}
        return Answer(
            text=checked.text,
            refused=checked.refused,
            citations=checked.citations,
            warnings=checked.warnings,
            llm_provider=getattr(resp, "provider", None),
            llm_model=getattr(resp, "model", None),
            fallback_used=bool(getattr(resp, "fallback_used", False)),
            timings=timings,
            **base,
        )
