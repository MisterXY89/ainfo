from ainfo import parse_data
from ainfo.extractors.links import extract_links
from ainfo.extractors.headings import extract_headings


def test_extract_links_and_headings() -> None:
    html = (
        "<html><body><h1>Main</h1><h2>Sub</h2>"
        '<a href="https://example.com">Example</a>'
        '<a href="/relative">Rel</a>'
        "</body></html>"
    )
    doc = parse_data(html, url="https://example.com")
    assert extract_links(doc) == ["https://example.com", "/relative"]
    assert extract_headings(doc) == {"h1": ["Main"], "h2": ["Sub"]}
