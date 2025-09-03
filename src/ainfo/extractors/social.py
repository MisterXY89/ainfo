from __future__ import annotations

"""Helpers for extracting social media profile links from text."""

import re

SOCIAL_PATTERN = re.compile(
    r"(https?://(?:www\.)?(?:twitter|facebook|linkedin)\.com/[^\s'\"]+)",
    re.IGNORECASE,
)


__all__ = ["extract_social_profiles"]


def extract_social_profiles(text: str) -> list[str]:
    """Return social media profile URLs discovered in ``text``."""
    urls: list[str] = []
    for match in SOCIAL_PATTERN.finditer(text):
        url = match.group(1).rstrip(".,)")
        urls.append(url)
    # Deduplicate while preserving order
    return list(dict.fromkeys(urls))
