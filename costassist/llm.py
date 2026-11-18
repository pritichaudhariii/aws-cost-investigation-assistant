"""LLM client for any OpenAI-compatible chat completions endpoint.

Set LLM_BASE_URL / LLM_API_KEY / LLM_MODEL to use a hosted model or a local
one (Ollama: LLM_BASE_URL=http://localhost:11434/v1). Token usage is returned
so the pipeline can report cost per query; prices are configured with
LLM_PRICE_IN_PER_1M and LLM_PRICE_OUT_PER_1M (USD per million tokens).
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int

    @property
    def cost_usd(self) -> float:
        p_in = float(os.environ.get("LLM_PRICE_IN_PER_1M", "0.15"))
        p_out = float(os.environ.get("LLM_PRICE_OUT_PER_1M", "0.60"))
        return (self.input_tokens * p_in + self.output_tokens * p_out) / 1_000_000


class ChatLLM:
    def __init__(self, model: str | None = None, base_url: str | None = None, api_key: str | None = None, timeout: int = 60):
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.timeout = timeout

    def complete(self, system: str, user: str, max_tokens: int = 700) -> LLMResult:
        import requests

        r = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "temperature": 0,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
            timeout=self.timeout,
        )
        r.raise_for_status()
        body = r.json()
        usage = body.get("usage", {})
        return LLMResult(body["choices"][0]["message"]["content"], usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def llm_from_env() -> ChatLLM | None:
    """Return a client only when an endpoint is configured; otherwise the pipeline uses its offline synthesizer."""
    return ChatLLM() if os.environ.get("LLM_API_KEY") or os.environ.get("LLM_BASE_URL") else None
