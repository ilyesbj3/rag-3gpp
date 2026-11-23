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
- Weighted RRF k = 60 (dense 1, BM25 0.5); the top 15 fused candidates go to the reranker.
- Finding: at full weight BM25 pushes keyword-only matches into the reranker's 15-slot pool
  (MRR 0.750); weight 0.5 → 0.807, which ties dense + reranker (`no_hybrid`, 0.807). Hybrid is
  kept for exact identifiers (timers, cause numbers); the difference is within noise.

## 8. Reranker and routing
- Cross-encoder reranker; its best score drives the refusal gate (threshold 0.40: out-of-
  corpus max 0.13, in-corpus min 0.66 → 3/3 refused before the LLM, 0 false refusals).
- Only robust ranking gain: MRR +0.16 with everything else on (95% CI [+0.06, +0.26]).
- CPU benchmark (`eval/results/reranker_bench.csv`): bge-reranker-v2-m3 with 30 candidates ×
  1,024 tokens = 43.8 s per answer → 15 × 512 = 12.8 s, same MRR. bge-reranker-base (3.9 s)
  was tried as default but answer correctness fell 0.88 → 0.80 → kept only as the fast demo
  profile (`configs/fast.yaml`).
- Soft routing: search both specs, boost the routed spec 1.5× in RRF → MRR 0.807 vs 0.770
  for hard filtering (cross MRR 0.59 vs 0.46): a wrong route no longer hides the other spec.
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
- Retrieval (`figures/retrieval_ablation.png`), final defaults, R@5 / MRR: best 0.889 /
  0.807; no_hybrid 0.889 / 0.807; no_reranker 0.889 / 0.648; no_routing 0.889 / 0.770;
  baseline (dense only) 0.889 / 0.677. Simple questions R@5 = 1.0; cross questions 0.57.
- Generation (`figures/generation_gemini.png`, gemini-3.5-flash-lite answers + judge, 30
  questions × 5 configs, one run): best faithfulness 1.00, correctness 0.97, citation
  accuracy 0.98, refusal F1 1.00, 0 false refusals; no_reranker 0.90 / 0.94 / 0.86;
  baseline 0.90 / 0.99 / 0.86.
- All 3 out-of-corpus questions refused by the score gate before the LLM (scores 0.003–0.13
  vs ≥ 0.66 in corpus).
- Cross-judge 2×2 (Gemini vs Groq answers × Gemini vs Groq judges), on an earlier frozen
  answer set (router v1) and only 9 common questions (Groq daily token cap): judge gaps
  ≤ 0.06, no consistent self-preference (table in REPORT.md).
- Latency (CPU): ≈ 13 s of reranking with v2-m3; fast profile (bge-reranker-base) 7.6 s per
  answer end to end; 3.0 s without the reranker.

## 14. Analysis
- Reranker = the only robust ranking gain (MRR +0.16, CI [+0.06, +0.26]) and the refusal
  signal; removing it costs the most in generation (correctness −0.07, citation acc. −0.04).
- Prompt v2 (answer the covered part, refuse only if nothing is relevant) + v2-m3 reranker:
  false refusals 6 → 0 in `best` compared with the previous round.
- Structural chunks + contextual headers make simple questions easy (R@5 = 1.0).
- BM25 must be down-weighted (0.5) so it does not crowd the reranker's 15-candidate pool.
- Cross-spec questions: still the weak spot (both remaining partial answers are cross
  questions) → query decomposition per spec is the next step.
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
