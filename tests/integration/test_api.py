# 验证健康检查、鉴权和 QMT 状态接口行为。
from __future__ import annotations

import logging
from http import HTTPStatus

from fastapi.testclient import TestClient

from qmt_data_api.app import create_app
from qmt_data_api.cache.memory import get_snapshot_cache
from qmt_data_api.core.config import clear_settings_cache
from qmt_data_api.core.errors import ErrorCode, QmtError
from qmt_data_api.domain.calendar.schemas import TradingCalendarResult
from qmt_data_api.domain.instrument.schemas import InstrumentInfo, InstrumentResult
from qmt_data_api.domain.market.schemas import KlineBar, KlineResult, SnapshotItem, SnapshotResult
from qmt_data_api.middleware.access_log import ACCESS_LOGGER_NAME


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


def test_access_log_records_success_request(monkeypatch, caplog) -> None:
    client = _build_client(monkeypatch)

    with caplog.at_level(logging.INFO, logger=ACCESS_LOGGER_NAME):
        response = client.get("/api/v1/health", headers={"X-Request-ID": "req_test_access"})

    assert response.status_code == HTTPStatus.OK
    records = [record for record in caplog.records if record.name == ACCESS_LOGGER_NAME]
    assert records
    record = records[-1]
    assert record.request_id == "req_test_access"
    assert record.method == "GET"
    assert record.path == "/api/v1/health"
    assert record.status_code == HTTPStatus.OK
    assert record.duration_ms >= 0
    assert record.error_code is None
    assert record.api_key_fingerprint is None


def test_access_log_records_error_code_and_api_key_fingerprint(monkeypatch, caplog) -> None:
    client = _build_client(monkeypatch)

    with caplog.at_level(logging.INFO, logger=ACCESS_LOGGER_NAME):
        response = client.get(
            "/api/v1/status/qmt",
            headers={"X-Request-ID": "req_auth_error", "X-API-Key": "bad-key"},
        )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    records = [record for record in caplog.records if record.name == ACCESS_LOGGER_NAME]
    assert records
    record = records[-1]
    assert record.request_id == "req_auth_error"
    assert record.status_code == HTTPStatus.UNAUTHORIZED
    assert record.error_code == ErrorCode.AUTH_INVALID_API_KEY
    assert record.api_key_fingerprint is not None
    assert record.api_key_fingerprint != "bad-key"


