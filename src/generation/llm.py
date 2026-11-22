"""LLM layer: Gemini as primary provider, Groq then Grok (xAI) as automatic fallbacks.

Usage
-----
    from src.generation.llm import build_llm

    llm = build_llm()                      # Gemini -> Groq -> Grok fallback
    res = llm.generate(system_prompt, user_prompt)
    print(res.text, res.provider, res.fallback_used)

    llm = build_llm(force="grok")          # force one provider (evaluation / LLM comparison)

Environment variables (.env)
----------------------------
    GEMINI_API_KEY=...
    GROQ_API_KEY=...                     # free tier, https://console.groq.com
    XAI_API_KEY=...
    GEMINI_MODEL=gemini-flash-latest     # optional override
    GROQ_MODEL=openai/gpt-oss-120b       # optional override
    GROK_MODEL=grok-4.7                  # optional override
    LLM_TIMEOUT_S=60                     # optional
    LLM_MAX_RETRIES=2                    # retries per provider on transient errors

Run `python -m src.generation.llm --list` to print the model IDs your keys can use.
"""
from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass, field
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

REFUSAL = "I could not find this information in the documents."

DEFAULTS = {
    "gemini_model": os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    "grok_model": os.getenv("GROK_MODEL", "grok-4.7"),
    "groq_model": os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b",
    "temperature": float(os.getenv("LLM_TEMPERATURE", "0")),
    "max_tokens": int(os.getenv("LLM_MAX_TOKENS", "1024")),
    "timeout_s": float(os.getenv("LLM_TIMEOUT_S", "60")),
    "max_retries": int(os.getenv("LLM_MAX_RETRIES", "2")),
}


@dataclass
class LLMResponse:
    text: str
    provider: str                 # "gemini" | "grok"
    model: str
    latency_s: float
    fallback_used: bool = False
    errors: list[str] = field(default_factory=list)


class ProviderError(RuntimeError):
    """Raised by a provider when it cannot produce an answer.

    `retry_after` (seconds) is set on rate limits when the API says how long to wait."""

    def __init__(self, msg: str, transient: bool, retry_after: float | None = None):
        super().__init__(msg)
        self.transient = transient
        self.retry_after = retry_after


def retry_after_seconds(text: str, headers=None) -> float | None:
    """Wait time from a `Retry-After` header or from messages such as
    "Please try again in 8.93s", "try again in 1m2.5s", "Please retry in 59.7s"."""
    if headers is not None:
        value = headers.get("retry-after")
        if value:
            try:
                return float(value)
            except ValueError:
                pass
    m = re.search(r"(?:try|retry)(?: again)? in (?:(\d+)m)?([\d.]+)(ms|s)(?![a-z])", text)
    if not m:
        return None
    minutes, value, unit = m.groups()
    secs = float(value) / 1000 if unit == "ms" else float(value)
    return secs + 60 * int(minutes or 0)


class LLMProvider(Protocol):
    name: str
    model: str

    def complete(self, system: str, user: str) -> str: ...


class GeminiProvider:
    name = "gemini"

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_s: float):
        from google import genai
        from google.genai import types

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not set", transient=False)
        self._types = types
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),  # ms
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        from google.genai import errors

        try:
            resp = self._client.models.generate_content(
                model=self.model,
                contents=user,
                config=self._types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                ),
            )
        except errors.APIError as e:
            transient = e.code in (408, 429) or (e.code or 0) >= 500
            wait = retry_after_seconds(str(e)) if e.code == 429 else None
            raise ProviderError(f"Gemini {e.code}: {e.message}", transient, wait) from e
        except Exception as e:  # network errors, timeouts
            raise ProviderError(f"Gemini error: {e!r}", transient=True) from e

        text = (resp.text or "").strip()
        if not text:
            reason = resp.candidates[0].finish_reason if resp.candidates else None
            raise ProviderError(f"Gemini returned empty text (finish_reason={reason})",
                                transient=False)
        return text


class GrokProvider:
    name = "grok"
    BASE_URL = "https://api.x.ai/v1"
    KEY_ENV = "XAI_API_KEY"
    LABEL = "Grok"

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_s: float):
        from openai import OpenAI

        api_key = os.getenv(self.KEY_ENV)
        if not api_key:
            raise ProviderError(f"{self.KEY_ENV} is not set", transient=False)
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL,
                              timeout=timeout_s, max_retries=0)  # we retry ourselves
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        import openai

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except openai.RateLimitError as e:  # honour Retry-After instead of a short backoff
            wait = retry_after_seconds(str(e), getattr(e.response, "headers", None))
            raise ProviderError(f"{self.LABEL} rate limited: {e!r}", True, wait) from e
        except (openai.APITimeoutError, openai.APIConnectionError,
                openai.InternalServerError) as e:
            raise ProviderError(f"{self.LABEL} transient error: {e!r}", transient=True) from e
        except openai.APIError as e:
            raise ProviderError(f"{self.LABEL} error: {e!r}", transient=False) from e

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError(f"{self.LABEL} returned empty text", transient=False)
        return text


