from ainfo import parse_data, extract_custom


class DummyLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []

    def extract(self, text: str, instruction: str, model: str | None = None) -> str:
        self.calls.append((text, instruction, model))
        return '{"prices": ["$30"]}'


def test_extract_custom_returns_matches() -> None:
    html = (
        "<html><body><p>This product costs $10 and also $20 altogether.</p></body></html>"
    )
    doc = parse_data(html, url="http://example.com")
    results = extract_custom(doc, {"prices": r"\$\d+"})
    assert results == {"prices": ["$10", "$20"]}


def test_extract_custom_llm() -> None:
    html = "<html><body><p>This product costs $30.</p></body></html>"
    doc = parse_data(html, url="http://example.com")
    llm = DummyLLM()
    results = extract_custom(doc, llm=llm, prompt="Extract prices", model="test-model")
    assert results == {"prices": ["$30"]}
    assert llm.calls[0][1] == "Extract prices"
    assert llm.calls[0][2] == "test-model"
