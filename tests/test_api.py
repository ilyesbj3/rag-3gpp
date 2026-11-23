"""Web API with a fake pipeline (no models, no network)."""

from __future__ import annotations

import json
import re

import pytest
from fastapi.testclient import TestClient

from app import server
from src.config import load_settings
from src.generation import citation_check
from src.generation.llm import REFUSAL
from src.schemas import Answer, Chunk, Citation, RetrievedChunk, RouteDecision


def chunk(spec_short: str, section: str, title: str = "T", text: str = "body") -> Chunk:
    return Chunk(
        chunk_id=f"{spec_short}:{section}:0",
        spec=f"TS {spec_short}",
        spec_short=spec_short,
        version="v",
        release="Rel-18",
        section=section,
        title=title,
        text=f"[TS {spec_short} §{section} {title}]\n{text}",
    )


class FakeRun:
    def __init__(self, parent, overrides):
        self.parent, self.overrides = parent, overrides

    def gate_threshold(self):
        return 0.45, "reranker" if self.overrides["retrieval"]["use_reranker"] else "dense"

    def answer(self, question: str) -> Answer:
        self.parent.calls.append((question, self.overrides))
        route = RouteDecision(specs={"TS 24.501"}, reason="NAS / stage 3 signals")
        if "index" in question:
            raise FileNotFoundError("chunks.jsonl not found")
        if "llmfail" in question:
            raise RuntimeError("All LLM providers failed:\n[groq try 1] Groq rate limited: 429")
        if "wifi" in question:
            cands = [RetrievedChunk(chunk=chunk("23.501", "5.7.4"), rerank_score=0.2, final_rank=1)]
            return Answer(
                question=question,
                text=REFUSAL,
                refused=True,
                route=route,
                gate_score=0.2,
                below_gate=cands,
                timings={"total": 0.5},
                warnings=["Refused by retrieval score gate (LLM not called)"],
            )
        src = [
            RetrievedChunk(
                chunk=chunk("24.501", "A.1", "Causes"),
                rerank_score=0.9,
                dense_rank=1,
                dense_score=0.7,
                final_rank=1,
            ),
            RetrievedChunk(chunk=chunk("24.501", "10.2", "Timers"), rerank_score=0.5, final_rank=2),
        ]
        return Answer(
            question=question,
            text="Cause #9 means X [TS 24.501 §A.1].",
            route=route,
            gate_score=0.9,
            sources=src,
            llm_provider="gemini",
            llm_model="m",
            citations=[
                Citation(spec="TS 24.501", section="A.1", valid=True),
                Citation(spec="TS 23.501", section="6.2.99", valid=False),
            ],
            warnings=["Removed citations not among the retrieved sources: [TS 23.501 §6.2.99]"],
            timings={"route": 0.001, "dense": 0.04, "llm": 2.1, "total": 2.8},
        )


class FakePipeline:
    def __init__(self):
        self.settings = load_settings()
        self.calls: list = []

    def with_overrides(self, overrides, llm=None):
        return FakeRun(self, overrides)

    def chunk_counts(self):
        return {"TS 23.501": 2, "TS 24.501": 3}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "secret-gemini-value")
    monkeypatch.setenv("GROQ_API_KEY", "secret-groq-value")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    fake = FakePipeline()
    app = server.create_app(
        pipeline=fake,
        llm_factory=lambda p: object(),
        results_dir=tmp_path / "results",
        warmup=False,
    )
    with TestClient(app) as c:
        c.fake = fake
        yield c


