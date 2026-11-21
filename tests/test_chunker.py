"""Chunker and heading parser on small fixture sections (no docx, no tiktoken download)."""

from __future__ import annotations

import pytest

from src.config import ChunkingConfig, SpecConfig
from src.ingest.chunker import chunk_sections, make_header, table_rows_consistent
from src.ingest.parse_docx import Block, Section, is_ancestor, parse_heading, rows_to_markdown

SPEC = SpecConfig(
    id="TS 24.501", short="24.501", version="18.14.0", release="Rel-18", file="x.zip", url="u"
)


def wc(text: str) -> int:
    """Whitespace token counter used instead of tiktoken in tests."""
    return len(text.split())


def section(number: str, blocks: list[Block], parents=("5", "5.5"), titles=("P5", "P55")):
    return Section(
        number=number,
        title=f"Title {number}",
        breadcrumb=[*parents, number],
        parent_titles=list(titles),
        blocks=blocks,
    )


def para(n_words: int, word: str = "w") -> Block:
    return Block("text", " ".join(f"{word}{i}." for i in range(n_words)))


def table(n_rows: int, title: str = "Table 9.9.9.1: Demo") -> Block:
    rows = [["IEI", "Name"]] + [[f"{i}", f"value {i}"] for i in range(n_rows)]
    return Block("table", rows_to_markdown(rows, title), rows, title)


CFG = ChunkingConfig(max_tokens=60, overlap_tokens=8, min_tokens=5)


@pytest.mark.parametrize(
    "text,expected",
    [
        (
            "5.5.1.2.4\tInitial registration accepted by the network",
            ("5.5.1.2.4", "Initial registration accepted by the network"),
        ),
        ("5.35A.2\t\tConfiguration of the MBSR", ("5.35A.2", "Configuration of the MBSR")),
        (
            "4.2.5a\tRadio Capabilities Signalling optimisation",
            ("4.2.5a", "Radio Capabilities Signalling optimisation"),
        ),
        (
            "Annex A (informative):\nCause values for 5GS mobility management",
            ("A", "Cause values for 5GS mobility management"),
        ),
        (
            "A.1\tCauses related to UE identification",
            ("A.1", "Causes related to UE identification"),
        ),
        ("Foreword", None),
    ],
)
def test_parse_heading(text, expected):
    assert parse_heading(text) == expected


def test_is_ancestor_respects_dot_boundaries():
    assert is_ancestor("5.5", "5.5.1")
    assert not is_ancestor("5.5", "5.50")
    assert is_ancestor("A", "A.1")
    assert not is_ancestor("5.35", "5.35A.1")


def test_header_prefix_and_single_chunk():
    sec = section("5.5.1", [para(10)])
    chunks = chunk_sections([sec], SPEC, CFG, wc)
    assert len(chunks) == 1
    c = chunks[0]
    assert c.chunk_id == "24.501:5.5.1:0"
    assert c.text.startswith("[TS 24.501 §5.5.1 Title 5.5.1 | 5 P5 > 5.5 P55]\n")
    assert c.text.split("\n", 1)[0] == make_header("TS 24.501", sec)
    assert c.label == "[TS 24.501 §5.5.1]"


def test_long_section_split_with_overlap_and_parts():
    sec = section("5.5.2", [para(20, "a"), para(20, "b"), para(20, "c")])
    chunks = chunk_sections([sec], SPEC, CFG, wc)
    assert [c.part for c in chunks] == list(range(len(chunks)))
    assert len(chunks) >= 2
    assert all(c.section == "5.5.2" for c in chunks)
    assert all(c.n_tokens <= CFG.max_tokens for c in chunks)
    # overlap: the second window starts with the tail of the first
    assert chunks[1].body.split()[0] in chunks[0].body


def test_sections_are_never_merged():
    secs = [section("5.5.3", [para(2)]), section("5.5.4", [para(2)])]
    chunks = chunk_sections(secs, SPEC, CFG, wc)
    assert [c.section for c in chunks] == ["5.5.3", "5.5.4"]  # short sections stay separate


def test_big_table_split_by_rows_with_header_repeated():
    sec = section("9.9.9", [table(40)])
    chunks = chunk_sections([sec], SPEC, CFG, wc)
    assert len(chunks) > 1
    data_rows = 0
    for c in chunks:
        lines = c.body.splitlines()
        assert lines[0] == "Table 9.9.9.1: Demo"
        assert lines[1] == "| IEI | Name |" and lines[2].startswith("|---")
        assert table_rows_consistent(c.text)
        assert c.content_type == "table"
        data_rows += len(lines) - 3
    assert data_rows == 40  # no row lost or duplicated


def test_small_table_is_not_split():
    sec = section("9.9.8", [para(5), table(3)])
    chunks = chunk_sections([sec], SPEC, CFG, wc)
    assert len(chunks) == 1 and "| 2 | value 2 |" in chunks[0].text


def test_repeated_clause_number_gets_distinct_ids():
    secs = [section("8.2.6.35", [para(3)]), section("8.2.6.35", [para(3)])]
    ids = [c.chunk_id for c in chunk_sections(secs, SPEC, CFG, wc)]
    assert ids == ["24.501:8.2.6.35:0", "24.501:8.2.6.35:1"]


def test_content_types():
    secs = [section("3.1", [para(3)], ("3",), ("Defs",)), section("2", [para(3)], (), ())]
    types = [c.content_type for c in chunk_sections(secs, SPEC, CFG, wc)]
    assert types == ["definitions", "references"]


def test_table_consistency_detects_bad_row():
    good = "x\n| a | b |\n|---|---|\n| 1 | 2 |\n| c |\n|---|\n| 3 |"
    assert table_rows_consistent(good)
    assert not table_rows_consistent("| a | b |\n|---|---|\n| 1 |")
