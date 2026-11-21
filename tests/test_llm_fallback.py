"""Behaviour of the Gemini -> Grok fallback chain, with fake providers (no network)."""

from __future__ import annotations

import pytest

from src.generation import llm as llm_mod
from src.generation.llm import REFUSAL, FallbackLLM, ProviderError, build_llm


class FakeProvider:
    """Replays a scripted sequence of outcomes: a string is returned, an exception raised."""

    def __init__(self, name: str, outcomes: list[str | ProviderError]):
        self.name = name
        self.model = f"{name}-fake"
        self.outcomes = list(outcomes)
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def transient() -> ProviderError:
    return ProviderError("429 rate limited", transient=True)


def permanent() -> ProviderError:
    return ProviderError("400 bad request", transient=False)


def make_llm(*providers: FakeProvider, max_retries: int = 2) -> FallbackLLM:
    return FallbackLLM(list(providers), max_retries=max_retries, backoff_s=0)


def test_refusal_sentence_is_exact():
    assert REFUSAL == "I could not find this information in the documents."


def test_success_on_primary():
    g, x = FakeProvider("gemini", ["ok"]), FakeProvider("grok", ["unused"])
    res = make_llm(g, x).generate("sys", "user")
    assert (res.text, res.provider, res.model, res.fallback_used) == (
        "ok",
        "gemini",
        "gemini-fake",
        False,
    )
    assert res.errors == []
    assert x.calls == 0


def test_retry_then_success_on_transient_error():
    g = FakeProvider("gemini", [transient(), "ok after retry"])
    x = FakeProvider("grok", ["unused"])
    res = make_llm(g, x).generate("sys", "user")
    assert res.text == "ok after retry"
    assert res.provider == "gemini" and not res.fallback_used
    assert g.calls == 2 and x.calls == 0
    assert len(res.errors) == 1


def test_immediate_fallback_on_permanent_error():
    g = FakeProvider("gemini", [permanent()])
    x = FakeProvider("grok", ["from grok"])
    res = make_llm(g, x).generate("sys", "user")
    assert res.text == "from grok"
    assert res.provider == "grok" and res.fallback_used
    assert g.calls == 1  # no retry on a permanent error


def test_fallback_after_exhausted_retries():
    g = FakeProvider("gemini", [transient(), transient(), transient()])
    x = FakeProvider("grok", ["from grok"])
    res = make_llm(g, x, max_retries=2).generate("sys", "user")
    assert res.provider == "grok" and res.fallback_used
    assert g.calls == 3  # 1 try + 2 retries
    assert len(res.errors) == 3


def test_runtime_error_when_all_fail():
    g = FakeProvider("gemini", [permanent()])
    x = FakeProvider("grok", [transient(), transient()])
    with pytest.raises(RuntimeError, match="All LLM providers failed"):
        make_llm(g, x, max_retries=1).generate("sys", "user")


@pytest.fixture
def no_keys(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    return monkeypatch


def test_value_error_when_no_key_is_set(no_keys):
    with pytest.raises(ValueError, match="No LLM provider"):
        build_llm()


def test_single_provider_when_only_one_key(no_keys):
    no_keys.setenv("XAI_API_KEY", "dummy-key-for-test")
    chain = build_llm()  # constructing the client makes no network call
    assert [p.name for p in chain.providers] == ["grok"]
    assert chain.providers[0].model == llm_mod.DEFAULTS["grok_model"]


def test_force_selects_one_provider(no_keys):
    no_keys.setenv("GEMINI_API_KEY", "dummy-key-for-test")
    no_keys.setenv("XAI_API_KEY", "dummy-key-for-test")
    assert [p.name for p in build_llm(force="grok").providers] == ["grok"]
    assert [p.name for p in build_llm().providers] == ["gemini", "grok"]
