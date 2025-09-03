import asyncio
from collections import defaultdict

from ainfo import crawler


def test_crawl_yields_html_once_per_url(monkeypatch):
    """The crawler should fetch each URL only a single time."""

    pages = {
        "https://example.com": '<a href="https://example.com/about">about</a>',
        "https://example.com/about": '<a href="https://example.com">home</a>',
    }
    counts: defaultdict[str, int] = defaultdict(int)

    async def fake_fetch(self, url: str) -> str:  # noqa: D401 - simple stub
        counts[url] += 1
        return pages[url]

    monkeypatch.setattr(crawler.AsyncFetcher, "fetch", fake_fetch)

    async def collect() -> list[tuple[str, str]]:
        return [pair async for pair in crawler.crawl("https://example.com", 2)]

    pairs = asyncio.run(collect())

    assert pairs == [
        ("https://example.com", pages["https://example.com"]),
        ("https://example.com/about", pages["https://example.com/about"]),
    ]
    assert counts["https://example.com"] == 1
    assert counts["https://example.com/about"] == 1
