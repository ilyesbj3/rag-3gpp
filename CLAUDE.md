# CLAUDE.md — RAG chatbot for 3GPP 5G specifications

> This file is the single source of truth for the project. The repository starts EMPTY except
> for this file. Everything below (structure, code contracts, prompts, evaluation, deliverables)
> must be built from it. When a decision changes, update this file in the same commit.

---

## 0. Project brief (from the assignment)

INSAT — Université de Carthage, course **"Futurs Réseaux Mobiles"**, level RT5, year 2026/2027,
instructor Dr Mériem Afif. Mini-project (contrôle continu): **"Chatbot RAG pour les
spécifications 3GPP 5G"**.

Goal: a chatbot that answers questions **in English** about 5G architecture, procedures, NAS
messages and mechanisms, **grounded exclusively** in two normative 3GPP Release 18 specs,
**citing spec + section**, and **explicitly refusing** with
`I could not find this information in the documents.` when the corpus lacks the answer.

### Required work (all mandatory)
1. **Corpus**: download TS 23.501 V18.12.0 and TS 24.501 V18.14.0; document the version used.
2. **Ingestion**: parsing + structural chunking with metadata (spec, release, section, title).
3. **Indexing**: English-capable embeddings + vector database.
4. **Retrieval**: hybrid search (vector + BM25), reranking, query routing by specification.
5. **Generation**: prompt enforcing English, context-grounded answers with citations
   (spec + section) and the explicit refusal sentence.
6. **Interface**: demo application displaying sources.
7. **Evaluation**: test set + metrics (below).
8. **Presentation**: slides covering context, architecture, technical choices, results,
   limits, perspectives.

### Test set (28–33 questions)
- 20 simple questions (10 per spec), in English — e.g. "What does cause #9 mean in 5GMM?"
- 5–10 cross-spec questions — e.g. "Describe the registration procedure and the NAS messages
  exchanged between the UE and the AMF."
- 3 out-of-corpus questions → must yield the refusal sentence.

### Metrics
- Retrieval: correct section in top-k (recall@k, MRR).
- Generation: faithfulness to context, answer correctness, citation correctness.
- Comparisons: with/without hybrid search, with/without reranker, with/without routing.

### Deliverables
Full source code (ingestion, indexing, retrieval, generation, interface) · working demo app ·
test set + evaluation results (comparison tables) · presentation · README (install + run).

### Grading criteria
Corpus & ingestion · Indexing & retrieval · Generation · Interface · Evaluation ·
Presentation & README · Code quality (structure, readability, **reproducibility**).
**Any invented information or wrong citation is penalized.**

### Bonuses (after the mandatory work is done)
- Add TS 23.502 (procedures) or TS 33.501 (security) and justify the impact on results.
- Multi-release (e.g. Rel-17 vs Rel-18) with answer comparison.
- Multilingual: French questions → English answers using bge-m3.
- Compare several LLMs (API vs local) and several embedding models.

### References to cite in README/slides
Lewis et al. 2020 (RAG, arXiv:2005.11401) · Robertson & Zaragoza 2009 (BM25) ·
Chen et al. 2024 (BGE M3, arXiv:2402.03216) · Es et al. 2023 (RAGAS, arXiv:2309.15217).

---

## 1. Corpus (pinned versions — never change silently)

| Spec | Version | Archive file | URL |
|---|---|---|---|
| TS 23.501 | V18.12.0 (Rel-18) | `23501-ic0.zip` | https://www.3gpp.org/ftp/Specs/archive/23_series/23.501/23501-ic0.zip |
| TS 24.501 | V18.14.0 (Rel-18) | `24501-ie0.zip` | https://www.3gpp.org/ftp/Specs/archive/24_series/24.501/24501-ie0.zip |

- 3GPP version code in file names: major/minor digits ≥10 use letters
  (`a`=10 … `i`=18, `c`=12, `e`=14), so `ic0` = 18.12.0 and `ie0` = 18.14.0.
- TS 23.501 = Stage 2 system architecture: network functions (AMF, SMF, UPF, PCF, NSSF, …),
  reference points (N1, N2, N3, N4, N6, N11…), mobility, sessions, QoS (5QI, QoS flows),
  network slicing (S-NSSAI, NSSAI).
- TS 24.501 = Stage 3 NAS protocol UE↔network: 5GMM and 5GSM procedures and messages,
  information elements (IEs), timers (T35xx), cause codes (Annex A).
- `scripts/download_corpus.py` downloads both zips into `data/raw/`, verifies they are valid
  zips, and writes `data/VERSIONS.md` (spec, version, release, file name, URL, download
  date, SHA-256, size, docx file names inside). If the download fails (network/proxy),
  STOP and ask the user to place the zips in `data/raw/` manually.
- A zip may contain one or several `.docx` files (large specs are sometimes split). Process
  all of them in order. If only a legacy `.doc` is present, convert with
  `soffice --headless --convert-to docx` (document this in README).

---

## 2. Stack

