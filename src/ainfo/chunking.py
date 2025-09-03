from __future__ import annotations

"""Utilities for chunking large strings for LLM processing."""

from collections.abc import Iterator

__all__ = ["chunk_text", "stream_chunks"]


def chunk_text(text: str, size: int) -> list[str]:
    """Return a list of substrings of ``text`` with at most ``size`` characters."""
    if size <= 0:
        raise ValueError("size must be positive")
    return [text[i : i + size] for i in range(0, len(text), size)]


def stream_chunks(text: str, size: int) -> Iterator[str]:
    """Yield successive ``size``-sized chunks from ``text``."""
    for i in range(0, len(text), size):
        yield text[i : i + size]
