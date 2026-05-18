# 验证行情快照服务的参数校验和结果整理。
from __future__ import annotations

from qmt_data_api.core.config import clear_settings_cache
from qmt_data_api.core.errors import ErrorCode, MarketDataError
from qmt_data_api.domain.market.schemas import SnapshotItem
from qmt_data_api.domain.market.service import get_market_snapshots


def test_market_snapshot_normalizes_symbols_and_reports_missing(monkeypatch) -> None:
    monkeypatch.setenv("MARKET_SNAPSHOT_MAX_SYMBOLS", "10")
    clear_settings_cache()

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
