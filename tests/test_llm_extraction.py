import json

from ainfo import parse_data, extract_information
from ainfo.schemas import Address


class DummyLLM:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []

    def extract(self, text: str, instruction: str, model: str | None = None) -> str:
        self.calls.append((text, instruction, model))
        return json.dumps(
            {
                "emails": ["test@example.com"],
                "phone_numbers": [],
                "addresses": [
                    {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "country": "USA",
                    }
                ],
                "social_media": [],
            }
        )


def test_extract_information_llm_custom_prompt_and_model() -> None:
    html = "<html><body><p>Contact us at test@example.com</p></body></html>"
    doc = parse_data(html, url="http://example.com")
    llm = DummyLLM()
    result = extract_information(
        doc,
        method="llm",
        llm=llm,
        instruction="Find all emails",
        model="custom-model",
    )
    assert result.emails == ["test@example.com"]
    assert result.addresses == [Address(street="123 Main St", city="Springfield", country="USA")]
    assert llm.calls[0][1] == "Find all emails"
    assert llm.calls[0][2] == "custom-model"
