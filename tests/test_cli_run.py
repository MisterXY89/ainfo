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
