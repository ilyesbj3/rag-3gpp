"""Streamlit demo: chat over TS 23.501 / TS 24.501 (Rel-18) with sources and ablation toggles.

streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DATA_DIR, load_settings  # noqa: E402
from src.generation.citation_check import NOT_GROUNDED  # noqa: E402
from src.pipeline import RAGPipeline  # noqa: E402
from src.schemas import Answer  # noqa: E402

st.set_page_config(page_title="3GPP 5G RAG Assistant", layout="wide")

EXAMPLES = [
    "What does cause #9 mean in 5GMM?",
    "When is timer T3510 started and what happens when it expires?",
    "What is the role of the SMF?",
    "Which information elements does the REGISTRATION REQUEST message contain?",
    "Describe the registration procedure and the NAS messages exchanged between the UE "
    "and the AMF.",
    "What is the maximum data rate of Wi-Fi 7?",
]
CITE_RE = re.compile(r"\[(TS \d{2}\.\d{3}) §([^\]]+)\]")


# ----------------------------------------------------------------------------- resources
@st.cache_resource(show_spinner="Loading indexes and models…")
def base_pipeline() -> RAGPipeline:
    """Shared heavy components (Qdrant client, BM25, embedder, reranker are cached inside)."""
    p = RAGPipeline(load_settings())
    _ = p.dense, p.sparse  # fail early with a clear error if an index is missing
    return p


@st.cache_resource(show_spinner=False)
def llm_for(provider: str):
    from src.generation.llm import build_llm

    s = load_settings()
    return build_llm(
        force=None if provider == "auto" else provider,
        temperature=s.llm.temperature,
        max_tokens=s.llm.max_tokens,
    )


def pipeline_for(hybrid: bool, reranker: bool, routing: bool, k: int, provider: str):
    base = base_pipeline()
    overrides = {
        "retrieval": {
            "use_hybrid": hybrid,
            "use_reranker": reranker,
            "use_routing": routing,
            "final_top_k": k,
        },
        "llm": {"provider": provider},
    }
    return RAGPipeline(
        base.settings,
        llm=llm_for(provider),
        overrides=overrides,
        dense=base.dense,
        sparse=base.sparse,
    )


def corpus_rows() -> list[str]:
    path = DATA_DIR / "VERSIONS.md"
    if not path.exists():
        return []
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.startswith("| TS ")]


# ----------------------------------------------------------------------------- rendering
def badge(text: str, color: str = "blue") -> str:
    safe = text.replace("[", "(").replace("]", ")")
    return f":{color}-badge[{safe}]"


def render_answer(ans: Answer) -> None:
    if ans.refused:
        st.info(ans.text, icon="🚫")
    else:
        st.markdown(CITE_RE.sub(lambda m: " " + badge(f"{m[1]} §{m[2]}"), ans.text))
    meta = [
        badge(
            "route: " + " + ".join(sorted(ans.route.specs)) if ans.route else "route: -", "violet"
        )
    ]
    if ans.llm_provider:
        meta.append(badge(f"LLM: {ans.llm_provider} / {ans.llm_model}", "green"))
    if ans.fallback_used:
        meta.append(badge("fallback used", "orange"))
    if ans.gate_score is not None:
        meta.append(badge(f"gate score {ans.gate_score:.3f}", "gray"))
    meta.append(badge(f"{ans.timings.get('total', 0):.1f} s", "gray"))
    st.markdown(" ".join(meta))
    for w in ans.warnings:
        if w == NOT_GROUNDED or w.startswith("Removed citations"):
            st.error(w)
        else:
            st.caption(w)
    render_sources(ans)


def render_sources(ans: Answer) -> None:
    if not ans.sources:
        return
    cited = {(c.spec, c.section) for c in ans.citations if c.valid}
    cited_loose = {(c.spec, c.section) for c in ans.citations if c.valid and c.loose}
    with st.container(border=True):
        st.markdown(f"**Sources** ({len(ans.sources)} retrieved)")
        for rc in ans.sources:
            c = rc.chunk
            is_cited = (c.spec, c.section) in cited or any(
                s == c.spec and c.section.startswith(sec + ".") for s, sec in cited_loose
            )
            mark = "★" if is_cited else "·"
            label = f"{mark} [{c.spec} §{c.section}] {c.title}"
            if not is_cited:
                label += "  (not cited)"
            with st.expander(label):
                scores = [
                    f"dense {rc.dense_score:.3f} (#{rc.dense_rank})"
                    if rc.dense_score
                    else "dense -",
                    f"BM25 #{rc.bm25_rank} ({rc.bm25_score:.2f})" if rc.bm25_rank else "BM25 -",
                    f"RRF {rc.rrf_score:.4f}" if rc.rrf_score else "RRF -",
                    f"rerank {rc.rerank_score:.3f}" if rc.rerank_score is not None else "rerank -",
                ]
                st.caption(" · ".join(scores) + f" · {c.content_type} · chunk `{c.chunk_id}`")
                st.markdown(c.body)


# ----------------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Settings")
    hybrid = st.toggle("Hybrid search (dense + BM25)", value=True)
    reranker = st.toggle("Reranker (bge-reranker-v2-m3)", value=True)
    routing = st.toggle("Routing by specification", value=True)
    provider = st.selectbox(
        "LLM provider",
        ["auto", "gemini", "grok"],
        help="auto = Gemini with automatic fallback to Grok",
    )
    top_k = st.slider("Chunks given to the LLM (final top-k)", 2, 12, 6)
    st.divider()
    st.subheader("Corpus")
    rows = corpus_rows()
    for r in rows:
        cells = [x.strip() for x in r.strip("|").split("|")]
        st.markdown(f"**{cells[0]}** V{cells[1]} ({cells[2]})")
    try:
        from src.ingest.chunker import load_chunks

        st.caption(f"{len(load_chunks())} chunks indexed")
    except FileNotFoundError:
        st.caption("No chunks yet: run `python -m src.index.build_index --rebuild`")
    if not rows:
        st.warning("Corpus not downloaded: run `python scripts/download_corpus.py`")
    st.divider()
    st.subheader("Example questions")
    for q in EXAMPLES:
        if st.button(q, use_container_width=True):
            st.session_state["pending"] = q

# ----------------------------------------------------------------------------- main
st.title("3GPP 5G RAG Assistant")
st.caption(
    "Answers grounded only in TS 23.501 V18.12.0 and TS 24.501 V18.14.0 (Release 18), "
    "with citations. Questions in any language, answers in English."
)

if "history" not in st.session_state:
    st.session_state["history"] = []

for msg in st.session_state["history"]:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            render_answer(Answer.model_validate(msg["answer"]))

question = st.chat_input("Ask about 5G architecture, procedures, NAS messages…")
question = question or st.session_state.pop("pending", None)

if question:
    st.session_state["history"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        try:
            with st.spinner("Retrieving and generating…"):
                pipe = pipeline_for(hybrid, reranker, routing, top_k, provider)
                ans = pipe.answer(question)
        except FileNotFoundError as e:
            st.error(f"{e}\n\nBuild the index: `python -m src.index.build_index --rebuild`")
            st.stop()
        except ValueError as e:  # no API key at all
            st.error(
                f"{e}\n\nCopy `.env.example` to `.env` and set GEMINI_API_KEY and/or XAI_API_KEY."
            )
            st.stop()
        except RuntimeError as e:  # Qdrant down, or all LLM providers failed
            st.error(str(e))
            st.stop()
        render_answer(ans)
    st.session_state["history"].append({"role": "assistant", "answer": ans.model_dump()})
