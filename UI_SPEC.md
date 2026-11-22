# UI_SPEC.md — Web interface for the 3GPP 5G RAG Assistant

> Implementation spec for the demo web app. It **replaces the Streamlit interface described
> in CLAUDE.md §10**. Read CLAUDE.md first: all of its hard rules (§16) still apply, including
> never pushing and never mentioning Claude/AI in commits.
> When you start this work, update CLAUDE.md: replace §10 with a short pointer to this file,
> swap Streamlit for FastAPI + static frontend in §2 and §3, and update the commands in §15.

Design reference: four screens on the design canvas
https://claude.ai/artifact/3UnABeEPVo7yiHTwEg99Hn (Chat with answer and sources, empty state,
out-of-corpus refusal, evaluation). This file describes them completely, so the canvas is
not needed to build the app.

**Sample content warning.** The answer text, section numbers, titles and scores in the design
are layout examples. They are NOT verified 3GPP content. Never copy them into code, tests,
example lists or gold data. Every value shown in the real app comes from the API.

---

## 1. Architecture

```
browser ──HTTP/JSON──▶ FastAPI (app/server.py) ──▶ RAGPipeline (src/pipeline.py)
   ▲                         │
   └── static files ◀────────┘  app/web/  (index.html, styles.css, js/*.js, vendor/*)
```

- **Backend:** FastAPI + Uvicorn. One process; the pipeline (embedder, reranker, Qdrant
  client, BM25, LLM chain) is built once at startup in the `lifespan` handler and kept in
  `app.state.pipeline`.
- **Frontend:** plain HTML + CSS + JavaScript ES modules, **no build step and no Node**. The
  grader runs one command and opens a browser.
- Served by FastAPI itself: `StaticFiles(directory="app/web", html=True)` mounted at `/`
  AFTER the `/api` routes.
- Dependencies to add (approved by this spec): `fastapi`, `uvicorn[standard]`, `httpx` (for
  `TestClient` in tests). Remove `streamlit` from requirements if nothing else uses it.
- Vendored frontend libraries (approved): `marked` (Markdown → HTML) and `DOMPurify`
  (sanitizing) as pinned minified files in `app/web/vendor/` with their LICENSE files and
  versions recorded in `app/web/vendor/VERSIONS.md`. Download them once with pip-free means
  (curl from the npm registry tarball or cdnjs); if the network blocks it, write a minimal
  safe Markdown renderer instead (paragraphs, ordered/unordered lists, bold, inline code) that
  builds DOM nodes with `textContent`, never `innerHTML` on model output.

### Files
```
app/
├── server.py            # FastAPI app, lifespan, routes, error handlers
├── api_models.py        # pydantic request/response models (mirror src/schemas.Answer)
└── web/
    ├── index.html       # single page, hash routes #/chat (default) and #/evaluation
    ├── styles.css       # design tokens (CSS custom properties) + components
    ├── js/
    │   ├── main.js      # router, app bootstrap, health check
    │   ├── api.js       # fetch wrappers with timeout + error mapping
    │   ├── state.js     # settings + chat history (localStorage, wrapped in try/catch)
    │   ├── chat.js      # messages, composer, answer rendering, citation chips
    │   ├── sources.js   # sources panel
    │   ├── settings.js  # sidebar controls
    │   └── evaluation.js
    └── vendor/          # marked.min.js, purify.min.js, licenses, VERSIONS.md
tests/test_api.py        # TestClient + fake pipeline, no network
```

---

## 2. API contract

All JSON. All routes under `/api`. Errors return `{"error": {"code": str, "message": str,
"fix": str | null}}` with the HTTP status shown.