def test_health_ok_and_no_key_values(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["index"]["ready"]
    assert body["chain"] == ["gemini", "groq"]
    assert body["llm"]["grok"]["configured"] is False
    assert body["index"]["per_spec"] == {"TS 23.501": 2, "TS 24.501": 3}
    assert "secret-" not in r.text


def test_ask_valid_maps_all_fields_and_overrides(client):
    r = client.post(
        "/api/ask",
        json={
            "question": "What does cause #9 mean?",
            "use_hybrid": False,
            "final_top_k": 4,
            "provider": "groq",
        },
    )
    assert r.status_code == 200
    b = r.json()
    assert set(b) >= {
        "id",
        "question",
        "text",
        "refused",
        "citations",
        "removed_citations",
        "warnings",
        "route",
        "gate",
        "llm",
        "sources",
        "config",
        "timings_ms",
    }
    assert b["removed_citations"] == [{"spec": "TS 23.501", "section": "6.2.99"}]
    assert not any(w.startswith("Removed citations") for w in b["warnings"])
    assert b["sources"][0]["cited"] is True and b["sources"][1]["cited"] is False
    assert b["sources"][1]["bm25_rank"] is None and b["timings_ms"]["total"] == 2800
    assert b["gate"] == {"score": 0.9, "threshold": 0.45, "passed": True, "kind": "reranker"}
    assert b["llm"]["called"] is True and b["config"]["provider"] == "groq"
    _, overrides = client.fake.calls[-1]
    assert overrides["retrieval"]["use_hybrid"] is False
    assert overrides["retrieval"]["final_top_k"] == 4


@pytest.mark.parametrize(
    "payload",
    [
        {"question": "  "},
        {"question": "x" * 1001},
        {"question": "valid question", "final_top_k": 20},
        {"question": "valid question", "provider": "gpt"},
    ],
)
def test_validation_errors(client, payload):
    r = client.post("/api/ask", json=payload)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_request"


def test_gate_refusal_returns_below_gate_sources(client):
    b = client.post("/api/ask", json={"question": "wifi 7 data rate"}).json()
    assert b["refused"] and b["text"] == REFUSAL
    assert b["llm"]["called"] is False and b["gate"]["passed"] is False
    assert b["sources"] and all(s["below_gate"] for s in b["sources"])
    assert all(not s["cited"] for s in b["sources"])


def test_index_missing_is_503_with_fix(client):
    r = client.post("/api/ask", json={"question": "index please"})
    assert r.status_code == 503
    err = r.json()["error"]
    assert err["code"] == "index_not_ready" and "build_index" in err["fix"]


def test_llm_rate_limit_is_502_with_friendly_message(client):
    r = client.post("/api/ask", json={"question": "llmfail now"})
    assert r.status_code == 502
    err = r.json()["error"]
    assert err["code"] == "llm_failed"
    assert err["message"] == "Rate limit reached, try again in about a minute"


def test_startup_error_reported_and_ask_503(monkeypatch, tmp_path):
    app = server.create_app(pipeline=None, warmup=False, results_dir=tmp_path)

    class Broken:
        def __init__(self, *a, **k):
            raise FileNotFoundError("BM25 index missing")

    monkeypatch.setattr("src.pipeline.RAGPipeline", Broken)
    with TestClient(app) as c:
        h = c.get("/api/health").json()
        assert h["status"] == "error" and h["error"]["code"] == "index_not_ready"
        r = c.post("/api/ask", json={"question": "anything here"})
        assert r.status_code == 503 and "build_index" in r.json()["error"]["fix"]


def test_eval_unavailable_then_parsed(client, tmp_path):
    assert client.get("/api/eval").json() == {"available": False}
    res = tmp_path / "results"
    res.mkdir()
    (res / "retrieval_ablation.csv").write_text(
        "config,hybrid,reranker,routing,group,n,recall@1,recall@3,recall@5,recall@10,mrr\n"
        "best,True,True,True,all,27,0.6,0.8,0.9,0.95,0.7\n"
        "best,True,True,True,cross,7,0.3,0.4,0.5,0.6,0.4\n",
        encoding="utf-8",
    )
    (res / "generation_gemini.csv").write_text(
        "config,n,faithfulness,correctness,citation_accuracy,refusal_recall,false_refusals,"
        "llm_models\nbest,30,0.9,0.8,0.95,1.0,2,m\n",
        encoding="utf-8",
    )
    b = client.get("/api/eval").json()
    assert b["available"] and b["retrieval"][0]["mrr"] == 0.7
    assert b["retrieval"][0]["by_type"]["cross"]["recall@5"] == 0.5
    assert b["testset"]["total"] == 30
    assert b["generation"][0]["refusal_accuracy"] == pytest.approx(28 / 30, abs=1e-4)


def test_examples_from_testset(client):
    b = client.get("/api/examples").json()
    assert set(b) == {"architecture", "nas", "cross"}
    assert all(1 <= len(v) <= 3 for v in b.values())


def test_static_index_and_csp(client):
    r = client.get("/")
    assert r.status_code == 200 and "<title>3GPP 5G Assistant</title>" in r.text
    assert "default-src 'self'" in r.headers["content-security-policy"]


def test_citation_pattern_matches_python(client):
    pat = json.loads((server.WEB_DIR / "citation_pattern.json").read_text(encoding="utf-8"))
    assert pat["bracket"] == citation_check.BRACKET_RE.pattern
    assert pat["citation"].replace("(?<", "(?P<") == citation_check.CITATION_RE.pattern
    # the JS-style pattern finds the same citations as the Python checker on fixtures
    text = "A [TS 24.501 §5.5.1.2.4] and [TS24.501 Section A.1; TS 23.501 § 5.35A.1]."
    js_like = re.compile(pat["citation"].replace("(?<", "(?P<"), re.I)
    found = [
        (m["spec"], m["section"])
        for b in citation_check.BRACKET_RE.finditer(text)
        for m in js_like.finditer(b.group(1))
    ]
    assert found == [("24.501", "5.5.1.2.4"), ("24.501", "A.1"), ("23.501", "5.35A.1")]
