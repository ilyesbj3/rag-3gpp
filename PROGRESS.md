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
| 11 | README + presentation + architecture | done | docs |
| 12 | Bonuses | done (Rel-17 generation partial) | feat(bonus) |

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

## Phase 11 — docs
- README: install (lock file), `.env`, corpus, Docker / local Qdrant, build time, app, eval,
  results tables (preliminary), re-run instructions, choices, limitations, perspectives,
  references. `docs/architecture.md` (mermaid offline/online diagrams + module map),
  `docs/presentation_outline.md` (16 slides with numbers). Makefile and CLAUDE.md §15
  commands synced.

## Phase 12 — bonuses (results in `eval/results/BONUS.md`, preliminary)
- Infrastructure: corpus variants via `RAG_CONFIG=configs/<name>.yaml` (own processed/,
  index/, Qdrant collection, VERSIONS_<name>.md; main index untouched); system prompt names
  the corpus specs/release from config (verbatim prompt for the default corpus); reranker
  cache keys include a text hash for variants; variant builds reuse main-index embeddings of
  byte-identical chunks; `--testset/--tag/--embedding-model/--translate-bm25/
  --allow-missing-gold` options on the eval scripts; local LLM provider via Ollama's
  OpenAI-compatible API (`src/generation/local_llm.py`, no new dependency).
- B1 French (`eval/testset_fr.json`, same gold): retrieval MRR best 0.785, no_hybrid 0.836,
  no_reranker 0.528, baseline 0.650 (EN: 0.734 / 0.790 / 0.622 / 0.677) → bge-m3 + reranker
  are robust to French; BM25 is the weak part. Generation best: correctness 0.87,
  faithfulness 1.0, citation acc. 0.94. Translated-BM25 run hit the 15 requests/min limit of
  flash-lite; eval now pre-translates once with pacing → re-run pending.
- B3: Grok impossible (invalid key) → API vs local instead: gemini-3.5-flash-lite vs
  `llama3.2:3b` via Ollama (local variant `llama3.2-3b-8k` created with num_ctx 8192 because
  prompts are ~5k tokens).
- B4/B5 corpora downloaded and chunked (acceptance checks pass): TS 23.502 V18.14.0
  (`23502-ie0.zip`, 1,619 chunks; 3-spec corpus 5,216 chunks); Rel-17 TS 23.501 V17.15.0
  (`23501-hf0.zip`) + TS 24.501 V17.18.1 (`24501-hi1.zip`), 3,033 chunks. Provenance in
  `data/VERSIONS_rel18_3specs.md` and `data/VERSIONS_rel17.md`.
- B1 French translated-BM25 (translator gemini-3.1-flash-lite, flash-lite quota used up):
  MRR best 0.776 / no_reranker 0.531 vs 0.785 / 0.528 untranslated → no gain; generation
  (best, French): correctness 0.87, 23/23 non-refused answers in English.
- B2 bge-small-en-v1.5: indexing 318 s vs 4,422 s; dense-only MRR 0.616 vs 0.677 (bge-m3);
  with reranker 0.759–0.771 vs 0.734–0.790 → the reranker hides most of the gap.
- B3 Gemini (API) vs llama3.2-3b-8k (local, CPU): faithfulness 0.97 vs 0.82, correctness 0.88
  vs 0.77, citation accuracy 0.98 vs 0.71, refusal F1 0.75 vs 1.00, 2 s vs 18 s per answer.
- B4 + TS 23.502 (no routing): MRR 0.762 → 0.725 (reranker_only 0.795 → 0.769), cross R@5
  0.71 → 0.57 for original gold; ~1.7/6 sources from 23.502 on cross questions; generation
  correctness 0.92 → 0.90. Index build reused 3,597 embeddings, computed 1,619.
- B5 Rel-17: retrieval MRR 0.731 vs 0.734; all Rel-18 gold sections also exist in Rel-17.
  Generation **partial (6/30)**: gemini-3.5-flash-lite daily quota (500 requests/day)
  exhausted. Resume: `RAG_CONFIG=configs/rel17.yaml python -m eval.run_generation_eval
  --provider gemini --tag rel17 --configs best` then `python -m eval.make_bonus_report`.

## Follow-up round (after phase 12) — status
1. Cross-judging — infra done (`eval/run_cross_judge.py`, frozen answer sets in
   `eval/results/raw/crossjudge/`, judgements cached per (answer model, judge model)).
   Groq `best` answers generated with **router v1** (env `RAG_RETRIEVAL__ROUTER_VERSION=1`) so
   they match the frozen Gemini answers; Groq-judge passes next; Gemini-judge pass on the
   Groq answers after the Gemini daily reset.
