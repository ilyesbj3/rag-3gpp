"""Named ablation configurations (hybrid, reranker, routing) used by both evaluations."""

from __future__ import annotations

from typing import Any

# name -> (use_hybrid, use_reranker, use_routing)
CONFIGS: dict[str, tuple[bool, bool, bool]] = {
    "best": (True, True, True),
    "no_hybrid": (False, True, True),
    "no_reranker": (True, False, True),
    "no_routing": (True, True, False),
    "hybrid_only": (True, False, False),
    "reranker_only": (False, True, False),
    "routing_only": (False, False, True),
    "baseline": (False, False, False),
}


def overrides_for(name: str) -> dict[str, Any]:
    h, r, t = CONFIGS[name]
    return {"retrieval": {"use_hybrid": h, "use_reranker": r, "use_routing": t}}


def describe(name: str) -> str:
    h, r, t = CONFIGS[name]
    on = lambda b: "on" if b else "off"  # noqa: E731
    return f"hybrid {on(h)}, reranker {on(r)}, routing {on(t)}"
