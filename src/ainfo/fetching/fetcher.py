"""Asynchronous URL fetching with robots.txt compliance and caching."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from urllib.robotparser import RobotFileParser

try:  # pragma: no cover - optional dependency
    from playwright.async_api import async_playwright  # type: ignore
except Exception:  # pragma: no cover
    async_playwright = None  # type: ignore[assignment]

try:  # pragma: no cover - optional dependency
    import aiofiles  # type: ignore
except Exception:  # pragma: no cover
    aiofiles = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class AsyncFetcher:
    """Fetch URLs asynchronously while respecting robots.txt rules.

    Parameters
    ----------
    user_agent:
        Value to send in the ``User-Agent`` header and to check against
        ``robots.txt`` rules. Defaults to a common desktop browser string to
        reduce the risk of being blocked.
    timeout:
        Timeout for HTTP requests in seconds.
    cache_dir:
        Optional directory for caching responses to disk. If provided, URL
        contents are stored using a SHA-256 hash of the URL as the filename.
    render_js:
        If ``True``, use a headless browser via Playwright to render pages. This
        allows JavaScript-heavy sites to be fetched at the cost of additional
        overhead.
    """

    def __init__(
        self,
        user_agent: str = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        timeout: float = 10.0,
        cache_dir: str | None = None,
        render_js: bool = False,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.render_js = render_js
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent}, timeout=timeout
        )
        self._pw = None
        self._browser = None
        self._context = None
        self._robots: dict[str, RobotFileParser] = {}

    async def __aenter__(self) -> "AsyncFetcher":
        if self.render_js:
            if async_playwright is None:  # pragma: no cover
                msg = "playwright is required for JavaScript rendering"
                raise RuntimeError(msg)
            self._pw = await async_playwright().start()
            self._browser = await self._pw.chromium.launch(headless=True)
            self._context = await self._browser.new_context(
                user_agent=self.user_agent
            )
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
        if self._context is not None:
            await self._context.close()
        if self._browser is not None:
            await self._browser.close()
        if self._pw is not None:
            await self._pw.stop()

    async def _allowed(self, url: str) -> bool:
        """Check whether a URL is allowed by ``robots.txt`` rules."""
        logger.debug("Checking robots.txt for %s", url)
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        parser = self._robots.get(base)
        if parser is None:
            parser = RobotFileParser()
            robots_url = f"{base}/robots.txt"
            try:
                resp = await self._client.get(robots_url)
                text = resp.text if resp.status_code == 200 else ""
            except httpx.HTTPError:
                text = ""
            parser.parse(text.splitlines())
            self._robots[base] = parser
        return parser.can_fetch(self.user_agent, url)

    async def fetch(self, url: str) -> str:
        """Fetch a URL's content, honoring robots rules and using a cache.

        Parameters
        ----------
        url:
            The URL to retrieve.

        Returns
        -------
        str
            The body of the HTTP response.
        """
        logger.info("Fetching %s", url)
        if not await self._allowed(url):
            msg = f"Fetching disallowed by robots.txt: {url}"
            logger.warning(msg)
            raise PermissionError(msg)

        cache_path: Path | None = None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            filename = hashlib.sha256(url.encode()).hexdigest()
            cache_path = self.cache_dir / filename
            if cache_path.exists():
                logger.debug("Cache hit for %s", url)
                if aiofiles is not None:
                    async with aiofiles.open(cache_path, "r") as f:
                        return await f.read()
                return cache_path.read_text()

        if self.render_js:
            assert self._context is not None  # for mypy
            logger.debug("Rendering page with JavaScript: %s", url)
            page = await self._context.new_page()
            try:
                await page.goto(url, timeout=int(self.timeout * 1000))
                await page.wait_for_load_state("networkidle")
                text = await page.content()
            finally:
                await page.close()
        else:
            resp = await self._client.get(url)
            resp.raise_for_status()
            text = resp.text

        if cache_path is not None:
            if aiofiles is not None:
                async with aiofiles.open(cache_path, "w") as f:
                    await f.write(text)
            else:
                cache_path.write_text(text)

        logger.info("Fetched %d bytes from %s", len(text), url)
        return text

