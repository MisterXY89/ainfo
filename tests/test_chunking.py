from ainfo.chunking import chunk_text, stream_chunks


def test_chunk_text() -> None:
    text = "abcdefg"
    assert chunk_text(text, 3) == ["abc", "def", "g"]


def test_stream_chunks() -> None:
    text = "abcdefg"
    assert list(stream_chunks(text, 2)) == ["ab", "cd", "ef", "g"]
