"""Retrieval evaluation (no LLM): recall@k / MRR for every ablation + router accuracy + gate
calibration.

    python -m eval.run_retrieval_eval --all-ablations
    python -m eval.run_retrieval_eval --configs best,baseline

Outputs (eval/results/): retrieval_ablation.csv, router_accuracy.csv, gate_calibration.csv,
gate_choice.json, raw/retrieval_<config>.json. Reranker scores are cached in
raw/rerank_cache.json so that configs sharing candidates (and re-runs) are cheap on CPU.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from eval.configs import CONFIGS, describe, overrides_for
from eval.metrics import (
    K_VALUES,
    PRELIMINARY,
    RAW_DIR,
    RESULTS_DIR,
    TESTSET_PATH,
    is_preliminary,
    load_testset,
    mean,
    retrieval_metrics,
    run_metadata,
    validate_gold,
)
from src.config import load_settings
from src.ingest.chunker import load_chunks
from src.pipeline import RAGPipeline
from src.retrieval.reranker import rerank as model_rerank
from src.schemas import RetrievedChunk

log = logging.getLogger(__name__)
RERANK_CACHE = RAW_DIR / "rerank_cache.json"
THRESHOLDS = [round(0.05 * i, 2) for i in range(13)]  # 0.00 .. 0.60


class CachedReranker:
    """Wraps the cross-encoder with a persistent (question, chunk_id) -> score cache."""

    def __init__(self, model: str, max_length: int):
        self.model, self.max_length = model, max_length
        self.cache: dict[str, float] = {}
        if RERANK_CACHE.exists():
            self.cache = json.loads(RERANK_CACHE.read_text(encoding="utf-8"))

    def key(self, q: str, rc: RetrievedChunk) -> str:
        return f"{self.model}||{q}||{rc.chunk.chunk_id}"

    def __call__(self, q: str, cands: list[RetrievedChunk]) -> list[RetrievedChunk]:
        todo = [rc for rc in cands if self.key(q, rc) not in self.cache]
        if todo:
            model_rerank(q, todo, self.model, self.max_length)
            for rc in todo:
                self.cache[self.key(q, rc)] = float(rc.rerank_score or 0.0)
        for rc in cands:
            rc.rerank_score = self.cache[self.key(q, rc)]
        return sorted(cands, key=lambda r: -(r.rerank_score or 0.0))

    def save(self) -> None:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        RERANK_CACHE.write_text(json.dumps(self.cache), encoding="utf-8")


def group_of(item: dict[str, Any]) -> str:
    if item["type"] == "simple":
        return "simple-23" if item["gold_specs"] == ["TS 23.501"] else "simple-24"
    return item["type"]


def evaluate_config(name: str, base: RAGPipeline, reranker: CachedReranker, items) -> dict:
    pipe = RAGPipeline(
        base.settings,
        overrides=overrides_for(name),
        dense=base.dense,
        sparse=base.sparse,
        rerank_fn=reranker,
    )
    rows = []
    for it in items:
        res = pipe.retrieve_full(it["question"])
        ranked = [(rc.chunk.spec, rc.chunk.section) for rc in res.candidates[:10]]
        row = {
            "id": it["id"],
            "type": it["type"],
            "group": group_of(it),
            "route": sorted(res.route.specs),
            "route_reason": res.route.reason,
            "gold_specs": it["gold_specs"],
            "top10": [f"{sp} §{sec}" for sp, sec in ranked],
            "max_rerank": max((c.rerank_score or 0.0 for c in res.candidates), default=None)
            if CONFIGS[name][1]
            else None,
            "max_dense": max(
                (c.dense_score for c in res.candidates if c.dense_score is not None), default=None
            ),
            "timings": res.timings,
        }
        if it["type"] != "out_of_corpus":
            row.update(retrieval_metrics(ranked, it))
        rows.append(row)
        reranker.save()
    return {"config": name, "description": describe(name), "rows": rows}


def aggregate(result: dict) -> list[dict[str, Any]]:
    rows = [r for r in result["rows"] if r["type"] != "out_of_corpus"]
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups[r["group"]].append(r)
    h, rr, t = CONFIGS[result["config"]]
    out = []
    for g in ("all", "simple-23", "simple-24", "cross"):
        rs = groups.get(g, [])
        rec: dict[str, Any] = {
            "config": result["config"],
            "hybrid": h,
            "reranker": rr,
            "routing": t,
            "group": g,
            "n": len(rs),
        }
        for k in K_VALUES:
            rec[f"recall@{k}"] = mean([r[f"recall@{k}"] for r in rs])
        rec["mrr"] = mean([r["mrr"] for r in rs])
        if g == "cross":
            for k in K_VALUES:
                rec[f"both_recall@{k}"] = mean([r[f"both_recall@{k}"] for r in rs])
        out.append(rec)
    return out


def router_accuracy(result: dict) -> dict[str, Any]:
    rows = [r for r in result["rows"] if r["type"] != "out_of_corpus"]
    sup = [set(r["route"]) >= set(r["gold_specs"]) for r in rows]
    exact = [set(r["route"]) == set(r["gold_specs"]) for r in rows]
    by = defaultdict(list)
    for r, s, e in zip(rows, sup, exact, strict=True):
        by[r["group"]].append((s, e))
    rec = {
        "config": result["config"],
        "n": len(rows),
        "route_superset": mean(sup),
        "route_exact": mean(exact),
    }
    for g, v in by.items():
        rec[f"exact_{g}"] = mean([e for _, e in v])
    return rec


def calibrate(rows: list[dict], score_key: str) -> tuple[list[dict], float | None]:
    """Sweep thresholds: refusal TPR on out-of-corpus vs false-refusal rate in-corpus.
    Choice: max TPR subject to zero false refusals; ties -> middle of the feasible range."""
    ooc = [r[score_key] for r in rows if r["type"] == "out_of_corpus"]
    inc = [r[score_key] for r in rows if r["type"] != "out_of_corpus"]
    table = []
    for th in THRESHOLDS:
        tpr = mean([float(s < th) for s in ooc])
        frr = mean([float(s < th) for s in inc])
        table.append(
            {"score": score_key, "threshold": th, "refusal_tpr": tpr, "false_refusal_rate": frr}
        )
    feasible = [t for t in table if t["false_refusal_rate"] == 0]
    if not feasible:
        return table, None
    best_tpr = max(t["refusal_tpr"] for t in feasible)
    cands = [t["threshold"] for t in feasible if t["refusal_tpr"] == best_tpr]
    return table, cands[len(cands) // 2]


def write_csv(path, rows: list[dict]) -> None:
    keys: list[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Retrieval ablation evaluation")
    ap.add_argument("--all-ablations", action="store_true")
    ap.add_argument("--configs", default="best,baseline,no_hybrid,no_reranker,no_routing")
    ap.add_argument("--testset", type=Path, default=TESTSET_PATH, help="test set JSON")
    ap.add_argument("--tag", default="", help="suffix for output files (bonus experiments)")
    ap.add_argument("--embedding-model", help="override embedding.model (index must exist)")
    args = ap.parse_args(argv)
    names = list(CONFIGS) if args.all_ablations else args.configs.split(",")
    sfx = f"_{args.tag}" if args.tag else ""

    overrides = {"embedding": {"model": args.embedding_model}} if args.embedding_model else None
    settings = load_settings(overrides)
    items = load_testset(args.testset)
    problems = validate_gold(items, load_chunks())
    if problems:
        print("Gold sections missing from chunks:", problems)
        return 1
    base = RAGPipeline(settings)
    reranker = CachedReranker(settings.reranker.model, settings.reranker.max_length)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    all_rows, routers, results = [], [], {}
    for name in names:
        print(f"[{name}] {describe(name)} ...", flush=True)
        res = evaluate_config(name, base, reranker, items)
        res["meta"] = run_metadata(
            settings,
            {"config": name, "status": PRELIMINARY if is_preliminary(items) else "validated"},
        )
        (RAW_DIR / f"retrieval_{name}{sfx}.json").write_text(
            json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8"
        )
        results[name] = res
        agg = aggregate(res)
        all_rows += agg
        routers.append(router_accuracy(res))
        a = agg[0]
        print(
            f"   R@1 {a['recall@1']:.3f}  R@5 {a['recall@5']:.3f}  R@10 {a['recall@10']:.3f}"
            f"  MRR {a['mrr']:.3f}"
        )

    write_csv(RESULTS_DIR / f"retrieval_ablation{sfx}.csv", all_rows)
    write_csv(RESULTS_DIR / f"router_accuracy{sfx}.csv", routers)
    if sfx:  # bonus runs do not recalibrate the gate
        print(f"Wrote {RESULTS_DIR / f'retrieval_ablation{sfx}.csv'}")
        return 0

    calib_rows, choice = [], {}
    if "best" in results:
        t, c = calibrate(results["best"]["rows"], "max_rerank")
        calib_rows += t
        choice["reranker_threshold"] = c
    dense_cfg = (
        "no_reranker"
        if "no_reranker" in results
        else next((n for n in results if not CONFIGS[n][1]), None)
    )
    if dense_cfg:
        t, c = calibrate(results[dense_cfg]["rows"], "max_dense")
        calib_rows += t
        choice["dense_threshold"] = c
    if calib_rows:
        write_csv(RESULTS_DIR / "gate_calibration.csv", calib_rows)
        (RESULTS_DIR / "gate_choice.json").write_text(
            json.dumps(
                {
                    **choice,
                    "status": PRELIMINARY if is_preliminary(items) else "validated",
                    "rule": "max refusal TPR with zero false refusals; ties -> middle threshold",
                },
                indent=1,
            ),
            encoding="utf-8",
        )
        print("gate choice:", choice)
    meta = run_metadata(
        settings,
        {"configs": names, "status": PRELIMINARY if is_preliminary(items) else "validated"},
    )
    (RESULTS_DIR / "retrieval_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"Wrote {RESULTS_DIR / 'retrieval_ablation.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
