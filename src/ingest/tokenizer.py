"""Telecom-aware tokenizer for BM25 (CLAUDE.md §6). Used for BOTH indexing and querying.

Rules, in order:
1. lowercase (and NBSP -> space);
2. protected patterns are kept whole: cause numbers (`#9` -> `cause_9`), timers (`t3510`),
   section references (`5.5.1.2.4`, `5.35a.1`), hyphenated terms (`s-nssai`, which also emits
   the de-hyphenated variant `snssai` and its parts longer than one character);
3. the rest is split on non-alphanumerics; a small English stopword list is removed
   (telecom words such as "request", "accept", "reject" are never stopwords);
4. the word "cause" followed by a number also emits `cause_<n>` ("cause 9", "cause value 9");
5. optional light suffix stemming (off by default, used only for an experiment).
"""

from __future__ import annotations

import re

STOPWORDS = frozenset(
    """a an and are as at be been being but by can could did do does for from had has have
    how i if in into is it its may might must of on or shall should so such than that the
    their them then there these they this those to was were what when where which while who
    whom why will with would you your about also any each other only same some both either
    via""".split()
)

_MASTER = re.compile(
    r"(?P<cause>#\s?\d+)"
    r"|(?P<timer>\bt\d{4}\b)"
    r"|(?P<section>\b\d+[a-z]?(?:\.\d+[a-z]?)+\b)"
    r"|(?P<hyphen>\b[a-z0-9]+(?:-[a-z0-9]+)+\b)"
    r"|(?P<word>[a-z0-9]+)"
)
_CAUSE_PREFIX = ("cause", "value", "#")


def _stem(tok: str) -> str:
    """Very light English suffix stripping; telecom tokens with digits are left untouched."""
    if any(ch.isdigit() for ch in tok) or len(tok) <= 4:
        return tok
    for suffix in ("ations", "ation", "ings", "ing", "ies", "ed", "es", "s"):
        if tok.endswith(suffix) and len(tok) - len(suffix) >= 3:
            return tok[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return tok


def tokenize(text: str, stem: bool = False) -> list[str]:
    """Return BM25 tokens for `text` (identical function for documents and queries)."""
    text = text.replace(" ", " ").lower()
    tokens: list[str] = []
    prev_words: list[str] = []  # last raw words, to detect "cause [value] <n>"
    for m in _MASTER.finditer(text):
        kind, tok = m.lastgroup, m.group()
        if kind == "cause":
            tokens.append("cause_" + tok.lstrip("#").strip())
            prev_words.append("#")
            continue
        if kind in ("timer", "section"):
            tokens.append(tok)
        elif kind == "hyphen":
            tokens.append(tok)
            tokens.append(tok.replace("-", ""))
            tokens.extend(p for p in tok.split("-") if len(p) > 1 and p not in STOPWORDS)
        else:  # plain word
            if tok.isdigit() and prev_words and prev_words[-1] in _CAUSE_PREFIX:
                if "cause" in prev_words[-2:]:
                    tokens.append(f"cause_{tok}")
            if tok not in STOPWORDS and not (len(tok) == 1 and tok.isalpha()):
                tokens.append(tok)
        prev_words = (prev_words + [tok])[-3:]
    if stem:
        tokens = [_stem(t) for t in tokens]
    return tokens
