"""Structural chunking: one chunk per section when it fits, else paragraph windows with overlap.

Rules: tables are never split mid-row (oversized tables are split by
rows, repeating title + header); chunks never merge different section numbers; each chunk
text starts with a one-line contextual header that BM25 and the embedder both see.

CLI:
    python -m src.ingest.chunker            # parse both specs -> data/processed/chunks.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from src.config import PROCESSED_DIR, RAW_DIR, ChunkingConfig, SpecConfig, load_settings
from src.ingest.parse_docx import ParseReport, Section, parse_spec_file, rows_to_markdown
from src.schemas import Chunk

log = logging.getLogger(__name__)

TokenCounter = Callable[[str], int]
CHUNKS_PATH = PROCESSED_DIR / "chunks.jsonl"
_SENTENCE_RE = re.compile(r"(?<=[.;:])\s+")
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")


@lru_cache(maxsize=1)
def _encoding():
    import tiktoken

    return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Approximate token count with tiktoken `cl100k_base` (used only for chunk sizing)."""
    return len(_encoding().encode(text, disallowed_special=()))


@dataclass
class Unit:
    """Smallest piece the windowing works with: a paragraph, a sentence group or a table."""

    kind: str  # "text" | "table"
    text: str
    tokens: int


def make_header(spec_id: str, sec: Section) -> str:
    """`[TS 24.501 §5.5.1.2.4 Title | 5 Parent > 5.5 Parent > ...]`"""
    head = f"[{spec_id} §{sec.number} {sec.title}"
    ancestors = list(zip(sec.breadcrumb[:-1], sec.parent_titles, strict=True))
    if ancestors:
        head += " | " + " > ".join(f"{n} {t}" for n, t in ancestors)
    return head + "]"


def content_type_for(section: str, units: list[Unit]) -> str:
    top = section.split(".")[0]
    if top == "2":
        return "references"
    if top == "3":
        return "definitions"
    if units and all(u.kind == "table" for u in units):
        return "table"
    return "text"


def split_table(rows: list[list[str]], title: str | None, budget: int, ct: TokenCounter):
    """Split a table by rows into Markdown parts <= budget, repeating title + header row.
    A single row larger than the budget stays whole (never split mid-row)."""
    header, body = rows[0], rows[1:]
    parts: list[list[list[str]]] = []
    cur: list[list[str]] = []
    base = ct(rows_to_markdown([header], title))
    cur_tok = base
    for row in body:
        row_tok = ct("| " + " | ".join(row) + " |") + 1
        if cur and cur_tok + row_tok > budget:
            parts.append(cur)
            cur, cur_tok = [], base
        cur.append(row)
        cur_tok += row_tok
    if cur or not parts:
        parts.append(cur)
    return [rows_to_markdown([header, *p], title) for p in parts]


def _split_long_text(text: str, budget: int, ct: TokenCounter) -> list[str]:
    """Split one oversized paragraph on sentence boundaries, then on words if needed."""
    pieces: list[str] = []
    cur = ""
    for sent in _SENTENCE_RE.split(text):
        cand = f"{cur} {sent}".strip()
        if cur and ct(cand) > budget:
            pieces.append(cur)
            cand = sent
        if ct(cand) > budget:  # a single huge "sentence": cut on words
            words, cur = cand.split(" "), ""
            for w in words:
                if cur and ct(cur + " " + w) > budget:
                    pieces.append(cur)
                    cur = w
                else:
                    cur = f"{cur} {w}".strip()
            continue
        cur = cand
    if cur:
        pieces.append(cur)
    return pieces


def _overlap_tail(units: list[Unit], overlap: int, ct: TokenCounter) -> list[Unit]:
    """Trailing text of the previous window (<= overlap tokens), never a table."""
    tail: list[Unit] = []
    used = 0
    for u in reversed(units):
        if u.kind == "table":
            break
        if used + u.tokens <= overlap:
            tail.insert(0, u)
            used += u.tokens
            continue
        sents = _SENTENCE_RE.split(u.text)  # take trailing sentences of a long paragraph
        kept: list[str] = []
        for s in reversed(sents):
            t = ct(s)
            if used + t > overlap:
                break
            kept.insert(0, s)
            used += t
        if kept and len(kept) < len(sents):
            text = " ".join(kept)
            tail.insert(0, Unit("text", text, ct(text)))
        break
    return tail


