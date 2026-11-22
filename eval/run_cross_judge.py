"""Cross-judging: every answer set judged by every judge, to measure self-preference bias.

    python -m eval.run_cross_judge --judge groq      # judge both answer sets with Groq
    python -m eval.run_cross_judge --judge gemini    # ... with Gemini
    python -m eval.run_cross_judge --report-only     # just rebuild eval/results/cross_judge.csv

Answer sets are FROZEN copies of `raw/gen_<config>_<provider>.jsonl` taken the first time
this script runs (`raw/crossjudge/answers_<config>_<provider>.jsonl`), so later evaluation
re-runs never change what is being judged and answers are never regenerated. Judgements are
cached per (answer model, judge model) in `raw/crossjudge/judge_<config>_<answers>__<judge>.jsonl`;
runs resume after rate limits. The judge prompt is the same rubric as the main evaluation
(`eval.metrics.JUDGE_TEMPLATE`).
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from eval.metrics import (
    PRELIMINARY,
    RAW_DIR,
    RESULTS_DIR,
    is_preliminary,
    judge_answer,
    load_testset,
    mean,
    refusal_scores,
)
from src.config import load_settings
from src.generation.llm import build_llm, retry_after_seconds
from src.generation.prompts import build_user_prompt
from src.schemas import Answer

CJ_DIR = RAW_DIR / "crossjudge"
ANSWER_SETS = ("gemini", "groq")


def frozen_answers(config: str, provider: str) -> dict[str, dict[str, Any]]:
    """Freeze (once) and load an answer set."""
    CJ_DIR.mkdir(parents=True, exist_ok=True)
    frozen = CJ_DIR / f"answers_{config}_{provider}.jsonl"
    if not frozen.exists():
        src = RAW_DIR / f"gen_{config}_{provider}.jsonl"
        if not src.exists():
            return {}
        shutil.copyfile(src, frozen)
    rows = [json.loads(x) for x in frozen.read_text(encoding="utf-8").splitlines() if x]
    return {r["id"]: r for r in rows}


def judge_path(config: str, answers: str, judge: str) -> Path:
    return CJ_DIR / f"judge_{config}_{answers}__{judge}.jsonl"


def load_judgements(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    return {
        json.loads(x)["id"]: json.loads(x)
        for x in path.read_text(encoding="utf-8").splitlines()
        if x
    }


def save_judgements(path: Path, rows: dict[str, dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows.values():
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def seed_from_main_run(config: str, answers: str, judge: str, ans: dict) -> None:
    """The main evaluation already judged its own answers: reuse those judgements when the
    judge provider is the answer provider (same rubric, same model)."""
    path = judge_path(config, answers, judge)
    if path.exists() or answers != judge:
        return
    rows = {}
    for qid, r in ans.items():
        j = r.get("judge") or {}
        if j.get("correctness") is not None:
            rows[qid] = {"id": qid, **j}
    if rows:
        save_judgements(path, rows)


def run_judge(
    config: str, judge: str, sleep_s: float, cooldowns: int, max_hours: float = 8.0
) -> None:
    deadline = time.time() + max_hours * 3600  # daily token quotas free up gradually
    settings = load_settings()
    items = {it["id"]: it for it in load_testset()}
    llm = build_llm(force=judge, temperature=0, max_tokens=settings.llm.max_tokens)
    for answers in ANSWER_SETS:
        ans = frozen_answers(config, answers)
        if not ans:
            print(f"[{answers}] no answer set yet, skipped")
            continue
        seed_from_main_run(config, answers, judge, ans)
        path = judge_path(config, answers, judge)
        done = load_judgements(path)
        print(f"[{answers} answers × {judge} judge] {len(done)}/{len(ans)} cached", flush=True)
        for qid, row in ans.items():
            prev = done.get(qid) or {}
            if prev.get("correctness") is not None or prev.get("skipped"):
                continue
            a = Answer.model_validate(row["answer"])
            context = build_user_prompt(a.question, a.sources) if a.sources else ""
            for attempt in range(cooldowns + 1):
                try:
                    done[qid] = {"id": qid, **judge_answer(llm, items[qid], a.text, context)}
                    break
                except RuntimeError as e:
                    if "413" in str(e) or "too large" in str(e).lower():
                        done[qid] = {"id": qid, "skipped": "request too large for the judge"}
                        break
                    wait = retry_after_seconds(str(e)) or 65.0
                    if attempt == cooldowns or time.time() + wait > deadline:
                        save_judgements(path, done)
                        print(f"   STOPPED at {qid}: {str(e).splitlines()[0]}")
                        return
                    print(f"   {qid}: rate limited, waiting {wait:.0f} s", flush=True)
                    time.sleep(wait + 1)
            save_judgements(path, done)
            time.sleep(sleep_s)
        print(
            f"   done: {sum(1 for r in done.values() if r.get('correctness') is not None)}"
            f"/{len(ans)}"
        )


def answer_metrics(ans: dict[str, dict[str, Any]]) -> dict[str, Any]:
    inc = [r for r in ans.values() if r["type"] != "out_of_corpus"]
    flat = [{"type": r["type"], "refused": r["answer"]["refused"]} for r in ans.values()]
    return {
        "model": next(
            (r["answer"]["llm_model"] for r in ans.values() if r["answer"].get("llm_model")), None
        ),
        "n": len(ans),
        "citation_accuracy": mean(
            [
                r["metrics"]["citation_accuracy"]
                for r in inc
                if r["metrics"]["citation_accuracy"] is not None
            ]
        ),
        "gold_citation_recall": mean(
            [r["metrics"]["gold_cited"] for r in inc if r["metrics"]["gold_cited"] is not None]
        ),
        **refusal_scores(flat),
    }


def common_ids(config: str) -> set[str]:
    """Questions answered by both models and judged by both judges (fair 2x2 comparison)."""
    sets = []
    for answers in ANSWER_SETS:
        for judge in ("gemini", "groq"):
            j = load_judgements(judge_path(config, answers, judge))
            sets.append({k for k, v in j.items() if v.get("correctness") is not None})
    return set.intersection(*sets) if sets else set()


def report(config: str) -> list[dict[str, Any]]:
    rows = []
    common = common_ids(config)
    for answers in ANSWER_SETS:
        ans = frozen_answers(config, answers)
        if not ans:
            continue
        am = answer_metrics(ans)
        for judge in ("gemini", "groq"):
            j = load_judgements(judge_path(config, answers, judge))
            vals = [
                v
                for k, v in j.items()
                if v.get("correctness") is not None and (not common or k in common)
            ]
            rows.append(
                {
                    "config": config,
                    "answers": answers,
                    "answer_model": am["model"],
                    "judge": judge,
                    "judge_model": next((v.get("judge_model") for v in vals), None),
                    "n_judged": len(vals),
                    "n_common": len(common),
                    "n_answers": am["n"],
                    "faithfulness": mean(
                        [v["faithfulness"] for v in vals if v.get("faithfulness") is not None]
                    ),
                    "correctness": mean([v["correctness"] for v in vals]),
                    **{
                        k: am[k]
                        for k in (
                            "citation_accuracy",
                            "gold_citation_recall",
                            "refusal_precision",
                            "refusal_recall",
                            "refusal_f1",
                            "false_refusals",
                        )
                    },
                }
            )
    out = RESULTS_DIR / "cross_judge.csv"
    if rows:
        with out.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        meta = {
            "status": PRELIMINARY if is_preliminary(load_testset()) else "validated",
            "note": "answer sets frozen in eval/results/raw/crossjudge/",
        }
        (RESULTS_DIR / "cross_judge_meta.json").write_text(
            json.dumps(meta, indent=1), encoding="utf-8"
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--judge", choices=["gemini", "groq"])
    ap.add_argument("--config", default="best")
    ap.add_argument("--sleep", type=float, default=4.0)
    ap.add_argument("--cooldowns", type=int, default=200)
    ap.add_argument("--max-hours", type=float, default=8.0, help="total waiting budget")
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args(argv)
    if args.judge and not args.report_only:
        run_judge(args.config, args.judge, args.sleep, args.cooldowns, args.max_hours)
    for r in report(args.config):
        print(
            f"  {r['answers']:6s} answers × {r['judge']:6s} judge: n={r['n_judged']}/"
            f"{r['n_answers']} faith={r['faithfulness']} corr={r['correctness']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
