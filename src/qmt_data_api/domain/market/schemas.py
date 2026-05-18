# 定义行情快照领域数据结构。
"""Market domain schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SnapshotRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    fields: list[str] | None = None
    source: str = "auto"


class SnapshotItem(BaseModel):
    symbol: str
    quote_time: str | None = None
    last_price: float | None = None
    pre_close: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    amount: float | None = None
    bid1: float | None = None
    bid1_volume: float | None = None
    ask1: float | None = None
    ask1_volume: float | None = None
    raw: dict[str, Any] | None = None


class SnapshotResult(BaseModel):
    items: list[SnapshotItem]
    missing_symbols: list[str]
    fields: list[str] | None = None
    source: str = "qmt"
    cache: str = "miss"


class KlineBar(BaseModel):
    time: str | None = None
    trade_date: str | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    amount: float | None = None
    pre_close: float | None = None
    suspend_flag: int | None = None


class KlineResult(BaseModel):
    symbol: str
    period: str
    adjust: str
    source: str
    bars: list[KlineBar]
    cache: str = "miss"