2. Rate limits — done: `ProviderError.retry_after` from the Retry-After header or the error
   text; FallbackLLM sleeps that long, or moves on when it exceeds `max_wait_s` (90 s, e.g.
   daily quotas). Unit tests with fake providers and a fake 429. The web API maps a
   rate-limited chain failure to 502 "Rate limit reached, try again in about a minute".
3. Web UI — done (`feat(ui)`): FastAPI + static frontend per UI_SPEC.md; acceptance run in
   headless Edge via the DevTools protocol: **24/24 checks pass** (empty state, chips →
   source flash, gate refusal with below-gate candidates, toggles → config/badge/score line,
   forced Groq, real Gemini-quota fallback badge + pill, removed-citation box, no horizontal
   scroll at 1440/1024/390 px, Tab order, evaluation page + preliminary banner, no console
   errors / CSP violations). Screenshots in `docs/screenshots/`. Streamlit removed.
   Dependencies added as approved by the spec: fastapi 0.165.0, uvicorn 0.54.0 (httpx was
   already present); vendored marked 12.0.2 + DOMPurify 3.1.6.
5. Router v2 — rules done, tuned only on `tests/test_router.py` (12 new cross questions +
   6 guards; v1 got 5/12 cross, v2 12/12). `retrieval.router_version` (1|2) keeps v1
   reproducible (v1 reproduces all 30 stored routes). Eval re-run pending (with the new
   reranker default).
4. Reranker latency — done. Benchmark (`eval/results/reranker_bench.csv`, router v2, MRR on
   27 questions, rerank seconds per answer on this CPU):

| Reranker | top_n | max_len | MRR | R@5 | rerank s |
|---|---|---|---|---|---|
| v2-m3 | 30 | 1024 (old default) | 0.734 | 0.852 | 43.8 |
| v2-m3 | 15 | 512 | 0.754 | 0.852 | 12.8 |
| v2-m3 | 20 | 1024 | 0.756 | 0.852 | 27.9 |
| base | 15 | 512 (**new default**) | 0.747 | 0.815 | **3.9** |
| base | 30 | 512 | 0.727 | 0.852 | 7.6 |

   Rule "fastest with MRR ≥ old − 0.02": v2-m3 alone could not get under 10 s, so
   bge-reranker-base (allowed by the task) was benchmarked and chosen: 15 candidates, 512
   tokens. Trade-offs: R@5 −1 question; not multilingual (French bonus used v2-m3); gate
   recalibrated to **0.10** (base scores: OOC 0.001/0.05/0.266 vs in-corpus min 0.145 → the
   OSPF question cannot be separated at the gate without a false refusal; 2/3 refused by the
   gate, the third must be refused by the LLM).
   Retrieval re-run (router v2 + new reranker): best MRR 0.747, no_hybrid 0.817,
   reranker_only 0.785, no_routing 0.691; non-reranker configs unchanged.
5. Router v2 on the eval set (same reranker, only `router_version` differs): exact route
   0.741 → 0.778, cross questions routed to both specs 1/7 → 2/7; retrieval metrics
   identical (the extra both-spec route did not add a gold hit in the top 10). Cross-spec
   retrieval remains the main failure mode.
- Groq free tier also has a daily token cap (200k tokens/day per model, rolling): Groq
  answered 24/30 (6 prompts > 8k tokens are rejected outright, HTTP 413); the Groq-judge
  pass trickles as the daily window frees up (`run_cross_judge --max-hours`).
- Gemini daily quota (500/day flash-lite) exhausted until ~09:00; post-reset chain queued
  (Rel-17 with new defaults, Gemini judge on Groq answers, 5-config generation re-run,
  latency, reports).
6. False-refusal breakdown — done in REPORT.md: all 15 false refusals across the 5
   generation configs were LLM refusals (gate scores 0.63–0.995); the gate refused none.
7. Statistical caution — done in REPORT.md (paired bootstrap, n = 27, 1 question = 0.037).
   Robust: reranker effect with dense-only retrieval (MRR +0.118, CI [+0.010, +0.232]) and
   the *negative* effect of BM25 fusion when the reranker is on (MRR −0.056, CI [−0.115,
   −0.010]). The reranker with everything else on (+0.112) has a CI touching 0
   ([−0.016, +0.243]); all other differences are within noise.
- Generation cache now regenerates answers whose settings (incl. router version, reranker
  length/top-n) differ from the current run — prevents stale numbers after default changes.