| Layer | Choice | Notes |
|---|---|---|
| Language | Python 3.11+ | type hints everywhere |
| Packaging | `uv` + `pyproject.toml` (pip fallback: `pip install -e ".[dev]"` in a Python 3.11 venv) | exact versions pinned in `requirements.lock` (`pip freeze`); `uv.lock` if uv is used |
| Config | `config.yaml` + `.env` (python-dotenv), loaded into a `pydantic-settings` `Settings` | |
| Parsing | `python-docx` | iterate body in order (paragraphs AND tables) |
| Token counting | `tiktoken` (`cl100k_base`) as an approximate counter | only for chunk sizing |
| Embeddings | `BAAI/bge-m3` via `sentence-transformers` (dense, 1024-d, normalized) | comparison model: `BAAI/bge-small-en-v1.5` |
| Vector DB | Qdrant (Docker `qdrant/qdrant`, port 6333) via `qdrant-client`; local on-disk mode (`path=data/index/qdrant`) as a no-Docker fallback | cosine distance |
| Sparse | `bm25s` with the custom tokenizer from §6 | persisted to `data/index/bm25/` |
| Fusion | Reciprocal Rank Fusion, own code | k = 60 |
| Reranker | `BAAI/bge-reranker-v2-m3` via `sentence_transformers.CrossEncoder` | sigmoid scores in [0,1] |
| LLM | **Gemini primary → Grok (xAI) fallback** (`google-genai`, `openai` SDK) | code in Appendix A |
| UI | Streamlit | |
| Eval | own retrieval metrics; RAGAS for faithfulness/correctness; own citation & refusal metrics | |
| Quality | `pytest`, `ruff` (lint + format), `pre-commit` optional | |
| Plots | `matplotlib` for result charts used in the slides | |

Rules:
- **No LangChain / LlamaIndex in `src/`.** Plain modules keep every component swappable for
  ablations. (RAGAS may pull LangChain wrappers inside `eval/` only.)
- Ask the user before adding a dependency not listed here.
- Must run on a CPU-only laptop. Auto-detect CUDA/MPS for embeddings/reranker; use fp16
  only on CUDA. Embedding the whole corpus on CPU can take tens of minutes → cache it (§7).

---

## 3. Repository layout

```
rag-3gpp/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── config.yaml
├── .env.example
├── .gitignore                 # .env, data/raw/, data/index/, data/processed/, .venv/, __pycache__/, eval/results/raw/
├── docker-compose.yml         # qdrant service, volume ./data/index/qdrant_storage
├── Makefile                   # shortcuts for the commands in §15
├── data/
│   ├── raw/                   # downloaded zips (git-ignored)
│   ├── processed/             # chunks.jsonl, parse_report.md
│   ├── index/                 # qdrant storage, bm25, embedding cache
│   └── VERSIONS.md            # committed: provenance of the corpus
├── scripts/
│   ├── download_corpus.py
│   └── inspect_docx_styles.py # prints style histogram of a docx (used once to tune the parser)
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── schemas.py             # Chunk, RetrievedChunk, Answer, Citation dataclasses / pydantic models
│   ├── ingest/
│   │   ├── __init__.py
│   │   ├── parse_docx.py
│   │   ├── chunker.py
│   │   └── tokenizer.py       # telecom-aware tokenizer for BM25
│   ├── index/
│   │   ├── __init__.py
│   │   ├── embed.py
│   │   ├── qdrant_store.py
│   │   ├── bm25_store.py
│   │   └── build_index.py     # CLI: parse → chunk → embed → index
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── hybrid.py          # dense, sparse, RRF, spec quotas
│   │   └── reranker.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── prompts.py
│   │   ├── llm.py             # Appendix A — copy verbatim
│   │   └── citation_check.py
│   └── pipeline.py            # RAGPipeline
├── app/
│   └── streamlit_app.py
├── eval/
│   ├── __init__.py
│   ├── testset.json
│   ├── metrics.py
│   ├── run_retrieval_eval.py
│   ├── run_generation_eval.py
│   ├── make_report.py         # CSV → markdown tables + PNG charts
│   └── results/               # committed: CSV, markdown, PNG (raw per-question JSON in results/raw/)
├── docs/
│   ├── presentation_outline.md
│   └── architecture.md        # mermaid diagrams
└── tests/
    ├── test_tokenizer.py
    ├── test_chunker.py
    ├── test_rrf.py
    ├── test_router.py
    ├── test_citation_check.py
    └── test_pipeline_smoke.py # uses tiny fixture chunks + a fake LLM, no network
```

---

## 4. Configuration (`config.yaml`)

```yaml
corpus:
  specs:
    - {id: "TS 23.501", short: "23.501", version: "18.12.0", release: "Rel-18", file: "23501-ic0.zip"}
    - {id: "TS 24.501", short: "24.501", version: "18.14.0", release: "Rel-18", file: "24501-ie0.zip"}
chunking:
  max_tokens: 800
  overlap_tokens: 100
  min_tokens: 30            # sections below this stay separate chunks (never merged), flagged in stats
embedding:
  model: "BAAI/bge-m3"
  batch_size: 16
  max_seq_length: 1024
qdrant:
  url: "http://localhost:6333"   # set to "" to use local path mode
  path: "data/index/qdrant"
  collection: "3gpp_rel18_bge-m3"
retrieval:
  dense_top_n: 50
  sparse_top_n: 50
  rrf_k: 60
  fused_top_n: 30           # candidates passed to the reranker
  final_top_k: 6            # chunks given to the LLM
  min_per_spec_when_both: 2 # quota for cross-spec questions
  use_hybrid: true
  use_reranker: true
  use_routing: true
gate:
  reranker_threshold: 0.15  # calibrate on eval (§12)
  dense_threshold: 0.45     # used when reranker disabled
reranker:
  model: "BAAI/bge-reranker-v2-m3"
  max_length: 1024
llm:
  provider: "auto"          # auto (gemini→grok) | gemini | grok
  temperature: 0
  max_tokens: 1024
seed: 42
```

Every ablation must be reachable by config/CLI flags only — never by editing code.

---

## 5. Ingestion

### 5.1 Inspect first
Before writing the parser, run `scripts/inspect_docx_styles.py` on both docx files and print
the paragraph-style histogram. 3GPP templates typically use:
- `Heading 1` … `Heading 5` (sometimes deeper) for numbered clauses, text like `5.5.1.2.4\tTitle`
  (number and title separated by a TAB);
