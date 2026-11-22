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


def parse_sets(pairs: list[str] | None) -> dict[str, Any]:
    """`["retrieval.routing_mode=soft", "reranker.max_length=512"]` -> nested overrides.
    Values are parsed as YAML scalars (numbers, booleans, strings)."""
    import yaml

    out: dict[str, Any] = {}
    for pair in pairs or []:
        key, _, raw = pair.partition("=")
        if not raw:
            raise ValueError(f"--set expects key=value, got {pair!r}")
        *parents, leaf = key.strip().split(".")
        node = out
        for part in parents:
            node = node.setdefault(part, {})
        node[leaf] = yaml.safe_load(raw)
    return out