### Follow-up round — final state
- Generation re-run with the new defaults: best / baseline / no_hybrid done (best
  correctness 0.80, faithfulness 1.00, citation accuracy 0.97); no_reranker / no_routing
  pending (Gemini 500/day quota, partly spent twice because a stopped chain left a process
  waiting on the same probe — both produced valid answers with identical settings).
  The complete previous-defaults run is kept (`generation_gemini_router_v1.csv`).
- best correctness 0.88 → 0.80 with the faster reranker: 5 questions refused by the LLM
  because a key chunk dropped out of the top 6 (s23-01 lost §6.2.1, s23-07 the 5QI-1 row),
  2 improved; paired Δ −0.08, CI [−0.23, +0.05]. Documented as a speed/quality trade-off;
  switching back is a one-line config change.
- Real latency (warm, CPU): best 7.6 s per answer (rerank 4.1 s, LLM 3.3 s, measured with
  gemini-3.1-flash-lite because the flash-lite quota was spent); no_reranker 3.0 s.
- Groq answer set: 27/30 (x-05 rejected as too large / daily cap, x-06 and x-07 pending the
  Groq daily token window; o-01..o-03 refused at the gate). My earlier note "6 prompts too
  large" was wrong: only x-05 got HTTP 413; the run then stopped.
- Cross-judge: Gemini judge done on all frozen answers; Groq judge limited by 200k tokens/day
  (~1 judgement / 40 min) → 2×2 currently on 9 common questions; the pass keeps running
  (`python -m eval.run_cross_judge --judge groq`, resumable).
- Rel-17 bonus re-run with the current defaults: 30/30 (MRR 0.709 vs 0.747 Rel-18;
  correctness 0.83 vs 0.80).
- Bonus sections 1–4 now compare against reference rows produced with the same (previous)
  settings.

## Second follow-up round (2026-11-22) — status
- **Test set**: the message said the set was validated, but `eval/testset.json` is unchanged
  since 2026-11-21 and all 30 items are still `verified: false` (no other copy found). Every
  number stays labelled preliminary; nothing was marked verified by me.
- Groq judge pass of the previous round stopped (it was judging an answer set the new
  defaults make obsolete); its cached judgements are kept in `raw/crossjudge/`.
- Code: `retrieval.routing_mode` hard|soft (+ `soft_routing_weight` 1.5),
  `retrieval.bm25_weight` (weighted RRF), `llm.prompt_version` (v2 = rule 4 refuses only when
  no source is relevant), recorded in every result file (`config_snapshot`, `run_metadata`);
  `--set key=value` in the eval CLIs; `--round` for cross-judge; `data_variant` so a settings
  profile (`configs/fast.yaml`) reuses the main index; stale-row-free generation summaries;
  `retry_after_seconds` now parses hours (`retry in 18h46m25s` was read as 46 min).
- Retrieval grid (v2-m3 and base, 15 / 512, hard/soft × BM25 w 1.0/0.5/0.25): chosen
  defaults by MRR = soft routing, BM25 w 0.5, hybrid on (ties no_hybrid at 0.807).
  All differences within bootstrap noise. Justification in REPORT.md.
- `--all-ablations` re-run with the new defaults: best MRR 0.807, R@5 0.889; gate
  recalibrated for v2-m3 @512: reranker 0.40 (out-of-corpus max 0.13, in-corpus min 0.66),
  dense 0.55 (thin margin). Base reranker gate for the fast profile: 0.15.
- Gemini: the daily quota was already exhausted after 1 answer (resets ≈ 09:00 local,
  2026-11-23). Generation (a) v2-m3, (b) base, (c) ablations resume then.
- Groq answers for the final best config running in the background (daily token cap).

## Open issues
- Cross-spec questions are the main failure mode (routing + retrieval), see REPORT.md.
- Rel-17 generation bonus partial (quota) — resumable.

## Blocked / needs human
- **Test set validation**: all 30 items `verified: false` (`eval/testset_review.md`); every
  reported number is preliminary until then.
- **Gemini free-tier quota** (500 requests/day for gemini-3.5-flash-lite): finish the
  generation table with
  `python -m eval.run_generation_eval --provider gemini --configs no_reranker,no_routing`
  then `python -m eval.make_report` (≈ 120 requests).
- **Groq free-tier daily token cap** (200k tokens/day for openai/gpt-oss-120b): the Groq
  judge pass and the last Groq answers (x-06, x-07) trickle in; resume with
  `python -m eval.run_cross_judge --judge groq` and the Groq generation command in the README.
- **xAI Grok**: needs a real `xai-` key in `XAI_API_KEY` (the earlier key was a Groq key).
- **Test set file**: please check that your validated `eval/testset.json` was saved in this
  repository (the current file has no `verified: true` item).
