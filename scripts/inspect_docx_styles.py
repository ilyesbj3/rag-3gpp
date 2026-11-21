"""Print the paragraph-style histogram of the spec Word documents (used to tune the parser).

Usage:
    python scripts/inspect_docx_styles.py [paths...] [--out data/processed/style_report.md]

Paths may be .zip archives (every .docx inside is inspected, read in memory) or .docx files.
Without paths, all zips in data/raw/ are inspected. Body paragraphs and table-cell
paragraphs are counted separately, and a few sample texts are shown per style.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
N_SAMPLES = 3


def iter_docx(path: Path):
    """Yield (name, Document) for a .docx or for every .docx inside a .zip."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            for name in sorted(n for n in zf.namelist() if n.lower().endswith(".docx")):
                yield f"{path.name}/{name}", Document(io.BytesIO(zf.read(name)))
    else:
        yield path.name, Document(str(path))


def style_name(p: Paragraph) -> str:
    try:
        return p.style.name if p.style is not None else "(none)"
    except (KeyError, ValueError):
        return "(unknown)"


def inspect(doc) -> dict:
    body: Counter[str] = Counter()
    cells: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)
    n_tables = 0
    for child in doc.element.body.iterchildren():
        if child.tag == W_NS + "p":
            p = Paragraph(child, doc)
            s = style_name(p)
            body[s] += 1
            text = p.text.strip().replace("\t", " <TAB> ")
            if text and len(samples[s]) < N_SAMPLES:
                samples[s].append(text[:110])
        elif child.tag == W_NS + "tbl":
            n_tables += 1
            for row in Table(child, doc).rows:
                seen = set()
                for cell in row.cells:
                    if id(cell._tc) in seen:  # merged cells repeat the same element
                        continue
                    seen.add(id(cell._tc))
                    for p in cell.paragraphs:
                        cells[style_name(p)] += 1
    return {"body": body, "cells": cells, "samples": samples, "n_tables": n_tables}


def render(name: str, res: dict) -> str:
    lines = [f"## {name}", "", f"Tables: {res['n_tables']}", ""]
    lines += ["### Body paragraph styles", "", "| Style | Count | Samples |", "|---|---:|---|"]
    for s, c in res["body"].most_common():
        smp = " ⟂ ".join(x.replace("|", "\\|") for x in res["samples"].get(s, []))
        lines.append(f"| `{s}` | {c} | {smp} |")
    lines += ["", "### Table-cell paragraph styles", "", "| Style | Count |", "|---|---:|"]
    lines += [f"| `{s}` | {c} |" for s, c in res["cells"].most_common()]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--out", type=Path, default=ROOT / "data/processed/style_report.md")
    args = ap.parse_args()

    paths = args.paths or sorted((ROOT / "data/raw").glob("*.zip"))
    if not paths:
        print("No input. Run scripts/download_corpus.py first.", file=sys.stderr)
        return 1
    parts = ["# Word style inspection\n"]
    for path in paths:
        for name, doc in iter_docx(path):
            res = inspect(doc)
            parts.append(render(name, res))
            print(
                f"\n=== {name}: {sum(res['body'].values())} body paragraphs, "
                f"{res['n_tables']} tables"
            )
            for s, c in res["body"].most_common(40):
                print(f"  {c:7d}  {s}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(parts), encoding="utf-8")
    print(f"\nFull report: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
