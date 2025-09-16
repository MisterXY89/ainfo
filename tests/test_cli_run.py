import json
from typer.testing import CliRunner

import ainfo


def test_cli_run_json_output(monkeypatch):
    html = (
        "<html><body><p>Please contact us at test@example.com for more info.</p></body></html>"
    )
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)
    runner = CliRunner()
    result = runner.invoke(
        ainfo.app,
        ["run", "https://example.com", "--json", "--extract", "contacts"],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert data["contacts"] == {
        "emails": ["test@example.com"],
        "phone_numbers": [],
        "addresses": [],
        "social_media": [],
    }
    assert "text" in data


def test_cli_run_contacts_in_footer(monkeypatch):
    html = "<html><body><footer>Kontakt: kontakt@example.de</footer></body></html>"
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)
    runner = CliRunner()
    result = runner.invoke(
        ainfo.app,
        [
            "run",
            "https://example.com",
            "--json",
            "--extract",
            "contacts",
            "--no-text",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert data["contacts"]["emails"] == ["kontakt@example.de"]


def test_cli_run_without_text(monkeypatch):
    html = "<html><body><p>no contacts</p></body></html>"
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)
    runner = CliRunner()
    result = runner.invoke(
        ainfo.app,
        [
            "run",
            "https://example.com",
            "--json",
            "--extract",
            "links",
            "--no-text",
        ],
    )
    assert result.exit_code == 0
    data = json.loads(result.stdout.strip())
    assert "text" not in data
    assert "links" in data


def test_cli_run_summary_uses_default_german(monkeypatch):
    html = "<html><body><p>some text</p></body></html>"
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)

    captured = {}

    class DummyLLM:
        def __enter__(self):
            captured["instance"] = self
            self.languages = []
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def summarize(self, text, model=None, language=None):
            self.languages.append(language)
            return "Zusammenfassung"

    monkeypatch.setattr(ainfo, "LLMService", DummyLLM)

    runner = CliRunner()
    result = runner.invoke(
        ainfo.app,
        ["run", "https://example.com", "--summarize", "--no-text"],
    )

    assert result.exit_code == 0
    assert "summary:" in result.stdout
    assert "Zusammenfassung" in result.stdout
    assert captured["instance"].languages == ["German"]


def test_cli_run_summary_custom_language(monkeypatch):
    html = "<html><body><p>some text</p></body></html>"
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)

    captured = {}

    class DummyLLM:
        def __enter__(self):
            captured["instance"] = self
            self.languages = []
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def summarize(self, text, model=None, language=None):
            self.languages.append(language)
            return "Resumen"

    monkeypatch.setattr(ainfo, "LLMService", DummyLLM)

    runner = CliRunner()
    result = runner.invoke(
        ainfo.app,
        [
            "run",
            "https://example.com",
            "--summarize",
            "--summary-language",
            "Spanish",
            "--no-text",
        ],
    )

    assert result.exit_code == 0
    assert "Resumen" in result.stdout
    assert captured["instance"].languages == ["Spanish"]
