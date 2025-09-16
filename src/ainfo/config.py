"""Configuration helpers for external services."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """Settings for connecting to the OpenRouter API."""

    api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    model: str = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
    base_url: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    summary_language: str = os.getenv("AINFO_SUMMARY_LANGUAGE", "German")


__all__ = ["LLMConfig"]
