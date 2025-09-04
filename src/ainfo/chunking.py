from __future__ import annotations

"""Utilities for chunking large strings for LLM processing."""

import asyncio
from collections.abc import Iterator

from .fetching import fetch_data
from .parsing import parse_data
from .extraction import extract_text

__all__ = ["chunk_text", "stream_chunks"]


def chunk_text(text: str, size: int) -> list[str]:
    """Return a list of substrings of ``text`` with at most ``size`` characters."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [text[i : i + size] for i in range(0, len(text), size)]


def stream_chunks(source: str, size: int) -> Iterator[str]:
    """Yield successive ``size``-sized chunks from ``source``.

    ``source`` may be raw text or a URL. When a URL is supplied the
    referenced page is fetched, parsed and its textual content chunked.
    """
    if size <= 0:
        raise ValueError("size must be positive")

    if source.startswith("http://") or source.startswith("https://"):
        raw = fetch_data(source)
        if isinstance(raw, asyncio.Task):
            raw = asyncio.run(raw)
        doc = parse_data(raw, url=source)
        text = extract_text(doc)
    else:
        text = source

    for i in range(0, len(text), size):
        yield text[i : i + size]
