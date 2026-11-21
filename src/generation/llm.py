"""LLM layer: Gemini as primary provider, Grok (xAI) as automatic fallback.

Usage
-----
    from src.generation.llm import build_llm

    llm = build_llm()                      # Gemini -> Grok fallback
    res = llm.generate(system_prompt, user_prompt)
    print(res.text, res.provider, res.fallback_used)

    llm = build_llm(force="grok")          # force one provider (evaluation / LLM comparison)

Environment variables (.env)
----------------------------
    GEMINI_API_KEY=...
    XAI_API_KEY=...
    GEMINI_MODEL=gemini-flash-latest     # optional override
    GROK_MODEL=grok-4.7                  # optional override
    LLM_TIMEOUT_S=60                     # optional
    LLM_MAX_RETRIES=2                    # retries per provider on transient errors

Run `python -m src.generation.llm --list` to print the model IDs your keys can use.
"""
from __future__ import annotations

import logging
import os
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
    """Raised by a provider when it cannot produce an answer."""

    def __init__(self, msg: str, transient: bool):
        super().__init__(msg)
        self.transient = transient


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
            raise ProviderError(f"Gemini {e.code}: {e.message}", transient) from e
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

    def __init__(self, model: str, temperature: float, max_tokens: int, timeout_s: float):
        from openai import OpenAI

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ProviderError("XAI_API_KEY is not set", transient=False)
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
        except (openai.RateLimitError, openai.APITimeoutError,
                openai.APIConnectionError, openai.InternalServerError) as e:
            raise ProviderError(f"Grok transient error: {e!r}", transient=True) from e
        except openai.APIError as e:
            raise ProviderError(f"Grok error: {e!r}", transient=False) from e

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError("Grok returned empty text", transient=False)
        return text


class FallbackLLM:
    """Tries providers in order. Each provider gets `max_retries` retries with
    exponential backoff on transient errors; on a permanent error or exhausted
    retries, moves on to the next provider."""

    def __init__(self, providers: list[LLMProvider], max_retries: int = 2,
                 backoff_s: float = 1.5):
        if not providers:
            raise ValueError("No LLM provider could be initialised (check API keys).")
        self.providers = providers
        self.max_retries = max_retries
        self.backoff_s = backoff_s

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
                    time.sleep(self.backoff_s * (2 ** attempt))
            log.warning("Falling back from %s", p.name)
        raise RuntimeError("All LLM providers failed:\n" + "\n".join(errors))


def build_llm(force: str | None = None, **overrides) -> FallbackLLM:
    """Build the Gemini -> Grok chain. `force="gemini"` or `force="grok"` uses one only."""
    cfg = {**DEFAULTS, **overrides}
    common = dict(temperature=cfg["temperature"], max_tokens=cfg["max_tokens"],
                  timeout_s=cfg["timeout_s"])
    factories = {
        "gemini": lambda: GeminiProvider(cfg["gemini_model"], **common),
        "grok": lambda: GrokProvider(cfg["grok_model"], **common),
    }
    order = [force] if force else ["gemini", "grok"]

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
    if os.getenv("XAI_API_KEY"):
        from openai import OpenAI
        print("Grok models:")
        for m in OpenAI(api_key=os.getenv("XAI_API_KEY"),
                        base_url=GrokProvider.BASE_URL).models.list():
            print("  ", m.id)


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list available model IDs")
    ap.add_argument("--force", choices=["gemini", "grok"])
    ap.add_argument("--q", default="In one sentence, what is the AMF in 5G?")
    a = ap.parse_args()
    if a.list:
        _list_models()
    else:
        r = build_llm(force=a.force).generate("Answer concisely in English.", a.q)
        print(f"[{r.provider}/{r.model} {r.latency_s}s fallback={r.fallback_used}]\n{r.text}")
