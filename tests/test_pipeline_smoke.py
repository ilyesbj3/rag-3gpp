"""End-to-end pipeline on fixture chunks with a fake LLM and fake dense search (no network)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest

from src.generation.llm import REFUSAL
from src.index.bm25_store import BM25Store
from src.ingest.tokenizer import tokenize
from src.pipeline import RAGPipeline
from src.schemas import Chunk


def mk(spec_short: str, section: str, title: str, body: str) -> Chunk:
    return Chunk(
        chunk_id=f"{spec_short}:{section}:0",
        spec=f"TS {spec_short}",
        spec_short=spec_short,
        version="v",
        release="Rel-18",
        section=section,
        title=title,
        text=f"[TS {spec_short} §{section} {title}]\n{body}",
    )


CHUNKS = [
    mk(
        "24.501",
        "A.1",
        "Causes related to UE identification",
        "Cause #9 - UE identity cannot be derived by the network.",
    ),
    mk(
        "24.501",
        "10.2",
        "Timers of 5GS mobility management",
        "| T3510 | 15s | started on REGISTRATION REQUEST |",
    ),
    mk("23.501", "6.2.1", "AMF", "The AMF includes registration management and mobility."),
    mk("23.501", "6.2.2", "SMF", "The SMF performs session management."),
]


class OverlapDense:
    """Fake dense search: score = token overlap ratio (stands in for cosine similarity)."""

    def __init__(self, chunks):
        self.chunks = chunks

    def search(self, query_vec, top_n, specs=None):
        q = set(self.query)
        out = []
        for c in self.chunks:
            if specs and c.spec not in specs:
                continue
            toks = set(tokenize(c.text))
            out.append((c, len(q & toks) / max(len(q), 1)))
        out.sort(key=lambda x: -x[1])
        return out[:top_n]


@dataclass
class FakeResp:
    text: str
    provider: str = "fake"
    model: str = "fake-1"
    fallback_used: bool = False


class FakeLLM:
    def __init__(self, reply):
        self.reply = reply
        self.calls = []

    def generate(self, system, user):
        self.calls.append(user)
        return FakeResp(self.reply(user))


def fake_rerank(query, cands):
    q = set(tokenize(query))
    for c in cands:
        toks = set(tokenize(c.chunk.text))
        c.rerank_score = len(q & toks) / max(len(q), 1)
    return sorted(cands, key=lambda c: -c.rerank_score)


def make_pipeline(llm, **retrieval):
    dense = OverlapDense(CHUNKS)

    def embed(text):
        dense.query = tokenize(text)
        return np.zeros(4, dtype=np.float32)

    overrides = {
        "retrieval": {"final_top_k": 2, **retrieval},
        "gate": {"reranker_threshold": 0.3, "dense_threshold": 0.3},
    }
    return RAGPipeline(
        llm=llm,
        overrides=overrides,
        dense=dense,
        sparse=BM25Store.build(CHUNKS),
        embed_fn=embed,
        rerank_fn=fake_rerank,
    )


def test_answer_with_valid_and_invalid_citations():
    llm = FakeLLM(
        lambda u: (
            "Cause #9 means the UE identity cannot be derived [TS 24.501 §A.1] [TS 24.501 §9.9]."
        )
    )
    p = make_pipeline(llm)
    ans = p.answer("What does cause #9 mean in 5GMM?")
    assert not ans.refused
    assert ans.route.specs == {"TS 24.501"}
    assert ans.sources[0].chunk.section == "A.1"
    assert '<source id="1" label="[TS 24.501 §A.1]"' in llm.calls[0]
    assert ans.text.endswith("[TS 24.501 §A.1].")
    assert [c.valid for c in ans.citations] == [True, False]
    assert ans.llm_provider == "fake" and ans.timings["total"] >= 0
    assert ans.config_snapshot["use_hybrid"] is True


def test_gate_refuses_without_calling_llm():
    llm = FakeLLM(lambda u: "should not be called")
    ans = make_pipeline(llm).answer("Explain OSPF Dijkstra route computation")
    assert ans.refused and ans.text == REFUSAL and llm.calls == []


def test_llm_refusal_is_normalized():
    llm = FakeLLM(lambda u: "Hmm. " + REFUSAL)
    ans = make_pipeline(llm).answer("What is the role of the SMF?")
    assert ans.refused and ans.text == REFUSAL


@pytest.mark.parametrize("hybrid", [True, False])
@pytest.mark.parametrize("reranker", [True, False])
@pytest.mark.parametrize("routing", [True, False])
def test_retrieve_all_flag_combinations(hybrid, reranker, routing):
    p = make_pipeline(
        FakeLLM(lambda u: ""), use_hybrid=hybrid, use_reranker=reranker, use_routing=routing
    )
    res = p.retrieve_full("When does timer T3510 start?")
    assert res.gate_passed
    assert res.candidates[0].chunk.section == "10.2"
    assert (res.candidates[0].bm25_rank is not None) == hybrid
    assert (res.candidates[0].rerank_score is not None) == reranker
    assert res.route.reason == ("routing disabled" if not routing else res.route.reason)


def test_bm25_query_translation_uses_llm_once():
    llm = FakeLLM(lambda u: "When does timer T3510 start?")
    p = make_pipeline(llm, translate_query_for_bm25=True)
    res = p.retrieve_full("Quand le temporisateur T3510 démarre-t-il ?")
    assert llm.calls == ["Quand le temporisateur T3510 démarre-t-il ?"]
    assert res.candidates[0].chunk.section == "10.2"
    p.retrieve_full("Quand le temporisateur T3510 démarre-t-il ?")
    assert len(llm.calls) == 1  # cached
    assert p.to_english("ascii question") == "ascii question"


def test_generation_cache_staleness():
    from eval.run_generation_eval import stale

    current = {
        "use_hybrid": True,
        "use_reranker": True,
        "use_routing": True,
        "final_top_k": 6,
        "fused_top_n": 30,
        "reranker_model": "m",
        "reranker_threshold": 0.45,
        "dense_threshold": 0.25,
        "router_version": 2,
        "reranker_max_length": 1024,
        "routing_mode": "hard",
        "soft_routing_weight": 1.5,
        "bm25_weight": 1.0,
        "prompt_version": 2,
    }
    old = {k: v for k, v in current.items() if k not in ("router_version", "reranker_max_length")}
    assert stale({"answer": {"config_snapshot": old}}, current)  # cached before router v2
    assert not stale({"answer": {"config_snapshot": dict(current)}}, current)
    assert stale({"answer": {"config_snapshot": {**current, "fused_top_n": 15}}}, current)
    assert stale({"answer": {"config_snapshot": {**current, "prompt_version": 1}}}, current)


def test_soft_routing_searches_both_specs():
    llm = FakeLLM(lambda u: "x [TS 24.501 §A.1].")
    hard = make_pipeline(llm, use_reranker=False, routing_mode="hard").retrieve_full(
        "What does cause #9 mean in 5GMM?"
    )
    assert {c.chunk.spec for c in hard.candidates} == {"TS 24.501"}
    soft = make_pipeline(llm, use_reranker=False, routing_mode="soft").retrieve_full(
        "What does cause #9 mean in 5GMM?"
    )
    assert soft.route.specs == {"TS 24.501"}
    assert {c.chunk.spec for c in soft.candidates} == {"TS 23.501", "TS 24.501"}
    assert soft.candidates[0].chunk.section == "A.1"


def test_prompt_version_selects_rules():
    from src.generation.prompts import SYSTEM_PROMPTS

    seen = []

    class Spy(FakeLLM):
        def generate(self, system, user):
            seen.append(system)
            return super().generate(system, user)

    for v in (1, 2):
        p = make_pipeline(Spy(lambda u: "x [TS 23.501 §6.2.2]."))
        p = p.with_overrides({"llm": {"prompt_version": v}})
        ans = p.answer("What is the role of the SMF?")
        assert ans.config_snapshot["prompt_version"] == v
    assert seen == [SYSTEM_PROMPTS[1], SYSTEM_PROMPTS[2]]
    assert "Refuse only when none of the sources is relevant" in SYSTEM_PROMPTS[2]
