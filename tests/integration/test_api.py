# 验证健康检查、鉴权和 QMT 状态接口行为。
from __future__ import annotations

from http import HTTPStatus

from fastapi.testclient import TestClient

from qmt_data_api.app import create_app
from qmt_data_api.core.config import clear_settings_cache
from qmt_data_api.core.errors import ErrorCode, QmtError


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_KEY_ENABLED", "true")
    monkeypatch.setenv("API_KEYS", "secret-key")
    clear_settings_cache()
    return TestClient(create_app())


def test_health_is_public(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/health")

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["environment"] == "test"
    assert "request_id" in payload


def test_qmt_status_requires_api_key(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/status/qmt")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    payload = response.json()
    assert payload["code"] == ErrorCode.AUTH_MISSING_API_KEY


def test_qmt_status_returns_probe_data(monkeypatch) -> None:
    client = _build_client(monkeypatch)
    monkeypatch.setattr(
        "qmt_data_api.api.http.system.probe_xtdata_status",
        lambda: {
            "status": "ok",
            "xtdata_imported": True,
            "qmt_running": True,
            "connected": True,
            "peer_addr": "127.0.0.1:58610",
            "data_dir": "D:/QMT/data",
            "quote_server_status": None,
            "quote_server_status_error": None,
        },
    )

    response = client.get("/api/v1/status/qmt", headers={"X-API-Key": "secret-key"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["connected"] is True


def test_status_summary_degrades_when_qmt_probe_fails(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _raise_qmt_error() -> None:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_UNAVAILABLE,
            message="xtdata 客户端不可用",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            retryable=True,
        )

    monkeypatch.setattr("qmt_data_api.api.http.system.probe_xtdata_status", _raise_qmt_error)

    response = client.get("/api/v1/status", headers={"X-API-Key": "secret-key"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"]["status"] == "degraded"
    assert payload["data"]["qmt"]["code"] == ErrorCode.QMT_XTDATA_UNAVAILABLE
