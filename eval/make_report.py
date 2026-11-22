"""Build eval/results/REPORT.md and PNG charts (eval/results/figures/) from the result files.

python -m eval.make_report
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from eval.configs import CONFIGS, describe  # noqa: E402
from eval.metrics import PRELIMINARY, RAW_DIR, RESULTS_DIR, is_preliminary, load_testset  # noqa: E402
from src.config import load_settings  # noqa: E402

FIG_DIR = RESULTS_DIR / "figures"
# Validated categorical order (dataviz reference palette, light mode).
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, INK2, MUTED, GRID, AXIS, SURFACE = (
    "#0b0b0b",
    "#52514e",
    "#898781",
    "#e1e0d9",
    "#c3c2b7",
    "#fcfcfb",
)


# ----------------------------------------------------------------------------- io
def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def f(v: Any, nd: int = 3) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "–"
    if x != x:  # NaN
        return "–"
    return f"{x:.{nd}f}"


def md_table(header: list[str], rows: list[list[str]]) -> list[str]:
    return [
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
        *["| " + " | ".join(r) + " |" for r in rows],
    ]


# ----------------------------------------------------------------------------- charts
def _style(ax, title: str) -> None:
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", color=INK, fontsize=12, pad=26)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def grouped_bars(
    path: Path,
    labels: list[str],
    series: dict[str, list[float]],
    title: str,
    subtitle: str,
    ymax: float = 1.0,
) -> None:
    n = len(series)
    width = 0.8 / n
    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=150)
    for i, (name, vals) in enumerate(series.items()):
        xs = [j + (i - (n - 1) / 2) * width for j in range(len(labels))]
        ax.bar(xs, vals, width=width * 0.9, color=SERIES[i], label=name, linewidth=0)
    ax.set_xticks(range(len(labels)), labels, rotation=0)
    ax.set_ylim(0, ymax)
    _style(ax, title)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=8, color=MUTED)
    ax.legend(
        frameon=False,
        ncol=n,
        loc="upper right",
        bbox_to_anchor=(1, 1.16),
        fontsize=9,
        labelcolor=INK2,
    )
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def calibration_chart(
    path: Path, rows: list[dict[str, str]], score: str, chosen: float | None, subtitle: str
) -> None:
    rs = [r for r in rows if r["score"] == score]
    if not rs:
        return
    th = [float(r["threshold"]) for r in rs]
    fig, ax = plt.subplots(figsize=(7.5, 4.2), dpi=150)
    tpr = [float(r["refusal_tpr"]) for r in rs]
    frr = [float(r["false_refusal_rate"]) for r in rs]
    ax.plot(th, tpr, color=SERIES[0], linewidth=2, marker="o", markersize=4)
    ax.plot(th, frr, color=SERIES[1], linewidth=2, marker="o", markersize=4)
    ax.text(
        th[-1] + 0.01, tpr[-1], "out-of-corpus refused (TPR)", color=INK2, fontsize=8, va="center"
    )
    ax.text(th[-1] + 0.01, frr[-1], "in-corpus refused (FRR)", color=INK2, fontsize=8, va="center")
    if chosen is not None:
        ax.axvline(chosen, color=MUTED, linewidth=1, linestyle="--")
        ax.text(chosen, 1.03, f"chosen {chosen:.2f}", color=INK2, fontsize=8, ha="center")
    ax.set_xlim(th[0] - 0.02, th[-1] + 0.25)
    ax.set_ylim(-0.03, 1.08)
    ax.set_xlabel(f"threshold on {score.replace('_', ' ')}", color=INK2, fontsize=9)
    _style(ax, f"Score-gate calibration ({score.replace('max_', '')} score)")
    ax.text(0, -0.2, subtitle, transform=ax.transAxes, fontsize=8, color=MUTED)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ----------------------------------------------------------------------------- sections
def retrieval_section(prelim: str) -> tuple[list[str], list[str]]:
    rows = read_csv(RESULTS_DIR / "retrieval_ablation.csv")
    if not rows:
        return ["_Retrieval evaluation not run yet._"], []
    allg = [r for r in rows if r["group"] == "all"]
    out = [f"### Retrieval ablation — all in-corpus questions (n={allg[0]['n']}) — *{prelim}*", ""]
    out += md_table(
        ["Config", "Hybrid", "Reranker", "Routing", "R@1", "R@3", "R@5", "R@10", "MRR"],
        [
            [
                r["config"],
                *("✓" if r[k] == "True" else "✗" for k in ("hybrid", "reranker", "routing")),
                f(r["recall@1"]),
                f(r["recall@3"]),
                f(r["recall@5"]),
                f(r["recall@10"]),
                f(r["mrr"]),
            ]
            for r in allg
        ],
    )
    out += ["", f"### Per question type (R@5 / MRR) — *{prelim}*", ""]
    groups = ["simple-23", "simple-24", "cross"]
    by = {(r["config"], r["group"]): r for r in rows}
    out += md_table(
        [
            "Config",
            *[f"{g} R@5" for g in groups],
            *[f"{g} MRR" for g in groups],
            "cross both-spec R@5",
            "cross both-spec R@10",
        ],
        [
            [
                c,
                *(f(by[(c, g)]["recall@5"]) for g in groups),
                *(f(by[(c, g)]["mrr"]) for g in groups),
                f(by[(c, "cross")].get("both_recall@5")),
                f(by[(c, "cross")].get("both_recall@10")),
            ]
            for c in [r["config"] for r in allg]
        ],
    )
    grouped_bars(
        FIG_DIR / "retrieval_ablation.png",
        [r["config"] for r in allg],
        {
            "Recall@1": [float(r["recall@1"]) for r in allg],
            "Recall@5": [float(r["recall@5"]) for r in allg],
            "MRR": [float(r["mrr"]) for r in allg],
        },
        "Retrieval quality per configuration",
        f"{prelim}; in-corpus questions, top-10 ranking after fusion/rerank",
    )
    summary = [r["config"] + f": R@5 {f(r['recall@5'])}, MRR {f(r['mrr'])}" for r in allg]
    return out, summary


def router_section(prelim: str) -> list[str]:
    rows = read_csv(RESULTS_DIR / "router_accuracy.csv")
    rows = [r for r in rows if CONFIGS.get(r["config"], (0, 0, 0))[2]]
    if not rows:
        return []
    r = rows[0]
    out = [f"### Router accuracy — *{prelim}*", ""]
    out += md_table(
        ["n", "route ⊇ gold specs", "exact", "exact simple-23", "exact simple-24", "exact cross"],
        [
            [
                r["n"],
                f(r["route_superset"]),
                f(r["route_exact"]),
                f(r.get("exact_simple-23")),
                f(r.get("exact_simple-24")),
                f(r.get("exact_cross")),
            ]
        ],
    )
    return out


def gate_section(prelim: str) -> list[str]:
    rows = read_csv(RESULTS_DIR / "gate_calibration.csv")
    choice_path = RESULTS_DIR / "gate_choice.json"
    if not rows or not choice_path.exists():
        return []
    choice = json.loads(choice_path.read_text(encoding="utf-8"))
    out = [
        f"### Score-gate calibration — *{prelim}*",
        "",
        f"Rule: {choice['rule']}. Chosen: reranker_threshold = "
        f"**{choice.get('reranker_threshold')}**, dense_threshold = "
        f"**{choice.get('dense_threshold')}** (recorded in `config.yaml`).",
        "",
    ]
    for score, key in (("max_rerank", "reranker_threshold"), ("max_dense", "dense_threshold")):
        rs = [r for r in rows if r["score"] == score]
        if rs:
            out += md_table(
                ["threshold", "refusal TPR (out-of-corpus)", "false-refusal rate"],
                [[r["threshold"], f(r["refusal_tpr"]), f(r["false_refusal_rate"])] for r in rs],
            )
            out.append("")
            calibration_chart(FIG_DIR / f"gate_{score}.png", rows, score, choice.get(key), prelim)
            out.append(f"![gate {score}](figures/gate_{score}.png)")
            out.append("")
    return out


def generation_section(
    provider: str, prelim: str, tag: str = "", label: str = ""
) -> tuple[list[str], list[str]]:
    rows = read_csv(RESULTS_DIR / f"generation_{provider}{tag}.csv")
    if not rows:
        return [f"_Generation evaluation ({provider}) not run yet._"], []
    meta_path = RESULTS_DIR / f"generation_{provider}_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    out = [
        f"### Generation{(' — ' + label) if label else ''} — provider `{provider}` "
        f"({rows[0].get('llm_models')}) — *{prelim}*",
        "",
    ]
    if meta.get("stopped"):
        out += [
            f"> Run stopped early (quota): {meta['stopped']}. Rows with n < "
            f"n_expected are partial; re-run the same command to resume.",
            "",
        ]
    out += md_table(
        [
            "Config",
            "n",
            "Faithfulness",
            "Correctness",
            "Citation acc.",
            "Citation acc. (loose)",
            "Gold cited",
            "Not grounded",
            "Refusal P",
            "Refusal R",
            "Refusal F1",
            "False refusals",
            "Latency mean (s)",
            "p95 (s)",
            "Fallback",
        ],
        [
            [
                r["config"],
                f"{r['n']}/{r['n_expected']}",
                f(r["faithfulness"], 2),
                f(r["correctness"], 2),
                f(r["citation_accuracy"], 2),
                f(r["citation_accuracy_loose"], 2),
                f(r["gold_citation_recall"], 2),
                f(r["not_grounded_rate"], 2),
                f(r["refusal_precision"], 2),
                f(r["refusal_recall"], 2),
                f(r["refusal_f1"], 2),
                f(r["false_refusals"], 0),
                f(r["latency_mean_s"], 1),
                f(r["latency_p95_s"], 1),
                f(r["fallback_rate"], 2),
            ]
            for r in rows
        ],
    )
    out += [
        "",
        "Faithfulness and correctness: LLM judge with a fixed 0 / 0.5 / 1 rubric "
        "(`eval/metrics.py`), judge = Gemini — **the same model that generated the "
        "answers**, so these two columns may carry self-preference bias; see the cross-judging "
        "section for the check. Citation accuracy = valid citations / all "
        "citations (strict: exact section among the sources; loose: also ancestors). Gold "
        "cited = answer cites ≥1 gold section.",
    ]
    grouped_bars(
        FIG_DIR / f"generation_{provider}{tag}.png",
        [r["config"] for r in rows],
        {
            "Faithfulness": [float(r["faithfulness"] or 0) for r in rows],
            "Correctness": [float(r["correctness"] or 0) for r in rows],
            "Citation accuracy": [float(r["citation_accuracy"] or 0) for r in rows],
            "Refusal F1": [float(r["refusal_f1"] or 0) for r in rows],
        },
        f"Generation quality per configuration ({provider})",
        prelim,
    )
    summary = [
        f"{r['config']}: correctness {f(r['correctness'], 2)}, faithfulness "
        f"{f(r['faithfulness'], 2)}, citation acc. {f(r['citation_accuracy'], 2)}, "
        f"refusal F1 {f(r['refusal_f1'], 2)}"
        for r in rows
    ]
    return out, summary


def latency_section() -> list[str]:
    rows = read_csv(RESULTS_DIR / "latency.csv")
    if not rows:
        return []
    out = ["### Real end-to-end latency (CPU laptop, no reranker cache)", ""]
    out += md_table(
        [
            "Config",
            "n",
            "LLM",
            "total mean (s)",
            "total max (s)",
            "dense (s)",
            "rerank (s)",
            "LLM (s)",
        ],
        [
            [
                r["config"],
                r["n"],
                r["model"],
                r["total_mean_s"],
                r["total_max_s"],
                r["dense_mean_s"],
                r["rerank_mean_s"],
                r["llm_mean_s"],
            ]
            for r in rows
        ],
    )
    out += [
        "",
        "The latency columns of the generation table above reuse cached reranker scores "
        "(`eval/results/raw/rerank_cache.json`) and therefore exclude the cross-encoder "
        "compute; this table (`python -m eval.measure_latency`) shows what an app user "
        "waits for on CPU.",
        "",
    ]
    return out


def load_gen(config: str, provider: str) -> dict[str, dict]:
    p = RAW_DIR / f"gen_{config}_{provider}.jsonl"
    if not p.exists():
        return {}
    return {
        json.loads(x)["id"]: json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x
    }


def qualitative_section(provider: str) -> list[str]:
    rows = load_gen("best", provider)
    if not rows:
        return []
    picks = []
    for want, label in (
        ("simple", "Simple question"),
        ("cross", "Cross-spec question"),
        ("out_of_corpus", "Out-of-corpus question"),
    ):
        cands = [r for r in rows.values() if r["type"] == want]
        cands.sort(key=lambda r: -(r.get("judge", {}).get("correctness") or 0))
        if cands:
            picks.append((label, cands[0]))
    out = ["## Qualitative examples (config `best`)", ""]
    for label, r in picks:
        a = r["answer"]
        srcs = ", ".join(f"{s['chunk']['spec']} §{s['chunk']['section']}" for s in a["sources"])
        out += [
            f"### {label} — `{r['id']}`",
            "",
            f"**Q:** {r['question']}",
            "",
            "**Answer:**",
            "",
            *[f"> {ln}" for ln in a["text"].splitlines()],
            "",
            f"Route: {', '.join(a['route']['specs'])} ({a['route']['reason']}) · gate "
            f"score {f(a['gate_score'])} · sources: {srcs or 'none'} · judge: "
            f"{r.get('judge', {}).get('judge_reason', '–')}",
            "",
        ]
    return out


def failure_section(provider: str) -> list[str]:
    out = ["## Failure analysis", ""]
    p = RAW_DIR / "retrieval_best.json"
    if p.exists():
        res = json.loads(p.read_text(encoding="utf-8"))
        items = {it["id"]: it for it in load_testset()}
        misses = [
            r for r in res["rows"] if r["type"] != "out_of_corpus" and r.get("recall@5", 1) == 0
        ]
        out += [
            f"**Retrieval misses (config `best`, no gold section in top-5): {len(misses)}**",
            "",
        ]
        for r in misses:
            gold = "; ".join(
                f"{s} §{', §'.join(g)}" for s, g in items[r["id"]]["gold_sections_per_spec"].items()
            )
            out.append(
                f"- `{r['id']}` gold {gold} — route {', '.join(r['route'])}; "
                f"top-3 retrieved: {', '.join(r['top10'][:3])}; R@10 = "
                f"{r.get('recall@10')}"
            )
        out.append("")
    rows = load_gen("best", provider)
    bad = [r for r in rows.values() if (r.get("judge", {}).get("correctness") or 0) < 1]
    if bad:
        out += [f"**Answers not judged fully correct (config `best`): {len(bad)}**", ""]
        for r in bad:
            j = r.get("judge", {})
            a = r["answer"]
            why = "refused" if a["refused"] else ("; ".join(a["warnings"]) or "")
            out.append(
                f"- `{r['id']}` correctness {j.get('correctness')} faithfulness "
                f"{j.get('faithfulness')} — {j.get('judge_reason', '')} {why}".rstrip()
            )
        out.append("")
    return out


# ----------------------------------------------------------------------------- added sections
def _raw_rows(name: str) -> list[dict]:
    path = RAW_DIR / name
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _json_file(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def paired_bootstrap(a: list[float], b: list[float], n_boot: int = 10000, seed: int = 42):
    """Mean difference a - b and its 95% paired-bootstrap interval."""
    import random

    rnd = random.Random(seed)
    diffs = [x - y for x, y in zip(a, b, strict=True)]
    n = len(diffs)
    boots = sorted(sum(diffs[rnd.randrange(n)] for _ in range(n)) / n for _ in range(n_boot))
    return sum(diffs) / n, boots[int(0.025 * n_boot)], boots[int(0.975 * n_boot)]


STAT_PAIRS = [
    ("best", "no_reranker", "reranker (all else on)"),
    ("reranker_only", "baseline", "reranker (dense only)"),
    ("best", "no_hybrid", "BM25 fusion (with reranker)"),
    ("hybrid_only", "baseline", "BM25 fusion (no reranker)"),
    ("best", "no_routing", "routing (with reranker)"),
    ("routing_only", "baseline", "routing (no reranker)"),
]


def statistics_section() -> list[str]:
    rows = {
        n: {r["id"]: r for r in _raw_rows(f"retrieval_{n}.json") if r["type"] != "out_of_corpus"}
        for n in CONFIGS
    }
    if not all(rows.values()):
        return []
    n = len(next(iter(rows.values())))
    out = [
        "## Statistical caution",
        "",
        f"Only **n = {n}** in-corpus questions are scored, so one question moves recall@k by "
        f"**{1 / n:.3f}** and a difference of a few hundredths is a single question. The table "
        "gives the paired difference of per-question scores between two configurations that "
        "differ by one component, with a 95% paired-bootstrap interval (10,000 resamples, seed "
        "42). A difference is called *robust* only when the interval excludes 0; otherwise it "
        "is within noise for this test set.",
        "",
    ]
    table = []
    for a, b, label in STAT_PAIRS:
        ids = sorted(rows[a])
        for metric in ("mrr", "recall@5"):
            d, lo, hi = paired_bootstrap(
                [rows[a][i][metric] for i in ids], [rows[b][i][metric] for i in ids]
            )
            verdict = "robust" if lo > 0 or hi < 0 else "within noise"
            table.append(
                [label, f"`{a}` − `{b}`", metric, f"{d:+.3f}", f"[{lo:+.3f}, {hi:+.3f}]", verdict]
            )
    out += md_table(["Component", "Comparison", "Metric", "Δ", "95% CI", "Verdict"], table)
    robust = sorted({r[0] for r in table if r[5] == "robust"})
    out += [
        "",
        "Robust effects on this set: "
        + (", ".join(robust) if robust else "none")
        + ". Every other difference in the ablation tables, including hybrid vs no-hybrid, "
        "should be read as *not established* until a larger, validated test set confirms it.",
        "",
    ]
    return out


def false_refusal_section(provider: str) -> list[str]:
    table = []
    current = [r["config"] for r in read_csv(RESULTS_DIR / f"generation_{provider}.csv")]
    for cfg in [c for c in CONFIGS if c in current]:  # only configs of the reported run
        for r in load_gen(cfg, provider).values():
            a = r["answer"]
            if r["type"] != "out_of_corpus" and a["refused"]:
                by = (
                    "gate (LLM not called)"
                    if not a.get("llm_provider")
                    else f"LLM ({a['llm_model']})"
                )
                table.append([f"`{cfg}`", f"`{r['id']}`", r["type"], by, f(a.get("gate_score"))])
    if not table:
        return []
    gate = sum(t[3].startswith("gate") for t in table)
    out = [
        "## False refusals: gate or LLM?",
        "",
        f"{len(table)} in-corpus questions were refused across the reported generation "
        "configurations (current defaults): "
        f"**{gate} by the score gate**, **{len(table) - gate} by the LLM** after it saw the "
        "sources. A gate refusal means retrieval found nothing above the threshold; an LLM "
        "refusal means the model judged the retrieved sources insufficient (typically one half "
        "of a cross-spec question was missing).",
        "",
    ]
    out += md_table(["Config", "Question", "Type", "Refused by", "Gate score"], table)
    return out + [""]


def cross_judge_section() -> list[str]:
    rows = read_csv(RESULTS_DIR / "cross_judge.csv")
    if not rows:
        return []
    cell = {(r["answers"], r["judge"]): r for r in rows}
    ans_models = {r["answers"]: r["answer_model"] for r in rows}
    judge_models = {r["judge"]: r["judge_model"] for r in rows if r["judge_model"]}
    out = [
        "## Cross-judging: self-preference check",
        "",
        "The main generation tables are judged by the same model that wrote the answers "
        "(gemini-3.5-flash-lite judges gemini-3.5-flash-lite). As a check, the `best` answers of "
        "two models are each judged by both judges, on frozen answer sets "
        "(`eval/results/raw/crossjudge/`) with the same rubric. Both answer sets were produced "
        "with router v1 (the router at the time of the original run).",
        "",
    ]

    def cell_txt(a, j, metric):
        c = cell.get((a, j))
        if not c or c["n_judged"] in ("0", ""):
            return "pending"
        return f"{f(c[metric], 2)} (n={c['n_judged']})"

    for metric in ("faithfulness", "correctness"):
        hdr = ["Answers \\ Judge"] + [
            f"{j} judge ({judge_models.get(j, '?')})" for j in ("gemini", "groq")
        ]
        body = [
            [f"{a} answers ({ans_models.get(a, '?')})"]
            + [cell_txt(a, j, metric) for j in ("gemini", "groq")]
            for a in ("gemini", "groq")
        ]
        out += [f"**{metric.capitalize()}**", ""] + md_table(hdr, body) + [""]
    out += ["Metrics that need no judge (same frozen answers):", ""]
    seen = []
    for a in ("gemini", "groq"):
        c = cell.get((a, "gemini")) or cell.get((a, "groq"))
        if c:
            seen.append(
                [
                    f"{a} ({c['answer_model']})",
                    f(c["citation_accuracy"], 2),
                    f(c["gold_citation_recall"], 2),
                    f(c["refusal_precision"], 2),
                    f(c["refusal_recall"], 2),
                    f(c["refusal_f1"], 2),
                    f(c["false_refusals"], 0),
                ]
            )
    out += md_table(
        [
            "Answers",
            "Citation acc.",
            "Gold cited",
            "Refusal P",
            "Refusal R",
            "Refusal F1",
            "False refusals",
        ],
        seen,
    ) + [""]

    def val(a, j, m):
        c = cell.get((a, j))
        if not c or c["n_judged"] in ("0", "") or c[m] in ("", "nan"):
            return None
        return float(c[m])

    notes = []
    for m in ("faithfulness", "correctness"):
        gg, gq, qg, qq = (
            val("gemini", "gemini", m),
            val("gemini", "groq", m),
            val("groq", "gemini", m),
            val("groq", "groq", m),
        )
        if None not in (gg, gq, qg, qq):
            bias = ((gg - gq) + (qq - qg)) / 2
            notes.append(
                f"{m}: on average a judge scores its own model's answers {bias:+.2f} higher than "
                f"the other judge does (Gemini judge on Gemini answers {gg - gq:+.2f}, Groq judge "
                f"on Groq answers {qq - qg:+.2f})"
            )
    if notes:
        out += [
            "**Self-preference.** " + "; ".join(notes) + ". A positive value is a "
            "self-preference bias of that size; with 30 questions, a few hundredths is one or "
            "two answers, so only a gap that both judges agree on (same ranking of the two "
            "answer sets) should be trusted.",
            "",
        ]
    else:
        out += [
            "Some cells are still pending (free-tier quotas); complete them with "
            "`python -m eval.run_cross_judge --judge gemini` / `--judge groq`.",
            "",
        ]
    return out


def reranker_bench_section() -> list[str]:
    rows = read_csv(RESULTS_DIR / "reranker_bench.csv")
    if not rows:
        return []
    out = [
        "## Reranker speed / quality benchmark (CPU)",
        "",
        "MRR / recall of the `best` configuration on the in-corpus questions for each number of "
        "fused candidates sent to the reranker (`retrieval.fused_top_n`) and truncation length "
        "(`reranker.max_length`). Latency = reranking time per answer, measured without cache "
        "on a fixed sample of questions; retrieval = reranking + routing / dense / BM25. The "
        "LLM adds ≈ 2 s (see the latency table).",
        "",
    ]
    out += md_table(
        [
            "Reranker",
            "fused_top_n",
            "max_length",
            "MRR",
            "R@5",
            "R@10",
            "rerank s/answer",
            "max s",
            "retrieval s/answer",
        ],
        [
            [
                r["model"].split("/")[-1],
                r["fused_top_n"],
                r["max_length"],
                f(r["mrr"]),
                f(r["recall@5"]),
                f(r["recall@10"]),
                r["rerank_s_mean"],
                r["rerank_s_max"],
                r["retrieval_s_mean"],
            ]
            for r in rows
        ],
    )
    choice = _json_file(RESULTS_DIR / "reranker_choice.json")
    if choice:
        out += ["", f"**Chosen default:** {choice.get('summary', '')}"]
    return out + [""]


def router_before_after_section() -> list[str]:
    tag = (
        "router_v1_same_reranker"
        if (RESULTS_DIR / "retrieval_ablation_router_v1_same_reranker.csv").exists()
        else "router_v1"
    )
    old = {r["config"]: r for r in read_csv(RESULTS_DIR / f"router_accuracy_{tag}.csv")}
    new = {r["config"]: r for r in read_csv(RESULTS_DIR / "router_accuracy.csv")}
    if "best" not in old or "best" not in new:
        return []
    ret_old = {
        (r["config"], r["group"]): r
        for r in read_csv(RESULTS_DIR / f"retrieval_ablation_{tag}.csv")
    }
    ret_new = {
        (r["config"], r["group"]): r for r in read_csv(RESULTS_DIR / "retrieval_ablation.csv")
    }
    out = [
        "## Router: before / after",
        "",
        "Router v2 adds three general rules (architecture AND NAS signals → both specs; "
        '"procedure … messages" phrasing → both specs; more verbs that ask what a network '
        "function does). It was tuned **only** on `tests/test_router.py` (12 new cross-spec "
        "questions written independently of the test set, plus single-spec guards); the "
        "evaluation set was not used for tuning. Both columns use the same retrieval settings "
        "(current reranker defaults); only `retrieval.router_version` differs.",
        "",
    ]
    body = []
    for k, label in (
        ("route_superset", "route ⊇ gold specs"),
        ("route_exact", "exact route"),
        ("exact_simple-23", "exact, simple 23.501"),
        ("exact_simple-24", "exact, simple 24.501"),
        ("exact_cross", "exact, cross-spec"),
    ):
        body.append([label, f(old["best"].get(k)), f(new["best"].get(k))])
    out += md_table(["Router accuracy (config best)", "v1", "v2"], body) + [""]
    body = []
    for cfg in ("best", "routing_only"):
        for g, m in (
            ("cross", "recall@5"),
            ("cross", "both_recall@5"),
            ("cross", "mrr"),
            ("all", "recall@5"),
            ("all", "mrr"),
        ):
            o, n = ret_old.get((cfg, g)), ret_new.get((cfg, g))
            if o and n:
                body.append([f"`{cfg}`", f"{g} {m}", f(o.get(m)), f(n.get(m))])
    out += md_table(["Config", "Metric", "v1", "v2"], body) + [""]
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    items = load_testset()
    prelim = PRELIMINARY if is_preliminary(items) else "validated gold set"
    rmeta_p = RESULTS_DIR / "retrieval_meta.json"
    rmeta = json.loads(rmeta_p.read_text(encoding="utf-8")) if rmeta_p.exists() else {}

    L = ["# Evaluation report", ""]
    if is_preliminary(items):
        L += [
            f"> **Status: {prelim}.** {sum(not i['verified'] for i in items)}/{len(items)} "
            "test items are not yet validated by a human (`eval/testset_review.md`). All "
            "tables below are preliminary.",
            "",
        ]
    L += [
        "## Setup",
        "",
        "- Corpus: "
        + ", ".join(f"{s.id} V{s.version} ({s.release})" for s in settings.corpus.specs)
        + " — see `data/VERSIONS.md`",
        f"- Embeddings: `{settings.embedding.model}` · reranker: `{settings.reranker.model}` "
        f"· vector DB: Qdrant (cosine) · BM25: bm25s + telecom tokenizer · RRF k = "
        f"{settings.retrieval.rrf_k}",
        f"- Retrieval: dense top {settings.retrieval.dense_top_n}, BM25 top "
        f"{settings.retrieval.sparse_top_n}, fused top {settings.retrieval.fused_top_n}, "
        f"final top-k {settings.retrieval.final_top_k}, ≥"
        f"{settings.retrieval.min_per_spec_when_both} chunks per spec for cross routes",
        f"- Test set: {len(items)} questions (20 simple, 7 cross, 3 out-of-corpus); retrieval "
        "metrics on the 27 in-corpus questions, top-10 ranking after fusion/rerank; a hit "
        "is the gold section or one of its sub-clauses, same spec",
        f"- Retrieval run: {rmeta.get('date', '–')}, commit `{rmeta.get('git_commit', '–')}`",
        "",
        "Configurations: " + "; ".join(f"`{n}` = {describe(n)}" for n in CONFIGS),
        "",
        "## Retrieval",
        "",
    ]
    rtab, rsum = retrieval_section(prelim)
    L += rtab + [""]
    if (FIG_DIR / "retrieval_ablation.png").exists():
        L += ["![retrieval ablation](figures/retrieval_ablation.png)", ""]
    L += router_section(prelim) + [""] + gate_section(prelim) + ["## Generation", ""]
    gsum_all = []
    for provider in ("gemini", "grok"):
        if (RESULTS_DIR / f"generation_{provider}.csv").exists():
            gtab, gsum = generation_section(provider, prelim, label="current defaults")
            gsum_all += [f"[{provider}] {s}" for s in gsum]
            L += gtab + ["", f"![generation {provider}](figures/generation_{provider}.png)", ""]
            L += [
                "Current defaults: router v2, bge-reranker-base, 15 candidates, 512 tokens, gate "
                "0.10. `no_reranker` and `no_routing` are pending (Gemini free-tier daily quota); "
                "the complete 5-configuration run with the previous defaults is below. Compared "
                "with that run, `best` correctness went 0.88 → 0.80: five questions were refused "
                "by the LLM because a key chunk was no longer among the 6 sources (e.g. s23-01: "
                "§6.2.1 AMF; s23-07: the 5QI-1 row of Table 5.7.4-1), two improved. The paired "
                "change is −0.08, 95% CI [−0.23, +0.05] (not established on 30 questions), but "
                "the mechanism is concrete: the faster reranker trades some answer quality for "
                "6× lower latency.",
                "",
            ]
    if (RESULTS_DIR / "generation_gemini_router_v1.csv").exists():
        gtab, _ = generation_section(
            "gemini",
            prelim,
            tag="_router_v1",
            label="previous defaults (router v1, bge-reranker-v2-m3, 30 candidates, 1024 tokens)",
        )
        L += gtab + [""]
    if not gsum_all:
        L += ["_Generation evaluation not run yet._", ""]
    L += latency_section()
    L += cross_judge_section() + false_refusal_section("gemini")
    L += reranker_bench_section() + router_before_after_section() + statistics_section()
    L += qualitative_section("gemini") + failure_section("gemini")
    (RESULTS_DIR / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Wrote", RESULTS_DIR / "REPORT.md")
    for s in rsum + gsum_all:
        print("  ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