def test_cache_status_requires_api_key(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/cache/status")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == ErrorCode.AUTH_MISSING_API_KEY


def test_cache_status_returns_runtime_cache_data(monkeypatch, tmp_path) -> None:
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    monkeypatch.setenv("CACHE_DIR", str(cache_dir))
    clear_settings_cache()
    client = _build_client(monkeypatch)

    response = client.get("/api/v1/cache/status", headers={"X-API-Key": "secret-key"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status"] == "ok"
    assert payload["data"]["enabled"] is True
    assert payload["data"]["cache_dir"] == str(cache_dir)
    assert payload["data"]["cache_dir_status"]["exists"] is True
    assert payload["data"]["cache_dir_status"]["is_dir"] is True
    assert payload["data"]["cache_dir_status"]["ready_for_file_cache"] is True
    assert payload["data"]["layers"][0]["name"] == "runtime"
    assert payload["data"]["layers"][0]["backend"] == "memory"
    assert "hit_count" in payload["data"]["layers"][0]
    assert payload["data"]["layers"][1]["name"] == "market_snapshot"
    assert payload["data"]["layers"][1]["backend"] == "memory"
    assert payload["data"]["layers"][2]["name"] == "kline_file"
    assert payload["data"]["layers"][2]["backend"] == "json_file"
    assert "kline_file_cache_status" in payload["data"]["capabilities"]


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


def test_instruments_returns_metadata(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _fake_instruments(symbols: list[str], source: str = "auto") -> InstrumentResult:
        assert symbols == ["600519.SH", "000001.SZ"]
        assert source == "local"
        return InstrumentResult(
            items=[
                InstrumentInfo(
                    symbol="600519.SH",
                    name="贵州茅台",
                    market="SH",
                    instrument_type="stock",
                )
            ],
            missing_symbols=["000001.SZ"],
            source="local",
        )

    monkeypatch.setattr("qmt_data_api.api.http.instruments.get_instruments", _fake_instruments)

    response = client.get(
        "/api/v1/instruments?symbols=600519.SH,000001.SZ&source=local",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"][0]["symbol"] == "600519.SH"
    assert payload["data"][0]["name"] == "贵州茅台"
    assert payload["meta"]["missing_symbols"] == ["000001.SZ"]
    assert payload["meta"]["source"] == "local"


def test_trading_calendar_returns_days(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    def _fake_calendar(
        market: str,
        start: str,
        end: str,
        source: str = "auto",
    ) -> TradingCalendarResult:
        assert market == "SH"
        assert start == "20260101"
        assert end == "20260105"
        assert source == "local"
        return TradingCalendarResult(
            market="SH",
            start="2026-01-01",
            end="2026-01-05",
            trading_days=["2026-01-01", "2026-01-02", "2026-01-05"],
            previous_trading_day="2025-12-31",
            next_trading_day="2026-01-06",
            source="local",
        )

    monkeypatch.setattr("qmt_data_api.api.http.calendar.get_trading_calendar", _fake_calendar)

    response = client.get(
        "/api/v1/calendar/trading-days?market=SH&start=20260101&end=20260105&source=local",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"]["trading_days"] == ["2026-01-01", "2026-01-02", "2026-01-05"]
    assert payload["meta"]["source"] == "local"
    assert payload["meta"]["count"] == 3


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


def test_cache_status_reports_snapshot_cache_stats(monkeypatch) -> None:
    get_snapshot_cache().clear()
    monkeypatch.setenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "30")
    clear_settings_cache()
    client = _build_client(monkeypatch)

    def _fake_snapshots(symbols: list[str]):
        assert symbols == ["600519.SH"]
        return ([SnapshotItem(symbol="600519.SH", last_price=1688.88)], [])

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_snapshots", _fake_snapshots)

    first_response = client.get(
        "/api/v1/market/snapshot?symbols=600519.SH",
        headers={"X-API-Key": "secret-key"},
    )
    second_response = client.get(
        "/api/v1/market/snapshot?symbols=600519.SH",
        headers={"X-API-Key": "secret-key"},
    )
    status_response = client.get("/api/v1/cache/status", headers={"X-API-Key": "secret-key"})

    assert first_response.json()["meta"]["cache"] == "miss"
    assert second_response.json()["meta"]["cache"] == "hit"
    snapshot_layer = [
        layer for layer in status_response.json()["data"]["layers"] if layer["name"] == "market_snapshot"
    ][0]
    assert snapshot_layer["item_count"] >= 1
    assert snapshot_layer["hit_count"] >= 1


def test_clear_kline_cache_requires_api_key(monkeypatch) -> None:
    client = _build_client(monkeypatch)

    response = client.delete("/api/v1/cache/kline")

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.json()["code"] == ErrorCode.AUTH_MISSING_API_KEY


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
    assert payload["meta"]["cache"] == "miss"
    assert payload["meta"]["count"] == 1


def test_market_kline_supports_field_filter(monkeypatch) -> None:
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
        return KlineResult(
            symbol=symbol,
            period=period,
            adjust=adjust,
            source="qmt",
            bars=[KlineBar(trade_date="2024-01-02", open=1.0, close=2.0, volume=100)],
        )

    monkeypatch.setattr("qmt_data_api.api.http.market.get_market_klines", _fake_klines)

    response = client.get(
        "/api/v1/market/kline"
        "?symbol=600519.SH&period=1d&start=20240101&end=20240110&fields=trade_date,close",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["data"]["bars"] == [{"trade_date": "2024-01-02", "close": 2.0}]
    assert payload["meta"]["fields"] == ["trade_date", "close"]


def test_market_klines_batch_returns_multi_symbol_data(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()
    client = _build_client(monkeypatch)

    def _fake_fetch(
        symbol: str,
        period: str,
        start_time: str,
        end_time: str,
        adjust: str,
        limit: int | None,
    ):
        return [KlineBar(trade_date="2024-01-02", close=1685.01)]

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_klines", _fake_fetch)

    response = client.post(
        "/api/v1/market/klines",
        headers={"X-API-Key": "secret-key"},
        json={
            "symbols": ["600519.SH", "000001.SZ"],
            "period": "1d",
            "start": "20240101",
            "end": "20240110",
            "limit": 5,
            "fields": ["trade_date", "close"],
        },
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert [item["symbol"] for item in payload["data"]] == ["600519.SH", "000001.SZ"]
    assert payload["data"][0]["bars"] == [{"trade_date": "2024-01-02", "close": 1685.01}]
    assert payload["meta"]["count"] == 2
    assert payload["meta"]["fields"] == ["trade_date", "close"]


def test_market_latest_kline_returns_recent_count(monkeypatch) -> None:
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
        assert period == "1m"
        assert start == "19700101"
        assert limit == 2
        return KlineResult(
            symbol=symbol,
            period=period,
            adjust=adjust,
            source="qmt",
            bars=[
                KlineBar(time="2024-01-02T09:31:00+08:00", close=1.0),
                KlineBar(time="2024-01-02T09:32:00+08:00", close=2.0),
            ],
        )

    monkeypatch.setattr("qmt_data_api.api.http.market.get_market_klines", _fake_klines)

    response = client.get(
        "/api/v1/market/kline/latest?symbol=600519.SH&period=1m&count=2&fields=time,close",
        headers={"X-API-Key": "secret-key"},
    )

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["meta"]["count"] == 2
    assert payload["data"]["bars"][1] == {"time": "2024-01-02T09:32:00+08:00", "close": 2.0}


def test_market_kline_uses_file_cache_between_requests(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()
    client = _build_client(monkeypatch)
    calls = []

    def _fake_fetch(
        symbol: str,
        period: str,
        start_time: str,
        end_time: str,
        adjust: str,
        limit: int | None,
    ):
        calls.append((symbol, period, start_time, end_time, adjust, limit))
        return [
            KlineBar(
                time="2024-01-02T00:00:00+08:00",
                trade_date="2024-01-02",
                close=1685.01,
            )
        ]

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_klines", _fake_fetch)

    url = "/api/v1/market/kline?symbol=600519.SH&period=1d&start=20240101&end=20240110&limit=5"
    first_response = client.get(url, headers={"X-API-Key": "secret-key"})
    second_response = client.get(url, headers={"X-API-Key": "secret-key"})
    status_response = client.get("/api/v1/cache/status", headers={"X-API-Key": "secret-key"})

    assert first_response.status_code == HTTPStatus.OK
    assert second_response.status_code == HTTPStatus.OK
    assert len(calls) == 1
    assert first_response.json()["meta"]["source"] == "qmt"
    assert first_response.json()["meta"]["cache"] == "miss"
    assert second_response.json()["meta"]["source"] == "cache"
    assert second_response.json()["meta"]["cache"] == "hit"
    assert second_response.json()["data"]["bars"][0]["close"] == 1685.01
    kline_layer = [
        layer for layer in status_response.json()["data"]["layers"] if layer["name"] == "kline_file"
    ][0]
    assert kline_layer["item_count"] >= 1
    assert kline_layer["hit_count"] >= 1


def test_clear_kline_cache_removes_file_cache(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()
    client = _build_client(monkeypatch)

    def _fake_fetch(
        symbol: str,
        period: str,
        start_time: str,
        end_time: str,
        adjust: str,
        limit: int | None,
    ):
        return [KlineBar(trade_date="2024-01-02", close=1685.01)]

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_klines", _fake_fetch)

    client.get(
        "/api/v1/market/kline?symbol=600519.SH&period=1d&start=20240101&end=20240110&limit=5",
        headers={"X-API-Key": "secret-key"},
    )
    response = client.delete("/api/v1/cache/kline", headers={"X-API-Key": "secret-key"})
    status_response = client.get("/api/v1/cache/status", headers={"X-API-Key": "secret-key"})

    assert response.status_code == HTTPStatus.OK
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["removed_count"] == 1
    assert payload["data"]["layer"]["name"] == "kline_file"
    assert payload["data"]["layer"]["item_count"] == 0
    kline_layer = [
        layer for layer in status_response.json()["data"]["layers"] if layer["name"] == "kline_file"
    ][0]
    assert kline_layer["item_count"] == 0
    assert kline_layer["evicted_count"] >= 1


def test_rate_limit_blocks_excess_requests(monkeypatch) -> None:
    monkeypatch.setenv("API_RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("API_RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("API_RATE_LIMIT_WINDOW_SECONDS", "60")
    client = _build_client(monkeypatch)

    first_response = client.get("/api/v1/health", headers={"X-API-Key": "secret-key"})
    second_response = client.get("/api/v1/health", headers={"X-API-Key": "secret-key"})

    assert first_response.status_code == HTTPStatus.OK
    assert second_response.status_code == HTTPStatus.TOO_MANY_REQUESTS
    assert second_response.json()["code"] == "RATE_LIMIT_EXCEEDED"