### `GET /api/health`
```json
{
  "status": "ok",                       // ok | degraded | error
  "index": {"ready": true, "chunks": 4321, "per_spec": {"TS 23.501": 2000, "TS 24.501": 2321},
            "embedding_model": "BAAI/bge-m3", "collection": "3gpp_rel18_bge-m3"},
  "corpus": [{"spec": "TS 23.501", "version": "18.12.0", "release": "Rel-18"},
             {"spec": "TS 24.501", "version": "18.14.0", "release": "Rel-18"}],
  "llm": {"gemini": {"configured": true, "model": "…"}, "grok": {"configured": true, "model": "…"}},
  "defaults": {"use_hybrid": true, "use_reranker": true, "use_routing": true, "final_top_k": 6,
               "provider": "auto"}
}
```
Never return API key values, only `configured: bool`. `status` is `degraded` when one LLM is
missing, `error` when the index is missing or no LLM is configured.

### `POST /api/ask`
Request:
```json
{"question": "…", "use_hybrid": true, "use_reranker": true, "use_routing": true,
 "final_top_k": 6, "provider": "auto"}
```
Validation: question 3–1000 characters after trimming; `final_top_k` 3–10; provider in
`auto|gemini|grok`. 422 otherwise.

Response: the pipeline `Answer` (CLAUDE.md §9.4) serialized as:
```json
{
  "id": "uuid4",
  "question": "…",
  "text": "answer text with [TS 24.501 §5.5.1.2.4] citations, Markdown allowed",
  "refused": false,
  "citations": [{"spec": "TS 24.501", "section": "5.5.1.2.4", "valid": true}],
  "removed_citations": [{"spec": "TS 23.501", "section": "6.2.99"}],
  "warnings": ["…"],
  "route": {"specs": ["TS 23.501", "TS 24.501"], "reason": "…"},
  "gate": {"score": 0.91, "threshold": 0.15, "passed": true, "kind": "reranker"},
  "llm": {"called": true, "provider": "gemini", "model": "…", "fallback_used": false},
  "sources": [{
    "chunk_id": "24.501:5.5.1.2.4:0", "spec": "TS 24.501", "section": "5.5.1.2.4",
    "title": "…", "content_type": "text", "text": "full chunk text without the context header",
    "final_rank": 1, "rerank_score": 0.88, "dense_rank": 1, "dense_score": 0.71,
    "bm25_rank": 4, "bm25_score": 12.3, "rrf_score": 0.032, "cited": true,
    "below_gate": false
  }],
  "config": {"use_hybrid": true, "use_reranker": true, "use_routing": true, "final_top_k": 6},
  "timings_ms": {"route": 1, "dense": 40, "sparse": 8, "rerank": 600, "llm": 2100, "total": 2800}
}
```
Rules:
- When the gate refuses, `refused=true`, `llm.called=false`, and `sources` still holds the
  closest candidates (up to 3) with `below_gate=true` so the UI can show what was found.
- `cited` is computed server-side by matching citations to sources.
- Fields that don't apply are `null` (e.g. `bm25_rank` when hybrid is off, `rerank_score` when
  the reranker is off). The UI must handle every nullable field.
- The endpoint is a plain `def` (not `async def`) so FastAPI runs the blocking pipeline in its
  thread pool.
- Errors: 503 `index_not_ready` (fix: `python -m src.index.build_index --rebuild`), 503
  `qdrant_unreachable` (fix: `docker compose up -d qdrant` or set `qdrant.url: ""`), 502
  `llm_failed` (message lists provider errors without keys), 500 `internal` (log the
  traceback server-side, generic message to the client).

### `GET /api/examples`
Returns example questions grouped as `{"architecture": [...], "nas": [...], "cross": [...]}`.
Source: `eval/testset.json` — take up to 3 per group from items whose type matches
(`simple` with gold spec 23.501 → architecture, 24.501 → nas, `cross` → cross). Never
out-of-corpus items. If the test set is missing, return a short hard-coded list in
`app/examples.json` written from questions already in the test set draft.

