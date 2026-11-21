# PROGRESS

Running log of the build (CLAUDE.md §17, autonomous mode). On restart: read CLAUDE.md, then
this file, then continue with the first phase not marked done.

Environment: Windows 11, CPU only, Python 3.11 venv in `.venv` (pip + `requirements.lock`),
Docker available (Qdrant default), API keys present in `.env` (never printed or committed).

## Phase status

| # | Phase | Status | Commit |
|---|---|---|---|
| 1 | Scaffold | done | feat(scaffold) |
| 2 | Corpus + VERSIONS.md + style inspection | done | feat(corpus) |
| 3 | Parser + chunker + tokenizer + tests | done | feat(ingest) |
| 4 | Embeddings + Qdrant + BM25 + build_index | done | feat(index) |
| 5 | Router, hybrid, reranker, quotas, gate | done | feat(retrieval) |
| 6 | Prompts, citation check, pipeline | done | feat(generation) |
| 7 | Streamlit app | done | feat(app) |
| 8 | Test set draft + review file | done (unverified) | feat(eval) |
| 9 | Retrieval eval + gate calibration | done (preliminary) | feat(eval) retrieval |
| 10 | Generation eval + report | done (preliminary) | feat(eval) generation |
| 11 | README + presentation + architecture | todo | |
| 12 | Bonuses | todo | |

## Phase 1–2 (summary)
- Corpus: TS 23.501 V18.12.0 (`23501-ic0.zip`, cover dated 2025-12) and TS 24.501 V18.14.0
  (`24501-ie0.zip`, cover dated 2026-09), one .docx each; SHA-256 in `data/VERSIONS.md`.
- Style findings recorded in CLAUDE.md §5.1 (H6/H2 heading styles, lettered clause numbers,
  annex titles with a line break, annex sub-clauses styled Heading 1, duplicate 8.2.6.35).

## Phase 3 — ingestion
- `python -m src.ingest.chunker` → `data/processed/chunks.jsonl` + `parse_report.md` (~28 s).
- **3,597 chunks**: TS 23.501 1,281 (860 sections with text, median 482 tokens, p95 777);
  TS 24.501 2,316 (1,124 sections, median 616, p95 782). Tables parsed: 54 + 541
  (3 cover tables per spec skipped). Change-history annexes skipped (23.501 R, 24.501 F).
- Acceptance checks (§5.5): all PASS (both specs, no empty section, unique ids, no table
  split mid-row).
- Spot checks, found by searching the chunks (verified section numbers):
  - 24.501 5GMM cause #9 → **§A.1** ("Causes related to UE identification").
  - 24.501 T3510 and T3502 → timer table in **§10.2** (Table 10.2.1, UE side).
  - 24.501 REGISTRATION REQUEST message content → **§8.2.6.1** (Table 8.2.6.1.1), under
    8.2.6 "Registration request".
  - 23.501 AMF / SMF / UPF → **§6.2.1 / §6.2.2 / §6.2.3**.
  - 23.501 standardized 5QI table → **§5.7.4** (Table 5.7.4-1, split by rows into parts 1–4).
  - 23.501 Network slicing → **§5.15** (heading only; text in 5.15.x sub-clauses).
- Decisions:
  - Heading-only sections (219 + 246) produce no chunk; their titles appear in descendants'
    headers/breadcrumbs.
  - 12 chunks exceed 800 tokens: each is a single table row too large to split (bit-coding
    IE tables, max 3,669 tokens). Kept whole per §16.4; the embedder truncates them at 1024
    tokens, BM25 sees everything.
  - Full-width table rows (notes) keep the text in the first column only (avoids repeating a
    long note in every column).
  - BM25 tokenizer additionally emits the parts of hyphenated terms (`5g-guti` → `guti`),
    besides the whole and de-hyphenated forms.
  - `parse_report.md` and `chunk_samples.md` are committed (rest of `data/processed/` ignored).
- Review file: `data/processed/chunk_samples.md` (15 random chunks, seed 42 + cause #9,
  T3510, REGISTRATION REQUEST, 5QI table).