def section_units(sec: Section, budget: int, ct: TokenCounter) -> list[list[Unit] | Unit]:
    """Blocks -> units. Oversized tables become a list of row-split table units."""
    out: list[list[Unit] | Unit] = []
    for b in sec.blocks:
        tok = ct(b.text)
        if b.kind == "table":
            if tok > budget and b.rows and len(b.rows) > 2:
                parts = split_table(b.rows, b.table_title, budget, ct)
                out.append([Unit("table", p, ct(p)) for p in parts])
            else:
                out.append(Unit("table", b.text, tok))
        elif tok > budget:
            out.extend(Unit("text", p, ct(p)) for p in _split_long_text(b.text, budget, ct))
        else:
            out.append(Unit("text", b.text, tok))
    return out


def window_section(
    sec: Section, header: str, cfg: ChunkingConfig, ct: TokenCounter
) -> list[list[Unit]]:
    """Group a section's units into windows of <= max_tokens (header included)."""
    budget = max(cfg.max_tokens - ct(header) - 1, 50)
    units = section_units(sec, budget, ct)
    total = sum(u.tokens + 1 for x in units for u in (x if isinstance(x, list) else [x]))
    if total <= budget and not any(isinstance(x, list) for x in units):
        return [units] if units else []  # type: ignore[list-item]

    windows: list[list[Unit]] = []
    cur: list[Unit] = []
    cur_tok = 0
    for item in units:
        if isinstance(item, list):  # oversized table: flush, one chunk per row-group
            if cur:
                windows.append(cur)
            windows.extend([part] for part in item)
            cur, cur_tok = [], 0
            continue
        if cur and cur_tok + item.tokens + 1 > budget:
            windows.append(cur)
            cur = _overlap_tail(cur, cfg.overlap_tokens, ct)
            cur_tok = sum(u.tokens + 1 for u in cur)
            if cur_tok + item.tokens + 1 > budget:
                cur, cur_tok = [], 0
        cur.append(item)
        cur_tok += item.tokens + 1
    if cur:
        windows.append(cur)
    return windows


def chunk_sections(
    sections: Iterable[Section],
    spec: SpecConfig,
    cfg: ChunkingConfig,
    ct: TokenCounter = count_tokens,
) -> list[Chunk]:
    """Turn parsed sections into chunks. Part numbers continue across repeated clause numbers."""
    chunks: list[Chunk] = []
    next_part: Counter[str] = Counter()
    for sec in sections:
        header = make_header(spec.id, sec)
        for window in window_section(sec, header, cfg, ct):
            text = header + "\n" + "\n".join(u.text for u in window)
            part = next_part[sec.number]
            next_part[sec.number] += 1
            chunks.append(
                Chunk(
                    chunk_id=f"{spec.short}:{sec.number}:{part}",
                    spec=spec.id,
                    spec_short=spec.short,
                    version=spec.version,
                    release=spec.release,
                    section=sec.number,
                    title=sec.title,
                    breadcrumb=sec.breadcrumb,
                    parent_titles=sec.parent_titles,
                    content_type=content_type_for(sec.number, window),
                    part=part,
                    n_tokens=ct(text),
                    text=text,
                )
            )
    return chunks


# --------------------------------------------------------------------------- checks / stats


def table_rows_consistent(text: str) -> bool:
    """Every Markdown table in `text` has rows with as many cells as its header.
    A new table starts at a line followed by a `|---` separator line."""
    lines = text.splitlines()
    width = None
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            width = None
            continue
        if line.startswith("|---"):
            continue
        n = len(_CELL_SPLIT_RE.split(line)) - 2
        if i + 1 < len(lines) and lines[i + 1].startswith("|---"):
            width = n  # header row of a (new) table
        elif width is None or n != width:
            return False
    return True


