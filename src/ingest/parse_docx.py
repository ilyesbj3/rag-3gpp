"""Parse a 3GPP spec .docx into an ordered list of sections with text and table blocks.

Findings from the real documents drive the rules (CLAUDE.md §5.1):
- headings use `Heading N` and the custom styles `H6` / `H2`; the level comes from the
  section number depth, not from the style (annex sub-clauses are styled `Heading 1`);
- clause numbers may carry letter suffixes (`5.35A.1`, `4.2.5a`);
- annex titles are `Annex X (informative):<line break>Title`;
- the cover page lives in tables before `1 Scope` -> everything before it is skipped;
- the "Change history" annex is skipped.
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from docx import Document
from docx.text.paragraph import Paragraph

log = logging.getLogger(__name__)

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

HEADING_STYLE_RE = re.compile(r"^(Heading \d|H\d)$")
SECTION_RE = re.compile(r"^(?P<num>(?:[A-Z]\.)?\d+[A-Za-z]?(?:\.\d+[A-Za-z]?)*)\s+(?P<title>.+)$")
ANNEX_RE = re.compile(
    r"^Annex (?P<letter>[A-Z])\s*\((?:normative|informative)\):\s*(?P<title>.+)$", re.I
)
BULLET_RE = re.compile(r"^B(\d)$")
SKIP_STYLES_PREFIX = ("toc", "TOC", "TT", "FP", "Z")
CHANGE_HISTORY = "change history"


@dataclass
class Block:
    """A paragraph-level text unit or a whole table inside a section."""

    kind: Literal["text", "table"]
    text: str  # paragraph text, or the table rendered as Markdown
    rows: list[list[str]] | None = None  # tables only: header row first
    table_title: str | None = None  # tables only: preceding `TH` paragraph


@dataclass
class Section:
    """One heading occurrence and the blocks until the next heading."""

    number: str  # "5.5.1.2.4", "A", "A.1"
    title: str
    breadcrumb: list[str]  # ancestor numbers + own number
    parent_titles: list[str]  # ancestor titles (outermost first)
    occurrence: int = 0  # >0 when the spec repeats a clause number
    blocks: list[Block] = field(default_factory=list)


@dataclass
class ParseReport:
    doc_name: str
    n_sections: int = 0
    n_tables: int = 0
    n_figures: int = 0
    skipped_styles: Counter = field(default_factory=Counter)
    unmatched_headings: list[str] = field(default_factory=list)
    duplicate_sections: list[str] = field(default_factory=list)
    skipped_annexes: list[str] = field(default_factory=list)


def normalize(text: str) -> str:
    """NBSP/TAB/line breaks -> space, collapse whitespace."""
    text = text.replace(" ", " ").replace("\t", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", text).strip()


def section_depth(number: str) -> int:
    return len(number.split("."))


def is_ancestor(anc: str, number: str) -> bool:
    """`5.5` is an ancestor of `5.5.1` but not of `5.50`; `A` is an ancestor of `A.1`."""
    return number.startswith(anc + ".")


def parse_heading(text: str) -> tuple[str, str] | None:
    """Return (section_number, title) for a clause or annex heading, else None."""
    flat = normalize(text)
    m = ANNEX_RE.match(flat)
    if m:
        return m["letter"], m["title"].strip()
    m = SECTION_RE.match(flat)
    if m:
        return m["num"], m["title"].strip()
    return None


def _style(p: Paragraph) -> str:
    try:
        return p.style.name if p.style is not None else ""
    except (KeyError, ValueError):
        return ""


def _cell_text(tc, parent) -> str:
    parts = [normalize(Paragraph(p, parent).text) for p in tc.iter(W + "p")]
    return " ".join(x for x in parts if x).replace("|", "\\|")


def _row_cells(tr):
    """Direct `w:tc` children of a row, including those wrapped in content controls."""
    for child in tr.iterchildren():
        if child.tag == W + "tc":
            yield child
        elif child.tag == W + "sdt":
            yield from child.iter(W + "tc")


def table_rows(tbl, parent) -> list[list[str]]:
    """Table -> rows of cell strings. Horizontal and vertical merges repeat the text;
    a row made of one cell spanning the full width keeps the text in the first column only."""
    rows: list[list[str]] = []
    above: dict[int, str] = {}
    for tr in tbl.iterchildren(W + "tr"):
        row: list[str] = []
        spans: list[int] = []
        for tc in _row_cells(tr):
            span, vmerge = 1, None
            tcpr = tc.find(W + "tcPr")
            if tcpr is not None:
                gs = tcpr.find(W + "gridSpan")
                if gs is not None:
                    span = int(gs.get(W + "val", "1"))
                vm = tcpr.find(W + "vMerge")
                if vm is not None:
                    vmerge = vm.get(W + "val") or "continue"
            col = len(row)
            text = above.get(col, "") if vmerge == "continue" else _cell_text(tc, parent)
            row.extend([text] * span)
            spans.append(span)
        for i, t in enumerate(row):
            above[i] = t
        if len(spans) == 1 and spans[0] > 1:  # full-width row (notes, sub-headers)
            row = [row[0]] + [""] * (len(row) - 1)
        if any(c for c in row):
            rows.append(row)
    width = max((len(r) for r in rows), default=0)
    return [r + [""] * (width - len(r)) for r in rows]


def rows_to_markdown(rows: list[list[str]], title: str | None = None) -> str:
    """Render rows (first = header) as a pipe table, optionally prefixed by its title."""
    if not rows:
        return title or ""
    header, *body = rows
    lines = [title] if title else []
    lines.append("| " + " | ".join(header) + " |")
    lines.append("|" + "---|" * len(header))
    lines += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(lines)


def _paragraph_text(p: Paragraph, style: str) -> str:
    raw = p.text.replace(" ", " ")
    if style == "PL":  # code: keep inner spacing
        return raw.replace("\t", "    ").rstrip()
    m = BULLET_RE.match(style)
    if m:
        level = int(m.group(1))
        text = normalize(re.sub(r"^\s*[-–•]\s*\t?", "", raw))
        return "  " * (level - 1) + "- " + text if text else ""
    if style == "EW":  # abbreviation / term line: "5GC<TAB>5G Core Network"
        head, sep, rest = raw.partition("\t")
        return f"{normalize(head)}: {normalize(rest)}" if sep else normalize(raw)
    if style == "TF":
        text = normalize(raw)
        return f"[Figure: {text}]" if text else ""
    return normalize(raw)


def load_documents(path: Path) -> list[tuple[str, Document]]:
    """Open a .docx, or every .docx inside a .zip (in name order), in memory."""
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            names = sorted(n for n in zf.namelist() if n.lower().endswith(".docx"))
            if not names:
                raise ValueError(
                    f"{path.name}: no .docx inside (legacy .doc must be converted with "
                    "`soffice --headless --convert-to docx`)"
                )
            return [(n, Document(io.BytesIO(zf.read(n)))) for n in names]
    return [(path.name, Document(str(path)))]


def parse_document(doc, doc_name: str = "") -> tuple[list[Section], ParseReport]:
    """Walk the body in order and return the sections with their blocks."""
    report = ParseReport(doc_name=doc_name)
    sections: list[Section] = []
    stack: list[Section] = []
    seen: Counter[str] = Counter()
    started = skipping_annex = False
    pending_th: str | None = None
    current: Section | None = None

    def flush_th() -> None:
        nonlocal pending_th
        if pending_th and current is not None:
            current.blocks.append(Block("text", pending_th))
        pending_th = None

    for el in doc.element.body.iterchildren():
        if el.tag == W + "tbl":
            if not started or skipping_annex or current is None:
                continue
            rows = table_rows(el, doc)
            if rows:
                current.blocks.append(
                    Block("table", rows_to_markdown(rows, pending_th), rows, pending_th)
                )
                report.n_tables += 1
            pending_th = None
            continue
        if el.tag != W + "p":
            continue

        p = Paragraph(el, doc)
        style = _style(p)
        if HEADING_STYLE_RE.match(style):
            parsed = parse_heading(p.text)
            if parsed is None:
                if started and normalize(p.text):
                    report.unmatched_headings.append(f"{style}: {normalize(p.text)[:80]}")
                    if current is not None and not skipping_annex:
                        current.blocks.append(Block("text", normalize(p.text)))
                continue
            number, title = parsed
            if not started:
                if number == "1" and title.lower().startswith("scope"):
                    started = True
                else:
                    continue
            if "." not in number and number.isalpha():  # annex title
                skipping_annex = CHANGE_HISTORY in title.lower()
                if skipping_annex:
                    report.skipped_annexes.append(f"Annex {number}: {title}")
                    current = None
                    continue
            elif skipping_annex:
                continue
            flush_th()
            while stack and not is_ancestor(stack[-1].number, number):
                stack.pop()
            occurrence = seen[number]
            seen[number] += 1
            if occurrence:
                report.duplicate_sections.append(f"{number} {title}")
            current = Section(
                number=number,
                title=title,
                breadcrumb=[s.number for s in stack] + [number],
                parent_titles=[s.title for s in stack],
                occurrence=occurrence,
            )
            sections.append(current)
            stack.append(current)
            continue

        if not started or skipping_annex or current is None:
            continue
        if style.startswith(SKIP_STYLES_PREFIX):
            report.skipped_styles[style] += 1
            continue
        if style == "TH":
            flush_th()
            pending_th = normalize(p.text) or None
            continue
        text = _paragraph_text(p, style)
        if not text:
            continue
        flush_th()
        if style == "TF":
            report.n_figures += 1
        current.blocks.append(Block("text", text))

    flush_th()
    report.n_sections = len(sections)
    return sections, report


def parse_spec_file(path: Path) -> tuple[list[Section], list[ParseReport]]:
    """Parse every .docx of a spec archive, concatenating sections in order."""
    all_sections: list[Section] = []
    reports: list[ParseReport] = []
    for name, doc in load_documents(path):
        secs, rep = parse_document(doc, name)
        log.info("%s: %d sections, %d tables", name, rep.n_sections, rep.n_tables)
        all_sections.extend(secs)
        reports.append(rep)
    return all_sections, reports
