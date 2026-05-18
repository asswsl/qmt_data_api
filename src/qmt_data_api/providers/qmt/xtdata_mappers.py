# 映射 xtdata 原始行情快照。
"""QMT raw data mapping helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from qmt_data_api.core.constants import DEFAULT_TIMEZONE
from qmt_data_api.domain.market.schemas import SnapshotItem

_FIELD_ALIASES = {
    "lastPrice": "last_price",
    "last_price": "last_price",
    "preClose": "pre_close",
    "lastClose": "pre_close",
    "pre_close": "pre_close",
    "open": "open",
    "high": "high",
    "low": "low",
    "volume": "volume",
    "amount": "amount",
    "bidPrice": "bid1",
    "askPrice": "ask1",
    "bidVol": "bid1_volume",
    "askVol": "ask1_volume",
    "time": "quote_time",
    "timetag": "quote_time",
}


def _first_level(value: Any) -> Any | None:
    if isinstance(value, (list, tuple)) and value:
        return value[0]
    return value


def _quote_time(value: Any) -> str | None:
    if value in (None, "", 0):
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 10_000_000_000 else value
        return datetime.fromtimestamp(timestamp, ZoneInfo(DEFAULT_TIMEZONE)).isoformat(
            timespec="seconds"
        )
    return str(value)


def _numeric(value: Any) -> float | None:
    value = _first_level(value)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def map_xtdata_snapshot(symbol: str, raw: dict[str, Any]) -> SnapshotItem:
    mapped: dict[str, Any] = {"symbol": symbol, "raw": raw}
    for raw_key, target_key in _FIELD_ALIASES.items():
        if raw_key not in raw:
            continue
        if mapped.get(target_key) is not None:
            continue
        if target_key == "quote_time":
            mapped[target_key] = _quote_time(raw[raw_key])
        else:
            mapped[target_key] = _numeric(raw[raw_key])
    return SnapshotItem(**mapped)
