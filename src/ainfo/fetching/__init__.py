"""High-level helpers for retrieving web pages."""

from __future__ import annotations

import asyncio

from .fetcher import AsyncFetcher


async def _fetch(url: str, render_js: bool) -> str:
    """Internal coroutine to fetch ``url`` using :class:`AsyncFetcher`."""

    async with AsyncFetcher(render_js=render_js) as fetcher:
        return await fetcher.fetch(url)


def fetch_data(url: str, render_js: bool = False) -> str:
    """Fetch raw HTML from ``url`` synchronously.

    Parameters
    ----------
    url:
        The address to retrieve.
    render_js:
        Whether to render the page with a headless browser so that any
        JavaScript on the page executes before the HTML is returned.

    Returns
    -------
    str
        The HTML body of the page.
    """

    return asyncio.run(_fetch(url, render_js))


__all__ = ["fetch_data", "AsyncFetcher"]

