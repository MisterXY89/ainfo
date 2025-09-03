"""Tests for HTML parsing into Document structures."""

from ainfo.parsing import parse_html


def test_parse_html_builds_document_structure() -> None:
    """``parse_html`` returns a Document with expected nodes."""
    html = (
        "<html><head><title>Sample</title></head>"
        "<body><nav>Menu</nav><div class=\"article\">"
        "<p>Hello world this is content.</p></div></body></html>"
    )
    doc = parse_html(html, url="http://example.com")

    assert doc.title == "Sample"
    assert doc.url == "http://example.com"
    assert [node.tag for node in doc.nodes] == ["nav", "div"]
    nav, div = doc.nodes
    assert not nav.is_content
    assert div.is_content
    assert div.children[0].tag == "p"
    assert div.children[0].text == "Hello world this is content."
