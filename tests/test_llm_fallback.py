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
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "XAI_API_KEY", "GROQ_API_KEY"):
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


def test_groq_is_second_in_the_chain(no_keys):
    for var in ("GEMINI_API_KEY", "GROQ_API_KEY", "XAI_API_KEY"):
        no_keys.setenv(var, "dummy-key-for-test")
    chain = build_llm()
    assert [p.name for p in chain.providers] == ["gemini", "groq", "grok"]
    groq = chain.providers[1]
    assert groq.BASE_URL == "https://api.groq.com/openai/v1"
    assert groq.model == llm_mod.DEFAULTS["groq_model"]


def test_groq_only_key(no_keys):
    no_keys.setenv("GROQ_API_KEY", "dummy-key-for-test")
    assert [p.name for p in build_llm().providers] == ["groq"]
    assert [p.name for p in build_llm(force="groq").providers] == ["groq"]


# ----------------------------------------------------------------------------- rate limits
def test_rate_limit_waits_retry_after_instead_of_backoff(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(llm_mod.time, "sleep", slept.append)
    g = FakeProvider("groq", [ProviderError("429", transient=True, retry_after=42.0), "ok"])
    res = FallbackLLM([g], max_retries=2, backoff_s=1.5).generate("sys", "user")
    assert res.text == "ok"
    assert slept == [42.5]  # Retry-After honoured (+0.5 s margin), not 1.5 s backoff


def test_rate_limit_longer_than_max_wait_falls_back_immediately(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(llm_mod.time, "sleep", slept.append)
    daily = ProviderError("429 daily quota", transient=True, retry_after=23000.0)
    g = FakeProvider("gemini", [daily])
    x = FakeProvider("groq", ["from groq"])
    res = FallbackLLM([g, x], max_retries=2, max_wait_s=90).generate("sys", "user")
    assert res.provider == "groq" and res.fallback_used
    assert slept == [] and g.calls == 1


def test_transient_without_retry_after_keeps_backoff(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(llm_mod.time, "sleep", slept.append)
    g = FakeProvider("gemini", [transient(), transient(), "ok"])
    FallbackLLM([g], max_retries=2, backoff_s=1.5).generate("sys", "user")
    assert slept == [1.5, 3.0]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Please try again in 8.9325s. Need more tokens?", 8.9325),
        ("Rate limit reached... try again in 1m2.5s", 62.5),
        ("Please retry in 59.755569523s.", 59.755569523),
        ("try again in 585ms", 0.585),
        ("Please retry in 18h46m25.940755311s.", 18 * 3600 + 46 * 60 + 25.940755311),
        ("Please try again in 43m2.496s.", 43 * 60 + 2.496),
        ("no hint here", None),
    ],
)
def test_retry_after_parsing(text, expected):
    got = llm_mod.retry_after_seconds(text)
    assert got == pytest.approx(expected) if expected is not None else got is None


def test_groq_provider_maps_429_with_retry_after_header(no_keys):
    import httpx
    import openai

    no_keys.setenv("GROQ_API_KEY", "dummy-key-for-test")
    prov = llm_mod.GroqProvider("m", temperature=0, max_tokens=10, timeout_s=5)
    response = httpx.Response(
        429, headers={"retry-after": "7"}, request=httpx.Request("POST", "https://example.test")
    )

    class Boom:
        def create(self, **kw):
            raise openai.RateLimitError("rate limited", response=response, body=None)

    prov._client = type("C", (), {"chat": type("Ch", (), {"completions": Boom()})()})()
    with pytest.raises(ProviderError) as info:
        prov.complete("sys", "user")
    assert info.value.transient and info.value.retry_after == 7.0