def acceptance_checks(chunks: list[Chunk], spec_ids: list[str]) -> list[tuple[str, bool, str]]:
    """Ingestion acceptance checks; returns (name, passed, detail)."""
    res: list[tuple[str, bool, str]] = []
    per_spec = Counter(c.spec for c in chunks)
    res.append(("both specs produce chunks", all(per_spec[s] > 0 for s in spec_ids), str(per_spec)))
    empty = [c.chunk_id for c in chunks if not c.section]
    res.append(("no chunk without section", not empty, f"{len(empty)} empty"))
    ids = Counter(c.chunk_id for c in chunks)
    dups = [i for i, n in ids.items() if n > 1]
    res.append(("chunk_ids unique", not dups, f"{len(dups)} duplicated ids"))
    bad_tables = [c.chunk_id for c in chunks if not table_rows_consistent(c.text)]
    res.append(("no table split mid-row", not bad_tables, ", ".join(bad_tables[:5]) or "ok"))
    return res


def grep_chunks(chunks: list[Chunk], spec: str, pattern: str, limit: int = 6) -> list[str]:
    """Sections of `spec` whose chunk text (header line included) matches `pattern`."""
    rx = re.compile(pattern)
    hits = [f"§{c.section}" for c in chunks if c.spec == spec and rx.search(c.text)]
    return list(dict.fromkeys(hits))[:limit]


SPOT_CHECKS = [
    ("TS 24.501", "5GMM cause #9 text", r"Cause #9 \S+ UE identity"),
    ("TS 24.501", "T3510 in a timer table", r"\| T3510 \|"),
    ("TS 24.501", "T3502 in a timer table", r"\| T3502 \|"),
    ("TS 24.501", "REGISTRATION REQUEST message content", r"REGISTRATION REQUEST message content"),
    ("TS 23.501", "AMF/SMF/UPF clauses", r"^\[TS 23\.501 §6\.2\.\d+ (AMF|SMF|UPF)[ |]"),
    ("TS 23.501", "standardized 5QI table", r"Standardized 5QI to QoS characteristics"),
    ("TS 23.501", "network slicing clauses", r"^\[TS 23\.501 §.*\d Network slicing( >|\])"),
]


def stats(chunks: list[Chunk]) -> dict:
    out: dict = {}
    for spec in sorted({c.spec for c in chunks}):
        cs = [c for c in chunks if c.spec == spec]
        toks = sorted(c.n_tokens for c in cs)
        out[spec] = {
            "chunks": len(cs),
            "sections": len({c.section for c in cs}),
            "tokens_min": toks[0],
            "tokens_median": int(statistics.median(toks)),
            "tokens_p95": toks[int(0.95 * (len(toks) - 1))],
            "tokens_max": toks[-1],
            "table_chunks": sum(c.content_type == "table" for c in cs),
            "chunks_with_tables": sum("\n|" in c.text for c in cs),
            "annex_chunks": sum(c.section[0].isalpha() for c in cs),
            "multi_part_sections": len({c.section for c in cs if c.part > 0}),
            "content_types": dict(Counter(c.content_type for c in cs)),
        }
    return out


