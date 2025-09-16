"""Simple wrapper around the OpenRouter API for text extraction and summarisation."""

from __future__ import annotations

import httpx

from .config import LLMConfig


DEFAULT_SUMMARY_LANGUAGE = "German"

SUMMARY_PROMPT_TEMPLATE = (
    "You are preparing research to personalise a B2B cold outreach email.\n"
    "Analyse the webpage content and capture details that make the outreach\n"
    "feel bespoke. Use only information that is explicitly stated or strongly\n"
    "implied; never fabricate facts.\n\n"
    "Respond in Markdown with these sections:\n"
    "1. **Company Overview** – one sentence describing what the organisation\n"
    "   does or offers.\n"
    "2. **Ideal Customers / Industries** – audiences they target; write 'Not\n"
    "   mentioned' if absent.\n"
    "3. **Notable Signals** – bullet list of recent initiatives, technologies, "
    "hiring plans, metrics or news relevant to outreach; state 'Not "
    "mentioned' if none.\n"
    "4. **Potential Needs or Pain Points** – briefly connect observed signals\n"
    "   to likely needs; say 'Not evident' when unsure.\n"
    "5. **Suggested Outreach Angle** – one sentence proposing how to tailor an\n"
    "   email using the above insights.\n\n"
    "Keep the entire response under 150 words.\n"
    "Write the full response in {language}."
)



def build_summary_prompt(language: str | None = None) -> str:
    """Return the default summary prompt rendered for ``language``."""

    selected = (language or DEFAULT_SUMMARY_LANGUAGE).strip()
    if not selected:
        selected = DEFAULT_SUMMARY_LANGUAGE
    return SUMMARY_PROMPT_TEMPLATE.format(language=selected)


DEFAULT_SUMMARY_PROMPT = build_summary_prompt()




class LLMService:
    """Client for interacting with an LLM via the OpenRouter API."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        configured_language = (
            self.config.summary_language or DEFAULT_SUMMARY_LANGUAGE
        )
        self.summary_language = configured_language.strip() or DEFAULT_SUMMARY_LANGUAGE
        if not self.config.api_key:
            msg = "OPENROUTER_API_KEY is required to use the LLM service"
            raise RuntimeError(msg)
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        self._client = httpx.Client(base_url=self.config.base_url, headers=headers)

    # ------------------------------------------------------------------
    # lifecycle management
    # ------------------------------------------------------------------
    def close(self) -> None:
        """Close the underlying :class:`httpx.Client` instance."""

        self._client.close()

    def __enter__(self) -> "LLMService":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.close()
        # Do not suppress exceptions
        return False

    def _chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        payload = {"model": model or self.config.model, "messages": messages}
        resp = self._client.post("/chat/completions", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    def extract(self, text: str, instruction: str, model: str | None = None) -> str:
        """Return the model's response to ``instruction`` applied to ``text``.

        Parameters
        ----------
        text:
            The content to analyse.
        instruction:
            The instruction or prompt supplied to the model.
        model:
            Optional identifier of the model to use. Defaults to the model
            configured on the service instance.
        """

        prompt = f"{instruction}\n\n{text}"
        return self._chat([{"role": "user", "content": prompt}], model=model)

    def summarize(
        self, text: str, model: str | None = None, language: str | None = None
    ) -> str:
        """Return a cold-outreach-ready summary of ``text``."""

        prompt = build_summary_prompt(language or self.summary_language)
        return self.extract(text, prompt, model=model)


class AsyncLLMService:
    """Asynchronous variant of :class:`LLMService`."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()
        configured_language = (
            self.config.summary_language or DEFAULT_SUMMARY_LANGUAGE
        )
        self.summary_language = configured_language.strip() or DEFAULT_SUMMARY_LANGUAGE
        if not self.config.api_key:
            msg = "OPENROUTER_API_KEY is required to use the LLM service"
            raise RuntimeError(msg)
        headers = {"Authorization": f"Bearer {self.config.api_key}"}
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url, headers=headers
        )

    async def _chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        payload = {"model": model or self.config.model, "messages": messages}
        resp = await self._client.post("/chat/completions", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()

    async def extract(
        self, text: str, instruction: str, model: str | None = None
    ) -> str:
        prompt = f"{instruction}\n\n{text}"
        return await self._chat([{"role": "user", "content": prompt}], model=model)

    async def summarize(
        self, text: str, model: str | None = None, language: str | None = None
    ) -> str:
        prompt = build_summary_prompt(language or self.summary_language)
        return await self.extract(text, prompt, model=model)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncLLMService":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        await self.aclose()
        return False


__all__ = [
    "LLMService",
    "AsyncLLMService",
    "DEFAULT_SUMMARY_PROMPT",
    "DEFAULT_SUMMARY_LANGUAGE",
    "SUMMARY_PROMPT_TEMPLATE",
    "build_summary_prompt",
]
