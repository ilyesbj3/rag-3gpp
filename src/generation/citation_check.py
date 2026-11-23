"""Post-generation citation check.

- Extracts citations such as `[TS 24.501 §5.5.1.2.4]` (also `[TS 24.501 Section 5.5]`,
  `[TS24.501 § 5.5]` and several citations inside one bracket) and normalizes them.
- valid: (spec, section) is one of the context labels; loose-valid: the cited section is an
  ancestor of a provided section of the same spec (kept, reported separately).
- Invalid citations are removed from the text and reported in warnings.
- An answer containing the refusal sentence is normalized to exactly that sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from src.generation.llm import REFUSAL
from src.schemas import Citation

_SECTION = r"(?:[A-Z]\.)?\d+[A-Za-z]?(?:\.\d+[A-Za-z]?)*|[A-Z]"
CITATION_RE = re.compile(
    rf"TS\s?(?P<spec>\d{{2}}\.\d{{3}})\s?(?:§|Section|clause)\s?(?P<section>{_SECTION})(?![\w.])",
    re.IGNORECASE,
)
BRACKET_RE = re.compile(r"\[([^\[\]]*?TS\s?\d{2}\.\d{3}[^\[\]]*?)\]", re.IGNORECASE)
NOT_GROUNDED = "Answer not grounded in cited sources"


@dataclass
class CheckResult:
    text: str
    refused: bool
    citations: list[Citation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _norm_section(s: str) -> str:
    return s.rstrip(".")


def _is_refusal(text: str) -> bool:
    flat = " ".join(text.split()).lower()
    return REFUSAL.lower().rstrip(".") in flat


def check_citations(text: str, context_labels: set[tuple[str, str]]) -> CheckResult:
    """Validate citations of `text` against `context_labels` = {("TS 24.501", "5.5.1"), ...}."""
    if _is_refusal(text):
        return CheckResult(text=REFUSAL, refused=True)

    citations: list[Citation] = []
    invalid: list[str] = []

    def classify(spec: str, section: str) -> Citation:
        if (spec, section) in context_labels:
            return Citation(spec=spec, section=section, valid=True)
        loose = any(s == spec and sec.startswith(section + ".") for s, sec in context_labels)
        return Citation(spec=spec, section=section, valid=loose, loose=loose)

    def replace(m: re.Match[str]) -> str:
        found = list(CITATION_RE.finditer(m.group(1)))
        if not found:
            return m.group(0)
        kept = []
        for f in found:
            spec, section = f"TS {f['spec']}", _norm_section(f["section"])
            cit = classify(spec, section)
            citations.append(cit)
            if cit.valid:
                kept.append(f"[{spec} §{section}]")
            else:
                invalid.append(f"[{spec} §{section}]")
        return "".join(kept)

    new_text = BRACKET_RE.sub(replace, text)
    new_text = re.sub(r"[ \t]+([.,;:])", r"\1", new_text)  # space left before punctuation
    new_text = re.sub(r"[ \t]{2,}", " ", new_text).strip()

    warnings: list[str] = []
    if invalid:
        warnings.append("Removed citations not among the retrieved sources: " + ", ".join(invalid))
    if not any(c.valid for c in citations):
        warnings.append(NOT_GROUNDED)
    return CheckResult(text=new_text, refused=False, citations=citations, warnings=warnings)
