"""Write eval/testset_review.md: each question with its gold sections and supporting excerpts.

    python -m eval.make_testset_review

The excerpt shown for each gold section is the part of that section (all its chunks and
sub-clauses) that shares the most words with the reference answer, so the reviewer can check
the gold label and the reference answer side by side.
"""

from __future__ import annotations

import re
import sys

from eval.metrics import ROOT, load_testset, section_hit, validate_gold
from src.ingest.chunker import load_chunks
from src.schemas import Chunk

WORD = re.compile(r"[A-Za-z0-9#\-]{3,}")


def best_excerpt(chunks: list[Chunk], reference: str, width: int = 900) -> tuple[str, str]:
    ref = {w.lower() for w in WORD.findall(reference)}
    best, best_score, best_pos = None, -1.0, 0
    for c in chunks:
        body = c.body
        words = list(WORD.finditer(body))
        # slide a window of ~120 words and keep the one with most reference words
        for i in range(0, max(len(words) - 1, 1), 20):
            win = words[i : i + 120]
            score = sum(w.group().lower() in ref for w in win)
            if score > best_score and win:
                best, best_score, best_pos = c, score, win[0].start()
    if best is None:
        return "", ""
    text = best.body[best_pos : best_pos + width].replace("\n", "\n> ")
    return best.chunk_id, text


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    items = load_testset()
    chunks = load_chunks()
    problems = validate_gold(items, chunks)
    out = [
        "# Test set review",
        "",
        f"Status: **{sum(i['verified'] for i in items)}/{len(items)} verified**. "
        "Gold sections and reference answers were drafted from `data/processed/chunks.jsonl` "
        "(searched, not recalled). For each item, check the question, the gold section(s) and "
        'the reference answer against the excerpt, then set `"verified": true` in '
        "`eval/testset.json` (or fix the item).",
        "",
        "Hit rule used by the evaluation: a retrieved chunk matches when its section equals a "
        "gold section or is a sub-clause of it (same spec). Cross questions additionally need "
        "at least one hit per gold spec.",
        "",
        f"Gold-section existence check: {'OK' if not problems else '; '.join(problems)}",
        "",
    ]
    for it in items:
        out += [
            f"## {it['id']} ({it['type']}) — {'verified' if it['verified'] else 'NOT verified'}",
            "",
            f"**Q:** {it['question']}",
            "",
        ]
        if it["type"] == "out_of_corpus":
            out += ["Expected: refusal sentence. Corpus search for the topic found no match.", ""]
            continue
        for spec, golds in it["gold_sections_per_spec"].items():
            out.append(f"- **{spec}** gold: " + ", ".join(f"§{g}" for g in golds))
        out += ["", f"**Reference answer:** {it['reference_answer']}", ""]
        for spec, golds in it["gold_sections_per_spec"].items():
            for g in golds:
                cs = [c for c in chunks if c.spec == spec and section_hit(c.section, g)]
                cid, text = best_excerpt(cs, it["reference_answer"])
                out += [
                    f"<details><summary>Excerpt {spec} §{g} — <code>{cid}</code></summary>",
                    "",
                    f"> {text}",
                    "",
                    "</details>",
                    "",
                ]
    path = ROOT / "eval" / "testset_review.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {path}; gold check: {'OK' if not problems else problems}")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
