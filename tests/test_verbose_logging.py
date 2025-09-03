import logging
from typer.testing import CliRunner

import ainfo


def test_verbose_sets_debug_level(monkeypatch):
    """The --verbose flag should configure the root logger for debugging."""

    html = "<html><body><p>hello</p></body></html>"
    monkeypatch.setattr(ainfo, "fetch_data", lambda url, render_js=False: html)

    runner = CliRunner()
    runner.invoke(ainfo.app, ["--verbose", "run", "https://example.com", "--json"])

    assert logging.getLogger().level == logging.DEBUG
    logging.getLogger().setLevel(logging.WARNING)

