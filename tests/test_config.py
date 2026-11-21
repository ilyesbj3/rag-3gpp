"""Settings load from config.yaml and accept nested overrides (used for ablations)."""

from src.config import load_settings


def test_loads_both_specs():
    s = load_settings()
    assert [sp.id for sp in s.corpus.specs] == ["TS 23.501", "TS 24.501"]
    assert s.spec("24.501").file == "24501-ie0.zip"


def test_overrides_are_nested_and_partial():
    s = load_settings({"retrieval": {"use_hybrid": False}})
    assert s.retrieval.use_hybrid is False
    assert s.retrieval.use_reranker is True  # untouched
    assert s.retrieval.rrf_k == 60
