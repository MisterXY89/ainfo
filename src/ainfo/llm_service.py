"""Simple wrapper around the OpenRouter API for text extraction and summarisation."""

from __future__ import annotations

import httpx

from .config import LLMConfig


class LLMService:
    """Client for interacting with an LLM via the OpenRouter API."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        if not self.config.api_key:
            msg = "OPENROUTER_API_KEY is required to use the LLM service"
            raise RuntimeError(msg)
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        self._client = httpx.Client(base_url=self.config.base_url, headers=headers)

    def _chat(self, messages: list[dict[str, str]]) -> str:
        payload = {"model": self.config.model, "messages": messages}
        resp = self._client.post("/chat/completions", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def extract(self, text: str, instruction: str) -> str:
        """Return the model's response to ``instruction`` applied to ``text``."""

        prompt = f"{instruction}\n\n{text}"
        return self._chat([{"role": "user", "content": prompt}])

    def summarize(self, text: str) -> str:
        """Return a brief summary of ``text``."""

        instruction = "Summarise the following content:"
        return self.extract(text, instruction)


__all__ = ["LLMService"]
