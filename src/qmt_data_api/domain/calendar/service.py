# 提供交易日历领域服务。
"""Trading calendar domain service."""

from __future__ import annotations

from datetime import datetime, timedelta

from qmt_data_api.core.errors import QmtError
from qmt_data_api.domain.calendar.schemas import TradingCalendarResult
from qmt_data_api.domain.market.errors import invalid_time_range_error, unsupported_source_error
from qmt_data_api.providers.qmt.xtdata_adapter import fetch_xtdata_trading_days

_SUPPORTED_SOURCES = {"auto", "qmt", "local"}


def _normalize_date(value: str) -> str:
    raw = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise invalid_time_range_error(value, value)


def _format_day(value: str) -> str:
    return datetime.strptime(value, "%Y%m%d").strftime("%Y-%m-%d")


def _weekday_trading_days(start: str, end: str) -> list[str]:
    current = datetime.strptime(start, "%Y%m%d").date()
    end_date = datetime.strptime(end, "%Y%m%d").date()
    days = []
    while current <= end_date:
        if current.weekday() < 5:
            days.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    return days


def _previous_weekday(start: str) -> str | None:
    current = datetime.strptime(start, "%Y%m%d").date() - timedelta(days=1)
    for _ in range(10):
        if current.weekday() < 5:
            return current.strftime("%Y-%m-%d")
        current -= timedelta(days=1)
    return None


def _next_weekday(end: str) -> str | None:
    current = datetime.strptime(end, "%Y%m%d").date() + timedelta(days=1)
    for _ in range(10):
        if current.weekday() < 5:
            return current.strftime("%Y-%m-%d")
        current += timedelta(days=1)
    return None


def get_trading_calendar(
    market: str,
    start: str,
    end: str,
    source: str = "auto",
) -> TradingCalendarResult:
    normalized_market = market.strip().upper() or "SH"
    normalized_start = _normalize_date(start)
    normalized_end = _normalize_date(end)
    if normalized_start > normalized_end:
        raise invalid_time_range_error(start, end)

    normalized_source = source.strip().lower()
    if normalized_source not in _SUPPORTED_SOURCES:
        raise unsupported_source_error(source)

    trading_days: list[str] = []
    result_source = "local"
    if normalized_source in {"auto", "qmt"}:
        try:
            trading_days = fetch_xtdata_trading_days(normalized_market, normalized_start, normalized_end)
        except QmtError:
            if normalized_source == "qmt":
                raise
            trading_days = []
        result_source = "qmt"
    if not trading_days and normalized_source == "auto":
        trading_days = _weekday_trading_days(normalized_start, normalized_end)
        result_source = "local"
    if normalized_source == "local":
        trading_days = _weekday_trading_days(normalized_start, normalized_end)

    return TradingCalendarResult(
        market=normalized_market,
        start=_format_day(normalized_start),
        end=_format_day(normalized_end),
        trading_days=trading_days,
        previous_trading_day=_previous_weekday(normalized_start),
        next_trading_day=_next_weekday(normalized_end),
        source=result_source,
    )
