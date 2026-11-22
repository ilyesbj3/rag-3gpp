"""Real end-to-end latency (no reranker cache) on a few test questions, per configuration.

    python -m eval.measure_latency [--n 5] [--configs best,no_reranker]

The generation evaluation reuses cached reranker scores, so its latency column excludes the
cross-encoder compute; this script measures the latency a user of the app actually sees.
Writes eval/results/latency.csv.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import sys

from eval.configs import describe, overrides_for, parse_sets
from eval.metrics import RESULTS_DIR, load_testset
from src.config import load_settings
from src.pipeline import RAGPipeline


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--configs", default="best,no_reranker")
    ap.add_argument("--provider", default="gemini", choices=["gemini", "groq", "grok"])
    ap.add_argument("--tag", default="", help="suffix for the output file")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE", help="settings override")
    args = ap.parse_args(argv)

    settings = load_settings(parse_sets(args.set) or None)
    items = [it for it in load_testset() if it["type"] != "out_of_corpus"][: args.n]
    base = RAGPipeline(settings)
    base.warmup()  # the app loads the models at startup; do not time the first load
    rows = []
    for name in args.configs.split(","):
        pipe = RAGPipeline(
            settings,
            overrides={**overrides_for(name), "llm": {"provider": args.provider}},
            dense=base.dense,
            sparse=base.sparse,
        )
        totals, parts = [], {"dense": [], "sparse": [], "rerank": [], "llm": []}
        for it in items:
            ans = pipe.answer(it["question"])
            totals.append(ans.timings["total"])
            for k in parts:
                parts[k].append(ans.timings.get(k, 0.0))
        rec = {
            "config": name,
            "description": describe(name),
            "n": len(totals),
            "model": ans.llm_model,
            "reranker_model": settings.reranker.model,
            "reranker_max_length": settings.reranker.max_length,
            "fused_top_n": settings.retrieval.fused_top_n,
            "total_mean_s": round(statistics.fmean(totals), 1),
            "total_max_s": round(max(totals), 1),
            **{f"{k}_mean_s": round(statistics.fmean(v), 2) for k, v in parts.items()},
        }
        rows.append(rec)
        print(rec)
    out = RESULTS_DIR / f"latency{'_' + args.tag if args.tag else ''}.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