- `Heading 8` (TS) / `Heading 9` for annex titles, e.g. `Annex A (informative):\tCause values …`;
- `TH` table title, `TF` figure title, `TAH` table header cell, `TAL`/`TAC`/`TAR` table cells,
  `TAN` table note, `NO` note, `EX` definitions/abbreviations, `B1`…`B5` bullets,
  `EditorsNote`, `PL` code, `TOC 1..9` table of contents, `ZA`/`ZB`/`ZT`… cover page.
Adapt the parser to what is actually found and record the findings in
`data/processed/parse_report.md`.

### 5.2 `parse_docx.py`
- Iterate the document body **in order**, yielding paragraphs and tables (walk
  `document.element.body` children, `w:p` and `w:tbl`).
- Detect headings by style name (`Heading N`) and parse `section_number` + `title` with a
  regex: `^(?P<num>(?:[A-Z]\.)?\d+(?:\.\d+)*)\s+(?P<title>.+)$` after replacing TABs with
  spaces. Annex: `^Annex (?P<letter>[A-Z])\s*\((normative|informative)\):\s*(?P<title>.+)$`
  → section `A`, and annex sub-clauses look like `A.1`, `A.2.3`.
- Maintain a heading stack to compute `breadcrumb` (list of ancestor section numbers) and
  `parent_titles`.
- Skip: cover page, Foreword, ToC (`TOC*` styles), "Change history" annex, empty paragraphs,
  figures (keep the `TF` figure title text as a line `[Figure: …]`).
- Keep: Scope (1), References (2 — keep but tag `content_type="references"`), Definitions
  and abbreviations (3 — very useful for "what is X" questions), all clauses, all annexes
  except change history.
- Tables → Markdown (pipe table). Header row from first row. Merged cells: repeat text.
  Prefix with the preceding `TH` title if present, e.g. `Table 9.11.3.2.1: 5GMM cause information element`.
- Normalize text: NBSP → space, collapse whitespace, keep line breaks between paragraphs,
  bullets `B1..B5` → `- ` with indentation by level.
- Output an ordered list of `Block(spec, section, title, breadcrumb, kind: "text"|"table", text)`.

### 5.3 `chunker.py`
- Group blocks by section (the deepest heading). **One chunk per section** when the section
  fits in `max_tokens`.
- If a section is longer: split on paragraph boundaries into windows of ≤ `max_tokens` with
  `overlap_tokens` of overlap; part index goes in `chunk_id`.
- **Never split a table.** A table larger than `max_tokens` becomes its own chunk(s) split
  **by rows**, repeating the header row and table title in every part.
- Very short sections (< `min_tokens`, e.g. a heading with one line) stay as their own chunk
  (do not merge across section numbers — citations must stay exact).
- Every chunk's `text` starts with a contextual header so both BM25 and the embedder see it:
  `[TS 24.501 §5.5.1.2.4 Initial registration accepted by the network | 5.5 5GMM procedures > 5.5.1 Registration procedure > 5.5.1.2 …]`
- Write `data/processed/chunks.jsonl` and print stats: chunks per spec, token distribution
  (min/median/p95/max), number of tables, number of annex chunks, sections with no text.

### 5.4 Chunk schema (`src/schemas.py`)
```json
{
  "chunk_id": "24.501:5.5.1.2.4:0",
  "spec": "TS 24.501",
  "spec_short": "24.501",
  "version": "18.14.0",
  "release": "Rel-18",
  "section": "5.5.1.2.4",
  "title": "Initial registration accepted by the network",
  "breadcrumb": ["5", "5.5", "5.5.1", "5.5.1.2", "5.5.1.2.4"],
  "parent_titles": ["Elementary procedures for 5GS mobility management", "..."],
  "content_type": "text",          // text | table | definitions | references
  "part": 0,
  "n_tokens": 512,
  "text": "[TS 24.501 §5.5.1.2.4 ...]\n..."
}
```

### 5.5 Ingestion acceptance checks (must pass before indexing)
- Both specs produce chunks; no chunk with empty `section` except explicitly tagged ones.
- Section numbers are unique per (spec, section, part).
- Spot-check by grep that these exist: in 24.501 the 5GMM cause values annex (Annex A) with
  cause #9; timer tables (T3510, T3502…); the REGISTRATION REQUEST message definition
  (clause 8.2.x); in 23.501 the AMF/SMF/UPF function clauses (6.2.x), 5QI table (5.7.4),
  network slicing clause (5.15). Report the actual section numbers found — do not trust
  these numbers from memory; verify.
- No table is split mid-row.

---

## 6. BM25 tokenizer (`src/ingest/tokenizer.py`)

Telecom terms must survive tokenization. Rules:
1. Lowercase.
2. Protect patterns before splitting (regex, applied in this order):
   - cause numbers: `#\d+` → `cause_9` style token (also emit `#9` → `cause_9` for queries
     like "cause #9" and "cause 9": when the word "cause" is followed by a number, emit `cause_<n>`)
   - timers: `t\d{4}` (T3510, T3346) kept whole
   - section refs: `\d+(\.\d+)+` kept whole (e.g. `5.5.1.2.4`)
   - hyphenated/alnum acronyms: `s-nssai`, `5gmm`, `5gsm`, `5g-guti`, `n1`, `n11`, `pdu`,
     `suci`, `supi`, `nssai`, `5qi`, `amf`, `smf`, `upf`… kept whole; ALSO emit the
     de-hyphenated variant (`s-nssai` → `s-nssai`, `snssai`).
3. Split remaining text on non-alphanumerics; drop English stopwords (small built-in list,
   NOT telecom words like "request", "accept", "reject").
