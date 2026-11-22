"""Rule-based query routing by specification (CLAUDE.md §8.1).

Each matching signal adds its weight to the spec's score. Decision (version 2, default):
explicit spec mention > cross-cutting phrase (incl. "procedure ... messages") > architecture
AND NAS signals both present (each >= 1) > one spec dominates (score >= 2x the other and
>= 1) > both specs (also when there is no signal at all).

Version 1 (the original rules, kept for before/after comparisons, `retrieval.router_version`)
has no mixed-signal rule, no "procedure ... messages" phrase and a narrower vocabulary.
"""

from __future__ import annotations

import re

from src.schemas import RouteDecision

TS23 = "TS 23.501"
TS24 = "TS 24.501"
BOTH = {TS23, TS24}
ROUTER_VERSION = 2  # default rules; recorded in every answer's config snapshot

_I = re.IGNORECASE

_NAS_VERB = r"(?:request|accept|reject|command|complete)"
_NAS_PROC_V1 = (
    r"(?:de-?registration|registration|service|authentication|security mode|identity|"
    r"configuration update|pdu session (?:establishment|modification|release)|notification)"
)
# v2: "PDU session request" also names a NAS message
_NAS_PROC_V2 = _NAS_PROC_V1.replace(
    r"pdu session (?:establishment|modification|release)",
    r"pdu session(?: establishment| modification| release)?",
)


def _signals_24(nas_proc: str) -> list[tuple[re.Pattern[str], float]]:
    """(pattern, weight). Patterns run on the original question, case-insensitively."""
    return [
        (re.compile(r"cause\s*(?:value\s*)?#?\s*\d+", _I), 3),
        (re.compile(r"\bcause values?\b", _I), 2),
        (re.compile(r"\b5g(?:mm|sm)\b", _I), 2),
        (re.compile(r"\bnas\b", _I), 1),
        (re.compile(r"\bt3\d{3}\b", _I), 3),
        (re.compile(r"\binformation elements?\b|\bies?\b", _I), 2),
        (re.compile(rf"\b{nas_proc}\s+{_NAS_VERB}\b", _I), 2),
        (re.compile(r"\bmessage type\b", _I), 2),
        (re.compile(r"\boctets?\b", _I), 2),
        (re.compile(r"\b(?:en)?coding\b|\bcoded\b", _I), 1),
        (re.compile(r"\bbits?\b", _I), 1),
        (re.compile(r"\bstage[ -]?3\b", _I), 2),
        (re.compile(r"\bmessages?\b", _I), 0.5),
    ]


SIGNALS_24 = {1: _signals_24(_NAS_PROC_V1), 2: _signals_24(_NAS_PROC_V2)}

_NF = r"\b(?:amf|smf|upf|pcf|udm|udr|ausf|nssf|nef|nrf|af|scp|sepp|nwdaf)\b"
# Words that ask about what a network function is or does (not just name it in passing).
_ARCH_CONTEXT = {
    1: r"\b(?:role|function|functionalit|responsib|architecture|purpose|what is|what does)",
    2: r"\b(?:role|function|functionalit|responsib|architecture|purpose|what is|what does|"
    r"handl|select|interact|serve|manage|work)",
}

SIGNALS_23: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\breference points?\b", _I), 2),
    (re.compile(r"\bservice-based\b|\bsba\b", _I), 2),
    (re.compile(r"\barchitecture\b", _I), 2),
    (re.compile(r"\bqos\b", _I), 1),
    (re.compile(r"\b5qi\b", _I), 2),
    (re.compile(r"\bqos flows?\b", _I), 1),
    (re.compile(r"\barp\b|\bgbr\b", _I), 1),
    (re.compile(r"\bnetwork slic", _I), 2),
    (re.compile(r"\bs-?nssai\b|\bnssai\b", _I), 1),
    (re.compile(r"\broaming\b", _I), 1),
    (re.compile(r"\bhome[- ]routed\b|\blocal breakout\b", _I), 2),
    (re.compile(r"\bedge computing\b", _I), 2),
    (re.compile(r"\bssc mode|\bsession and service continuity\b", _I), 2),
    (re.compile(r"\bregistration area\b", _I), 1),
    (re.compile(r"\bstage[ -]?2\b", _I), 2),
    (re.compile(r"\bdeployment", _I), 1),
    (re.compile(r"\bnetwork functions?\b", _I), 2),
]

_CROSS_V1 = [
    re.compile(r"procedure and the (?:nas )?messages", _I),
    re.compile(r"\bend-to-end\b", _I),
    re.compile(r"architecture and signall?ing", _I),
    re.compile(r"\b(?:stage 2 and stage 3|both specifications|both specs)\b", _I),
]
CROSS_PHRASES = {
    1: _CROSS_V1,
    # v2: a procedure together with the messages it uses (Stage 2 + Stage 3 signalling)
    2: _CROSS_V1
    + [re.compile(r"\bprocedures?\b.*\bmessages?\b|\bmessages?\b.*\bprocedures?\b", _I)],
}
# v2: architecture AND NAS signals both at least this strong -> search both specs.
MIXED_MIN_SCORE = 1.0
_UE_AMF = re.compile(r"between the ue and the amf", _I)
_PROCEDURE = re.compile(r"\bprocedure", _I)


def _nf_role_score(q: str, version: int) -> float:
    """Network function names count for TS 23.501 only when asked about role/architecture."""
    if re.search(_NF, q, _I) and re.search(_ARCH_CONTEXT[version], q, _I):
        return 2.0
    return 0.0


def route(question: str, use_routing: bool = True, version: int = ROUTER_VERSION) -> RouteDecision:
    """Decide which spec(s) to search for `question` (rules of router `version` 1 or 2)."""
    if not use_routing:
        return RouteDecision(specs=set(BOTH), reason="routing disabled")
    if version not in SIGNALS_24:
        raise ValueError(f"unknown router version {version}")
    q = question
    mentions = {TS23} if re.search(r"23\.501", q) else set()
    if re.search(r"24\.501", q):
        mentions.add(TS24)
    s24 = sum(w for rx, w in SIGNALS_24[version] if rx.search(q))
    s23 = sum(w for rx, w in SIGNALS_23 if rx.search(q)) + _nf_role_score(q, version)
    scores = {TS23: s23, TS24: s24}
    if mentions:
        return RouteDecision(specs=mentions, reason="explicit spec mention", scores=scores)
    if any(rx.search(q) for rx in CROSS_PHRASES[version]) or (
        _UE_AMF.search(q) and _PROCEDURE.search(q)
    ):
        return RouteDecision(specs=set(BOTH), reason="cross-spec phrase", scores=scores)
    if version >= 2 and s23 >= MIXED_MIN_SCORE and s24 >= MIXED_MIN_SCORE:
        return RouteDecision(specs=set(BOTH), reason="architecture and NAS signals", scores=scores)
    if s24 >= 1 and s24 >= 2 * s23:
        return RouteDecision(specs={TS24}, reason="NAS / stage 3 signals", scores=scores)
    if s23 >= 1 and s23 >= 2 * s24:
        return RouteDecision(specs={TS23}, reason="architecture / stage 2 signals", scores=scores)
    reason = "no signal" if s23 == s24 == 0 else "mixed signals"
    return RouteDecision(specs=set(BOTH), reason=reason, scores=scores)
