# Presentation outline (≈15 slides)

Charts come from `eval/results/figures/`, tables from `eval/results/REPORT.md`. All numbers
are **preliminary until the test set is validated** — re-run `make report` and refresh the
slides after validation.

## 1. Title
- "RAG chatbot for 3GPP 5G specifications" — INSAT, Futurs Réseaux Mobiles, RT5 2026/2027.
- Author, instructor (Dr Mériem Afif), date.

## 2. Context and problem
- 3GPP specs are huge: TS 23.501 alone is ~11,400 paragraphs and TS 24.501 ~18,200 paragraphs
  with 541 tables (our parse).
- Engineers need precise, citable answers (timers, cause values, IEs, procedures).
- Plain LLMs hallucinate clause numbers and values → we need grounding and refusal.

## 3. Objectives
- English answers grounded only in TS 23.501 V18.12.0 + TS 24.501 V18.14.0.
- Citation `[TS x §y]` on every fact; exact refusal sentence when out of corpus.
- Measurable: retrieval recall/MRR, faithfulness, correctness, citation accuracy, refusals.

## 4. Corpus
- Complementarity: 23.501 = Stage 2 architecture (NFs, reference points, QoS, slicing);
  24.501 = Stage 3 NAS (5GMM/5GSM procedures, messages, IEs, timers, cause values).
- Versions pinned, SHA-256 recorded (`data/VERSIONS.md`).

## 5. Architecture
- Diagram: `docs/architecture.md` (offline indexing + online answering).

## 6. Ingestion and structural chunking
- Parser findings: custom `H6`/`H2` heading styles, clause numbers with letter suffixes
  (`5.35A.1`), annex titles with line breaks, a clause number repeated in the spec
  (24.501 §8.2.6.35).
- One chunk per clause, ≤800 tokens, 100-token overlap; tables to Markdown, split only by rows
  with repeated header; contextual header line.
- Numbers: 3,597 chunks (1,281 / 2,316), median 482 / 616 tokens; acceptance checks pass.
- Show one chunk example (cause #9 in §A.1, timer table §10.2).

## 7. Hybrid retrieval + RRF
- Dense bge-m3 (1024-d, Qdrant cosine) + BM25 with telecom tokenizer (`cause_9`, `t3510`,
  `s-nssai`/`snssai`, section numbers).
- RRF k = 60; the top 15 fused candidates go to the reranker.
- Finding: with the reranker on, BM25 fusion *lowers* MRR (−0.07, 95% CI excludes 0): BM25
  candidates take slots in the small reranker pool. Dense + reranker is the best retrieval.

## 8. Reranker and routing
- Cross-encoder reranker; its best score drives the refusal gate (calibrated threshold).
- CPU benchmark (`figures`/table from `eval/results/reranker_bench.csv`): bge-reranker-v2-m3
  with 30 candidates × 1,024 tokens = 43.8 s per answer; bge-reranker-base with 15 × 512 =
  3.9 s, MRR 0.747 vs 0.734 → new default (end-to-end 48 s → 7.6 s). Trade-off: answer
  correctness of `best` 0.88 → 0.80 (−0.08, CI [−0.23, +0.05]: not established, but 5
  questions lost a key chunk).
- Rule-based router v2 (architecture AND NAS signals → both; "procedure … messages" → both),
  tuned only on `tests/test_router.py` (12 new cross-spec questions): exact route 0.74 →
  0.78, cross questions routed to both 1/7 → 2/7; retrieval unchanged → cross-spec remains
  the weak spot.

## 9. Generation, citations, refusal
- System prompt rules (English, only sources, cite labels, exact refusal).
- `<source label="[TS 24.501 §A.1]">` blocks; citation check removes unknown citations and
  flags ungrounded answers; score gate refuses before calling the LLM.

## 10. LLM layer
- Chain Gemini → Groq → Grok (providers without a key are skipped); on HTTP 429 the client
  waits for the API's Retry-After, then falls back; provider/model recorded per answer.
- Free-tier reality: Gemini flash 20 req/day, flash-lite 500 req/day; Groq 8k tokens/min and
  200k tokens/day; prompts > 8k tokens rejected by Groq (413) → resumable, cached evaluation.
- Gemini 3.x thinking tokens share the output budget → `max_tokens` 8192.

## 11. Demo
- Web app (FastAPI + static HTML/CSS/JS, `UI_SPEC.md`): screenshots
  `docs/screenshots/chat.png`, `refusal.png`, `evaluation.png`, `chat_390.png`.
- Citation chips open and highlight the source; refusal card says whether the gate or the
  LLM refused; fallback badge "answered by Groq"; settings sidebar; evaluation page.
- Acceptance checklist verified in headless Edge: 24/24 checks.

## 12. Evaluation setup
- 30 questions: 20 simple (10 per spec), 7 cross-spec, 3 out-of-corpus; gold sections found
  in the chunks; hit = gold clause or sub-clause.
- 8 retrieval configurations (hybrid × reranker × routing); generation on 5 configurations.

## 13. Results (preliminary — gold set pending human validation)
- Retrieval (`figures/retrieval_ablation.png`), current defaults, R@5 / MRR: best 0.815 /
  0.747; dense + reranker (no_hybrid) 0.852 / 0.817; no_reranker 0.815 / 0.622; baseline
  (dense only) 0.889 / 0.677. Simple questions R@5 = 1.0; cross questions ≈ 0.4.
- Generation (`figures/generation_gemini.png`, gemini-3.5-flash-lite answers + judge): best
  faithfulness 1.00, correctness 0.80, citation accuracy 0.97; all 3 out-of-corpus questions
  refused; all false refusals are LLM refusals (gate refused none), mostly cross questions.
- Cross-judge 2×2 (Gemini vs Groq answers × Gemini vs Groq judges) on the common judged
  questions: no self-preference larger than one question so far (table in REPORT.md).
- Latency (CPU): 7.6 s per answer (rerank 4.1 s, LLM 3.3 s), 3.0 s without the reranker.

## 14. Analysis
- Reranker = the only robust ranking gain (MRR +0.13 with everything else on) and the refusal
  signal; but its candidate pool size and model trade latency against answer quality.
- Structural chunks + contextual headers make simple questions easy (R@5 = 1.0).
- BM25 helps exact identifiers without reranker, but hurts in the reranker's small pool.
- Cross-spec questions: routing rules alone do not fix them; the LLM refuses half-covered
  questions → query decomposition per spec is the next step.
- Statistical caution: n = 27, one question = 0.037 of recall; most differences are noise.

## 15. Limits and perspectives
- Small, author-drafted test set (pending validation); LLM judge instead of RAGAS; figures as
  captions only; rule-based router; CPU latency.
- Bonuses done (table from `eval/results/BONUS.md`): French questions (bge-m3 + reranker
  robust: MRR 0.785 FR vs 0.734 EN, answers in English); bge-small-en (14× faster indexing,
  on par after reranking); Gemini API vs local Llama 3.2 3B (correctness 0.88 vs 0.77,
  citation accuracy 0.98 vs 0.71); + TS 23.502 (takes ~1.7/6 sources on cross questions, no
  gain without a 3-spec router); Rel-17 vs Rel-18 (retrieval equivalent).
- Next steps: router/query decomposition for cross-spec questions, separate candidate pools
  per retriever, GPU reranking, human-validated larger test set.

## 16. References
- Lewis et al. 2020 (RAG, arXiv:2005.11401); Robertson & Zaragoza 2009 (BM25); Chen et al.
  2024 (BGE M3, arXiv:2402.03216); Es et al. 2023 (RAGAS, arXiv:2309.15217).
