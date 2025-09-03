"""High-level helpers for retrieving web pages."""

from __future__ import annotations

import asyncio

from .fetcher import AsyncFetcher


async def _fetch(url: str, render_js: bool) -> str:
    """Internal coroutine to fetch ``url`` using :class:`AsyncFetcher`."""

    async with AsyncFetcher(render_js=render_js) as fetcher:
        return await fetcher.fetch(url)


async def async_fetch_data(url: str, render_js: bool = False) -> str:
    """Fetch raw HTML from ``url`` asynchronously."""

    return await _fetch(url, render_js)


def fetch_data(url: str, render_js: bool = False) -> str | asyncio.Task[str]:
    """Fetch raw HTML from ``url``.

    The function adapts to the surrounding asynchronous environment. If no
    event loop is running, the coroutine is executed immediately and the HTML
    is returned. When called while an event loop is already running, the
    coroutine is scheduled on that loop and an :class:`asyncio.Task` is
    returned. For fully asynchronous workflows use :func:`async_fetch_data`.

    Parameters
    ----------
    url:
        The address to retrieve.
    render_js:
        Whether to render the page with a headless browser so that any
        JavaScript on the page executes before the HTML is returned.

    Returns
    -------
    str | asyncio.Task[str]
        The HTML body of the page or a task that resolves to it.
    """

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_fetch(url, render_js))
    else:
        return loop.create_task(_fetch(url, render_js))


__all__ = ["fetch_data", "async_fetch_data", "AsyncFetcher"]

