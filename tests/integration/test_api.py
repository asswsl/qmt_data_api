# 验证健康检查、鉴权和 QMT 状态接口行为。
from __future__ import annotations

from http import HTTPStatus

from fastapi.testclient import TestClient

from qmt_data_api.app import create_app
from qmt_data_api.cache.memory import snapshot_cache
from qmt_data_api.core.config import clear_settings_cache
from qmt_data_api.core.errors import ErrorCode, QmtError
from qmt_data_api.domain.market.schemas import KlineBar, KlineResult, SnapshotItem, SnapshotResult


def _build_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_KEY_ENABLED", "true")
    monkeypatch.setenv("API_KEYS", "secret-key")
    monkeypatch.setenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "30")
    clear_settings_cache()
    snapshot_cache.clear()
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


def test_market_snapshot_requires_api_key(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/market/snapshot?symbols=600519.SH")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == ErrorCode.AUTH_MISSING_API_KEY


def test_market_snapshot_get_returns_data(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _fake_snapshots(
        symbols: list[str],
        fields: list[str] | None = None,
        source: str = "auto",
    ) -> SnapshotResult:
        assert symbols == ["600519.SH", "000001.SZ"]
        assert fields == ["last_price", "volume"]
        assert source == "auto"
        return SnapshotResult(
            items=[
                SnapshotItem(
                    symbol="600519.SH",
                    quote_time="2026-05-18T10:00:00+08:00",
                    last_price=1688.88,
                    volume=1000,
                    raw={"lastPrice": 1688.88},
                )
            ],
            missing_symbols=["000001.SZ"],
            fields=fields,
            source="qmt",
            cache="miss",
        )

    monkeypatch.setattr("qmt_data_api.api.http.market.get_market_snapshots", _fake_snapshots)

    response = client.get(
        "/api/v1/market/snapshot?symbols=600519.SH,000001.SZ&fields=last_price,volume",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"][0]["symbol"] == "600519.SH"
    assert payload["data"][0]["last_price"] == 1688.88
    assert "raw" not in payload["data"][0]
    assert payload["meta"]["missing_symbols"] == ["000001.SZ"]
    assert payload["meta"]["source"] == "qmt"
    assert payload["meta"]["cache"] == "miss"


def test_market_snapshot_post_returns_data(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _fake_snapshots(
        symbols: list[str],
        fields: list[str] | None = None,
        source: str = "auto",
    ) -> SnapshotResult:
        assert symbols == ["600519.SH"]
        assert fields == ["last_price"]
        assert source == "auto"
        return SnapshotResult(
            items=[SnapshotItem(symbol="600519.SH", last_price=1688.88)],
            missing_symbols=[],
            fields=fields,
            source="cache",
            cache="hit",
        )

    monkeypatch.setattr("qmt_data_api.api.http.market.get_market_snapshots", _fake_snapshots)

    response = client.post(
        "/api/v1/market/snapshot",
        headers={"X-API-Key": "secret-key"},
        json={"symbols": ["600519.SH"], "fields": ["last_price"]},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"] == [{"symbol": "600519.SH", "last_price": 1688.88}]
    assert payload["meta"]["fields"] == ["last_price"]
    assert payload["meta"]["source"] == "cache"
    assert payload["meta"]["cache"] == "hit"


def test_cache_status_requires_api_key(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/cache/status")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == ErrorCode.AUTH_MISSING_API_KEY


def test_cache_status_returns_snapshot_cache_stats(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/cache/status", headers={"X-API-Key": "secret-key"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    cache_data = payload["data"]["market_snapshot"]
    assert cache_data["backend"] == "memory"
    assert cache_data["ttl_seconds"] == 30
    assert cache_data["size"] == 0


def test_market_kline_returns_bars(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _fake_klines(
        symbol: str,
        period: str,
        start: str,
        end: str,
        adjust: str = "none",
        source: str = "auto",
        limit: int | None = None,
    ) -> KlineResult:
        assert symbol == "600519.SH"
        assert period == "1d"
        assert start == "20240101"
        assert end == "20240110"
        assert adjust == "none"
        assert source == "auto"
        assert limit == 5
        return KlineResult(
            symbol="600519.SH",
            period="1d",
            adjust="none",
            source="qmt",
            bars=[
                KlineBar(
                    time="2024-01-02T00:00:00+08:00",
                    trade_date="2024-01-02",
                    open=1715.0,
                    high=1718.19,
                    low=1678.1,
                    close=1685.01,
                    volume=32156,
                    amount=5440083000.0,
                )
            ],
        )

    monkeypatch.setattr("qmt_data_api.api.http.market.get_market_klines", _fake_klines)

    response = client.get(
        "/api/v1/market/kline"
        "?symbol=600519.SH&period=1d&start=20240101&end=20240110&limit=5",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"]["symbol"] == "600519.SH"
    assert payload["data"]["bars"][0]["close"] == 1685.01
    assert payload["meta"]["source"] == "qmt"
    assert payload["meta"]["count"] == 1
