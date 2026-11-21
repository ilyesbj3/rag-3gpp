# Evaluation report

> **Status: preliminary — gold set pending human validation.** 30/30 test items are not yet validated by a human (`eval/testset_review.md`). All tables below are preliminary.

## Setup

- Corpus: TS 23.501 V18.12.0 (Rel-18), TS 24.501 V18.14.0 (Rel-18) — see `data/VERSIONS.md`
- Embeddings: `BAAI/bge-m3` · reranker: `BAAI/bge-reranker-v2-m3` · vector DB: Qdrant (cosine) · BM25: bm25s + telecom tokenizer · RRF k = 60
- Retrieval: dense top 50, BM25 top 50, fused top 30, final top-k 6, ≥2 chunks per spec for cross routes
- Test set: 30 questions (20 simple, 7 cross, 3 out-of-corpus); retrieval metrics on the 27 in-corpus questions, top-10 ranking after fusion/rerank; a hit is the gold section or one of its sub-clauses, same spec
- Retrieval run: 2026-11-21 20:51 UTC, commit `49b110c`

Configurations: `best` = hybrid on, reranker on, routing on; `no_hybrid` = hybrid off, reranker on, routing on; `no_reranker` = hybrid on, reranker off, routing on; `no_routing` = hybrid on, reranker on, routing off; `hybrid_only` = hybrid on, reranker off, routing off; `reranker_only` = hybrid off, reranker on, routing off; `routing_only` = hybrid off, reranker off, routing on; `baseline` = hybrid off, reranker off, routing off

## Retrieval

### Retrieval ablation — all in-corpus questions (n=27) — *preliminary — gold set pending human validation*

| Config | Hybrid | Reranker | Routing | R@1 | R@3 | R@5 | R@10 | MRR |
|---|---|---|---|---|---|---|---|---|
| best | ✓ | ✓ | ✓ | 0.667 | 0.778 | 0.852 | 0.926 | 0.734 |
| no_hybrid | ✗ | ✓ | ✓ | 0.704 | 0.852 | 0.926 | 0.963 | 0.790 |
| no_reranker | ✓ | ✗ | ✓ | 0.481 | 0.704 | 0.815 | 0.889 | 0.622 |
| no_routing | ✓ | ✓ | ✗ | 0.667 | 0.852 | 0.926 | 0.963 | 0.762 |
| hybrid_only | ✓ | ✗ | ✗ | 0.407 | 0.667 | 0.778 | 0.889 | 0.574 |
| reranker_only | ✗ | ✓ | ✗ | 0.704 | 0.926 | 0.926 | 0.963 | 0.795 |
| routing_only | ✗ | ✗ | ✓ | 0.630 | 0.852 | 0.889 | 0.926 | 0.730 |
| baseline | ✗ | ✗ | ✗ | 0.556 | 0.815 | 0.889 | 0.926 | 0.677 |

### Per question type (R@5 / MRR) — *preliminary — gold set pending human validation*

| Config | simple-23 R@5 | simple-24 R@5 | cross R@5 | simple-23 MRR | simple-24 MRR | cross MRR | cross both-spec R@5 | cross both-spec R@10 |
|---|---|---|---|---|---|---|---|---|
| best | 1.000 | 1.000 | 0.429 | 0.787 | 0.870 | 0.465 | 0.000 | 0.000 |
| no_hybrid | 1.000 | 1.000 | 0.714 | 0.792 | 0.950 | 0.559 | 0.000 | 0.000 |
| no_reranker | 0.800 | 0.900 | 0.714 | 0.717 | 0.623 | 0.486 | 0.000 | 0.000 |
| no_routing | 1.000 | 1.000 | 0.714 | 0.792 | 0.870 | 0.566 | 0.143 | 0.143 |
| hybrid_only | 0.800 | 0.900 | 0.571 | 0.625 | 0.625 | 0.427 | 0.143 | 0.143 |
| reranker_only | 1.000 | 1.000 | 0.714 | 0.800 | 0.950 | 0.568 | 0.143 | 0.286 |
| routing_only | 0.900 | 1.000 | 0.714 | 0.796 | 0.792 | 0.548 | 0.000 | 0.000 |
| baseline | 0.900 | 1.000 | 0.714 | 0.679 | 0.792 | 0.512 | 0.143 | 0.286 |

