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
- RRF k = 60, top 30 fused candidates.

## 8. Reranker and routing
- bge-reranker-v2-m3 cross-encoder (sigmoid score) → reorder; best score drives the gate.
- Rule-based router (NAS signals vs architecture signals, explicit spec mentions, cross
  phrases) + ≥2 chunks per spec for cross questions. Router accuracy: exact route 10/10
  simple 23.501, 9/10 simple 24.501, but only 1/7 cross questions routed to both specs.

## 9. Generation, citations, refusal
- System prompt rules (English, only sources, cite labels, exact refusal).
- `<source label="[TS 24.501 §A.1]">` blocks; citation check removes unknown citations and
  flags ungrounded answers; score gate refuses before calling the LLM.

## 10. LLM layer
- Gemini primary → Grok fallback (retry with backoff on transient errors, immediate fallback
  on permanent ones); provider/model recorded per answer.
- Practical constraints met: free-tier flash models allow 20 requests/day → evaluation on
  `gemini-3.5-flash-lite`; Gemini 3.x thinking tokens share the output budget →
  `max_tokens` 8192; resumable evaluation cache with rate-limit cool-downs.

## 11. Demo
- Screenshots of the Streamlit app: answer with citation badges, sources panel with scores,
  toggles, refusal box.

## 12. Evaluation setup
- 30 questions: 20 simple (10 per spec), 7 cross-spec, 3 out-of-corpus; gold sections found
  in the chunks; hit = gold clause or sub-clause.
- 8 retrieval configurations (hybrid × reranker × routing); generation on 5 configurations.

## 13. Results (preliminary — gold set pending human validation)
- Chart: `figures/retrieval_ablation.png`. Key rows (R@5 / MRR): best 0.852 / 0.734;
  dense + reranker (no_hybrid) 0.926 / 0.790; no_reranker 0.815 / 0.622; baseline (dense
  only) 0.889 / 0.677. Simple questions R@5 = 1.0; cross questions R@5 = 0.43.
- Chart: `figures/generation_gemini.png` (gemini-3.5-flash-lite, LLM judge): best —
  faithfulness 0.97, correctness 0.88, citation accuracy 0.98, refusal F1 0.75 (3/3
  out-of-corpus refused, 2 false refusals on cross questions); no_reranker correctness 0.77,
  6 false refusals.
- Gate calibration chart `figures/gate_max_rerank.png`: OOC ≤ 0.20 vs in-corpus ≥ 0.66 →
  threshold 0.45; dense cosine cannot separate (`figures/gate_max_dense.png`).
- Latency (CPU): 48 s with reranker (43.6 s reranking), 2 s without.

## 14. Analysis
- Reranker = biggest gain (MRR +0.11, correctness +0.11) and the only reliable refusal
  signal; it also reduces false refusals because better context reaches the LLM.
- Structural chunks + contextual headers make simple questions easy (R@5 = 1.0).
- BM25 helps exact identifiers without reranker, but crowds the reranker's 30 slots when
  fused → dense + reranker is best here; a separate candidate pool per retriever is the fix.
- Routing filters look-alike clauses on simple questions but under-routes cross questions
  (NAS vocabulary dominates) → cross-spec questions are the main failure mode.
- Citation checker: citation accuracy ≥ 0.97 in every config; no ungrounded answers.

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
