"""`--set key=value` parsing used by the evaluation CLIs."""

import pytest

from eval.configs import parse_sets


def test_parse_sets_nested_and_typed():
    out = parse_sets(
        ["retrieval.routing_mode=soft", "retrieval.bm25_weight=0.5", "reranker.max_length=512"]
    )
    assert out == {
        "retrieval": {"routing_mode": "soft", "bm25_weight": 0.5},
        "reranker": {"max_length": 512},
    }


def test_parse_sets_rejects_missing_value():
    with pytest.raises(ValueError):
        parse_sets(["retrieval.routing_mode"])