4. No stemming by default (configurable flag for an experiment).
5. Same tokenizer for indexing and querying.
Unit tests must cover: `"cause #9"`, `"T3510 expiry"`, `"S-NSSAI"`, `"5GMM"`,
`"REGISTRATION REQUEST"`, `"N2 interface"`, `"section 5.5.1.2.4"`.

---

## 7. Indexing

### `embed.py`
- `get_embedder()` cached with `functools.lru_cache`. Device auto-detect.
- `embed_documents(texts)` / `embed_query(text)`: `normalize_embeddings=True`.
  bge-m3 needs no query instruction. For `bge-small-en-v1.5` (comparison), prefix queries
  with `"Represent this sentence for searching relevant passages: "`.
- Cache: `data/index/emb_<model_slug>_<sha256(chunks.jsonl)[:12]>.npy` + ids file. Reuse if
  present → re-indexing is fast and reproducible.

### `qdrant_store.py`
- Collection name includes the release and model slug (from config). Recreate on `--rebuild`.
- Vectors: size from model, `Distance.COSINE`.
- Payload = all chunk metadata + text. Create payload indexes (keyword) on `spec`,
  `release`, `section`, `content_type`.
- Point id: deterministic UUID5 of `chunk_id`.
- `search(query_vec, top_n, specs: set[str] | None, release: str | None)` → filter with
  `MatchAny` on `spec` when specs given.
- Upload in batches of 256.

### `bm25_store.py`
- One global `bm25s` index over all chunks (+ saved list of chunk_ids in the same order).
- `search(query, top_n, specs=None)`: retrieve a larger pool (e.g. `top_n * 4`, capped at
  corpus size), filter by spec, return top_n with ranks and scores.

### `build_index.py` (CLI)
`python -m src.index.build_index [--rebuild] [--embedding-model ...]`
Runs parse → chunk → embed → Qdrant upsert → BM25 build. Idempotent. Prints timings and counts.

---

## 8. Retrieval

### 8.1 Router (`router.py`) — returns `RouteDecision(specs: set[str], reason: str, scores)`
Rule-based scoring with keyword/regex lists (case-insensitive); each hit adds weight:
- **TS 24.501 (NAS / Stage 3) signals**: `cause #\d+`, `cause value`, `5gmm`, `5gsm`, `nas`,
  `\bt3\d{3}\b` timers, `information element`, `\bie\b`, message names in uppercase or
  words like `request|accept|reject|command|complete` next to `registration|deregistration|
  service|authentication|security mode|identity|configuration update|pdu session
  establishment|pdu session modification|pdu session release|notification`, `message type`,
  `octet`, `coding`, `encoding`, `bit`, `stage 3`.
- **TS 23.501 (Architecture / Stage 2) signals**: network function names (`amf`, `smf`, `upf`,
  `pcf`, `udm`, `udr`, `ausf`, `nssf`, `nef`, `nrf`, `af`, `scp`, `sepp`, `nwdaf`) **when asked
  about role/function/architecture**, `reference point`, `service-based`, `sba`,
  `architecture`, `qos`, `5qi`, `qos flow`, `arp`, `gbr`, `network slic`, `s-nssai`, `nssai`,
  `roaming`, `home-routed`, `local breakout`, `edge computing`, `ssc mode`, `session and service
  continuity`, `registration area`, `stage 2`, `deployment`.
- **Both**: explicit cross-cutting phrases (`procedure and the (nas )?messages`, `end-to-end`,
  `architecture and signalling`, `between the ue and the amf` + `procedure`), or both scores
  above threshold, or no signal at all (ambiguous → search both).
- Decision: if one spec's score ≥ 2× the other and ≥ 1 → that spec only; else both.
- Explicit spec mention (`23.501`, `24.501`) overrides everything.
- `use_routing=false` → always both specs (no filter).
Unit tests with ≥ 12 labeled questions (the router test set is separate from the eval set).

### 8.2 Hybrid search (`hybrid.py`)
```
dense  = qdrant.search(embed_query(q), dense_top_n, specs)
sparse = bm25.search(q, sparse_top_n, specs)            # only if use_hybrid
fused  = rrf([dense, sparse], k=rrf_k)[:fused_top_n]    # if not use_hybrid: fused = dense[:fused_top_n]
```
RRF: `score(d) = Σ_lists 1 / (k + rank_list(d))`, rank starting at 1. Keep per-chunk
provenance: dense rank/score, bm25 rank/score, rrf score.

### 8.3 Reranker (`reranker.py`)
- `CrossEncoder(model, max_length=1024, activation_fn=Sigmoid)` → score per (query, chunk text).
- Sort fused candidates by rerank score. If `use_reranker=false`, keep RRF order.
- Batch size 16; cached model.

### 8.4 Final selection
- Take `final_top_k`. If the route is **both specs**, enforce `min_per_spec_when_both`:
  ensure at least that many chunks from each spec when candidates exist (swap the lowest
  ranked of the dominant spec).
- De-duplicate overlapping parts of the same section (keep the best; merge adjacent parts
  if both selected).

### 8.5 Score gate (anti-hallucination, before calling the LLM)
- Reranker enabled: if `max(rerank_score) < reranker_threshold` → return refusal, skip LLM.
- Reranker disabled: same with top dense cosine vs `dense_threshold`.
- Thresholds are calibrated in §12 (choose the value maximizing refusal accuracy without
  refusing in-corpus questions); record the chosen values in config and README.

---

## 9. Generation

### 9.1 Prompt (`prompts.py`)
Context block format (one per chunk, ordered by final rank):
```
<source id="1" label="[TS 24.501 §5.5.1.2.4]" title="Initial registration accepted by the network">
...chunk text without the contextual header...
</source>
```

