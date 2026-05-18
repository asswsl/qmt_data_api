# 提供行情快照领域服务。
"""Market domain service."""

from __future__ import annotations

from datetime import datetime

from qmt_data_api.cache.file_cache import get_kline_file_cache
from qmt_data_api.cache.keys import snapshot_key
from qmt_data_api.cache.memory import get_snapshot_cache
from qmt_data_api.cache.policies import snapshot_ttl_seconds
from qmt_data_api.core.config import get_settings
from qmt_data_api.domain.market.errors import (
    cache_miss_error,
    invalid_adjust_error,
    invalid_period_error,
    invalid_symbol_error,
    invalid_time_range_error,
    too_many_symbols_error,
    unsupported_source_error,
)
from qmt_data_api.domain.market.schemas import KlineResult, SnapshotResult
from qmt_data_api.providers.qmt.xtdata_adapter import fetch_xtdata_klines, fetch_xtdata_snapshots
from qmt_data_api.utils.symbols import is_valid_symbol, normalize_symbol_list

_DEFAULT_FIELDS = [
    "symbol",
    "quote_time",
    "last_price",
    "pre_close",
    "open",
    "high",
    "low",
    "volume",
    "amount",
    "bid1",
    "bid1_volume",
    "ask1",
    "ask1_volume",
]

_SUPPORTED_PERIODS = {"tick", "1m", "5m", "15m", "30m", "60m", "1d", "1w", "1mon"}
_SUPPORTED_ADJUST = {"none", "front", "back"}
_SUPPORTED_SOURCES = {"auto", "cache", "qmt"}
_SUPPORTED_SNAPSHOT_SOURCES = {"auto", "cache", "qmt"}


def _normalize_fields(fields: list[str] | None) -> list[str] | None:
    if fields is None:
        return None
    normalized = []
    seen = set()
    for field in fields:
        item = field.strip()
        if item and item not in seen:
            normalized.append(item)
            seen.add(item)
    return normalized or None


def _normalize_date(value: str) -> str:
    raw = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    raise invalid_time_range_error(value, value)


def _cache_status(cached_count: int, fetched_count: int) -> str:
    if cached_count and fetched_count:
        return "mixed"
    if cached_count:
        return "hit"
    return "miss"


def _snapshot_source(cached_count: int, fetched_count: int, requested_source: str) -> str:
    if requested_source == "cache":
        return "cache"
    if cached_count and fetched_count:
        return "mixed"
    if cached_count:
        return "cache"
    return "qmt"


def get_market_snapshots(
    symbols: list[str],
    fields: list[str] | None = None,
    source: str = "auto",
) -> SnapshotResult:
    settings = get_settings()
    normalized_symbols = normalize_symbol_list(symbols)
    if not normalized_symbols:
        raise invalid_symbol_error(symbols)
    if len(normalized_symbols) > settings.market_snapshot_max_symbols:
        raise too_many_symbols_error(len(normalized_symbols), settings.market_snapshot_max_symbols)

    invalid_symbols = [symbol for symbol in normalized_symbols if not is_valid_symbol(symbol)]
    if invalid_symbols:
        raise invalid_symbol_error(invalid_symbols)

    normalized_source = source.strip().lower()
    if normalized_source not in _SUPPORTED_SNAPSHOT_SOURCES:
        raise unsupported_source_error(source)

    requested_fields = _normalize_fields(fields)
    snapshot_cache = get_snapshot_cache()
    items_by_symbol = {}
    cached_count = 0
    fetched_count = 0
    missing_symbols: list[str] = []

    if normalized_source in {"auto", "cache"}:
        for symbol in normalized_symbols:
            item = snapshot_cache.get(snapshot_key(symbol))
            if item is not None:
                items_by_symbol[symbol] = item.model_copy(deep=True)
                cached_count += 1

    symbols_to_fetch = [
        symbol
        for symbol in normalized_symbols
        if symbol not in items_by_symbol and normalized_source in {"auto", "qmt"}
    ]
    if symbols_to_fetch:
        fetched_items, missing_symbols = fetch_xtdata_snapshots(symbols_to_fetch)
        ttl_seconds = snapshot_ttl_seconds()
        for item in fetched_items:
            items_by_symbol[item.symbol] = item
            fetched_count += 1
            if ttl_seconds > 0:
                snapshot_cache.set(
                    snapshot_key(item.symbol),
                    item.model_copy(deep=True),
                    ttl_seconds=ttl_seconds,
                )
    elif normalized_source == "cache":
        missing_symbols = [symbol for symbol in normalized_symbols if symbol not in items_by_symbol]
        if missing_symbols:
            raise cache_miss_error(missing_symbols)

    items = [items_by_symbol[symbol] for symbol in normalized_symbols if symbol in items_by_symbol]
    if requested_fields:
        allowed = {"symbol", *requested_fields}
        items = [
            item.model_copy(
                update={key: None for key in _DEFAULT_FIELDS if key not in allowed and key != "symbol"}
            )
            for item in items
        ]

    return SnapshotResult(
        items=items,
        missing_symbols=missing_symbols,
        fields=requested_fields,
        source=_snapshot_source(cached_count, fetched_count, normalized_source),
        cache=_cache_status(cached_count, fetched_count),
    )


def get_market_klines(
    symbol: str,
    period: str,
    start: str,
    end: str,
    adjust: str = "none",
    source: str = "auto",
    limit: int | None = None,
) -> KlineResult:
    normalized_symbols = normalize_symbol_list([symbol])
    if not normalized_symbols or not is_valid_symbol(normalized_symbols[0]):
        raise invalid_symbol_error(normalized_symbols or [symbol])
    normalized_symbol = normalized_symbols[0]

    normalized_period = period.strip()
    if normalized_period not in _SUPPORTED_PERIODS:
        raise invalid_period_error(period)

    normalized_adjust = adjust.strip().lower()
    if normalized_adjust not in _SUPPORTED_ADJUST:
        raise invalid_adjust_error(adjust)

    normalized_source = source.strip().lower()
    if normalized_source not in _SUPPORTED_SOURCES:
        raise unsupported_source_error(source)

    start_time = _normalize_date(start)
    end_time = _normalize_date(end)
    if start_time > end_time:
        raise invalid_time_range_error(start, end)

    kline_cache = get_kline_file_cache()
    if normalized_source in {"auto", "cache"}:
        cached_payload = kline_cache.get(
            normalized_symbol,
            normalized_period,
            normalized_adjust,
            start_time,
            end_time,
            limit,
        )
        if cached_payload is not None:
            cached_result = KlineResult.model_validate(cached_payload)
            return cached_result.model_copy(update={"source": "cache", "cache": "hit"})
        if normalized_source == "cache":
            raise cache_miss_error([normalized_symbol])

    bars = fetch_xtdata_klines(
        normalized_symbol,
        normalized_period,
        start_time,
        end_time,
        normalized_adjust,
        limit,
    )
    result = KlineResult(
        symbol=normalized_symbol,
        period=normalized_period,
        adjust=normalized_adjust,
        source="qmt",
        bars=bars,
        cache="miss",
    )
    kline_cache.set(
        normalized_symbol,
        normalized_period,
        normalized_adjust,
        start_time,
        end_time,
        limit,
        result.model_dump(mode="json"),
    )
    return result