### `GET /api/eval`
Reads `eval/results/` and returns:
```json
{
  "available": true,
  "run": {"date": "…", "commit": "…", "provider": "gemini", "model": "…"},
  "testset": {"total": 30, "by_type": {"simple": 20, "cross": 7, "out_of_corpus": 3},
              "verified": 0},
  "retrieval": [{"config": "full", "use_hybrid": true, "use_reranker": true, "use_routing": true,
                 "recall@1": 0.0, "recall@3": 0.0, "recall@5": 0.0, "recall@10": 0.0, "mrr": 0.0,
                 "by_type": {"simple_23": {"recall@5": 0.0}, "simple_24": {...}, "cross": {...}}}],
  "generation": [{"config": "full", "faithfulness": 0.0, "answer_correctness": 0.0,
                  "citation_accuracy": 0.0, "refusal_accuracy": 0.0}],
  "router_accuracy": 0.0,
  "gate": {"threshold": 0.15}
}
```
`available=false` (HTTP 200) when no results exist yet; the page then shows how to run the
evaluation.

### `GET /api/sources/{chunk_id}` (optional)
Returns one chunk's full payload; used only if answers ever send truncated text.

---

## 3. Design tokens (`styles.css` `:root`)

| Token | Value | Use |
|---|---|---|
| `--bg` | `#F6F7F9` | page background |
| `--surface` | `#FFFFFF` | header, panels, cards |
| `--surface-2` | `#FAFBFC` | expanded source text, example buttons |
| `--muted-bg` | `#EEF1F5` | active nav tab, segmented control, route badge |
| `--border` | `#E3E6EB` | card and panel borders |
| `--border-strong` | `#D5DAE1` | inputs, composer |
| `--text` | `#14171C` | body text, user bubble background |
| `--text-2` | `#3A4250` | secondary text |
| `--text-muted` | `#5B6472` | hints, metadata (passes 4.5:1 on white) |
| `--accent` | `#2F55D4` | primary button, switches on, links |
| `--accent-hover` | `#1E3FA8` | |
| `--spec23-bg` / `--spec23-fg` | `#E8EEFC` / `#1E3FA8` | everything TS 23.501 |
| `--spec24-bg` / `--spec24-fg` | `#FDEEE3` / `#9A4310` | everything TS 24.501 |
| `--both-bg` / `--both-fg` | `#EEF1F5` / `#3A4250` | "both specs" route |
| `--refusal-bg` / `--refusal-border` / `--refusal-fg` | `#FFF8EB` / `#EBCF97` / `#5C3D00` | refusal card, preliminary banner |
| `--fallback-bg` / `--fallback-fg` | `#FFF1D6` / `#7A4F00` | "answered by Grok" badge |
| `--danger-bg` / `--danger-border` / `--danger-fg` | `#FDECEC` / `#F2C2C2` / `#7D1F1F` | warnings, errors |
| `--ok` | `#1F8A4C` | health dot ok; "Cited" label uses `#1F6B3E` |
| `--warn` | `#B26A00` | health dot degraded |
| `--radius-sm` / `--radius` / `--radius-lg` | `6px` / `10px` / `14px` | chips / cards / bubbles and answer cards |

Spec colors are blue vs orange so they differ in lightness as well as hue; never use
red/green to tell the two specs apart.

Typography (Google Fonts, one `<link>` in `index.html`, with system fallbacks):
- **Inter** 400/500/600: all UI text. Body 15px / line-height 1.65 in answers, 14px in panels,
  12px metadata.
- **Space Grotesk** 600: app name 16px, page titles (28px evaluation, 40px empty-state
  hero), panel titles 18px.
- **JetBrains Mono** 400/500: spec labels, citation chips, scores, message/timer names
  inside answers (`REGISTRATION REQUEST`), config names in tables. 11–13px.
- Section labels in the sidebar: 12px, weight 600, uppercase, letter-spacing 0.04em, muted.

Spacing: 4px base; panels padded 20px; chat column padded 28px 32px; gaps 8/12/16/20/24.
Minimum touch target 44px for buttons and inputs (chips inside text may be smaller but must
have at least 24px height including padding).

---

## 4. Layout

