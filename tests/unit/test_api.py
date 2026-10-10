"""API tests: index, health, UI page, Temporal-unreachable path (no network)."""

import os

from fastapi.testclient import TestClient


def _client() -> TestClient:
    from f1_api import app

    return TestClient(app, raise_server_exceptions=False)


def test_index_lists_routes() -> None:
    r = _client().get("/")
    assert r.status_code == 200
    assert "/ui" in r.json()["routes"]


def test_ui_page_serves() -> None:
    r = _client().get("/ui")
    assert r.status_code == 200
    assert "Prediction workflows" in r.text


def test_workflows_503_when_temporal_down(monkeypatch) -> None:
    monkeypatch.setenv("TEMPORAL_ADDRESS", "localhost:1")  # nothing listens here
    r = _client().get("/api/workflows?session_id=nope")
    assert r.status_code == 503
    os.environ.pop("TEMPORAL_ADDRESS", None)
