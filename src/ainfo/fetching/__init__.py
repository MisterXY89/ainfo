"""High-level helpers for retrieving web pages."""

from __future__ import annotations

import asyncio

from .fetcher import AsyncFetcher


async def _fetch(url: str) -> str:
    """Internal coroutine to fetch ``url`` using :class:`AsyncFetcher`."""

    async with AsyncFetcher() as fetcher:
        return await fetcher.fetch(url)


def fetch_data(url: str) -> str:
    """Fetch raw HTML from ``url`` synchronously.

    Parameters
    ----------
    url:
        The address to retrieve.

    Returns
    -------
    str
        The HTML body of the page.
    """

    return asyncio.run(_fetch(url))


__all__ = ["fetch_data", "AsyncFetcher"]

