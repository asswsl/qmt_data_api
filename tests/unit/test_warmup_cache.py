# 验证历史 K 线缓存预热任务。
from __future__ import annotations

from qmt_data_api.domain.market.errors import invalid_period_error
from qmt_data_api.domain.market.schemas import KlineBar, KlineResult
from qmt_data_api.tasks.warmup_cache import KlineWarmupRequest, run_kline_cache_warmup


def test_kline_warmup_collects_success_and_failure(monkeypatch) -> None:
    calls = []

    def _fake_klines(
        symbol: str,
        period: str,
        start: str,
        end: str,
        adjust: str = "none",
        source: str = "auto",
        limit: int | None = None,
    ) -> KlineResult:
        calls.append((symbol, period, source))
        if period == "5m":
            raise invalid_period_error(period)
        return KlineResult(
            symbol=symbol,
            period=period,
            adjust=adjust,
            source="qmt",
            cache="miss",
            bars=[KlineBar(trade_date="2024-01-02", close=1685.01)],
        )

    monkeypatch.setattr("qmt_data_api.tasks.warmup_cache.get_market_klines", _fake_klines)

    result = run_kline_cache_warmup(
        KlineWarmupRequest(
            symbols=["600519.SH"],
            periods=["1d", "5m"],
            start="20240101",
            end="20240110",
        )
    )

    assert calls == [("600519.SH", "1d", "auto"), ("600519.SH", "5m", "auto")]
    assert result.status == "partial_failed"
    assert result.requested_count == 2
    assert result.success_count == 1
    assert result.refreshed_count == 1
    assert result.failed_count == 1
    assert result.items[1].error_code == "INVALID_PERIOD"


def test_kline_warmup_force_refresh_uses_qmt_source(monkeypatch) -> None:
    calls = []

    def _fake_klines(
        symbol: str,
        period: str,
        start: str,
        end: str,
        adjust: str = "none",
        source: str = "auto",
        limit: int | None = None,
    ) -> KlineResult:
        calls.append(source)
        return KlineResult(
            symbol=symbol,
            period=period,
            adjust=adjust,
            source="qmt",
            cache="miss",
            bars=[],
        )

    monkeypatch.setattr("qmt_data_api.tasks.warmup_cache.get_market_klines", _fake_klines)

    result = run_kline_cache_warmup(
        KlineWarmupRequest(
            symbols=["600519.SH"],
            periods=["1d"],
            start="20240101",
            end="20240110",
            force_refresh=True,
        )
    )

    assert calls == ["qmt"]
    assert result.status == "ok"
    assert result.success_count == 1
