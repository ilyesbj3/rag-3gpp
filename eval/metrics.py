"""Test set loading and evaluation metrics (retrieval, citations, refusal, LLM judge)."""

from __future__ import annotations

import json
import logging
import re
import statistics
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.config import ROOT, Settings
from src.generation.llm import REFUSAL
from src.schemas import Answer, Chunk

log = logging.getLogger(__name__)

TESTSET_PATH = ROOT / "eval" / "testset.json"
RESULTS_DIR = ROOT / "eval" / "results"
RAW_DIR = RESULTS_DIR / "raw"
PRELIMINARY = "preliminary — gold set pending human validation"
K_VALUES = (1, 3, 5, 10)


# ----------------------------------------------------------------------------- test set
def load_testset(path: Path = TESTSET_PATH) -> list[dict[str, Any]]:
    items = json.loads(path.read_text(encoding="utf-8"))
    n_unverified = sum(not it.get("verified") for it in items)
    if n_unverified:
        log.warning(
            "%d/%d test items are not verified by a human yet (%s)",
            n_unverified,
            len(items),
            PRELIMINARY,
        )
    return items


def is_preliminary(items: list[dict[str, Any]]) -> bool:
    return any(not it.get("verified") for it in items)


def validate_gold(items: list[dict[str, Any]], chunks: list[Chunk]) -> list[str]:
    """Every gold section must exist in chunks.jsonl (exactly or as an ancestor)."""
    have: dict[str, set[str]] = {}
    for c in chunks:
        have.setdefault(c.spec, set()).add(c.section)
    problems = []
    for it in items:
        for spec, secs in it.get("gold_sections_per_spec", {}).items():
            for g in secs:
                if not any(section_hit(s, g) for s in have.get(spec, ())):
                    problems.append(f"{it['id']}: {spec} §{g} not found in chunks")
    return problems


# ----------------------------------------------------------------------------- retrieval
def section_hit(retrieved: str, gold: str) -> bool:
    """Equal, or a sub-clause of gold on `.` boundaries (5.5.1 matches 5.5.1.2, not 5.5.10)."""
    return retrieved == gold or retrieved.startswith(gold + ".")


def is_hit(spec: str, section: str, item: dict[str, Any]) -> bool:
    golds = item.get("gold_sections_per_spec", {}).get(spec, [])
    return any(section_hit(section, g) for g in golds)


def retrieval_metrics(ranked: list[tuple[str, str]], item: dict[str, Any]) -> dict[str, float]:
    """recall@k (any gold hit in top-k), MRR, and both-spec recall@k for cross questions.

    `ranked` is the list of (spec, section) in rank order (top 10 used)."""
    hits = [is_hit(sp, sec, item) for sp, sec in ranked[:10]]
    out: dict[str, float] = {}
    for k in K_VALUES:
        out[f"recall@{k}"] = float(any(hits[:k]))
    first = next((i for i, h in enumerate(hits, start=1) if h), None)
    out["mrr"] = 1.0 / first if first else 0.0
    if item["type"] == "cross":
        for k in K_VALUES:
            ok = all(
                any(sp == spec and is_hit(sp, sec, item) for sp, sec in ranked[:k])
                for spec in item["gold_specs"]
            )
            out[f"both_recall@{k}"] = float(ok)
    return out


def mean(xs: list[float]) -> float:
    return round(statistics.fmean(xs), 4) if xs else float("nan")


# ----------------------------------------------------------------------------- generation
def citation_metrics(ans: Answer, item: dict[str, Any]) -> dict[str, float | None]:
    """Citation accuracy (strict and loose) and whether a gold section is cited."""
    cits = ans.citations
    total = len(cits)
    strict = sum(c.valid and not c.loose for c in cits)
    loose = sum(c.valid for c in cits)
    gold_cited = any(c.valid and is_hit(c.spec, c.section, item) for c in cits)
    return {
        "n_citations": float(total),
        "citation_accuracy": strict / total if total else None,
        "citation_accuracy_loose": loose / total if total else None,
        "gold_cited": float(gold_cited) if item["type"] != "out_of_corpus" else None,
        "not_grounded": float(any("not grounded" in w.lower() for w in ans.warnings)),
    }


