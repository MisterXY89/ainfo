"""Asynchronous URL fetching with robots.txt compliance and caching."""

from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import httpx
from urllib.robotparser import RobotFileParser


class AsyncFetcher:
    """Fetch URLs asynchronously while respecting robots.txt rules.

    Parameters
    ----------
    user_agent:
        Value to send in the ``User-Agent`` header and to check against
        ``robots.txt`` rules.
    timeout:
        Timeout for HTTP requests in seconds.
    cache_dir:
        Optional directory for caching responses to disk. If provided, URL
        contents are stored using a SHA-256 hash of the URL as the filename.
    """

    def __init__(
        self,
        user_agent: str = "ainfo-fetcher",
        timeout: float = 10.0,
        cache_dir: str | None = None,
    ) -> None:
        self.user_agent = user_agent
        self.timeout = timeout
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self._client = httpx.AsyncClient(
            headers={"User-Agent": user_agent}, timeout=timeout
        )
        self._robots: dict[str, RobotFileParser] = {}

    async def __aenter__(self) -> "AsyncFetcher":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def _allowed(self, url: str) -> bool:
        """Check whether a URL is allowed by ``robots.txt`` rules."""
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
        if not await self._allowed(url):
            msg = f"Fetching disallowed by robots.txt: {url}"
            raise PermissionError(msg)

        cache_path: Path | None = None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            filename = hashlib.sha256(url.encode()).hexdigest()
            cache_path = self.cache_dir / filename
            if cache_path.exists():
                async with aiofiles.open(cache_path, "r") as f:
                    return await f.read()

        resp = await self._client.get(url)
        resp.raise_for_status()
        text = resp.text

        if cache_path is not None:
            async with aiofiles.open(cache_path, "w") as f:
                await f.write(text)

        return text