System prompt (use verbatim, keep in `prompts.py`):
```
You are a 3GPP 5G standards assistant. You answer questions using ONLY the sources provided
in the user message, which are excerpts from 3GPP TS 23.501 (Release 18) and TS 24.501
(Release 18).

Rules:
1. Answer in English, whatever the language of the question.
2. Use only facts stated in the sources. Do not use prior knowledge, do not guess, do not
   fill gaps. If the sources only partially answer, answer the supported part and state
   clearly which part is not covered by the documents.
3. Cite every factual sentence with the label of the source it comes from, exactly as
   written in the source's label attribute, e.g. [TS 24.501 §5.5.1.2.4]. Several labels may
   follow one sentence. Never cite a section that is not among the provided labels.
4. If the sources do not contain the information needed to answer, reply with exactly this
   sentence and nothing else:
   I could not find this information in the documents.
5. Keep names of messages, information elements, timers, cause values and network
   functions exactly as written in the sources (e.g. REGISTRATION REQUEST, T3510, 5GMM cause #9).
6. Be precise and concise. Use short paragraphs or bullet lists for procedures (ordered
   steps). For questions spanning architecture and NAS signalling, explain the procedure
   (TS 23.501) and then the NAS messages involved (TS 24.501).
```

User prompt template:
```
Sources:
{context_blocks}

Question: {question}

Answer (English, with citations like [TS 24.501 §x.y.z]):
```

### 9.2 LLM (`llm.py`)
Copy **Appendix A verbatim**. Gemini is primary; on transient errors it retries (exponential
backoff), on permanent errors / empty or blocked output it falls back to Grok via the
OpenAI-compatible xAI endpoint `https://api.x.ai/v1`. Model IDs come from `.env`
(`GEMINI_MODEL`, `GROK_MODEL`); `python -m src.generation.llm --list` prints the IDs available
to the user's keys — model names change often, never hard-code them elsewhere.
Each `LLMResponse` carries `provider`, `model`, `fallback_used` — propagate them to `Answer`.

### 9.3 Citation check (`citation_check.py`)
- Extract citations with regex `\[TS\s?(\d{2}\.\d{3})\s?§\s?([A-Z]?\d*(?:\.\d+)*)\]`
  (also tolerate `§ ` and `Section`; normalize).
- `valid` = cited (spec, section) is among the context labels (exact match, or the cited
  section is an ancestor of a provided section → count as "loose-valid", report separately).
- Invalid citations: remove them from the text and set `answer.warnings`.
- If the answer has **zero valid citations** and is not the refusal → append warning
  "Answer not grounded in cited sources" (UI shows it in red; eval counts it).
- If the LLM output contains the refusal sentence → normalize the whole answer to exactly
  the refusal sentence and set `refused=True`.

### 9.4 `Answer` schema
`question, text, refused, citations: list[Citation(spec, section, valid)], warnings,
sources: list[RetrievedChunk(chunk, dense_rank, dense_score, bm25_rank, bm25_score,
rrf_score, rerank_score, final_rank)], route: RouteDecision, gate_score, llm_provider,
llm_model, fallback_used, config_snapshot (flags), timings (route, dense, sparse, rerank,
llm, total)`.

### 9.5 `pipeline.py`
`RAGPipeline(settings, llm=None, overrides=None)`:
`answer(question) -> Answer` and `retrieve(question) -> list[RetrievedChunk]` (used by the
retrieval eval without calling the LLM). The LLM is injectable (fake LLM in tests).

---

