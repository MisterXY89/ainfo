import pytest

from ainfo.chunking import chunk_text, stream_chunks


def test_chunk_text() -> None:
    text = "abcdefg"
    assert chunk_text(text, 3) == ["abc", "def", "g"]


def test_stream_chunks() -> None:
    text = "abcdefg"
    assert list(stream_chunks(text, 2)) == ["ab", "cd", "ef", "g"]


def test_stream_chunks_negative_size() -> None:
    with pytest.raises(ValueError):
        list(stream_chunks("abc", 0))


def test_stream_chunks_from_url(monkeypatch) -> None:
    html = "<html><body><p>one two three four five</p></body></html>"

    def fake_fetch(url: str, render_js: bool = False):  # noqa: D401 - simple stub
        return html

    monkeypatch.setattr("ainfo.chunking.fetch_data", fake_fetch)
    chunks = list(stream_chunks("http://example.com", 5))
    assert chunks == ["one t", "wo th", "ree f", "our f", "ive"]