def write_parse_report(
    path: Path,
    reports: dict[str, list[ParseReport]],
    empty_sections: dict[str, list[str]],
    chunks: list[Chunk],
    cfg: ChunkingConfig,
    checks: list[tuple[str, bool, str]],
    spots: list[tuple[str, str, list[str]]],
) -> None:
    st = stats(chunks)
    small = [c for c in chunks if c.n_tokens < cfg.min_tokens + 25]
    over = [c for c in chunks if c.n_tokens > cfg.max_tokens]
    L = ["# Parse report", "", "Generated by `python -m src.ingest.chunker`.", ""]
    L += [
        f"Chunking: max_tokens={cfg.max_tokens}, overlap={cfg.overlap_tokens}, "
        f"min_tokens={cfg.min_tokens} (tiktoken cl100k_base).",
        "",
    ]
    L += [
        "## Chunk statistics",
        "",
        "| Metric | " + " | ".join(st) + " |",
        "|---|" + "---|" * len(st),
    ]
    for key in next(iter(st.values())):
        L.append(f"| {key} | " + " | ".join(str(v[key]) for v in st.values()) + " |")
    L += ["", "## Acceptance checks (§5.5)", ""]
    L += [f"- [{'x' if ok else ' '}] {name}: {detail}" for name, ok, detail in checks]
    L += ["", "## Spot checks (sections found by searching the chunks)", ""]
    L += [f"- {spec} — {what}: {', '.join(hits) or 'NOT FOUND'}" for spec, what, hits in spots]
    for spec, reps in reports.items():
        for r in reps:
            L += [
                "",
                f"## {spec} — `{r.doc_name}`",
                "",
                f"- sections: {r.n_sections}, tables: {r.n_tables}, figures: {r.n_figures}",
                f"- skipped annexes: {r.skipped_annexes or 'none'}",
                f"- repeated clause numbers in the spec: {r.duplicate_sections or 'none'}",
                f"- skipped paragraph styles: {dict(r.skipped_styles)}",
                f"- unmatched headings (kept as text): {r.unmatched_headings or 'none'}",
            ]
        es = empty_sections.get(spec, [])
        L.append(
            f"- headings with no text of their own ({len(es)}): {', '.join(es[:60])}"
            + (" …" if len(es) > 60 else "")
        )
    L += ["", f"## Chunks below {cfg.min_tokens + 25} tokens incl. header ({len(small)})", ""]
    L += [f"- `{c.chunk_id}` ({c.n_tokens}) {c.title}" for c in small[:40]]
    if len(small) > 40:
        L.append(f"- … {len(small) - 40} more")
    L += ["", f"## Chunks above max_tokens ({len(over)}) — single oversize rows/sentences", ""]
    L += [f"- `{c.chunk_id}` ({c.n_tokens})" for c in over]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


def write_chunks(chunks: list[Chunk], path: Path = CHUNKS_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        for c in chunks:
            fh.write(json.dumps(c.model_dump(), ensure_ascii=False) + "\n")


def load_chunks(path: Path = CHUNKS_PATH) -> list[Chunk]:
    """Read `chunks.jsonl` (raises FileNotFoundError with a hint if missing)."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run `python -m src.ingest.chunker` first")
    with path.open(encoding="utf-8") as fh:
        return [Chunk.model_validate_json(line) for line in fh if line.strip()]


def build_chunks(out: Path = CHUNKS_PATH) -> list[Chunk]:
    """Parse both specs, chunk them, write chunks.jsonl + parse_report.md. Returns chunks."""
    settings = load_settings()
    cfg = settings.chunking
    all_chunks: list[Chunk] = []
    reports: dict[str, list[ParseReport]] = {}
    empty: dict[str, list[str]] = defaultdict(list)
    for spec in settings.corpus.specs:
        path = RAW_DIR / spec.file
        if not path.exists():
            raise FileNotFoundError(f"{path} missing: run `python scripts/download_corpus.py`")
        t0 = time.perf_counter()
        sections, reps = parse_spec_file(path)
        reports[spec.id] = reps
        empty[spec.id] = [s.number for s in sections if not s.blocks]
        chunks = chunk_sections(sections, spec, cfg)
        log.info(
            "%s: %d sections -> %d chunks in %.1fs",
            spec.id,
            len(sections),
            len(chunks),
            time.perf_counter() - t0,
        )
        all_chunks.extend(chunks)
    write_chunks(all_chunks, out)
    spec_ids = [s.id for s in settings.corpus.specs]
    checks = acceptance_checks(all_chunks, spec_ids)
    spots = [(s, w, grep_chunks(all_chunks, s, p)) for s, w, p in SPOT_CHECKS]
    write_parse_report(
        out.parent / "parse_report.md", reports, empty, all_chunks, cfg, checks, spots
    )
    return all_chunks


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    argparse.ArgumentParser(description="Parse + chunk the corpus").parse_args()
    chunks = build_chunks()
    st = stats(chunks)
    print(f"Wrote {len(chunks)} chunks to {CHUNKS_PATH}")
    for spec, s in st.items():
        print(f"  {spec}: {s}")
    settings = load_settings()
    checks = acceptance_checks(chunks, [s.id for s in settings.corpus.specs])
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    for spec, what, pattern in SPOT_CHECKS:
        print(f"  spot {spec} {what}: {grep_chunks(chunks, spec, pattern) or 'NOT FOUND'}")
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