## Phase 4 — indexing
- `python -m src.index.build_index --rebuild`: 3,597 points in Qdrant collection
  `3gpp_rel18_bge-m3` (1024-d, cosine) on Docker `qdrant/qdrant:v1.20.0`; BM25 in
  `data/index/bm25/`. Timings on this CPU laptop: BM25 1.6 s, **bge-m3 embedding 4,422 s
  (74 min)**, upload 14 s. Embeddings cached in `data/index/emb_bge-m3_<sha12>.npy`.
- Sanity: dense and BM25 both rank 24.501 §A.1 in top-4 for "cause #9", 23.501 §6.2.2 first
  (dense) for "role of the SMF", 24.501 §10.2 first for "T3510".
- Environment issue fixed: Windows Smart App Control blocked the DLL of `regex==2026.11.19`
  (released 2 days before); pinned `regex==2026.9.29` in `requirements.lock`.
- Model pre-download note: bge-m3 ships `pytorch_model.bin` (2.3 GB), not safetensors.

## Phase 5 — retrieval
- Router (17 labeled questions + 2 extra tests), RRF (hand-computed), quotas and part merging
  unit-tested; `retrieve_full` works with all 8 flag combinations on the real index.
- **Reranker latency on CPU: ~45–65 s per query** (30 candidates × up to 1,024 tokens).
  max_length 512 is only ~2× faster; kept 1,024 (spec value, slightly better ranking).
  The UI reranker toggle gives a ~1 s retrieval mode. Eval caches rerank scores per
  (question, chunk) in `eval/results/raw/rerank_cache.json`.
- Loading a second reranker instance in the same process exhausted the Windows paging file
  → reranker is cached per model only once per process.

## Phase 6 — generation
- End-to-end with Gemini on 3 questions: cause #9 (cites §A.1, §5.5.1.3.5, all valid), SMF
  role (cites §6.2.2), cross registration question (cites both specs, all valid).
- Model: `gemini-flash-latest` and `gemini-2.5-flash` are no longer served for this key;
  `gemini-3.8-flash` returned 503 (overloaded) at test time → **`GEMINI_MODEL=gemini-3.5-flash`**
  (set in `.env` and `.env.example`; only the model line of `.env` was edited).
- `llm.max_tokens` raised 1024 → **8192**: gemini-3.5 "thinking" tokens count against
  `max_output_tokens` (measured 3,536 thinking + 1,063 answer tokens on a cross question,
  answers were truncated mid-citation at 1,024 / 4,096).
- Fixed `_list_models()` in `llm.py` (google-genai 3.x closes an unreferenced client before
  iteration); Appendix A updated identically.

## Phase 7 — app
- Verified with `streamlit.testing.v1.AppTest`: no exception, sidebar corpus info and
  "3597 chunks indexed", answer with citation badges, route/LLM/gate/latency badges, source
  expanders marked ★ cited / (not cited).

## Phase 8 — test set
- `eval/testset.json`: 30 items (s23-01..10, s24-01..10, x-01..07, o-01..03), **all
  `verified: false`**. Gold sections found by searching chunks; reference answers written from
  chunk text. `eval/testset_review.md` shows the best-matching excerpt per gold section.
- Out-of-corpus topics checked absent from the corpus (Wi-Fi 7/802.11be, GSM A5/1, OSPF: 0
  hits). An "LTE X2 handover" question was dropped because "X2" occurs in the corpus.
- Decision: faithfulness / correctness use an own LLM-as-judge (rubric 0/0.5/1, Gemini)
  instead of RAGAS — RAGAS's Gemini integration needs LangChain packages not in the
  approved stack; lightest option, documented in README.

## Phase 9 — retrieval evaluation (preliminary — gold set pending human validation)
- `python -m eval.run_retrieval_eval --all-ablations` (~2 h on CPU, reranker dominated; rerank
  scores cached). 27 in-corpus questions, top-10 after fusion/rerank.

