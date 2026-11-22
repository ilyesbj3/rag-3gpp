"""Generation evaluation: answers, citations, refusals, latency and LLM-judged faithfulness /
correctness for several ablation configs. Resumable: every answer and judgement is cached in
eval/results/raw/gen_<config>_<provider>.jsonl and skipped on re-run.

    python -m eval.run_generation_eval --provider gemini \
        --configs best,baseline,no_hybrid,no_reranker,no_routing

Faithfulness / correctness use an LLM judge with a fixed 0 / 0.5 / 1 rubric
(`eval.metrics.JUDGE_TEMPLATE`), judged by Gemini. RAGAS is not used: its Gemini integration
needs extra LangChain packages that are not part of the approved stack (see PROGRESS.md).
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import statistics
import sys
import time
from pathlib import Path
from typing import Any

from eval.configs import CONFIGS, describe, overrides_for
from eval.metrics import (
    PRELIMINARY,
    RAW_DIR,
    RESULTS_DIR,
    TESTSET_PATH,
    citation_metrics,
    is_preliminary,
    judge_answer,
    load_testset,
    mean,
    refusal_scores,
    run_metadata,
)
from eval.run_retrieval_eval import CachedReranker
from src.config import load_settings
from src.generation.llm import build_llm
from src.generation.prompts import build_user_prompt
from src.pipeline import RAGPipeline
from src.schemas import Answer

log = logging.getLogger(__name__)


class QuotaExhausted(RuntimeError):
    pass


SFX = ""  # output suffix for bonus experiments (--tag)


def cache_path(config: str, provider: str) -> Path:
    return RAW_DIR / f"gen_{config}_{provider}{SFX}.jsonl"


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {r["id"]: r for r in rows}


def save_cache(path: Path, rows: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows.values():
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def run_config(
    name: str,
    provider: str,
    items,
    base: RAGPipeline,
    reranker,
    judge_llm,
    sleep_s: float,
    judge: bool,
) -> dict[str, dict[str, Any]]:
    path = cache_path(name, provider)
    rows = load_cache(path)
    llm = None
    overrides = {**overrides_for(name)}
    if provider == "ollama":  # local model (bonus): not part of the Gemini -> Grok chain
        from src.generation.local_llm import build_local_llm

        llm = build_local_llm(base.settings.llm.temperature, base.settings.llm.max_tokens)
    else:
        overrides["llm"] = {"provider": provider}
    pipe = RAGPipeline(
        base.settings,
        llm=llm,
        overrides=overrides,
        dense=base.dense,
        sparse=base.sparse,
        rerank_fn=reranker,
    )
    for it in items:
        row = rows.get(it["id"])
        if row is None:
            try:
                ans = pipe.answer(it["question"])
            except RuntimeError as e:  # all retries failed (quota / rate limit)
                save_cache(path, rows)
                raise QuotaExhausted(f"{name}/{it['id']}: {e}") from e
            row = {
                "id": it["id"],
                "type": it["type"],
                "question": it["question"],
                "answer": ans.model_dump(mode="json"),
                "metrics": citation_metrics(ans, it),
            }
            rows[it["id"]] = row
            save_cache(path, rows)
            if ans.llm_provider:
                time.sleep(sleep_s)
        if judge and (row.get("judge") or {}).get("correctness") is None:
            ans = Answer.model_validate(row["answer"])
            context = build_user_prompt(it["question"], ans.sources) if ans.sources else ""
            try:
                row["judge"] = judge_answer(judge_llm, it, ans.text, context)
            except RuntimeError as e:
                save_cache(path, rows)
                raise QuotaExhausted(f"judge {name}/{it['id']}: {e}") from e
            save_cache(path, rows)
            time.sleep(sleep_s)
    return rows


def summarize(name: str, provider: str, rows: dict[str, dict[str, Any]], items) -> dict:
    ids = [it["id"] for it in items]
    rs = [rows[i] for i in ids if i in rows]
    flat = []
    for r in rs:
        a = r["answer"]
        flat.append(
            {
                "type": r["type"],
                "refused": a["refused"],
                "total_s": a["timings"].get("total", 0.0),
                "fallback": a["fallback_used"],
                **r["metrics"],
                **{
                    k: v
                    for k, v in r.get("judge", {}).items()
                    if k in ("faithfulness", "correctness")
                },
            }
        )
    inc = [f for f in flat if f["type"] != "out_of_corpus"]
    lat = sorted(f["total_s"] for f in flat)

    def vals(key, rows_):
        return [f[key] for f in rows_ if f.get(key) is not None]

    models = sorted({r["answer"].get("llm_model") for r in rs if r["answer"].get("llm_model")})
    out = {
        "config": name,
        "description": describe(name),
        "provider": provider,
        "llm_models": ";".join(models),
        "n": len(flat),
        "n_expected": len(items),
        "faithfulness": mean(vals("faithfulness", flat)),
        "correctness": mean(vals("correctness", flat)),
        "correctness_in_corpus": mean(vals("correctness", inc)),
        "citation_accuracy": mean(vals("citation_accuracy", inc)),
        "citation_accuracy_loose": mean(vals("citation_accuracy_loose", inc)),
        "gold_citation_recall": mean(vals("gold_cited", inc)),
        "not_grounded_rate": mean([f["not_grounded"] for f in inc if not f["refused"]]),
        **refusal_scores(flat),
        "latency_mean_s": round(statistics.fmean(lat), 2) if lat else None,
        "latency_p95_s": round(lat[int(0.95 * (len(lat) - 1))], 2) if lat else None,
        "fallback_rate": mean([float(f["fallback"]) for f in flat]),
    }
    return out


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(description="Generation evaluation (resumable)")
    ap.add_argument("--provider", choices=["gemini", "groq", "grok", "ollama"], default="gemini")
    ap.add_argument("--configs", default="best,baseline,no_hybrid,no_reranker,no_routing")
    ap.add_argument("--judge-provider", choices=["gemini", "groq", "grok"], default="gemini")
    ap.add_argument("--no-judge", action="store_true")
    ap.add_argument("--sleep", type=float, default=6.0, help="pause between LLM calls (s)")
    ap.add_argument("--limit", type=int, help="only the first N items (debug)")
    ap.add_argument("--cooldowns", type=int, default=5, help="65 s waits on rate limits")
    ap.add_argument("--testset", type=Path, default=TESTSET_PATH)
    ap.add_argument("--tag", default="", help="suffix for output files (bonus experiments)")
    ap.add_argument("--embedding-model", help="override embedding.model (index must exist)")
    args = ap.parse_args(argv)
    names = list(CONFIGS) if args.configs == "all" else args.configs.split(",")

    global SFX
    SFX = f"_{args.tag}" if args.tag else ""
    emb = {"embedding": {"model": args.embedding_model}} if args.embedding_model else None
    settings = load_settings(emb)
    items = load_testset(args.testset)
    items = items[: args.limit] if args.limit else items
    base = RAGPipeline(settings)
    reranker = CachedReranker(settings.reranker.model, settings.reranker.max_length)
    judge_llm = (
        None
        if args.no_judge
        else build_llm(force=args.judge_provider, temperature=0, max_tokens=settings.llm.max_tokens)
    )

    summaries, stopped = [], None
    for name in names:
        print(f"[{name}] {describe(name)} with {args.provider} ...", flush=True)
        for attempt in range(args.cooldowns + 1):
            try:
                rows = run_config(
                    name,
                    args.provider,
                    items,
                    base,
                    reranker,
                    judge_llm,
                    args.sleep,
                    not args.no_judge,
                )
                break
            except QuotaExhausted as e:
                reranker.save()
                if attempt < args.cooldowns:  # per-minute quota: wait and resume
                    print(
                        f"   rate limited ({str(e).splitlines()[0]}); cooling down 65 s", flush=True
                    )
                    time.sleep(65)
                    continue
                stopped = str(e).splitlines()[0]
                print(f"   STOPPED (quota/rate limit): {stopped}")
                rows = load_cache(cache_path(name, args.provider))
        reranker.save()
        s = summarize(name, args.provider, rows, items)
        summaries.append(s)
        print(
            f"   n={s['n']}/{s['n_expected']} faith {s['faithfulness']} corr "
            f"{s['correctness']} cit_acc {s['citation_accuracy']} refusal_f1 "
            f"{s['refusal_f1']} lat {s['latency_mean_s']}s"
        )
        if stopped:
            break

    out = RESULTS_DIR / f"generation_{args.provider}{SFX}.csv"
    existing = {}
    if out.exists():
        with out.open(encoding="utf-8") as fh:
            existing = {r["config"]: r for r in csv.DictReader(fh)}
    for s in summaries:
        existing[s["config"]] = s
    keys: list[str] = []
    for r in existing.values():
        keys += [k for k in r if k not in keys]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(existing.values())
    meta = run_metadata(
        settings,
        {
            "provider": args.provider,
            "judge_provider": args.judge_provider,
            "configs": names,
            "stopped": stopped,
            "status": PRELIMINARY if is_preliminary(items) else "validated",
            "judge": "LLM-as-judge, rubric 0/0.5/1 (eval/metrics.py JUDGE_TEMPLATE)",
        },
    )
    (RESULTS_DIR / f"generation_{args.provider}{SFX}_meta.json").write_text(
        json.dumps(meta, indent=1), encoding="utf-8"
    )
    print(f"Wrote {out}" + (f" (stopped early: {stopped})" if stopped else ""))
    return 2 if stopped else 0


if __name__ == "__main__":
    sys.exit(main())
