from collections import defaultdict

from typer.testing import CliRunner

import ainfo


def test_cli_crawl_fetches_each_url_once(monkeypatch):
    """CLI crawl should not re-fetch pages returned by the crawler."""

    pages = {
        "https://example.com": '<a href="https://example.com/about">about</a>',
        "https://example.com/about": '<a href="https://example.com">home</a>',
    }
    counts: defaultdict[str, int] = defaultdict(int)

    async def fake_fetch(self, url: str) -> str:  # noqa: D401 - simple stub
        counts[url] += 1
        return pages[url]

    monkeypatch.setattr(ainfo.crawler.AsyncFetcher, "fetch", fake_fetch)

    # Prevent any accidental calls to fetch_data which would refetch URLs
    def fail_fetch(*args, **kwargs):  # noqa: D401 - simple stub
        raise AssertionError("fetch_data should not be called")

    monkeypatch.setattr(ainfo, "fetch_data", fail_fetch)

    # Simplify downstream processing to keep the test focused on fetch counts
    monkeypatch.setattr(ainfo, "parse_data", lambda raw, url=None: raw)
    monkeypatch.setattr(ainfo, "extract_text", lambda doc, joiner=" ", as_list=False: "")
    monkeypatch.setattr(ainfo, "output_results", lambda results: None)
    monkeypatch.setattr(ainfo, "to_json", lambda results, path: None)

    runner = CliRunner()
    result = runner.invoke(ainfo.app, ["crawl", "https://example.com", "--depth", "2"])
    assert result.exit_code == 0
    assert counts == {
        "https://example.com": 1,
        "https://example.com/about": 1,
    }
