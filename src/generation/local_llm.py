"""Local LLM through Ollama's OpenAI-compatible endpoint (bonus: API vs local comparison).

Uses the `openai` SDK already required by the Grok provider. Not part of the Gemini -> Grok
chain of `llm.py`; it is only used when explicitly requested (`--provider ollama`).

    OLLAMA_BASE_URL=http://localhost:11434/v1   (default)
    OLLAMA_MODEL=llama3.2:3b                    (default)
"""

from __future__ import annotations

import os

from src.generation.llm import FallbackLLM, ProviderError


class OllamaProvider:
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout_s: float = 300.0,
    ):
        from openai import OpenAI

        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        self._client = OpenAI(api_key="ollama", base_url=base_url, timeout=timeout_s, max_retries=0)
        self.temperature = temperature
        self.max_tokens = max_tokens

    def complete(self, system: str, user: str) -> str:
        import openai

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            raise ProviderError(f"Ollama unreachable: {e!r}", transient=True) from e
        except openai.APIError as e:
            raise ProviderError(f"Ollama error: {e!r}", transient=False) from e
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            raise ProviderError("Ollama returned empty text", transient=False)
        return text


def build_local_llm(temperature: float = 0.0, max_tokens: int = 1024) -> FallbackLLM:
    return FallbackLLM(
        [OllamaProvider(temperature=temperature, max_tokens=max_tokens)], max_retries=1
    )
