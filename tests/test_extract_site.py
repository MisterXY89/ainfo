import asyncio

import ainfo


def test_async_extract_site_dedupes_and_limits_domain(monkeypatch):
    pages = [
        ("https://example.com", "<html><body>home</body></html>"),
        ("https://example.com/about", "<html><body>about</body></html>"),
        ("https://example.com/?ref=1", "<html><body>home</body></html>"),
        ("https://external.example.org", "<html><body>other</body></html>"),
    ]

    async def fake_crawl(url, depth, render_js=False):  # noqa: D401 - simple stub
        for link, raw in pages:
            yield link, raw

    monkeypatch.setattr(ainfo, "crawl_urls", fake_crawl)
    monkeypatch.setattr(
        ainfo,
        "parse_data",
        lambda raw, url=None: {"url": url, "raw": raw},
    )
    monkeypatch.setattr(
        ainfo,
        "extract_text",
        lambda doc: f"text:{doc['url']}",
    )

    def fake_contacts(doc, method="regex", llm=None):  # noqa: D401 - simple stub
        return {"contacts": doc["url"], "method": method}

    monkeypatch.setattr(
        ainfo,
        "AVAILABLE_EXTRACTORS",
        {"contacts": fake_contacts},
    )

    result = asyncio.run(
        ainfo.async_extract_site(
            "https://example.com",
            depth=2,
            include_text=True,
        )
    )

    assert set(result) == {
        "https://example.com",
        "https://example.com/about",
    }
    assert result["https://example.com"]["text"] == "text:https://example.com"
    assert result["https://example.com"]["contacts"] == {
        "contacts": "https://example.com",
        "method": "regex",
    }


def test_extract_site_runs_synchronously(monkeypatch):
    async def fake_crawl(url, depth, render_js=False):  # noqa: D401 - simple stub
        yield url, "<html><body>home</body></html>"

    monkeypatch.setattr(ainfo, "crawl_urls", fake_crawl)
    monkeypatch.setattr(
        ainfo,
        "parse_data",
        lambda raw, url=None: {"url": url, "raw": raw},
    )

    def fake_contacts(doc, method="regex", llm=None):  # noqa: D401 - simple stub
        return doc["url"]

    monkeypatch.setattr(
        ainfo,
        "AVAILABLE_EXTRACTORS",
        {"contacts": fake_contacts},
    )

    result = ainfo.extract_site("https://example.com")
    assert result == {"https://example.com": {"contacts": "https://example.com"}}

