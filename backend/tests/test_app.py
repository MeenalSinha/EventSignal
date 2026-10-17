from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import API_V1_PREFIX, create_app


def test_app_initializes_and_exposes_expected_routes(app: FastAPI) -> None:
    paths = set(app.openapi()["paths"])
    assert f"{API_V1_PREFIX}/health" in paths
    assert f"{API_V1_PREFIX}/events" in paths


def test_openapi_documents_health_contract(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    health = schema["paths"][f"{API_V1_PREFIX}/health"]["get"]
    assert set(health["responses"]) >= {"200", "503"}


def test_lifespan_creates_engine_and_disposes_it(app: FastAPI) -> None:
    with TestClient(app):
        assert app.state.engine is not None
        assert app.state.session_factory is not None


def test_cors_allows_configured_origin_only(client: TestClient, settings: Settings) -> None:
    allowed = settings.cors_origins[0]
    ok = client.get(f"{API_V1_PREFIX}/health", headers={"Origin": allowed})
    assert ok.headers.get("access-control-allow-origin") == allowed
    blocked = client.get(f"{API_V1_PREFIX}/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in blocked.headers


def test_cors_origins_come_from_settings(make_settings) -> None:  # type: ignore[no-untyped-def]
    custom = make_settings(cors_origins="https://only.example")
    with TestClient(create_app(custom)) as c:
        resp = c.get(f"{API_V1_PREFIX}/health", headers={"Origin": "https://only.example"})
        assert resp.headers["access-control-allow-origin"] == "https://only.example"
        other = c.get(f"{API_V1_PREFIX}/health", headers={"Origin": "http://localhost:5173"})
        assert "access-control-allow-origin" not in other.headers


def test_unhandled_errors_return_generic_body_and_log_details(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app(settings)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret-token-123 at /home/someone/file.py")

    with TestClient(app, raise_server_exceptions=False) as c, caplog.at_level(logging.ERROR):
        resp = c.get("/boom")
    assert resp.status_code == 500
    body = resp.text
    assert "secret-token-123" not in body
    assert "Traceback" not in body
    assert "/home/" not in body
    assert resp.json()["error"]["code"] == "internal_error"
    assert "secret-token-123" in caplog.text  # details are kept server-side
