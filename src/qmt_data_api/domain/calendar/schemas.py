# 定义交易日历领域数据结构。
"""Trading calendar domain schemas."""

from __future__ import annotations

from pydantic import BaseModel


class TradingCalendarResult(BaseModel):
    market: str
    start: str
    end: str
    trading_days: list[str]
    previous_trading_day: str | None = None
    next_trading_day: str | None = None
    source: str = "qmt"
