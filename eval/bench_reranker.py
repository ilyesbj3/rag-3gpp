"""Reranker speed/quality benchmark: fused_top_n × max_length (× reranker model).

    python -m eval.bench_reranker                       # bge-reranker-v2-m3, 15/20/30 × 512/1024
    python -m eval.bench_reranker --models BAAI/bge-reranker-v2-m3,BAAI/bge-reranker-base

For every combination, MRR / recall@5 are computed on the in-corpus test questions with the
`best` configuration (scores cached in raw/rerank_cache.json, so top-15/20 reuse the top-30
scores), and the reranking latency per answer is measured WITHOUT cache on a fixed sample of
questions. Writes eval/results/reranker_bench.csv.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys
import time

from eval.configs import overrides_for
from eval.metrics import RESULTS_DIR, load_testset, mean, retrieval_metrics
from eval.run_retrieval_eval import CachedReranker
from src.config import load_settings
from src.pipeline import RAGPipeline
from src.retrieval.reranker import rerank as model_rerank


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--models", default="BAAI/bge-reranker-v2-m3")
    ap.add_argument("--top-n", default="15,20,30")
    ap.add_argument("--max-length", default="512,1024")
    ap.add_argument("--latency-sample", type=int, default=6, help="questions timed per combo")
    args = ap.parse_args(argv)

    settings = load_settings()
    items = [it for it in load_testset() if it["type"] != "out_of_corpus"]
    sample = items[:: max(1, len(items) // args.latency_sample)][: args.latency_sample]
    base = RAGPipeline(settings, overrides={"retrieval": {"use_reranker": False}})
    # fused candidates (top 30, best config without reranking) computed once per question
    fused = {it["id"]: base.retrieve_full(it["question"]).candidates for it in items}
    nonrerank = []
    for it in sample:
        t = base.retrieve_full(it["question"]).timings
        nonrerank.append(sum(v for k, v in t.items() if k != "rerank"))

    rows = []
    for model in args.models.split(","):
        for ml in [int(x) for x in args.max_length.split(",")]:
            cache = CachedReranker(model, ml)
            for top_n in [int(x) for x in args.top_n.split(",")]:
                pipe = RAGPipeline(
                    settings,
                    overrides={
                        **overrides_for("best"),
                        "retrieval": {**overrides_for("best")["retrieval"], "fused_top_n": top_n},
                        "reranker": {"model": model, "max_length": ml},
                    },
                    dense=base.dense,
                    sparse=base.sparse,
                    rerank_fn=cache,
                )
                mets = []
                for it in items:
                    cands = pipe.retrieve_full(it["question"]).candidates
                    ranked = [(c.chunk.spec, c.chunk.section) for c in cands[:10]]
                    mets.append(retrieval_metrics(ranked, it))
                cache.save()
                lat = []
                for it in sample:  # uncached timing on fresh copies of the candidates
                    cands = [c.model_copy() for c in fused[it["id"]][:top_n]]
                    t0 = time.perf_counter()
                    model_rerank(it["question"], cands, model, ml)
                    lat.append(time.perf_counter() - t0)
                rec = {
                    "model": model,
                    "fused_top_n": top_n,
                    "max_length": ml,
                    "mrr": mean([m["mrr"] for m in mets]),
                    "recall@5": mean([m["recall@5"] for m in mets]),
                    "recall@10": mean([m["recall@10"] for m in mets]),
                    "rerank_s_mean": round(statistics.fmean(lat), 1),
                    "rerank_s_max": round(max(lat), 1),
                    "retrieval_s_mean": round(
                        statistics.fmean(lat) + statistics.fmean(nonrerank), 1
                    ),
                }
                rows.append(rec)
                print(rec, flush=True)
    out = RESULTS_DIR / "reranker_bench.csv"
    if out.exists():  # keep rows of other combinations (e.g. another reranker model)
        with out.open(encoding="utf-8") as fh:
            keep = [
                r
                for r in csv.DictReader(fh)
                if (r["model"], int(r["fused_top_n"]), int(r["max_length"]))
                not in {(x["model"], x["fused_top_n"], x["max_length"]) for x in rows}
            ]
        rows = keep + rows
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
