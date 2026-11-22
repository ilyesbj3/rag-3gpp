"""Build eval/results/BONUS.md from the bonus experiment result files (missing ones are skipped).

    python -m eval.make_bonus_report

Bonuses (CLAUDE.md §17, phase 12): French questions, embedding comparison, LLM comparison,
TS 23.502 added to the corpus, Release 17 vs Release 18.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from eval.make_report import f, md_table, read_csv
from eval.metrics import PRELIMINARY, RAW_DIR, RESULTS_DIR

FR_WORDS = set(
    "le la les des est une dans pour que qui avec sur du au aux est sont pas ce cette "
    "il elle ils lorsque procédure message".split()
)
EN_WORDS = set("the is and of to in when for with are by this that which from be on as".split())


def is_english(text: str) -> bool:
    """Crude language check: more English than French function words."""
    words = re.findall(r"[a-zA-Zàâçéèêëîïôûùüÿœ]+", text.lower())
    en = sum(w in EN_WORDS for w in words)
    fr = sum(w in FR_WORDS for w in words)
    return en >= fr


def load_jsonl(name: str) -> dict[str, dict[str, Any]]:
    p = RAW_DIR / name
    if not p.exists():
        return {}
    return {
        json.loads(x)["id"]: json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x
    }


def retrieval_rows(tag: str, label: str, configs: list[str] | None = None) -> list[list[str]]:
    sfx = f"_{tag}" if tag else ""
    rows = [
        r
        for r in read_csv(RESULTS_DIR / f"retrieval_ablation{sfx}.csv")
        if r["group"] == "all" and (configs is None or r["config"] in configs)
    ]
    return [
        [label, r["config"], f(r["recall@1"]), f(r["recall@5"]), f(r["recall@10"]), f(r["mrr"])]
        for r in rows
    ]


def by_group(tag: str, config: str) -> dict[str, dict[str, str]]:
    sfx = f"_{tag}" if tag else ""
    return {
        r["group"]: r
        for r in read_csv(RESULTS_DIR / f"retrieval_ablation{sfx}.csv")
        if r["config"] == config
    }


def gen_rows(provider: str, tag: str, label: str, configs: list[str]) -> list[list[str]]:
    sfx = f"_{tag}" if tag else ""
    rows = [
        r
        for r in read_csv(RESULTS_DIR / f"generation_{provider}{sfx}.csv")
        if r["config"] in configs
    ]
    return [
        [
            label,
            r["config"],
            r.get("llm_models", ""),
            f"{r['n']}/{r['n_expected']}",
            f(r["faithfulness"], 2),
            f(r["correctness"], 2),
            f(r["citation_accuracy"], 2),
            f(r["gold_citation_recall"], 2),
            f(r["refusal_f1"], 2),
            f(r["false_refusals"], 0),
            f(r["latency_mean_s"], 1),
        ]
        for r in rows
    ]


GEN_HEADER = [
    "Run",
    "Config",
    "LLM",
    "n",
    "Faithfulness",
    "Correctness",
    "Citation acc.",
    "Gold cited",
    "Refusal F1",
    "False refusals",
    "Latency (s)",
]
RET_HEADER = ["Run", "Config", "R@1", "R@5", "R@10", "MRR"]


def section_french() -> list[str]:
    rows = (
        retrieval_rows("", "English questions", ["best", "no_hybrid", "no_reranker", "baseline"])
        + retrieval_rows("fr", "French questions")
        + retrieval_rows("fr_translated", "French + BM25 query translation")
    )
    if not any(r[0].startswith("French") for r in rows):
        return []
    out = [
        "## 1. French questions → English answers (bge-m3)",
        "",
        "The 30 questions were translated to French (`eval/testset_fr.json`, same gold "
        "labels). bge-m3 and bge-reranker-v2-m3 are multilingual; the BM25 tokenizer is "
        "not, so a variant translates the question to English for BM25 only "
        "(`retrieval.translate_query_for_bm25`, one LLM call per question; translator = "
        "gemini-3.1-flash-lite, because the gemini-3.5-flash-lite daily quota was used up).",
        "",
        f"### Retrieval — *{PRELIMINARY}*",
        "",
    ]
    out += md_table(RET_HEADER, rows)
    gen = load_jsonl("gen_best_gemini_fr.jsonl")
    if gen:
        answered = [r for r in gen.values() if not r["answer"]["refused"]]
        eng = sum(is_english(r["answer"]["text"]) for r in answered)
        out += ["", "### Generation (config `best`)", ""]
        out += md_table(
            GEN_HEADER,
            gen_rows("gemini", "", "English questions", ["best"])
            + gen_rows("gemini", "fr", "French questions", ["best"]),
        )
        out += [
            "",
            f"Answers in English (function-word heuristic): **{eng}/{len(answered)}** "
            "non-refused answers to French questions.",
        ]
    return out + [""]


def section_embeddings() -> list[str]:
    rows = retrieval_rows(
        "", "bge-m3 (1024-d)", ["baseline", "no_hybrid", "best"]
    ) + retrieval_rows("bge-small", "bge-small-en-v1.5 (384-d)")
    if not any("small" in r[0] for r in rows):
        return []
    meta_p = RESULTS_DIR / "embedding_build_times.json"
    times = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    out = [
        "## 2. Embedding models: bge-m3 vs bge-small-en-v1.5",
        "",
        f"Same chunks, same BM25 and reranker; only the dense model changes "
        f"(*{PRELIMINARY}*). `baseline` = dense only.",
        "",
    ]
    out += md_table(RET_HEADER, rows)
    if times:
        out += ["", "Indexing time on CPU: " + ", ".join(f"{k}: {v}" for k, v in times.items())]
    return out + [""]


def section_llms() -> list[str]:
    rows = gen_rows("gemini", "", "API", ["best"]) + gen_rows("ollama", "", "local", ["best"])
    if len(rows) < 2:
        return []
    out = [
        "## 3. LLM comparison: Gemini (API) vs Llama 3.2 3B (local, Ollama)",
        "",
        "Same retrieval (`best`, identical sources thanks to the cache), same prompt; the "
        "judge is gemini-3.5-flash-lite for both. Grok could not be compared: the xAI key "
        f"was rejected (see PROGRESS.md). *{PRELIMINARY}*",
        "",
    ]
    out += md_table(GEN_HEADER, rows)
    return out + [""]


def section_23502() -> list[str]:
    rows = retrieval_rows(
        "", "TS 23.501 + TS 24.501", ["no_routing", "reranker_only"]
    ) + retrieval_rows("3specs", "+ TS 23.502")
    if not any("23.502" in r[0] for r in rows):
        return []
    out = [
        "## 4. Adding TS 23.502 (procedures)",
        "",
        "Corpus extended with TS 23.502 V18.14.0 (`configs/rel18_3specs.yaml`, 5,216 "
        "chunks). The router only knows the two original specs, so the comparison uses "
        "configurations without routing. Gold labels only cover TS 23.501 / TS 24.501, so "
        "retrieval recall measures how much TS 23.502 *displaces* gold chunks; generation "
        f"shows whether the procedure text helps the answers. *{PRELIMINARY}*",
        "",
        "### Retrieval",
        "",
    ]
    out += md_table(RET_HEADER, rows)
    share = load_jsonl("gen_no_routing_gemini_3specs.jsonl")
    if share:
        cross = [r for r in share.values() if r["type"] == "cross"]
        n502 = [
            sum(s["chunk"]["spec"] == "TS 23.502" for s in r["answer"]["sources"]) for r in cross
        ]
        out += [
            "",
            f"Cross questions: on average **{sum(n502) / max(len(n502), 1):.1f} of "
            f"{len(cross[0]['answer']['sources']) if cross else 0}** sources come from "
            "TS 23.502.",
        ]
    out += ["", "### Generation", ""]
    out += md_table(
        GEN_HEADER,
        gen_rows("gemini", "", "2 specs", ["no_routing"])
        + gen_rows("gemini", "3specs", "3 specs", ["no_routing"]),
    )
    by2, by3 = by_group("", "no_routing"), by_group("3specs", "no_routing")
    if by2 and by3:
        out += [
            "",
            "Per question type (R@5): "
            + "; ".join(
                f"{g}: {f(by2[g]['recall@5'])} → {f(by3[g]['recall@5'])}"
                for g in ("simple-23", "simple-24", "cross")
                if g in by3
            ),
        ]
    return out + [""]


def write_release_examples(gen17: dict, gen18: dict, path) -> None:
    """Side-by-side Rel-18 / Rel-17 answers for questions whose cited sections differ."""
    lines = [
        "# Rel-18 vs Rel-17 answers (config `best`)",
        "",
        f"*{PRELIMINARY}.* Questions where the two answers cite different sections or "
        "where one release refused.",
        "",
    ]
    for qid in sorted(gen17):
        if qid not in gen18 or gen17[qid]["type"] == "out_of_corpus":
            continue
        a17, a18 = gen17[qid]["answer"], gen18[qid]["answer"]
        c17 = sorted({(c["spec"], c["section"]) for c in a17["citations"] if c["valid"]})
        c18 = sorted({(c["spec"], c["section"]) for c in a18["citations"] if c["valid"]})
        if c17 == c18 and a17["refused"] == a18["refused"]:
            continue
        lines += [
            f"## {qid} — {gen17[qid]['question']}",
            "",
            "**Rel-18** (" + (", ".join(f"§{s}" for _, s in c18) or "no citation") + "):",
            "",
            *[f"> {x}" for x in a18["text"].splitlines()],
            "",
            "**Rel-17** (" + (", ".join(f"§{s}" for _, s in c17) or "no citation") + "):",
            "",
            *[f"> {x}" for x in a17["text"].splitlines()],
            "",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def section_rel17() -> list[str]:
    gen17 = load_jsonl("gen_best_gemini_rel17.jsonl")
    if not gen17:
        return []
    gen18 = load_jsonl("gen_best_gemini.jsonl")
    out = [
        "## 5. Release 17 vs Release 18",
        "",
        "Same pipeline (`best`) on TS 23.501 V17.15.0 + TS 24.501 V17.18.1 "
        "(`configs/rel17.yaml`, 3,033 chunks vs 3,597 in Rel-18). Reference answers were "
        "written from Rel-18, so a lower correctness can be a *real release difference*, "
        f"not an error. *{PRELIMINARY}*",
        "",
    ]
    out += md_table(
        RET_HEADER, retrieval_rows("", "Rel-18", ["best"]) + retrieval_rows("rel17", "Rel-17")
    )
    out += [""]
    out += md_table(
        GEN_HEADER,
        gen_rows("gemini", "", "Rel-18", ["best"])
        + gen_rows("gemini", "rel17", "Rel-17", ["best"]),
    )
    partial = [
        r
        for r in read_csv(RESULTS_DIR / "generation_gemini_rel17.csv")
        if r["n"] != r["n_expected"]
    ]
    if partial:
        out += [
            "",
            f"> **Partial run**: {partial[0]['n']}/{partial[0]['n_expected']} questions "
            "answered before the free-tier daily quota of gemini-3.5-flash-lite (500 "
            "requests/day) was exhausted. Resume with the same command (cached answers are "
            "skipped): `RAG_CONFIG=configs/rel17.yaml python -m eval.run_generation_eval "
            "--provider gemini --tag rel17 --configs best`, then `python -m "
            "eval.make_bonus_report`.",
        ]
    diff_p = RESULTS_DIR / "rel17_vs_rel18_examples.md"
    write_release_examples(gen17, gen18, diff_p)
    if diff_p.exists():
        out += [
            "",
            "Side-by-side answers where the two releases differ: "
            "[`rel17_vs_rel18_examples.md`](rel17_vs_rel18_examples.md).",
        ]
    changed = []
    for qid, r17 in gen17.items():
        r18 = gen18.get(qid)
        if not r18:
            continue
        j17 = (r17.get("judge") or {}).get("correctness")
        j18 = (r18.get("judge") or {}).get("correctness")
        if j17 is not None and j18 is not None and j17 != j18:
            changed.append(f"`{qid}` {j18} → {j17}")
    if changed:
        out += [
            "",
            "Questions whose judged correctness changed (Rel-18 → Rel-17): " + ", ".join(changed),
        ]
    return out + [""]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    L = [
        "# Bonus experiments",
        "",
        f"> All numbers are *{PRELIMINARY}* (same unverified test set as REPORT.md). "
        "Generation runs use gemini-3.5-flash-lite unless stated otherwise.",
        "",
    ]
    for sec in (section_french, section_embeddings, section_llms, section_23502, section_rel17):
        L += sec()
    (RESULTS_DIR / "BONUS.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("Wrote", RESULTS_DIR / "BONUS.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
