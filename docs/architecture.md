# Architecture

## Offline: ingestion and indexing

```mermaid
flowchart LR
    Z["3GPP zips<br/>23501-ic0.zip · 24501-ie0.zip"] --> P["parse_docx.py<br/>body order · headings by<br/>section number · tables → Markdown"]
    P --> C["chunker.py<br/>1 chunk / section · ≤800 tokens<br/>100-token overlap · tables split by rows<br/>contextual header"]
    C --> J[("chunks.jsonl<br/>3,597 chunks")]
    J --> E["embed.py<br/>BAAI/bge-m3 · 1024-d · normalized<br/>cached .npy"]
    E --> Q[("Qdrant<br/>cosine · payload index on<br/>spec / release / section")]
    J --> T["tokenizer.py<br/>telecom-aware (cause_9, t3510,<br/>s-nssai, 5.5.1.2.4)"]
    T --> B[("BM25 (bm25s)")]
```

## Online: question answering

```mermaid
flowchart TD
    U["Question"] --> R["Router v2 (rules)<br/>TS 23.501 · TS 24.501 · both"]
    R --> D["Dense search<br/>Qdrant top 50, spec filter"]
    R --> S["BM25 top 50, spec filter"]
    D --> F["Reciprocal Rank Fusion<br/>k = 60 → top 15"]
    S --> F
    F --> X["Cross-encoder reranker<br/>bge-reranker-base, 512 tokens (sigmoid)"]
    X --> G{"Score gate<br/>max rerank ≥ threshold?"}
    G -- no --> REF["I could not find this information<br/>in the documents."]
    G -- yes --> K["Final top-k = 6<br/>≥2 per spec on cross routes<br/>adjacent parts merged"]
    K --> PR["Prompt: system rules +<br/>&lt;source label='[TS x §y]'&gt; blocks"]
    PR --> L["LLM: Gemini → Groq → Grok fallback<br/>temperature 0"]
    L --> CC["Citation check<br/>invalid citations removed ·<br/>refusal normalized · warnings"]
    CC --> A["Answer + sources + scores<br/>(web UI)"]
```

## Modules

| Layer | Module | Responsibility |
|---|---|---|
| Config | `src/config.py` | `config.yaml` → typed `Settings`; nested overrides for ablations |
| Ingestion | `src/ingest/parse_docx.py` | ordered paragraphs/tables, headings, annexes, Markdown tables |
| | `src/ingest/chunker.py` | structural chunks, acceptance checks, `parse_report.md` |
| | `src/ingest/tokenizer.py` | BM25 tokenizer shared by indexing and querying |
| Indexing | `src/index/embed.py`, `qdrant_store.py`, `bm25_store.py`, `build_index.py` | dense + sparse indexes |
| Retrieval | `src/retrieval/router.py`, `hybrid.py`, `reranker.py` | routing, RRF, quotas, part merging, reranking |
| Generation | `src/generation/prompts.py`, `llm.py`, `citation_check.py` | prompt, LLM fallback, citation validation |
| Orchestration | `src/pipeline.py` | `RAGPipeline.retrieve()` / `.answer()`, score gate, timings |
| UI | `app/server.py`, `app/web/` | FastAPI API + static web frontend (UI_SPEC.md): chat, toggles, sources panel, evaluation page |
| Evaluation | `eval/` | test set, retrieval and generation evaluations, report |

Every component is injectable in `RAGPipeline` (dense searcher, BM25, embedder, reranker,
LLM), which is how the unit tests run offline and how the evaluation reuses one loaded index
across all ablation configurations.