## 10. Interface (`app/streamlit_app.py`)
- `st.set_page_config(page_title="3GPP 5G RAG Assistant", layout="wide")`.
- Pipeline built once with `st.cache_resource`.
- **Sidebar**: toggles Hybrid / Reranker / Routing; LLM provider select (auto / gemini / grok);
  final top-k slider; corpus info (spec, version, release, #chunks) from `data/VERSIONS.md`
  and the index; a "Example questions" list (click to ask).
- **Main**: chat (`st.chat_input`, `st.chat_message`), history in `st.session_state`.
- Each answer shows: answer text (citations rendered as badges), badges for route decision,
  LLM provider/model (+ "fallback used" warning), gate score, total latency; warnings in red.
- **Sources panel**: one `st.expander` per retrieved chunk: `[TS x §y] title`, scores (dense,
  BM25 rank, RRF, rerank), content type, full text (tables as Markdown). Cited sources
  highlighted; uncited ones dimmed.
- Refusals displayed with a distinct info box.
- Must work with no GPU and show a clear error if Qdrant/index or API keys are missing
  (with the command to fix it).

---

## 11. Test set (`eval/testset.json`)
Schema:
```json
{
  "id": "s24-01",
  "type": "simple",                    // simple | cross | out_of_corpus
  "question": "What does cause #9 mean in 5GMM?",
  "gold_specs": ["TS 24.501"],
  "gold_sections": ["A.?"],            // list; any match counts; [] for out_of_corpus
  "gold_sections_per_spec": {"TS 24.501": ["A.?"]},   // cross questions: need ≥1 hit per spec
  "reference_answer": "…written from the spec text…",
  "verified": false                    // set true only after a human checked it
}
```
Composition: 10 simple on TS 23.501 (`s23-01..10`), 10 simple on TS 24.501 (`s24-01..10`),
7 cross (`x-01..07`), 3 out-of-corpus (`o-01..03`) → 30 questions.

Process to build it (Claude Code drafts, the human validates):
1. Draft questions covering diverse topics: 23.501 — AMF/SMF/UPF/NSSF roles, reference points
   (N2/N3/N4/N11), QoS flow & 5QI, S-NSSAI structure, SSC modes, registration area, network
   slicing selection, PDU session types; 24.501 — cause values (#9 and others), timers (T3510,
   T3502, T3346…), REGISTRATION REQUEST/ACCEPT contents, registration types, service request,
   deregistration, security mode control, PDU session establishment (5GSM), 5GSM causes.
   Cross — registration procedure + NAS messages; PDU session establishment + 5GSM messages;
   network slicing + NSSAI IEs in NAS; mobility/registration area + periodic registration timer;
   service request + UP activation; deregistration; authentication/security mode.
   Out-of-corpus — clearly outside both specs but telecom-flavored (e.g. Wi-Fi 7 PHY data rate,
   LTE X2 handover details, OSPF route computation) so the test is meaningful.
2. **Find gold sections by searching `chunks.jsonl`** (grep + reading), never from memory.
3. Write reference answers from the chunk text only.
4. Keep `verified: false`; produce `eval/testset_review.md` listing each question, gold
   sections and the supporting excerpt so the human can validate quickly. Eval scripts print a
   warning while any item is unverified.

---

## 12. Evaluation

### 12.1 Retrieval (`run_retrieval_eval.py`) — no LLM calls, fast
- For each of the **8 configs** (hybrid × reranker × routing ∈ {on,off}³) and each
  non-out-of-corpus question: run `pipeline.retrieve`, get the ranked list (after rerank /
  fusion, before final_top_k truncation — evaluate on the top 10).
- Hit rule: retrieved `section` equals a gold section **or is a sub-clause of it** (prefix
  match on `.`-boundaries: gold `5.5.1` matches `5.5.1.2`, not `5.5.10`), and same spec.
- Metrics: recall@1, @3, @5, @10 and MRR (reciprocal rank of first hit, 0 if none).
  Cross questions: also "both-spec recall@k" (≥1 hit per gold spec in top-k).
- Router accuracy (route ⊇ gold_specs, and exact match) reported separately.
- Break down by question type (simple-23, simple-24, cross).
- Output: `eval/results/retrieval_ablation.csv`, per-question JSON in `results/raw/`.

### 12.2 Generation (`run_generation_eval.py`)
- Run on: best config, baseline (all off), and each single-component-removed config
  (≥ 4 configs; all 8 if quota allows). `--provider gemini` forced for comparability
  (`--provider grok` for the LLM comparison bonus). Cache LLM outputs to
  `results/raw/gen_<config>_<provider>.jsonl` and skip already-done items (resumable — free
  tiers hit rate limits).
- Metrics:
  - **Faithfulness** and **answer correctness** with RAGAS (judge LLM = Gemini via RAGAS's
    LLM wrapper; check the installed RAGAS version's API). If RAGAS fails, fall back to an
    own LLM-as-judge in `metrics.py` with a fixed rubric (0/0.5/1) and document it.
  - **Citation accuracy** = valid citations / total citations; **citation recall** = fraction
    of answers citing ≥1 gold section.
  - **Refusal accuracy**: out-of-corpus refused (true positives) and in-corpus answered
    (false refusals) → precision/recall/F1 of refusal.
  - Latency (mean/p95), fallback rate.
- Gate calibration: sweep `reranker_threshold` over [0.0 … 0.6] step 0.05 using retrieval-only
  scores; plot refusal TPR vs false-refusal rate; choose and record the threshold.

### 12.3 Report (`make_report.py`)
Produce `eval/results/REPORT.md` with: corpus versions, config, retrieval ablation table,
generation table, per-type breakdown, router accuracy, gate calibration plot, 3 qualitative
examples (good answer, cross-spec answer, refusal), failure analysis (list of misses with
reason). PNG charts in `eval/results/figures/` for the slides.

---

## 13. README.md (deliverable — write it for a grader on a fresh machine)
Sections: project summary · architecture diagram (mermaid) · corpus & versions (link
`data/VERSIONS.md`) · requirements (Python, Docker optional, API keys) · installation
(`uv sync` / pip) · `.env` setup (Gemini key from Google AI Studio, xAI key from console.x.ai) ·
download corpus · build index (expected time on CPU) · run app · run evaluation · results
summary table (copied from REPORT.md) · technical choices & justification · limitations ·
perspectives · project structure · references.

---

## 14. Presentation (`docs/presentation_outline.md`)
Write a slide-by-slide outline (~12–15 slides) with the content and which chart/table to use:
title · context & problem (spec size, hallucinations) · objectives · corpus (23.501 vs 24.501
complementarity, versions) · architecture diagram · ingestion & structural chunking ·
hybrid retrieval + RRF · reranker + routing · generation prompt, citations, refusal, citation
check · LLM fallback (Gemini → Grok) · demo screenshots · evaluation setup · results (ablation
table + chart) · analysis of what helped and why · limits · perspectives & bonuses · references.

---

## 15. Commands (keep in sync with reality; mirror them in the Makefile)
```bash
uv sync                                           # or: pip install -e ".[dev]"
cp .env.example .env                              # add GEMINI_API_KEY and XAI_API_KEY
python scripts/download_corpus.py                 # → data/raw/*.zip + data/VERSIONS.md
docker compose up -d qdrant                       # optional; else local mode (qdrant.url: "")
python -m src.index.build_index --rebuild         # parse → chunk → embed → index
python -m src.generation.llm --list               # model IDs available to your keys
streamlit run app/streamlit_app.py
python -m eval.run_retrieval_eval --all-ablations
python -m eval.run_generation_eval --provider gemini --configs best,baseline,no_hybrid,no_reranker,no_routing
python -m eval.make_report
pytest -q && ruff check . && ruff format --check .
```

---

## 16. Hard rules (never violate)
1. Refusal sentence is exactly `I could not find this information in the documents.` —
   defined once as `REFUSAL` in `src/generation/llm.py`; import it everywhere.
2. Citation format `[TS 24.501 §5.5.1.2.4]`; context labels use the identical format.
3. Answers always in English. Temperature 0.
4. Never split a table mid-row; never merge chunks across different section numbers.
5. Same tokenizer for BM25 indexing and querying.
6. Never invent 3GPP facts in code, tests, gold data, README or slides. When unsure what the
   spec says, read the parsed chunks. Section numbers quoted anywhere must be verified
   against `chunks.jsonl`.
7. Gold sections/reference answers are drafted from chunks and validated by the human
   (`verified` flag). Do not mark items verified yourself.
8. Never mix providers inside one reported eval run; every result file records config,
   model IDs, corpus versions, git commit, date.
9. No secrets in code or git. `.env`, `data/raw/`, `data/index/` are git-ignored.
10. No network calls in unit tests (fake LLM, fixture chunks).
11. Ablations via flags/config only.
12. **Never push.** Do not run `git push` (or `gh repo create`, `gh pr create`, or anything that
    uploads code to a remote), and do not add or change remotes. Only local commits; the user
    pushes the project themselves.
13. **No AI attribution anywhere in git history.** Commit messages must not mention Claude,
    Claude Code, Anthropic or AI, and must not contain `Co-Authored-By:` trailers or
    "Generated with …" lines. Do not change `git config user.name` / `user.email`; commits use
    the user's identity. The same applies to code comments, README, docs and slides.

---

## 17. Build plan (phases) — stop for user review at the end of each phase

| # | Phase | Done when |
|---|---|---|
| 1 | Scaffold: pyproject, config, .gitignore, .env.example, docker-compose, Makefile, `src/` packages, `schemas.py`, `config.py`, `llm.py` (Appendix A) | `pytest` runs (even if empty), `python -m src.generation.llm --help` works |
| 2 | Corpus download + `VERSIONS.md` + style inspection | zips present, hashes recorded, style histogram saved |
| 3 | Parser + chunker + tokenizer + tests | `chunks.jsonl` + stats + acceptance checks (§5.5) pass; user spot-checks 10 random chunks |
| 4 | Embeddings + Qdrant + BM25 + `build_index` | index built; a dense-only and BM25-only query print sensible results |
| 5 | Router, hybrid (RRF), reranker, quotas, gate + tests | `pipeline.retrieve` works with all flag combos |
| 6 | Prompts, citation check, `RAGPipeline.answer` + smoke test with fake LLM | end-to-end answer with real LLM on 3 questions |
| 7 | Streamlit app | demo usable, sources shown, toggles work |
| 8 | Test set draft + review file | `testset.json` (30 items) + `testset_review.md` delivered for human validation |
| 9 | Retrieval eval (8 configs) + gate calibration | CSV + table |
| 10 | Generation eval + report | `REPORT.md` + figures |
| 11 | README + presentation outline + `docs/architecture.md` | grader can install and run from README |
| 12 | Bonuses (in order): French questions with bge-m3 (+ optional query translation for BM25), embedding comparison (bge-small-en), LLM comparison (Gemini vs Grok), add TS 23.502, Rel-17 vs Rel-18 | each bonus has its own results section |

Commit locally at the end of every phase with a conventional message (`feat(ingest): …`).
Commit messages: subject line + optional body describing the change — nothing else
(no attribution trailers, no mention of Claude/AI; see §16 rules 12–13). Never push.

---

## 18. Working conventions
- Small typed functions, docstrings on public functions, `logging` (not `print`) inside
  `src/`; CLIs use `argparse` and print concise summaries.
- Heavy models loaded once (`lru_cache`). Deterministic seeds.
- Tests alongside code: tokenizer, chunker (section numbers, table integrity, header prefix),
  RRF (hand-computed example), router (labeled questions), citation check (valid/invalid/
  ancestor/refusal normalization), pipeline smoke test (fake LLM, fixture chunks).
- Prefer clear code over clever code — graders read it.
- When a phase reveals that something in this file is wrong (e.g. actual docx styles,
  real section numbers), fix this file and mention it in the phase summary.

---

## Appendix A — `src/generation/llm.py` (copy verbatim)

Dependencies: `google-genai`, `openai`, `python-dotenv`.

```python
"""LLM layer: Gemini as primary provider, Grok (xAI) as automatic fallback.

Usage
-----
    from src.generation.llm import build_llm

    llm = build_llm()                      # Gemini -> Grok fallback
    res = llm.generate(system_prompt, user_prompt)
    print(res.text, res.provider, res.fallback_used)

    llm = build_llm(force="grok")          # force one provider (evaluation / LLM comparison)

Environment variables (.env)
----------------------------
    GEMINI_API_KEY=...
    XAI_API_KEY=...
    GEMINI_MODEL=gemini-flash-latest     # optional override
    GROK_MODEL=grok-4.7                  # optional override
    LLM_TIMEOUT_S=60                     # optional
    LLM_MAX_RETRIES=2                    # retries per provider on transient errors

Run `python -m src.generation.llm --list` to print the model IDs your keys can use.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

REFUSAL = "I could not find this information in the documents."

DEFAULTS = {
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    "grok_model": os.getenv("GROK_MODEL", "grok-4.7"),
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
    "timeout_s": float(os.getenv("LLM_TIMEOUT_S", "60")),
    "max_retries": int(os.getenv("LLM_MAX_RETRIES", "2")),
}


@dataclass
class LLMResponse:
    text: str
    provider: str                 # "gemini" | "grok"
    model: str
    latency_s: float
    fallback_used: bool = False
    errors: list[str] = field(default_factory=list)


class ProviderError(RuntimeError):
    """Raised by a provider when it cannot produce an answer."""

    def __init__(self, msg: str, transient: bool):
        super().__init__(msg)
        self.transient = transient


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, system: str, user: str) -> str: ...


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_s: float):
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not set", transient=False)
        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),  # ms
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        from google.genai import errors

        try:
            resp = self._client.models.generate_content(
                model=self.model,
                contents=user,
                config=self._types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )
        except errors.APIError as e:
            transient = e.code in (408, 429) or (e.code or 0) >= 500
            raise ProviderError(f"Gemini {e.code}: {e.message}", transient) from e
        except Exception as e:  # network errors, timeouts
            raise ProviderError(f"Gemini error: {e!r}", transient=True) from e

        text = (resp.text or "").strip()
        if not text:
            reason = resp.candidates[0].finish_reason if resp.candidates else None
            raise ProviderError(f"Gemini returned empty text (finish_reason={reason})",
                                transient=False)
        return text


class GrokProvider:
    name = "grok"
    BASE_URL = "https://api.x.ai/v1"

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_s: float):
        from openai import OpenAI

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ProviderError("XAI_API_KEY is not set", transient=False)
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL,
                              timeout=timeout_s, max_retries=0)  # we retry ourselves
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        import openai

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except (openai.RateLimitError, openai.APITimeoutError,
                openai.APIConnectionError, openai.InternalServerError) as e:
            raise ProviderError(f"Grok transient error: {e!r}", transient=True) from e
        except openai.APIError as e:
            raise ProviderError(f"Grok error: {e!r}", transient=False) from e

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError("Grok returned empty text", transient=False)
        return text


class FallbackLLM:
    """Tries providers in order. Each provider gets `max_retries` retries with
    exponential backoff on transient errors; on a permanent error or exhausted
    retries, moves on to the next provider."""

    def __init__(self, providers: list[LLMProvider], max_retries: int = 2,
                 backoff_s: float = 1.5):
        if not providers:
            raise ValueError("No LLM provider could be initialised (check API keys).")
        self.providers = providers
        self.max_retries = max_retries
        self.backoff_s = backoff_s

    def generate(self, system: str, user: str) -> LLMResponse:
        errors: list[str] = []
        for idx, p in enumerate(self.providers):
            for attempt in range(self.max_retries + 1):
                t0 = time.perf_counter()
                try:
                    text = p.complete(system, user)
                    return LLMResponse(
                        text=text, provider=p.name, model=p.model,
                        latency_s=round(time.perf_counter() - t0, 3),
                        fallback_used=idx > 0, errors=errors,
                    )
                except ProviderError as e:
                    errors.append(f"[{p.name} try {attempt + 1}] {e}")
                    log.warning("%s failed: %s", p.name, e)
                    if not e.transient or attempt == self.max_retries:
                        break
                    time.sleep(self.backoff_s * (2 ** attempt))
            log.warning("Falling back from %s", p.name)
        raise RuntimeError("All LLM providers failed:\n" + "\n".join(errors))


def build_llm(force: str | None = None, **overrides) -> FallbackLLM:
    """Build the Gemini -> Grok chain. `force="gemini"` or `force="grok"` uses one only."""
    cfg = {**DEFAULTS, **overrides}
    common = dict(temperature=cfg["temperature"], max_tokens=cfg["max_tokens"],
                  timeout_s=cfg["timeout_s"])
    factories = {
        "gemini": lambda: GeminiProvider(cfg["gemini_model"], **common),
        "grok": lambda: GrokProvider(cfg["grok_model"], **common),
    }
    order = [force] if force else ["gemini", "grok"]

    providers: list[LLMProvider] = []
    for name in order:
        try:
            providers.append(factories[name]())
        except ProviderError as e:  # missing key -> skip, keep the other one
            log.warning("Skipping %s: %s", name, e)
    return FallbackLLM(providers, max_retries=cfg["max_retries"])


def _list_models() -> None:
    if os.getenv("GEMINI_API_KEY"):
        from google import genai
        print("Gemini models supporting generateContent:")
        for m in genai.Client().models.list():
            if "generateContent" in (m.supported_actions or []):
                print("  ", m.name.removeprefix("models/"))
    if os.getenv("XAI_API_KEY"):
        from openai import OpenAI
        print("Grok models:")
        for m in OpenAI(api_key=os.getenv("XAI_API_KEY"),
                        base_url=GrokProvider.BASE_URL).models.list():
            print("  ", m.id)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list available model IDs")
    ap.add_argument("--force", choices=["gemini", "grok"])
    ap.add_argument("--q", default="In one sentence, what is the AMF in 5G?")
    a = ap.parse_args()
    if a.list:
        _list_models()
    else:
        r = build_llm(force=a.force).generate("Answer concisely in English.", a.q)
        print(f"[{r.provider}/{r.model} {r.latency_s}s fallback={r.fallback_used}]\n{r.text}")
```

Its behaviour was verified with fake providers: success on primary; retry then success on a
transient error; immediate fallback on a permanent error; fallback after exhausted retries;
`RuntimeError` when all fail; `ValueError` when no key is set; a single provider is used when
only one key exists. Re-create these as `tests/test_llm_fallback.py` (no network).

## Appendix B — `.env.example`
```
# Primary LLM: Google Gemini  (key: https://aistudio.google.com/apikey)
GEMINI_API_KEY=
GEMINI_MODEL=gemini-flash-latest

# Fallback LLM: xAI Grok  (key: https://console.x.ai)
XAI_API_KEY=
GROK_MODEL=grok-4.7

# Generation settings
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=1024
LLM_TIMEOUT_S=60
LLM_MAX_RETRIES=2
```