![retrieval ablation](figures/retrieval_ablation.png)

### Router accuracy — *preliminary — gold set pending human validation*

| n | route ⊇ gold specs | exact | exact simple-23 | exact simple-24 | exact cross |
|---|---|---|---|---|---|
| 27 | 0.778 | 0.741 | 1.000 | 0.900 | 0.143 |

### Score-gate calibration — *preliminary — gold set pending human validation*

Rule: max refusal TPR with zero false refusals; ties -> middle threshold. Chosen: reranker_threshold = **0.45**, dense_threshold = **0.25** (recorded in `config.yaml`).

| threshold | refusal TPR (out-of-corpus) | false-refusal rate |
|---|---|---|
| 0.0 | 0.000 | 0.000 |
| 0.05 | 0.333 | 0.000 |
| 0.1 | 0.667 | 0.000 |
| 0.15 | 0.667 | 0.000 |
| 0.2 | 0.667 | 0.000 |
| 0.25 | 1.000 | 0.000 |
| 0.3 | 1.000 | 0.000 |
| 0.35 | 1.000 | 0.000 |
| 0.4 | 1.000 | 0.000 |
| 0.45 | 1.000 | 0.000 |
| 0.5 | 1.000 | 0.000 |
| 0.55 | 1.000 | 0.000 |
| 0.6 | 1.000 | 0.000 |

![gate max_rerank](figures/gate_max_rerank.png)

| threshold | refusal TPR (out-of-corpus) | false-refusal rate |
|---|---|---|
| 0.0 | 0.000 | 0.000 |
| 0.05 | 0.000 | 0.000 |
| 0.1 | 0.000 | 0.000 |
| 0.15 | 0.000 | 0.000 |
| 0.2 | 0.000 | 0.000 |
| 0.25 | 0.000 | 0.000 |
| 0.3 | 0.000 | 0.000 |
| 0.35 | 0.000 | 0.000 |
| 0.4 | 0.000 | 0.000 |
| 0.45 | 0.000 | 0.000 |
| 0.5 | 0.000 | 0.000 |
| 0.55 | 0.333 | 0.037 |
| 0.6 | 1.000 | 0.148 |

![gate max_dense](figures/gate_max_dense.png)

## Generation

_Generation evaluation not run yet._

## Failure analysis

**Retrieval misses (config `best`, no gold section in top-5): 4**

- `x-01` gold TS 23.501 §5.3.2; TS 24.501 §5.5.1.2 — route TS 23.501, TS 24.501; top-3 retrieved: TS 24.501 §4.4.2.5, TS 24.501 §5.3.1.1, TS 24.501 §4.4.2.5; R@10 = 0.0
- `x-02` gold TS 23.501 §5.6.1; TS 24.501 §6.4.1 — route TS 24.501; top-3 retrieved: TS 24.501 §6.1.1, TS 24.501 §4.2, TS 24.501 §6.2.18; R@10 = 0.0
- `x-04` gold TS 23.501 §5.3.2.3; TS 24.501 §5.3.7, §10.2 — route TS 23.501; top-3 retrieved: TS 23.501 §5.4.1.1, TS 23.501 §5.3.2.4, TS 23.501 §5.4.1.3; R@10 = 1.0
- `x-07` gold TS 23.501 §5.10.1, §6.2.1; TS 24.501 §5.4.1, §5.4.2 — route TS 24.501; top-3 retrieved: TS 24.501 §4.4.2.1.1, TS 24.501 §4.4.2.5, TS 24.501 §4.4.2.5; R@10 = 1.0

