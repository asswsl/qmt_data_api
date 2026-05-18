# 提供行情快照领域服务。
"""Market domain service."""

from __future__ import annotations

from qmt_data_api.core.config import get_settings
from qmt_data_api.domain.market.errors import invalid_symbol_error, too_many_symbols_error
from qmt_data_api.domain.market.schemas import SnapshotResult
from qmt_data_api.providers.qmt.xtdata_adapter import fetch_xtdata_snapshots
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


def get_market_snapshots(symbols: list[str], fields: list[str] | None = None) -> SnapshotResult:
    settings = get_settings()
    normalized_symbols = normalize_symbol_list(symbols)
    if not normalized_symbols:
        raise invalid_symbol_error(symbols)
    if len(normalized_symbols) > settings.market_snapshot_max_symbols:
        raise too_many_symbols_error(len(normalized_symbols), settings.market_snapshot_max_symbols)

    invalid_symbols = [symbol for symbol in normalized_symbols if not is_valid_symbol(symbol)]
    if invalid_symbols:
        raise invalid_symbol_error(invalid_symbols)

    requested_fields = _normalize_fields(fields)
    items, missing_symbols = fetch_xtdata_snapshots(normalized_symbols)
    if requested_fields:
        allowed = {"symbol", *requested_fields}
        items = [
            item.model_copy(
                update={key: None for key in _DEFAULT_FIELDS if key not in allowed and key != "symbol"}
            )
            for item in items
        ]

    return SnapshotResult(items=items, missing_symbols=missing_symbols, fields=requested_fields)