### 4.1 Header (all pages)
Left: 34px black square with "5G" (Space Grotesk 600 14px, white) + app name "3GPP 5G
Assistant" + subtitle "Grounded answers from Release 18 specifications".
Nav: two links `Chat` (`#/chat`) and `Evaluation` (`#/evaluation`); active = `--muted-bg`
background, inactive = muted text; `aria-current="page"` on the active one.
Right (chat pages): corpus chips from `/api/health` (`TS 23.501 V18.12.0` in spec23 colors,
`TS 24.501 V18.14.0` in spec24 colors) and an LLM status pill with a colored dot:
- green "Gemini · Grok fallback ready" when both are configured;
- amber "Only Grok configured" / "Only Gemini configured (no fallback)";
- amber "Gemini unavailable · using Grok" after an answer had `fallback_used=true` (resets on
  the next answer that used Gemini);
- red "No LLM configured" with a tooltip giving the `.env` fix.
Header wraps on narrow screens.

### 4.2 Chat page — three columns
`display:flex; flex-wrap:wrap`:
1. **Settings sidebar** (`flex: 1 1 260px; max-width: 300px`).
2. **Chat column** (`flex: 999 1 560px; min-width: 0`), messages centered in max-width 860px.
3. **Sources panel** (`flex: 1 1 360px; max-width: 420px`).

Responsive:
- ≥ 1280px: three columns.
- 900–1279px: sidebar becomes a "Settings" button in the chat column's top bar that opens it
  as a panel above the messages (not a fixed overlay); sources stay on the right.
- < 900px: one column. Settings as above; the sources panel moves below the selected answer
  as a collapsible "Sources (n)" section.
No `position: fixed` overlays; the composer is `position: sticky; bottom: 0` inside the chat
column.

