"""Dense + BM25 retrieval, Reciprocal Rank Fusion, spec quotas and part merging (§8.2, §8.4)."""

from __future__ import annotations

from collections.abc import Sequence

from src.schemas import Chunk, RetrievedChunk


def rrf(
    ranked_lists: Sequence[Sequence[str]],
    k: int = 60,
    weights: Sequence[float] | None = None,
) -> dict[str, float]:
    """(Weighted) Reciprocal Rank Fusion: score(d) = sum over lists of w / (k + rank),
    ranks from 1; every weight is 1 when `weights` is None."""
    weights = weights or [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}
    for lst, w in zip(ranked_lists, weights, strict=True):
        for rank, doc_id in enumerate(lst, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + w / (k + rank)
    return scores


def fuse(
    dense: list[tuple[Chunk, float]],
    sparse: list[tuple[Chunk, float]] | None,
    k: int,
    top_n: int,
    bm25_weight: float = 1.0,
    spec_boost: dict[str, float] | None = None,
) -> list[RetrievedChunk]:
    """Fuse dense and (optional) sparse results, keeping per-list provenance.

    `bm25_weight` weights the sparse list in RRF. `spec_boost` (soft routing) multiplies the
    fused score of chunks from the given specs. Without sparse results and boost the dense
    order is kept (RRF of one list is monotonic anyway)."""
    by_id: dict[str, RetrievedChunk] = {}
    for rank, (c, s) in enumerate(dense, start=1):
        by_id[c.chunk_id] = RetrievedChunk(chunk=c, dense_rank=rank, dense_score=s)
    for rank, (c, s) in enumerate(sparse or [], start=1):
        rc = by_id.setdefault(c.chunk_id, RetrievedChunk(chunk=c))
        rc.bm25_rank, rc.bm25_score = rank, s
    lists, weights = [[c.chunk_id for c, _ in dense]], [1.0]
    if sparse is not None:
        lists.append([c.chunk_id for c, _ in sparse])
        weights.append(bm25_weight)
    scores = rrf(lists, k, weights)
    for doc_id, rc in by_id.items():
        boost = (spec_boost or {}).get(rc.chunk.spec, 1.0)
        rc.rrf_score = scores.get(doc_id, 0.0) * boost
    ordered = sorted(by_id.values(), key=lambda r: (-(r.rrf_score or 0.0), r.chunk.chunk_id))
    return ordered[:top_n]


def _merge_adjacent(a: RetrievedChunk, b: RetrievedChunk) -> RetrievedChunk:
    """Merge two consecutive parts of one section into a single source (keeps best scores)."""
    first, second = sorted([a, b], key=lambda r: r.chunk.part)
    header, body1 = (
        first.chunk.text.split("\n", 1) if "\n" in first.chunk.text else (first.chunk.text, "")
    )
    body2 = second.chunk.body
    merged = first.chunk.model_copy(
        update={
            "chunk_id": f"{first.chunk.chunk_id}+{second.chunk.part}",
            "text": f"{header}\n{body1}\n{body2}",
            "n_tokens": first.chunk.n_tokens + second.chunk.n_tokens,
        }
    )
    best = a if (a.final_rank or 0) <= (b.final_rank or 0) else b
    return best.model_copy(update={"chunk": merged})


def merge_parts(selected: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Merge selected chunks that are adjacent parts of the same section occurrence."""
    out: list[RetrievedChunk] = []
    for rc in selected:
        merged = False
        for i, kept in enumerate(out):
            kc, c = kept.chunk, rc.chunk
            if (kc.spec, kc.section, kc.title) != (c.spec, c.section, c.title):
                continue
            kept_parts = [int(p) for p in kc.chunk_id.split(":")[-1].split("+")]
            if c.part in (min(kept_parts) - 1, max(kept_parts) + 1):
                out[i] = _merge_adjacent(kept, rc)
                merged = True
                break
        if not merged:
            out.append(rc)
    return out


def select_final(
    ranked: list[RetrievedChunk],
    k: int,
    route_specs: set[str],
    min_per_spec: int,
) -> list[RetrievedChunk]:
    """Pick the final top-k: quota per spec when both are routed, then merge adjacent parts.

    Slots freed by merging are refilled with the next candidates."""
    if not ranked:
        return []
    for i, rc in enumerate(ranked, start=1):
        rc.final_rank = i
    pool = list(ranked)
    selected: list[RetrievedChunk] = []
    while pool and len(selected) < k:
        need = k - len(selected)
        selected = merge_parts(selected + pool[:need])
        pool = pool[need:]

    if len(route_specs) > 1 and min_per_spec > 0:
        for spec in sorted(route_specs):
            have = [r for r in selected if r.chunk.spec == spec]
            extra = [r for r in pool if r.chunk.spec == spec]
            while len(have) < min_per_spec and extra:
                counts = {s: sum(r.chunk.spec == s for r in selected) for s in route_specs}
                dominant = max(counts, key=counts.get)
                if dominant == spec or counts[dominant] <= min_per_spec:
                    break
                victim = max(
                    (r for r in selected if r.chunk.spec == dominant),
                    key=lambda r: r.final_rank or 0,
                )
                selected.remove(victim)
                newcomer = extra.pop(0)
                pool.remove(newcomer)
                selected.append(newcomer)
                have.append(newcomer)
        selected.sort(key=lambda r: r.final_rank or 0)
    return selected
