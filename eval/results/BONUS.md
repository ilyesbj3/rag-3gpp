# Bonus experiments

> All numbers are *preliminary — gold set pending human validation* (same unverified test set as REPORT.md). Generation runs use gemini-3.5-flash-lite unless stated otherwise.

## 1. French questions → English answers (bge-m3)

The 30 questions were translated to French (`eval/testset_fr.json`, same gold labels). bge-m3 and bge-reranker-v2-m3 are multilingual; the BM25 tokenizer is not, so a variant translates the question to English for BM25 only (`retrieval.translate_query_for_bm25`, one LLM call per question; translator = gemini-3.1-flash-lite, because the gemini-3.5-flash-lite daily quota was used up).

### Retrieval — *preliminary — gold set pending human validation*

| Run | Config | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| English questions | best | 0.704 | 0.815 | 0.852 | 0.747 |
| English questions | no_hybrid | 0.778 | 0.852 | 0.926 | 0.817 |
| English questions | no_reranker | 0.481 | 0.815 | 0.889 | 0.622 |
| English questions | baseline | 0.556 | 0.889 | 0.926 | 0.677 |
| French questions | best | 0.704 | 0.889 | 0.963 | 0.785 |
| French questions | no_hybrid | 0.778 | 0.926 | 0.963 | 0.836 |
| French questions | no_reranker | 0.407 | 0.778 | 0.778 | 0.528 |
| French questions | baseline | 0.518 | 0.889 | 0.926 | 0.650 |
| French + BM25 query translation | best | 0.704 | 0.889 | 0.926 | 0.776 |
| French + BM25 query translation | no_reranker | 0.370 | 0.741 | 0.889 | 0.531 |

### Generation (config `best`)

| Run | Config | LLM | n | Faithfulness | Correctness | Citation acc. | Gold cited | Refusal F1 | False refusals | Latency (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| English questions | best | gemini-3.5-flash-lite | 30/30 | 1.00 | 0.80 | 0.97 | 0.74 | 0.50 | 6 | 4.0 |
| French questions | best | gemini-3.5-flash-lite | 30/30 | 1.00 | 0.87 | 0.94 | 0.78 | 0.60 | 4 | 1.9 |

Answers in English (function-word heuristic): **23/23** non-refused answers to French questions.

## 2. Embedding models: bge-m3 vs bge-small-en-v1.5

Same chunks, same BM25 and reranker; only the dense model changes (*preliminary — gold set pending human validation*). `baseline` = dense only.

| Run | Config | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| bge-m3 (1024-d) | best | 0.704 | 0.815 | 0.852 | 0.747 |
| bge-m3 (1024-d) | no_hybrid | 0.778 | 0.852 | 0.926 | 0.817 |
| bge-m3 (1024-d) | baseline | 0.556 | 0.889 | 0.926 | 0.677 |
| bge-small-en-v1.5 (384-d) | baseline | 0.481 | 0.815 | 0.963 | 0.616 |
| bge-small-en-v1.5 (384-d) | no_hybrid | 0.667 | 0.889 | 1.000 | 0.771 |
| bge-small-en-v1.5 (384-d) | best | 0.667 | 0.889 | 1.000 | 0.759 |

Indexing time on CPU: bge-small-en-v1.5: 318 s (build incl. BM25), bge-m3: 4422 s embeddings (phase 4)

## 3. LLM comparison: Gemini (API) vs Llama 3.2 3B (local, Ollama)

Same retrieval (`best`, identical sources thanks to the cache), same prompt; the judge is gemini-3.5-flash-lite for both. Grok could not be compared: the xAI key was rejected (see PROGRESS.md). *preliminary — gold set pending human validation*

| Run | Config | LLM | n | Faithfulness | Correctness | Citation acc. | Gold cited | Refusal F1 | False refusals | Latency (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| API | best | gemini-3.5-flash-lite | 30/30 | 1.00 | 0.80 | 0.97 | 0.74 | 0.50 | 6 | 4.0 |
| local | best | llama3.2-3b-8k | 30/30 | 0.82 | 0.77 | 0.71 | 0.59 | 1.00 | 0 | 17.7 |

## 4. Adding TS 23.502 (procedures)

Corpus extended with TS 23.502 V18.14.0 (`configs/rel18_3specs.yaml`, 5,216 chunks). The router only knows the two original specs, so the comparison uses configurations without routing. Gold labels only cover TS 23.501 / TS 24.501, so retrieval recall measures how much TS 23.502 *displaces* gold chunks; generation shows whether the procedure text helps the answers. *preliminary — gold set pending human validation*

### Retrieval

| Run | Config | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| TS 23.501 + TS 24.501 | no_routing | 0.593 | 0.852 | 0.889 | 0.691 |
| TS 23.501 + TS 24.501 | reranker_only | 0.704 | 0.889 | 0.926 | 0.785 |
| + TS 23.502 | no_routing | 0.630 | 0.889 | 0.926 | 0.725 |
| + TS 23.502 | reranker_only | 0.667 | 0.926 | 0.963 | 0.769 |

Cross questions: on average **1.7 of 6** sources come from TS 23.502.

### Generation

| Run | Config | LLM | n | Faithfulness | Correctness | Citation acc. | Gold cited | Refusal F1 | False refusals | Latency (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| 3 specs | no_routing | gemini-3.5-flash-lite | 30/30 | 0.98 | 0.90 | 0.94 | 0.81 | 0.75 | 2 | 2.1 |

Per question type (R@5): simple-23: 0.800 → 1.000; simple-24: 1.000 → 1.000; cross: 0.714 → 0.571

## 5. Release 17 vs Release 18

Same pipeline (`best`) on TS 23.501 V17.15.0 + TS 24.501 V17.18.1 (`configs/rel17.yaml`, 3,033 chunks vs 3,597 in Rel-18). Reference answers were written from Rel-18, so a lower correctness can be a *real release difference*, not an error. *preliminary — gold set pending human validation*

| Run | Config | R@1 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|
| Rel-18 | best | 0.704 | 0.815 | 0.852 | 0.747 |
| Rel-17 | best | 0.630 | 0.815 | 0.852 | 0.709 |

| Run | Config | LLM | n | Faithfulness | Correctness | Citation acc. | Gold cited | Refusal F1 | False refusals | Latency (s) |
|---|---|---|---|---|---|---|---|---|---|---|
| Rel-18 | best | gemini-3.5-flash-lite | 30/30 | 1.00 | 0.80 | 0.97 | 0.74 | 0.50 | 6 | 4.0 |
| Rel-17 | best | gemini-3.5-flash-lite | 30/30 | 1.00 | 0.83 | 1.00 | 0.78 | 0.60 | 4 | 5.0 |

Side-by-side answers where the two releases differ: [`rel17_vs_rel18_examples.md`](rel17_vs_rel18_examples.md).

Questions whose judged correctness changed (Rel-18 → Rel-17): `x-02` 0.0 → 0.5, `x-04` 0.0 → 1.0, `x-06` 1.0 → 0.5