| Config | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|
| best (all on) | 0.667 | 0.852 | 0.926 | 0.734 |
| no_hybrid | 0.704 | 0.926 | 0.963 | 0.790 |
| no_reranker | 0.481 | 0.815 | 0.889 | 0.622 |
| no_routing | 0.667 | 0.926 | 0.963 | 0.762 |
| hybrid_only | 0.407 | 0.778 | 0.889 | 0.574 |
| reranker_only | 0.704 | 0.926 | 0.963 | 0.795 |
| routing_only | 0.630 | 0.889 | 0.926 | 0.730 |
| baseline | 0.556 | 0.889 | 0.926 | 0.677 |

- Findings: the reranker is the component that helps most (MRR +0.11 for best vs
  no_reranker, +0.12 reranker_only vs baseline). BM25 fusion helps *without* reranker on
  simple questions but slightly hurts when the reranker is on (BM25 candidates displace
  good dense candidates from the 30 sent to the reranker). Simple questions: R@5 = 1.0 for
  both specs in `best`; cross questions are the weak spot (R@5 0.43, both-spec R@5 0.0).
- Router: simple questions routed exactly (23.501: 10/10, 24.501: 9/10) but only 1/7 cross
  questions routed to both specs (they contain mostly NAS words) → routing hurts cross
  recall. Not tuned on the eval set (would overfit); listed as a perspective.
- Gate calibration: max rerank score of out-of-corpus questions 0.005 / 0.071 / 0.202 vs
  lowest in-corpus 0.661 → **reranker_threshold = 0.45** (middle of the zero-false-refusal
  range). Dense cosine cannot separate (OOC 0.549–0.559 vs in-corpus min 0.533) → rule gives
  0.25, i.e. the dense gate never refuses; refusal then relies on the LLM. Both in config.yaml.
- Defaults left as specified (all components on). The data suggest dense+reranker without
  BM25 is better; this is reported, not baked in, because the gold set is unvalidated.

## Phase 10 — generation evaluation (preliminary — gold set pending human validation)
- Gemini free tier = **20 requests/day per model** for the flash models
  (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, observed on gemini-3.5-flash and
  gemini-3.6-flash). The generation eval needs ~290 calls (answers + judge) → impossible on
  a flash model. **Switched the reported run (answers + judge) to `gemini-3.5-flash-lite`**
  (also the new default in `.env` / `.env.example`). The 6 answers produced earlier with
  gemini-3.5-flash were moved to `eval/results/raw/archive/` so models are never mixed in a
  reported run.
- Results (gemini-3.5-flash-lite answers + judge, 30 questions per config):

| Config | Faithfulness | Correctness | Citation acc. | Gold cited | Refusal F1 | False refusals |
|---|---|---|---|---|---|---|
| best | 0.97 | 0.88 | 0.98 | 0.81 | 0.75 | 2 |
| baseline | 1.00 | 0.83 | 0.99 | 0.78 | 0.60 | 4 |
| no_hybrid | 1.00 | 0.92 | 0.97 | 0.93 | 0.75 | 2 |
| no_reranker | 1.00 | 0.77 | 0.97 | 0.67 | 0.50 | 6 |
| no_routing | 0.97 | 0.92 | 0.97 | 0.89 | 0.86 | 1 |

- All 3 out-of-corpus questions refused in every config (refusal recall 1.0). All false
  refusals are cross-spec questions whose context lacks one side (LLM refuses although a
  partial answer was possible) → refusal precision < 1. Fallback rate 0 (Grok key invalid
  anyway).
- Real latency on CPU (`eval/results/latency.csv`): best 48 s mean (reranker 43.6 s, LLM
  2.5 s); no_reranker 2.0 s. Generation-table latencies exclude reranking (cached scores).
- Judge robustness: judge LLM now gets the 8,192-token budget and unparsable judgements are
  retried on resume (x-03 was initially unparsed).
- Per-minute limits are handled by 65 s cool-downs (`--cooldowns`, default 5); per-day
  limits stop the run, which resumes from the cache when re-launched.

## Open issues
- none

## Blocked / needs human
- **xAI key rejected**: `Incorrect API key provided` on both models.list and chat. Grok
  fallback and the Gemini-vs-Grok bonus cannot run until a valid `XAI_API_KEY` is set in `.env`.
- Test set validation (all 30 items `verified: false`) — see `eval/testset_review.md`.
