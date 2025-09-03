"""Asynchronous web crawler utilities."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping, AsyncIterator
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .fetching import AsyncFetcher

logger = logging.getLogger(__name__)


@dataclass
class DomainRule:
    """Rules controlling crawling behaviour for a specific domain.

    Parameters
    ----------
    max_pages:
        Optional limit on the number of pages to crawl for the domain.
    allow_external:
        Whether links to other domains should be followed. Defaults to ``False``
        which keeps the crawl limited to the current domain.
    """

    max_pages: int | None = None
    allow_external: bool = False


async def crawl(
    start_url: str,
    max_depth: int,
    rules: Mapping[str, DomainRule] | None = None,
    render_js: bool = False,
) -> AsyncIterator[tuple[str, str]]:
    """Crawl web pages starting from ``start_url`` up to ``max_depth`` levels.

    URLs are processed in a breadth-first manner using a queue. A set of
    visited URLs ensures the crawler does not fetch the same page multiple
    times or fall into cycles. Per-domain rules can limit the number of pages
    fetched and control whether external links are followed.

    The function yields ``(url, html)`` tuples for each successfully fetched
    page in the order they were processed.

    Parameters
    ----------
    start_url:
        URL to begin crawling from.
    max_depth:
        Maximum depth to follow links from the starting page. A depth of ``0``
        will fetch only the starting URL.
    rules:
        Optional mapping of domain names to :class:`DomainRule` instances which
        configure crawling behaviour on a per-domain basis.
    render_js:
        If ``True``, use a headless browser to render pages before parsing them.
    """

    logger.info("Starting crawl at %s up to depth %d", start_url, max_depth)
    rules = dict(rules or {})
    visited: set[str] = set()
    domain_counts: dict[str, int] = defaultdict(int)

    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    await queue.put((start_url, 0))

    async with AsyncFetcher(render_js=render_js) as fetcher:
            while not queue.empty():
                url, depth = await queue.get()
                if depth > max_depth or url in visited:
                    continue

                visited.add(url)
                parsed = urlparse(url)
                domain = parsed.netloc
                rule = rules.get(domain, DomainRule())

                if rule.max_pages is not None and domain_counts[domain] >= rule.max_pages:
                    continue
                domain_counts[domain] += 1

                try:
                    logger.info("Fetching %s (depth %d)", url, depth)
                    html = await fetcher.fetch(url)
                except Exception:
                    logger.debug("Failed to fetch %s", url)
                    continue

                # Provide the fetched HTML to the caller before parsing links so
                # consumers can process the page without re-fetching it.
                yield url, html

                if depth == max_depth:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                for tag in soup.find_all("a", href=True):
                    href = tag.get("href")
                    if not href or href.startswith("#"):
                        continue
                    link = urljoin(url, href)
                    if link in visited:
                        continue
                    link_domain = urlparse(link).netloc
                    if not rule.allow_external and link_domain != domain:
                        continue
                    await queue.put((link, depth + 1))

    # When the queue is exhausted the generator simply stops.
