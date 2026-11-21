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


def generation_section(provider: str, prelim: str) -> tuple[list[str], list[str]]:
    rows = read_csv(RESULTS_DIR / f"generation_{provider}.csv")
    if not rows:
        return [f"_Generation evaluation ({provider}) not run yet._"], []
    meta_path = RESULTS_DIR / f"generation_{provider}_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    out = [f"### Generation — provider `{provider}` ({rows[0].get('llm_models')}) — *{prelim}*", ""]
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
        "(`eval/metrics.py`), judge = Gemini. Citation accuracy = valid citations / all "
        "citations (strict: exact section among the sources; loose: also ancestors). Gold "
        "cited = answer cites ≥1 gold section.",
    ]
    grouped_bars(
        FIG_DIR / f"generation_{provider}.png",
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
            gtab, gsum = generation_section(provider, prelim)
            gsum_all += [f"[{provider}] {s}" for s in gsum]
            L += gtab + ["", f"![generation {provider}](figures/generation_{provider}.png)", ""]
    if not gsum_all:
        L += ["_Generation evaluation not run yet._", ""]
    L += latency_section()
    L += qualitative_section("gemini") + failure_section("gemini")
    (RESULTS_DIR / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Wrote", RESULTS_DIR / "REPORT.md")
    for s in rsum + gsum_all:
        print("  ", s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
