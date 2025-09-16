import importlib
import sys

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


MODULE_NAME = "integration.api"


def reload_integration_api(monkeypatch: pytest.MonkeyPatch, api_key: str) -> object:
    """Load the integration API module with a specific API key configured."""

    monkeypatch.setenv("AINFO_API_KEY", api_key)
    sys.modules.pop(MODULE_NAME, None)
    return importlib.import_module(MODULE_NAME)


def test_import_requires_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AINFO_API_KEY", raising=False)
    sys.modules.pop(MODULE_NAME, None)

    with pytest.raises(RuntimeError):
        importlib.import_module(MODULE_NAME)


def test_run_endpoint_blocks_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    api_module = reload_integration_api(monkeypatch, api_key="secret")
    client = TestClient(api_module.app)

    response = client.get("/run", params={"url": "https://example.com"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid or missing API key"}


def test_run_endpoint_accepts_valid_key(monkeypatch: pytest.MonkeyPatch) -> None:
    api_module = reload_integration_api(monkeypatch, api_key="valid-key")

    class DummyCompletedProcess:
        def __init__(self) -> None:
            self.stdout = "{\"ok\": true}"

    commands: list[list[str]] = []

    def fake_run(*args, **kwargs):
        commands.append(list(args[0]))
        return DummyCompletedProcess()

    monkeypatch.setattr(api_module.subprocess, "run", fake_run)

    client = TestClient(api_module.app)
    response = client.get(
        "/run",
        params={"url": "https://example.com"},
        headers={"X-API-Key": "valid-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert commands
    cmd = commands[0]
    assert "--summary-language" in cmd
    lang_index = cmd.index("--summary-language") + 1
    assert cmd[lang_index] == "German"


def test_run_endpoint_custom_summary_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    api_module = reload_integration_api(monkeypatch, api_key="valid-key")

    class DummyCompletedProcess:
        def __init__(self) -> None:
            self.stdout = "{\"ok\": true}"

    commands: list[list[str]] = []

    def fake_run(*args, **kwargs):
        commands.append(list(args[0]))
        return DummyCompletedProcess()

    monkeypatch.setattr(api_module.subprocess, "run", fake_run)

    client = TestClient(api_module.app)
    response = client.get(
        "/run",
        params={"url": "https://example.com", "summary_language": "Spanish"},
        headers={"X-API-Key": "valid-key"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    cmd = commands[0]
    lang_index = cmd.index("--summary-language") + 1
    assert cmd[lang_index] == "Spanish"