### 4.3 Settings sidebar
- **New chat** button (outline, plus icon). Clears history after no confirmation (it's cheap)
  and returns to the empty state.
- Section "RETRIEVAL PIPELINE": three switches, each with label + one-line hint:
  - Hybrid search — "Vector + BM25 (RRF)"
  - Reranker — "Cross-encoder rescoring"
  - Spec routing — "Filter by TS 23.501 / 24.501"
  Use `<button role="switch" aria-checked>`; on = accent track with knob right, off = `#C9CFD8`
  track with knob left; 44×26px.
- "Chunks to the LLM": `<input type="number" min=3 max=10>` with a `<label>`.
- Section "LANGUAGE MODEL": segmented control (`role="radiogroup"`, three `role="radio"`
  buttons) Auto / Gemini / Grok; selected = white button on `--muted-bg` track, weight 600.
  Hint under it: "Auto uses Gemini and switches to Grok if Gemini fails." Disable an option
  whose provider is not configured (with `title` explaining why).
- Section "EXAMPLE QUESTIONS": up to 3 buttons from `/api/examples` (one per group); click
  fills the composer and sends.
- Settings persist in `localStorage` (`rag3gpp.settings.v1`); every change applies to the
  NEXT question only. A small line "Applies to your next question" appears for 3 seconds after
  a change.

### 4.4 Chat column
**Empty state** (no messages): hero "Ask the 5G specifications" (Space Grotesk 40px) and the
paragraph: "Every answer comes from TS 23.501 (architecture) and TS 24.501 (NAS protocol),
Release 18, with the spec and section it was taken from. When the documents don't cover a
question, the assistant says so." Then a large composer (3 rows), then three cards in an
auto-fit grid (`minmax(280px, 1fr)`): **Architecture** (spec23 chip), **NAS signalling**
(spec24 chip), **Cross-spec** ("Both" chip), each listing that group's example questions as
full-width buttons. Footer line showing current pipeline settings
("Pipeline: hybrid search on · reranker on · spec routing on"). In the empty state the
sources panel shows a placeholder: "Sources for an answer appear here."

**User message:** right-aligned bubble, `--text` background, white 15px text, radius
`14px 14px 4px 14px`, max-width 80%. Text set with `textContent`.

**Assistant answer card** (white, border, radius 14px, padding 20px 22px):
1. Badge row: route badge — "Routed to TS 23.501" (spec23 colors), "Routed to TS 24.501"
   (spec24), "Routed to both specs" (both colors), "Routing off — searched both specs" (both
   colors) — then the route reason in 12px muted text (truncate to one line, full text in
   `title`). If `llm.fallback_used`: badge "Fallback: answered by Grok" (fallback colors).
2. Answer body: Markdown rendered then sanitized (DOMPurify with an allowlist: p, ol, ul, li,
   strong, em, code, pre, br, table, thead, tbody, tr, th, td). Then replace every citation
   pattern (same regex as `src/generation/citation_check.py`) in text nodes with a
   **citation chip**: `<button class="cite cite-23|cite-24">TS 24.501 §5.5.1.2.4</button>`,
   JetBrains Mono 12px, spec colors, radius 5px. Click → select this message, open the
   matching source in the panel, scroll it into view, flash its border (accent, 1.2s). Uppercase
   protocol names in answers (message names, IE names, timers like T3510) are wrapped in
   `<code>` by the model only if it does so; don't post-process them.
3. Warnings (`warnings` and `removed_citations`): red alert box (`role="alert"`) with a
   triangle icon, e.g. "1 citation removed: TS 23.501 §6.2.99 was not among the retrieved
   sources." One box listing all items.
4. Footer row (top border, 12px muted): `{Provider} · {model}` · `{n} citations · {k} valid`
   · `Gate score {score}` · `{total} s` · spacer · **Copy answer** button (copies the plain
   text answer with citations; shows "Copied" for 2s).
5. Clicking anywhere on an answer card (not on a chip or button) selects it; the selected card
   has an accent border and its sources fill the sources panel. The newest answer is selected
   automatically.

**Refusal card** (when `refused=true`): replaces the answer card. Background
`--refusal-bg`, border `--refusal-border`, info-circle icon, bold first line with the exact
refusal sentence from the API text (`I could not find this information in the documents.`),
then an explanation line:
- gate refusal (`llm.called=false`): "No passage in TS 23.501 or TS 24.501 is relevant enough.
  The best {reranker|similarity} score was {score}, below the {threshold} threshold, so no answer
  was generated."
- LLM refusal (`llm.called=true`): "The retrieved passages don't contain this information."
Then a metadata line: route text · "LLM not called" or provider · time.

**Loading state** (after sending): a placeholder card with three animated skeleton lines
(respect `prefers-reduced-motion`) and a status line that steps through "Routing the
question…", "Searching the specifications…", "Reranking passages…", "Writing the answer…"
every ~700ms, staying on the last one until the response arrives. The composer is disabled
while a request is in flight; one request at a time.

**Error card** (network/API error): danger colors, the error `message`, the `fix` in a
monospace copyable line when present, and a **Retry** button that resends the same question
with the same settings.

**Composer:** white box, border-strong, radius 14px; `<textarea>` (auto-grows 2→6 rows) with
a visually hidden `<label>`; placeholder "Ask about 5G architecture, procedures or NAS
messages…"; 44px accent send button with arrow icon and `aria-label="Send question"`.
Enter sends, Shift+Enter inserts a newline. Character counter appears after 800 characters;
send disabled when empty or > 1000. Under the composer, centered 12px muted: "Answers are in
English and come only from TS 23.501 and TS 24.501 (Release 18)."

History: kept in memory and mirrored in `localStorage` (`rag3gpp.history.v1`, last 30
messages); restored on reload. Questions in French are allowed (answers come back in
English).

### 4.5 Sources panel
Title "Sources" (Space Grotesk 18px) + right-aligned meta "{n} chunks · reranked" (or "· RRF
order" when the reranker was off).
One card per source in `final_rank` order:
- Header button (`aria-expanded`): `#rank` (mono 11px muted), spec chip with label
  `TS 24.501 §5.5.1.2.4`, "Cited" label (green-dark, 11px 600) when `cited`.
- Title 14px 500.
- Score line, mono 11px muted, showing only available values:
  `rerank 0.88 · dense #1 · BM25 #4` (omit parts that are null; "RRF 0.032" when the reranker
  is off).
- Expanded body: `--surface-2` background, mono 12px, `white-space: pre-wrap`, full chunk
  text. `content_type="table"` chunks render their Markdown table as an HTML table (sanitized)
  inside a horizontally scrollable box.
- Uncited sources are shown at 75% opacity until hovered/focused.
- Only one card expanded at a time; the first cited source is expanded by default.
- For a gate refusal: a dashed box "No source passed the relevance gate — The closest
  candidates are listed below, so you can see what was found." then the `below_gate` sources
  at 75% opacity with "rerank {score} · below gate {threshold}".

---

## 5. Evaluation page (`#/evaluation`)

Max-width 1200px, padding 28px 24px.
1. Title "Evaluation" + subtitle "{total} questions · {simple} simple, {cross} cross-spec,
   {ooc} out-of-corpus · LLM: {provider} (forced)"; right side mono 12px
   "eval/results/ · run {date} · commit {hash}".
2. If `testset.verified < testset.total`: banner (refusal colors, `role="status"`):
   "Preliminary: the gold set is pending human validation. {verified} of {total} items
   verified."
3. KPI tiles (auto-fit grid, min 200px): Best MRR (+ config name), Recall@5 of the best
   config, Refusal accuracy, Citation accuracy. Values with 2 decimals; "—" when missing.
4. **Retrieval ablation table**: columns Config, Hybrid, Reranker, Routing (on/off text, not
   icons alone), Recall@1, Recall@5, Recall@10, MRR. 8 rows sorted by MRR descending. Best
   value per metric column in bold. Table in an `overflow-x: auto` box. Caption: "{n}
   in-corpus questions · gold section in top-k (prefix match)".
5. Two cards side by side (auto-fit, min 340px):
   - **Generation** table: Config, Faithfulness, Correctness, Citation acc. (+ Refusal acc.
     if present).
   - **Recall@5 by question type**: for each type (Simple — TS 23.501, Simple — TS 24.501,
     Cross-spec) two horizontal bars: best config (accent) and baseline (`#9AA3B2`), with values
     at the right and a legend. Pure HTML/CSS bars (width = value × 100%), no chart library.
6. `available=false`: an empty state with the commands to run
   (`python -m eval.run_retrieval_eval --all-ablations`, then generation, then report), in a
   copyable code block.

All numbers come from `/api/eval`. Nothing is hard-coded.

---

## 6. Behavior details

- **Startup:** `main.js` calls `/api/health`. If `status=error`, show a full-width danger
  banner under the header with the message and fix command; the composer stays disabled
  until a successful health check (retry button).
- **Routing:** hash-based (`#/chat`, `#/evaluation`); unknown hash → chat.
- **Fetch:** 120s timeout via `AbortController`; map HTTP errors to the error card. Never
  log question text to the console in production mode.
- **Security:** model output and chunk text are untrusted. Only insert them via
  `textContent` or after DOMPurify sanitizing. No inline event handlers in generated HTML;
  use `addEventListener`. Set a Content-Security-Policy in `server.py` responses for the
  static files: `default-src 'self'; style-src 'self' https://fonts.googleapis.com;
  font-src https://fonts.gstatic.com; script-src 'self'; connect-src 'self'`.
- **Accessibility:** real buttons/inputs/labels; visible focus rings (2px accent outline,
  2px offset); `aria-live="polite"` region announcing "Answer ready" / "Refused" / "Error";
  color contrast ≥ 4.5:1 for all text (the tokens above pass); everything keyboard-reachable;
  icons `aria-hidden="true"`; icon-only buttons have `aria-label`.
- **Icons:** inline stroke SVGs (24px viewBox, 2px stroke, round caps), no icon font, no emoji.
- **Performance:** first answer may take long while models warm up; the server warms the
  embedder and reranker at startup (one dummy encode) so the first request is fast. Log the
  warm-up time.

---

## 7. Backend implementation notes (`app/server.py`)

```python
@asynccontextmanager
async def lifespan(app):
    settings = load_settings()
    app.state.pipeline = RAGPipeline(settings)      # loads models, connects Qdrant, BM25
    app.state.pipeline.warmup()
    yield

app = FastAPI(title="3GPP 5G RAG Assistant", lifespan=lifespan)
# /api routes first, then:
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
```
- Per-request overrides (`use_hybrid`, …, `provider`) are passed to `pipeline.answer(question,
  overrides=...)`, never by mutating shared settings (requests can overlap).
- The provider override maps to `build_llm(force=...)`; cache one `FallbackLLM` per provider
  value at startup.
- If the pipeline cannot start (index missing, Qdrant down), the app still starts: keep the
  error in `app.state.startup_error`, `/api/health` reports it and `/api/ask` returns 503 with
  the fix.
- Log one line per request: id, route, gate score, refused, provider, fallback, total ms (no
  question text at INFO level; DEBUG only).

---

## 8. Commands

```bash
uvicorn app.server:app --host 127.0.0.1 --port 8000      # then open http://127.0.0.1:8000
make app                                                  # same thing
```
Update the README "Run the app" section and CLAUDE.md §15 accordingly, with a screenshot of
the chat page saved as `docs/screenshots/chat.png` (and `refusal.png`, `evaluation.png`) for
the README and slides.

---

## 9. Tests (`tests/test_api.py`, no network, no models)

Use a `FakePipeline` injected through a dependency or app factory (`create_app(pipeline=...)`):
- `/api/health` returns ok and never contains a key value.
- `/api/ask` valid request → 200 with all schema fields; overrides reach the pipeline.
- Validation: empty question, 1001-char question, `final_top_k=20`, provider `"gpt"` → 422.
- Gate refusal → `refused=true`, `llm.called=false`, `below_gate` sources present.
- Pipeline raising "index missing" → 503 with `fix`.
- LLM chain failure → 502 `llm_failed`.
- `/api/eval` with no results → `available=false`; with a fixture results folder → parsed.
- Static `/` serves `index.html`.

Frontend: add `app/web/js/citations.js` with a pure function `splitCitations(text)` and a
tiny test page or a Node-free check (e.g. Python test that runs the same regex on fixtures)
so the citation regex stays identical to `citation_check.py`. Keep the regex in one JSON
file `app/web/citation_pattern.json` generated from Python at startup, or assert equality in a
test.

---

## 10. Acceptance checklist

- [ ] `uvicorn app.server:app` starts with no GPU; opening `/` shows the empty state.
- [ ] Asking a question shows loading → answer card with clickable citation chips; clicking a
      chip opens and highlights the matching source.
- [ ] Out-of-corpus question → refusal card with the exact sentence; sources panel shows
      below-gate candidates; "LLM not called" when the gate refused.
- [ ] Toggling hybrid/reranker/routing changes the next answer's `config`, the route badge and
      the score line (e.g. no BM25 rank when hybrid is off).
- [ ] Forcing Grok shows provider "Grok" in the footer; a simulated Gemini failure shows the
      fallback badge and updates the header pill.
- [ ] Removed citations appear in the red warning box.
- [ ] Evaluation page renders real numbers from `eval/results/` and the preliminary banner
      while items are unverified.
- [ ] Works at 1440px, 1024px and 390px wide without horizontal page scroll.
- [ ] Keyboard-only use works (Tab order: header → sidebar → messages → composer → sources).
- [ ] No console errors; no unsanitized HTML insertion; CSP header present.
- [ ] `pytest -q` and `ruff check .` pass.
- [ ] README and CLAUDE.md updated; screenshots saved.
- [ ] Committed locally with a conventional message (`feat(ui): …`), nothing pushed, no
      mention of Claude/AI in the commit.