def refusal_scores(rows: list[dict[str, Any]]) -> dict[str, float]:
    """Precision / recall / F1 of refusing, with out-of-corpus questions as positives."""
    tp = sum(r["refused"] and r["type"] == "out_of_corpus" for r in rows)
    fp = sum(r["refused"] and r["type"] != "out_of_corpus" for r in rows)
    fn = sum((not r["refused"]) and r["type"] == "out_of_corpus" for r in rows)
    p = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * rec / (p + rec) if p + rec else 0.0
    n_in = sum(r["type"] != "out_of_corpus" for r in rows)
    return {
        "refusal_precision": round(p, 4),
        "refusal_recall": round(rec, 4),
        "refusal_f1": round(f1, 4),
        "false_refusals": float(fp),
        "false_refusal_rate": round(fp / n_in, 4) if n_in else 0.0,
    }


JUDGE_SYSTEM = """You are a strict evaluator of answers produced by a retrieval-augmented assistant
about 3GPP specifications. You output only JSON."""

JUDGE_TEMPLATE = """Score the ANSWER on two criteria, each with exactly one of 0, 0.5 or 1.

faithfulness: are all factual statements in the ANSWER supported by the CONTEXT?
  1 = every statement is supported; 0.5 = mostly supported, minor unsupported detail;
  0 = contains significant unsupported or contradicted claims.
  If the ANSWER is a refusal, faithfulness = 1.
correctness: does the ANSWER agree with the REFERENCE answer?
  1 = covers the key facts of the reference without contradiction; 0.5 = partially
  correct or incomplete; 0 = wrong, contradicts the reference, or refuses although the
  reference has an answer. If the REFERENCE is a refusal, correctness = 1 only when the
  ANSWER also refuses.

QUESTION: {question}

REFERENCE: {reference}

CONTEXT:
{context}

ANSWER: {answer}

Return JSON: {{"faithfulness": <0|0.5|1>, "correctness": <0|0.5|1>, "reason": "<one sentence>"}}"""


def judge_answer(llm, item: dict[str, Any], answer_text: str, context: str) -> dict[str, Any]:
    """LLM-as-judge with a fixed 0 / 0.5 / 1 rubric (fallback when RAGAS is unavailable)."""
    prompt = JUDGE_TEMPLATE.format(
        question=item["question"],
        reference=item["reference_answer"],
        context=context[:24000] or "(no context: refused before generation)",
        answer=answer_text,
    )
    resp = llm.generate(JUDGE_SYSTEM, prompt)
    m = re.search(r"\{.*\}", resp.text, re.S)
    try:
        data = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        data = {}

    def clamp(v: Any) -> float | None:
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        return min((0.0, 0.5, 1.0), key=lambda x: abs(x - v))

    return {
        "faithfulness": clamp(data.get("faithfulness")),
        "correctness": clamp(data.get("correctness")),
        "judge_reason": str(data.get("reason", ""))[:300],
        "judge_model": getattr(resp, "model", None),
    }


def is_refusal_text(text: str) -> bool:
    return text.strip() == REFUSAL


# ----------------------------------------------------------------------------- provenance
def run_metadata(settings: Settings, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Provenance recorded in every result file (§16.8)."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
    except OSError:
        commit = "unknown"
    return {
        "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "git_commit": commit or "unknown",
        "corpus": {s.id: s.version for s in settings.corpus.specs},
        "embedding_model": settings.embedding.model,
        "reranker_model": settings.reranker.model,
        "reranker_max_length": settings.reranker.max_length,
        "retrieval": {
            k: getattr(settings.retrieval, k)
            for k in (
                "fused_top_n",
                "routing_mode",
                "soft_routing_weight",
                "bm25_weight",
                "router_version",
            )
        },
        "gate": settings.gate.model_dump(),
        "prompt_version": settings.llm.prompt_version,
        "status": None,
        **(extra or {}),
    }
