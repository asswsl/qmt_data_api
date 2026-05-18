# 验证行情快照服务的参数校验和结果整理。
from __future__ import annotations

from qmt_data_api.core.config import clear_settings_cache
from qmt_data_api.core.errors import ErrorCode, MarketDataError
from qmt_data_api.domain.market.schemas import KlineBar, SnapshotItem
from qmt_data_api.domain.market.service import get_market_klines, get_market_snapshots
from qmt_data_api.cache.memory import get_snapshot_cache


def test_market_snapshot_normalizes_symbols_and_reports_missing(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "10")
    monkeypatch.setenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "30")
    clear_settings_cache()
    get_snapshot_cache().clear()

    def _fake_fetch(symbols: list[str]):
        assert symbols == ["600519.SH", "000001.SZ"]
        return (
            [
                SnapshotItem(
                    symbol="600519.SH",
                    last_price=1688.88,
                    volume=1000,
                )
            ],
            ["000001.SZ"],
        )

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_snapshots", _fake_fetch)

    result = get_market_snapshots(["600519.sh", "600519.SH", "000001.sz"])

    assert len(result.items) == 1
    assert result.items[0].symbol == "600519.SH"
    assert result.missing_symbols == ["000001.SZ"]
    assert result.source == "qmt"
    assert result.cache == "miss"

    clear_settings_cache()


def test_market_snapshot_uses_cache_after_first_fetch(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "10")
    monkeypatch.setenv("MARKET_SNAPSHOT_CACHE_TTL_SECONDS", "30")
    clear_settings_cache()
    get_snapshot_cache().clear()
    calls = []

    def _fake_fetch(symbols: list[str]):
        calls.append(symbols)
        return ([SnapshotItem(symbol="600519.SH", last_price=1688.88)], [])

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_snapshots", _fake_fetch)

    first_result = get_market_snapshots(["600519.SH"])
    second_result = get_market_snapshots(["600519.SH"])

    assert len(calls) == 1
    assert first_result.cache == "miss"
    assert first_result.source == "qmt"
    assert second_result.cache == "hit"
    assert second_result.source == "cache"
    assert second_result.items[0].last_price == 1688.88

    clear_settings_cache()


def test_market_snapshot_cache_source_reports_cache_miss(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "10")
    clear_settings_cache()
    get_snapshot_cache().clear()

    try:
        get_market_snapshots(["000001.SZ"], source="cache")
    except MarketDataError as exc:
        assert exc.code == ErrorCode.CACHE_MISS
        assert exc.detail == {"symbols": ["000001.SZ"]}
    else:
        raise AssertionError("expected MarketDataError")

    clear_settings_cache()


def test_market_snapshot_rejects_invalid_symbol(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "10")
    clear_settings_cache()

    try:
        get_market_snapshots(["bad-symbol"])
    except MarketDataError as exc:
        assert exc.code == ErrorCode.INVALID_SYMBOL
        assert exc.detail["symbols"] == ["BAD-SYMBOL"]
    else:
        raise AssertionError("expected MarketDataError")

    clear_settings_cache()


def test_market_snapshot_rejects_too_many_symbols(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "1")
    clear_settings_cache()

    try:
        get_market_snapshots(["600519.SH", "000001.SZ"])
    except MarketDataError as exc:
        assert exc.code == ErrorCode.TOO_MANY_SYMBOLS
        assert exc.detail == {"count": 2, "limit": 1}
    else:
        raise AssertionError("expected MarketDataError")

    clear_settings_cache()


def test_market_kline_normalizes_params_and_returns_bars(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()

    def _fake_fetch(
        symbol: str,
        period: str,
        start_time: str,
        end_time: str,
        adjust: str,
        limit: int | None,
    ):
        assert symbol == "600519.SH"
        assert period == "1d"
        assert start_time == "20240101"
        assert end_time == "20240110"
        assert adjust == "none"
        assert limit == 10
        return [
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
        ]

    monkeypatch.setattr("qmt_data_api.domain.market.service.fetch_xtdata_klines", _fake_fetch)

    result = get_market_klines("600519.sh", "1d", "2024-01-01", "20240110", limit=10)

    assert result.symbol == "600519.SH"
    assert result.source == "qmt"
    assert result.cache == "miss"
    assert result.bars[0].close == 1685.01

    clear_settings_cache()


def test_market_kline_uses_file_cache_after_first_fetch(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()
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

    first_result = get_market_klines("600519.SH", "1d", "20240101", "20240110", limit=5)
    second_result = get_market_klines("600519.SH", "1d", "20240101", "20240110", limit=5)

    assert len(calls) == 1
    assert first_result.source == "qmt"
    assert first_result.cache == "miss"
    assert second_result.source == "cache"
    assert second_result.cache == "hit"
    assert second_result.bars[0].close == 1685.01

    clear_settings_cache()


def test_market_kline_cache_source_reports_cache_miss(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CACHE_DIR", str(tmp_path / "cache"))
    clear_settings_cache()

    try:
        get_market_klines("600519.SH", "1d", "20240101", "20240110", source="cache")
    except MarketDataError as exc:
        assert exc.code == ErrorCode.CACHE_MISS
        assert exc.detail == {"symbols": ["600519.SH"]}
    else:
        raise AssertionError("expected MarketDataError")

    clear_settings_cache()


def test_market_kline_rejects_invalid_period() -> None:
    try:
        get_market_klines("600519.SH", "2m", "20240101", "20240110")
    except MarketDataError as exc:
        assert exc.code == ErrorCode.INVALID_PERIOD
        assert exc.detail == {"period": "2m"}
    else:
        raise AssertionError("expected MarketDataError")


def test_market_kline_rejects_invalid_time_range() -> None:
    try:
        get_market_klines("600519.SH", "1d", "20240110", "20240101")
    except MarketDataError as exc:
        assert exc.code == ErrorCode.INVALID_TIME_RANGE
    else:
        raise AssertionError("expected MarketDataError")