class GroqProvider(GrokProvider):
    """Groq (free tier): same OpenAI-compatible client, different endpoint and key."""

    name = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"
    KEY_ENV = "GROQ_API_KEY"
    LABEL = "Groq"


class FallbackLLM:
    """Tries providers in order. Each provider gets `max_retries` retries with
    exponential backoff on transient errors; on a permanent error or exhausted
    retries, moves on to the next provider."""

    def __init__(self, providers: list[LLMProvider], max_retries: int = 2,
                 backoff_s: float = 1.5, max_wait_s: float = 90.0):
        if not providers:
            raise ValueError("No LLM provider could be initialised (check API keys).")
        self.providers = providers
        self.max_retries = max_retries
        self.backoff_s = backoff_s
        self.max_wait_s = max_wait_s  # longer waits (e.g. daily quota) -> next provider

    def generate(self, system: str, user: str) -> LLMResponse:
        errors: list[str] = []
        for idx, p in enumerate(self.providers):
            for attempt in range(self.max_retries + 1):
                t0 = time.perf_counter()
                try:
                    text = p.complete(system, user)
                    return LLMResponse(
                        text=text, provider=p.name, model=p.model,
                        latency_s=round(time.perf_counter() - t0, 3),
                        fallback_used=idx > 0, errors=errors,
                    )
                except ProviderError as e:
                    errors.append(f"[{p.name} try {attempt + 1}] {e}")
                    log.warning("%s failed: %s", p.name, e)
                    if not e.transient or attempt == self.max_retries:
                        break
                    if e.retry_after is not None:  # rate limit: wait as long as asked
                        if e.retry_after > self.max_wait_s:
                            break
                        time.sleep(e.retry_after + 0.5)
                    else:
                        time.sleep(self.backoff_s * (2 ** attempt))
            log.warning("Falling back from %s", p.name)
        raise RuntimeError("All LLM providers failed:\n" + "\n".join(errors))


def build_llm(force: str | None = None, **overrides) -> FallbackLLM:
    """Build the Gemini -> Groq -> Grok chain (providers without a key are skipped).
    `force="gemini"`, `force="groq"` or `force="grok"` uses one only."""
    cfg = {**DEFAULTS, **overrides}
    common = dict(temperature=cfg["temperature"], max_tokens=cfg["max_tokens"],
                  timeout_s=cfg["timeout_s"])
    factories = {
        "gemini": lambda: GeminiProvider(cfg["gemini_model"], **common),
        "groq": lambda: GroqProvider(cfg["groq_model"], **common),
        "grok": lambda: GrokProvider(cfg["grok_model"], **common),
    }
    order = [force] if force else ["gemini", "groq", "grok"]

    providers: list[LLMProvider] = []
    for name in order:
        try:
            providers.append(factories[name]())
        except ProviderError as e:  # missing key -> skip, keep the other one
            log.warning("Skipping %s: %s", name, e)
    return FallbackLLM(providers, max_retries=cfg["max_retries"])


def _list_models() -> None:
    if os.getenv("GEMINI_API_KEY"):
        from google import genai
        print("Gemini models supporting generateContent:")
        client = genai.Client()  # keep a reference: the client closes when collected
        for m in client.models.list():
            if "generateContent" in (m.supported_actions or []):
                print("  ", m.name.removeprefix("models/"))
    for prov in (GroqProvider, GrokProvider):
        if os.getenv(prov.KEY_ENV):
            from openai import OpenAI
            print(f"{prov.LABEL} models:")
            for m in OpenAI(api_key=os.getenv(prov.KEY_ENV),
                            base_url=prov.BASE_URL).models.list():
                print("  ", m.id)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list available model IDs")
    ap.add_argument("--force", choices=["gemini", "groq", "grok"])
    ap.add_argument("--q", default="In one sentence, what is the AMF in 5G?")
    a = ap.parse_args()
    if a.list:
        _list_models()
    else:
        r = build_llm(force=a.force).generate("Answer concisely in English.", a.q)
        print(f"[{r.provider}/{r.model} {r.latency_s}s fallback={r.fallback_used}]\n{r.text}")
