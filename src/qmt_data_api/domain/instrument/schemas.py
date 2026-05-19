# 预留证券基础信息数据结构。
"""Instrument domain schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InstrumentInfo(BaseModel):
    symbol: str
    name: str | None = None
    market: str | None = None
    instrument_type: str | None = None
    status: str | None = None
    listed_date: str | None = None
    delisted_date: str | None = None
    raw: dict[str, Any] | None = None


class InstrumentResult(BaseModel):
    items: list[InstrumentInfo]
    missing_symbols: list[str]
    source: str = "qmt"


class InstrumentRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    source: str = "auto"
