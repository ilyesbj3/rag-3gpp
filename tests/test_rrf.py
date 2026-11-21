"""RRF on a hand-computed example, fusion provenance, quotas and part merging."""

import pytest

from src.retrieval.hybrid import fuse, merge_parts, rrf, select_final
from src.schemas import Chunk, RetrievedChunk


def mk(spec_short: str, section: str, part: int = 0, title: str = "T") -> Chunk:
    return Chunk(
        chunk_id=f"{spec_short}:{section}:{part}",
        spec=f"TS {spec_short}",
        spec_short=spec_short,
        version="v",
        release="Rel-18",
        section=section,
        title=title,
        part=part,
        text=f"[TS {spec_short} §{section} {title}]\nbody {section} part {part}",
    )


def test_rrf_hand_computed():
    # k=60: a = 1/61 + 1/62, b = 1/62 + 1/61, c = 1/63, d = 1/63
    s = rrf([["a", "b", "c"], ["b", "a", "d"]], k=60)
    assert s["a"] == pytest.approx(1 / 61 + 1 / 62)
    assert s["b"] == pytest.approx(1 / 62 + 1 / 61)
    assert s["c"] == pytest.approx(1 / 63) and s["d"] == pytest.approx(1 / 63)


def test_rrf_rewards_agreement():
    s = rrf([["x", "y"], ["y", "z"]], k=60)
    assert s["y"] > s["x"] > s["z"] or s["y"] > s["x"]


def test_fuse_keeps_provenance():
    a, b, c = mk("24.501", "1"), mk("24.501", "2"), mk("24.501", "3")
    out = fuse([(a, 0.9), (b, 0.8)], [(b, 7.0), (c, 3.0)], k=60, top_n=10)
    assert [r.chunk.chunk_id for r in out][0] == b.chunk_id  # in both lists
    rb = out[0]
    assert (rb.dense_rank, rb.bm25_rank, rb.bm25_score) == (2, 1, 7.0)
    rc = next(r for r in out if r.chunk.chunk_id == c.chunk_id)
    assert rc.dense_rank is None and rc.bm25_rank == 2


def test_fuse_without_sparse_keeps_dense_order():
    a, b = mk("23.501", "1"), mk("23.501", "2")
    out = fuse([(a, 0.9), (b, 0.8)], None, k=60, top_n=10)
    assert [r.chunk.chunk_id for r in out] == [a.chunk_id, b.chunk_id]


def ranked(chunks):
    return [RetrievedChunk(chunk=c) for c in chunks]


def test_quota_when_both_specs():
    cands = ranked([mk("24.501", str(i)) for i in range(1, 7)] + [mk("23.501", "9")])
    out = select_final(cands, k=4, route_specs={"TS 23.501", "TS 24.501"}, min_per_spec=2)
    specs = [r.chunk.spec for r in out]
    assert len(out) == 4 and specs.count("TS 23.501") == 1  # only one 23.501 candidate exists
    assert out[-1].chunk.spec == "TS 23.501"  # swapped in for the lowest-ranked 24.501 chunk


def test_no_quota_for_single_spec_route():
    cands = ranked([mk("24.501", str(i)) for i in range(1, 7)] + [mk("23.501", "9")])
    out = select_final(cands, k=4, route_specs={"TS 24.501"}, min_per_spec=2)
    assert all(r.chunk.spec == "TS 24.501" for r in out)


def test_adjacent_parts_are_merged_and_slot_refilled():
    cands = ranked(
        [mk("24.501", "5.5", 0), mk("24.501", "5.5", 1), mk("24.501", "6"), mk("24.501", "7")]
    )
    out = select_final(cands, k=3, route_specs={"TS 24.501"}, min_per_spec=0)
    ids = [r.chunk.chunk_id for r in out]
    assert ids == ["24.501:5.5:0+1", "24.501:6:0", "24.501:7:0"]
    assert "part 0" in out[0].chunk.text and "part 1" in out[0].chunk.text
    assert out[0].chunk.text.count("[TS 24.501 §5.5") == 1


def test_non_adjacent_parts_stay_separate():
    out = merge_parts(ranked([mk("24.501", "5.5", 0), mk("24.501", "5.5", 3)]))
    assert len(out) == 2
