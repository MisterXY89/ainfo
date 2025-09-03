from ainfo import parse_data, extract_custom


def test_extract_custom_returns_matches() -> None:
    html = (
        "<html><body><p>This product costs $10 and also $20 altogether.</p></body></html>"
    )
    doc = parse_data(html, url="http://example.com")
    results = extract_custom(doc, {"prices": r"\$\d+"})
    assert results == {"prices": ["$10", "$20"]}
