"""FastAPI backend + static web UI for the 3GPP 5G RAG Assistant (UI_SPEC.md).

    uvicorn app.server:app --host 127.0.0.1 --port 8000      # then open http://127.0.0.1:8000

The pipeline (embedder, reranker, Qdrant client, BM25) is built once at startup. If it cannot
start (index missing, Qdrant down), the app still starts: /api/health reports the problem and
/api/ask answers 503 with the command that fixes it.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import sys
import time
import uuid
from collections.abc import Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api_models import AskRequest, AskResponse  # noqa: E402
from src.config import load_settings  # noqa: E402
from src.generation import citation_check  # noqa: E402
from src.generation.llm import DEFAULTS, build_llm  # noqa: E402
from src.schemas import Answer, RetrievedChunk  # noqa: E402

log = logging.getLogger("rag3gpp.api")
WEB_DIR = ROOT / "app" / "web"
RESULTS_DIR = ROOT / "eval" / "results"
TESTSET_PATH = ROOT / "eval" / "testset.json"
EXAMPLES_FALLBACK = ROOT / "app" / "examples.json"

CSP = (
    "default-src 'self'; style-src 'self' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'"
)
FIX_INDEX = "python -m src.index.build_index --rebuild"
FIX_QDRANT = 'docker compose up -d qdrant   (or set qdrant.url: "" in config.yaml)'
FIX_ENV = "cp .env.example .env, then set GEMINI_API_KEY and/or GROQ_API_KEY / XAI_API_KEY"
RATE_LIMIT_MSG = "Rate limit reached, try again in about a minute"
PROVIDERS = {  # name -> (key env var, model)
    "gemini": ("GEMINI_API_KEY", DEFAULTS["gemini_model"]),
    "groq": ("GROQ_API_KEY", DEFAULTS["groq_model"]),
    "grok": ("XAI_API_KEY", DEFAULTS["grok_model"]),
}


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, fix: str | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.fix = status, code, message, fix


def error_response(status: int, code: str, message: str, fix: str | None = None):
    return JSONResponse({"error": {"code": code, "message": message, "fix": fix}}, status)


def configured(name: str) -> bool:
    key = os.getenv(PROVIDERS[name][0]) or (
        os.getenv("GOOGLE_API_KEY") if name == "gemini" else None
    )
    return bool(key)


def write_citation_pattern() -> dict[str, str]:
    """Export the citation regexes for the frontend (JS named groups use `(?<name>`)."""
    pat = {
        "bracket": citation_check.BRACKET_RE.pattern,
        "citation": citation_check.CITATION_RE.pattern.replace("(?P<", "(?<"),
        "flags": "gi",
    }
    path = WEB_DIR / "citation_pattern.json"
    text = json.dumps(pat, indent=1) + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    return pat


# ----------------------------------------------------------------------------- mapping
def _is_cited(rc: RetrievedChunk, ans: Answer) -> bool:
    c = rc.chunk
    for cit in ans.citations:
        if not cit.valid or cit.spec != c.spec:
            continue
        if cit.section == c.section or c.section.startswith(cit.section + "."):
            return True
    return False


def _source(rc: RetrievedChunk, ans: Answer, below_gate: bool) -> dict[str, Any]:
    c = rc.chunk
    return {
        "chunk_id": c.chunk_id,
        "spec": c.spec,
        "section": c.section,
        "title": c.title,
        "content_type": c.content_type,
        "text": c.body,
        "final_rank": rc.final_rank,
        "rerank_score": rc.rerank_score,
        "dense_rank": rc.dense_rank,
        "dense_score": rc.dense_score,
        "bm25_rank": rc.bm25_rank,
        "bm25_score": rc.bm25_score,
        "rrf_score": rc.rrf_score,
        "cited": (not below_gate) and _is_cited(rc, ans),
        "below_gate": below_gate,
    }


def to_response(ans: Answer, req: AskRequest, threshold: float, kind: str) -> dict[str, Any]:
    called = ans.llm_provider is not None
    gate_refused = ans.refused and not called
    srcs = ans.below_gate if gate_refused else ans.sources
    if gate_refused:  # rank the closest candidates for display
        for i, rc in enumerate(srcs, start=1):
            rc.final_rank = rc.final_rank or i
    return {
        "id": str(uuid.uuid4()),
        "question": ans.question,
        "text": ans.text,
        "refused": ans.refused,
        "citations": [
            {"spec": c.spec, "section": c.section, "valid": c.valid} for c in ans.citations
        ],
        "removed_citations": [
            {"spec": c.spec, "section": c.section} for c in ans.citations if not c.valid
        ],
        "warnings": [
            w
            for w in ans.warnings
            if not w.startswith("Removed citations") and "score gate" not in w
        ],
        "route": {
            "specs": sorted(ans.route.specs) if ans.route else [],
            "reason": ans.route.reason if ans.route else "",
        },
        "gate": {
            "score": ans.gate_score,
            "threshold": threshold,
            "passed": not gate_refused,
            "kind": kind,
        },
        "llm": {
            "called": called,
            "provider": ans.llm_provider,
            "model": ans.llm_model,
            "fallback_used": ans.fallback_used,
        },
        "sources": [_source(rc, ans, gate_refused) for rc in srcs],
        "config": {
            "use_hybrid": req.use_hybrid,
            "use_reranker": req.use_reranker,
            "use_routing": req.use_routing,
            "final_top_k": req.final_top_k,
            "provider": req.provider,
        },
        "timings_ms": {k: int(round(v * 1000)) for k, v in ans.timings.items()},
    }


# ----------------------------------------------------------------------------- eval data
def _csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return None if x != x else x


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def eval_payload(results_dir: Path, testset_path: Path) -> dict[str, Any]:
    ret = _csv(results_dir / "retrieval_ablation.csv")
    if not ret:
        return {"available": False}
    items = _json(testset_path) if testset_path.exists() else []
    items = items if isinstance(items, list) else []
    by_type: dict[str, int] = {}
    for it in items:
        by_type[it.get("type", "?")] = by_type.get(it.get("type", "?"), 0) + 1
    groups = {"simple-23": "simple_23", "simple-24": "simple_24", "cross": "cross"}
    retrieval = []
    for r in [x for x in ret if x["group"] == "all"]:
        rec = {
            "config": r["config"],
            "use_hybrid": r["hybrid"] == "True",
            "use_reranker": r["reranker"] == "True",
            "use_routing": r["routing"] == "True",
            "n": int(r["n"]),
            **{k: _num(r[k]) for k in ("recall@1", "recall@3", "recall@5", "recall@10", "mrr")},
            "by_type": {},
        }
        for x in ret:
            if x["config"] == r["config"] and x["group"] in groups:
                rec["by_type"][groups[x["group"]]] = {
                    "recall@5": _num(x["recall@5"]),
                    "mrr": _num(x["mrr"]),
                }
        retrieval.append(rec)
    generation = []
    gen = _csv(results_dir / "generation_gemini.csv")
    for r in gen:
        n = _num(r.get("n")) or 0
        ooc = by_type.get("out_of_corpus", 0)
        fp = _num(r.get("false_refusals")) or 0
        fn = ooc * (1 - (_num(r.get("refusal_recall")) or 0))
        generation.append(
            {
                "config": r["config"],
                "faithfulness": _num(r.get("faithfulness")),
                "answer_correctness": _num(r.get("correctness")),
                "citation_accuracy": _num(r.get("citation_accuracy")),
                "refusal_accuracy": round((n - fp - fn) / n, 4) if n else None,
                "model": r.get("llm_models"),
            }
        )
    router = [r for r in _csv(results_dir / "router_accuracy.csv") if r["config"] == "best"]
    gmeta = _json(results_dir / "generation_gemini_meta.json")
    rmeta = _json(results_dir / "retrieval_meta.json")
    gate = _json(results_dir / "gate_choice.json")
    return {
        "available": True,
        "run": {
            "date": gmeta.get("date") or rmeta.get("date"),
            "commit": gmeta.get("git_commit") or rmeta.get("git_commit"),
            "provider": gmeta.get("provider", "gemini"),
            "model": generation[0]["model"] if generation else None,
        },
        "testset": {
            "total": len(items),
            "by_type": by_type,
            "verified": sum(bool(it.get("verified")) for it in items),
        },
        "retrieval": retrieval,
        "generation": generation,
        "router_accuracy": _num(router[0]["route_exact"]) if router else None,
        "gate": {"threshold": gate.get("reranker_threshold")},
    }


def examples_payload(testset_path: Path) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {"architecture": [], "nas": [], "cross": []}
    items = _json(testset_path) if testset_path.exists() else []
    if isinstance(items, list) and items:
        for it in items:
            if it.get("type") == "simple":
                key = "architecture" if it.get("gold_specs") == ["TS 23.501"] else "nas"
            elif it.get("type") == "cross":
                key = "cross"
            else:
                continue
            if len(out[key]) < 3:
                out[key].append(it["question"])
        return out
    return _json(EXAMPLES_FALLBACK) or out


# ----------------------------------------------------------------------------- app
def create_app(
    pipeline: Any = None,
    llm_factory: Callable[[str], Any] | None = None,
    results_dir: Path = RESULTS_DIR,
    testset_path: Path = TESTSET_PATH,
    warmup: bool = True,
) -> FastAPI:
    """App factory. Tests inject a fake `pipeline` and `llm_factory` (no models, no network)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.startup_error = None
        app.state.llms = {}
        app.state.settings = None
        write_citation_pattern()
        if pipeline is not None:
            app.state.pipeline = pipeline
            app.state.settings = getattr(pipeline, "settings", None)
        else:
            app.state.pipeline = None
            try:
                from src.pipeline import RAGPipeline

                settings = load_settings()
                app.state.settings = settings
                app.state.pipeline = RAGPipeline(settings)
                if warmup:
                    secs = app.state.pipeline.warmup()
                    log.info("Warm-up done in %.1f s", secs)
            except FileNotFoundError as e:
                app.state.startup_error = ("index_not_ready", str(e), FIX_INDEX)
            except RuntimeError as e:  # QdrantUnavailable is a RuntimeError
                app.state.startup_error = ("qdrant_unreachable", str(e), FIX_QDRANT)
            except Exception as e:  # pragma: no cover - logged for the operator
                log.exception("Pipeline failed to start")
                app.state.startup_error = ("internal", f"Pipeline failed to start: {e}", None)
        yield

    app = FastAPI(title="3GPP 5G RAG Assistant", lifespan=lifespan)

    def llm_for(provider: str):
        if provider not in app.state.llms:
            if llm_factory is not None:
                app.state.llms[provider] = llm_factory(provider)
            else:
                s = app.state.settings or load_settings()
                app.state.llms[provider] = build_llm(
                    force=None if provider == "auto" else provider,
                    temperature=s.llm.temperature,
                    max_tokens=s.llm.max_tokens,
                )
        return app.state.llms[provider]

    @app.exception_handler(ApiError)
    async def _api_error(_: Request, exc: ApiError):
        return error_response(exc.status, exc.code, exc.message, exc.fix)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        msg = "; ".join(
            f"{'.'.join(str(x) for x in e['loc'][1:])}: {e['msg']}" for e in exc.errors()
        )
        return error_response(422, "invalid_request", msg or "Invalid request")

    @app.middleware("http")
    async def _csp(request: Request, call_next):
        response = await call_next(request)
        if not request.url.path.startswith("/api"):
            response.headers["Content-Security-Policy"] = CSP
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/api/health")
    def health():
        s = app.state.settings
        err = app.state.startup_error
        llm = {n: {"configured": configured(n), "model": PROVIDERS[n][1]} for n in PROVIDERS}
        n_llm = sum(v["configured"] for v in llm.values())
        index: dict[str, Any] = {"ready": err is None and app.state.pipeline is not None}
        if s is not None:
            from src.index.qdrant_store import collection_name

            index.update(embedding_model=s.embedding.model, collection=collection_name(s))
        chunks = getattr(app.state.pipeline, "chunk_counts", None)
        if callable(chunks):
            per = chunks()
            index.update(chunks=sum(per.values()), per_spec=per)
        status = "ok"
        if err is not None or n_llm == 0:
            status = "error"
        elif n_llm == 1:
            status = "degraded"
        body: dict[str, Any] = {
            "status": status,
            "index": index,
            "corpus": [
                {"spec": x.id, "version": x.version, "release": x.release}
                for x in (s.corpus.specs if s else [])
            ],
            "llm": llm,
            "chain": [n for n in ("gemini", "groq", "grok") if llm[n]["configured"]],
            "defaults": (
                {
                    "use_hybrid": s.retrieval.use_hybrid,
                    "use_reranker": s.retrieval.use_reranker,
                    "use_routing": s.retrieval.use_routing,
                    "final_top_k": s.retrieval.final_top_k,
                    "provider": s.llm.provider,
                }
                if s
                else {}
            ),
        }
        if err is not None:
            body["error"] = {"code": err[0], "message": err[1], "fix": err[2]}
        elif n_llm == 0:
            body["error"] = {
                "code": "llm_not_configured",
                "message": "No LLM API key is set.",
                "fix": FIX_ENV,
            }
        return body

    @app.post("/api/ask", response_model=AskResponse)
    def ask(req: AskRequest):  # plain def: FastAPI runs the blocking pipeline in a thread
        if app.state.startup_error is not None:
            code, message, fix = app.state.startup_error
            raise ApiError(503, code, message, fix)
        t0 = time.perf_counter()
        try:
            llm = llm_for(req.provider)
        except ValueError as e:
            raise ApiError(503, "llm_not_configured", str(e), FIX_ENV) from e
        overrides = {
            "retrieval": {
                "use_hybrid": req.use_hybrid,
                "use_reranker": req.use_reranker,
                "use_routing": req.use_routing,
                "final_top_k": req.final_top_k,
            }
        }
        pipe = app.state.pipeline.with_overrides(overrides, llm=llm)
        try:
            ans = pipe.answer(req.question)
        except FileNotFoundError as e:
            raise ApiError(503, "index_not_ready", str(e), FIX_INDEX) from e
        except RuntimeError as e:
            text = str(e)
            if "All LLM providers failed" in text:
                limited = "429" in text or "rate limit" in text.lower()
                lines = [ln for ln in text.splitlines()[1:] if ln.strip()]
                message = (
                    RATE_LIMIT_MSG
                    if limited
                    else "The language model failed: "
                    + (" | ".join(ln[:160] for ln in lines) or text[:300])
                )
                raise ApiError(502, "llm_failed", message, None) from e
            if "Qdrant" in text:
                raise ApiError(503, "qdrant_unreachable", text, FIX_QDRANT) from e
            log.exception("ask failed")
            raise ApiError(500, "internal", "Internal error, see the server log.") from e
        except Exception as e:
            log.exception("ask failed")
            raise ApiError(500, "internal", "Internal error, see the server log.") from e
        threshold, kind = pipe.gate_threshold()
        body = to_response(ans, req, threshold, kind)
        log.info(
            "ask id=%s route=%s gate=%s refused=%s provider=%s fallback=%s total_ms=%d",
            body["id"],
            "+".join(body["route"]["specs"]),
            body["gate"]["score"],
            body["refused"],
            body["llm"]["provider"],
            body["llm"]["fallback_used"],
            (time.perf_counter() - t0) * 1000,
        )
        log.debug("question=%r", req.question)
        return body

    @app.get("/api/examples")
    def examples():
        return examples_payload(testset_path)

    @app.get("/api/eval")
    def evaluation():
        return eval_payload(results_dir, testset_path)

    @app.get("/api/sources/{chunk_id:path}")
    def source(chunk_id: str):
        from src.ingest.chunker import load_chunks

        for c in load_chunks():
            if c.chunk_id == chunk_id:
                return {
                    "chunk_id": c.chunk_id,
                    "spec": c.spec,
                    "section": c.section,
                    "title": c.title,
                    "content_type": c.content_type,
                    "text": c.body,
                }
        raise ApiError(404, "not_found", f"No chunk {chunk_id}")

    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
    return app


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
app = create_app()
