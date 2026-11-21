"""Write data/processed/chunk_samples.md: random chunks + chunks for key spot-check topics.

Usage:
    python scripts/sample_chunks.py [--n 15] [--seed 42]
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import PROCESSED_DIR  # noqa: E402
from src.ingest.chunker import load_chunks  # noqa: E402
from src.schemas import Chunk  # noqa: E402

# (label, spec, regex on chunk text) — located by search, not by known section numbers
TOPICS = [
    ("5GMM cause #9", "TS 24.501", r"Cause #9 \S+ UE identity"),
    ("Timer T3510", "TS 24.501", r"\| T3510 \|"),
    ("REGISTRATION REQUEST", "TS 24.501", r"Table \S+: REGISTRATION REQUEST message content"),
    ("Standardized 5QI table", "TS 23.501", r"Table \S+: Standardized 5QI to QoS characteristics"),
]


def render(c: Chunk, why: str) -> str:
    return (
        f"### `{c.chunk_id}` — {why}\n\n"
        f"- spec: {c.spec} {c.version} ({c.release}) · section: **{c.section}** · "
        f"title: {c.title}\n"
        f"- breadcrumb: {' > '.join(c.breadcrumb)} · content_type: {c.content_type} · "
        f"part: {c.part} · tokens: {c.n_tokens}\n\n"
        f"````text\n{c.text}\n````\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    chunks = load_chunks()
    out = [
        "# Chunk samples for human review",
        "",
        f"{len(chunks)} chunks in `data/processed/chunks.jsonl`. Regenerate with "
        f"`python scripts/sample_chunks.py --n {args.n} --seed {args.seed}`.",
        "",
        "## Topic chunks (found by searching the chunk text)",
        "",
    ]
    for label, spec, pattern in TOPICS:
        rx = re.compile(pattern)
        hits = [c for c in chunks if c.spec == spec and rx.search(c.text)]
        out.append(f"**{label}** — matching chunks: {', '.join(c.chunk_id for c in hits)}\n")
        for c in hits[:2]:
            out.append(render(c, label))
    out += ["## Random chunks", ""]
    rnd = random.Random(args.seed)
    for c in rnd.sample(chunks, args.n):
        out.append(render(c, "random"))
    path = PROCESSED_DIR / "chunk_samples.md"
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
