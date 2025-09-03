from ainfo import parse_data, extract_text


def test_extract_text_string_and_list() -> None:
    html = "<html><body><p>First paragraph has enough words here.</p><p>Second block also contains several words.</p></body></html>"
    doc = parse_data(html, url="http://example.com")
    assert (
        extract_text(doc)
        == "First paragraph has enough words here. Second block also contains several words."
    )
    assert (
        extract_text(doc, joiner="\n")
        == "First paragraph has enough words here.\nSecond block also contains several words."
    )
    assert extract_text(doc, as_list=True) == [
        "First paragraph has enough words here.",
        "Second block also contains several words.",
    ]
