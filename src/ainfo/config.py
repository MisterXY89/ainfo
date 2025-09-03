"""Configuration helpers for external services."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Settings for connecting to the OpenRouter API."""

    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    model: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")
    base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


__all__ = ["LLMConfig"]
