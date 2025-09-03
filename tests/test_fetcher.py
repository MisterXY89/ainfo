"""Tests for the asynchronous URL fetcher."""

import asyncio

import httpx
import pytest

from ainfo.fetching import AsyncFetcher


def test_fetcher_caches_responses(monkeypatch, tmp_path) -> None:
    """Responses are cached to disk and reused."""
    calls: list[str] = []

    async def fake_get(self, url, *args, **kwargs):  # noqa: D401 - simple stub
        calls.append(url)
        class Resp:
            status_code = 200
            text = "OK"
            def raise_for_status(self) -> None:  # noqa: D401 - simple stub
                return None
        return Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    async def always_allowed(self, url):  # noqa: D401 - simple stub
        return True

    monkeypatch.setattr(AsyncFetcher, "_allowed", always_allowed)

    async def run() -> None:
        async with AsyncFetcher(cache_dir=str(tmp_path)) as fetcher:
            first = await fetcher.fetch("http://example.com")
            second = await fetcher.fetch("http://example.com")
        assert first == second == "OK"
        assert calls == ["http://example.com"]

    asyncio.run(run())


def test_fetcher_respects_robots(monkeypatch) -> None:
    """Disallowed URLs raise ``PermissionError`` before fetching."""
    calls: list[str] = []

    async def fake_get(self, url, *args, **kwargs):  # noqa: D401 - simple stub
        calls.append(url)
        class Resp:
            def __init__(self, text: str, status_code: int = 200) -> None:
                self.text = text
                self.status_code = status_code
            def raise_for_status(self) -> None:  # noqa: D401 - simple stub
                return None
        if url.endswith("/robots.txt"):
            return Resp("User-agent: *\nDisallow: /private")
        raise AssertionError("Page fetch should not occur for disallowed URLs")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    async def run() -> None:
        async with AsyncFetcher() as fetcher:
            with pytest.raises(PermissionError):
                await fetcher.fetch("http://example.com/private")
        assert calls == ["http://example.com/robots.txt"]

    asyncio.run(run())
