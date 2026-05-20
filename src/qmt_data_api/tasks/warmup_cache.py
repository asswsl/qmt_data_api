# 提供缓存预热任务。
"""Cache warmup tasks."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from qmt_data_api.core.constants import DEFAULT_TIMEZONE
from qmt_data_api.domain.market.service import get_market_klines


class KlineWarmupRequest(BaseModel):
    symbols: list[str] = Field(min_length=1)
    periods: list[str] = Field(default_factory=lambda: ["1d"], min_length=1)
    start: str
    end: str
    adjust: str = "none"
    limit: int | None = Field(default=None, ge=1)
    force_refresh: bool = False


class KlineWarmupItem(BaseModel):
    symbol: str
    period: str
    status: str
    source: str | None = None
    cache: str | None = None
    count: int = 0
    error_code: str | None = None
    error_message: str | None = None


class KlineWarmupResult(BaseModel):
    status: str
    started_at: str
    finished_at: str
    requested_count: int
    success_count: int
    cached_count: int
    refreshed_count: int
    failed_count: int
    items: list[KlineWarmupItem]


_last_kline_warmup_result: KlineWarmupResult | None = None


def _now_iso() -> str:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat(timespec="seconds")


def run_kline_cache_warmup(payload: KlineWarmupRequest) -> KlineWarmupResult:
    global _last_kline_warmup_result

    started_at = _now_iso()
    source = "qmt" if payload.force_refresh else "auto"
    items: list[KlineWarmupItem] = []
    for symbol in payload.symbols:
        for period in payload.periods:
            try:
                result = get_market_klines(
                    symbol,
                    period,
                    payload.start,
                    payload.end,
                    payload.adjust,
                    source,
                    payload.limit,
                )
            except Exception as exc:
                items.append(_failed_item(symbol, period, exc))
                continue
            items.append(
                KlineWarmupItem(
                    symbol=result.symbol,
                    period=result.period,
                    status="ok",
                    source=result.source,
                    cache=result.cache,
                    count=len(result.bars),
                )
            )

    failed_count = len([item for item in items if item.status == "failed"])
    cached_count = len([item for item in items if item.cache == "hit"])
    refreshed_count = len([item for item in items if item.cache == "miss"])
    success_count = len(items) - failed_count
    status = "ok" if failed_count == 0 else "partial_failed"
    result = KlineWarmupResult(
        status=status,
        started_at=started_at,
        finished_at=_now_iso(),
        requested_count=len(payload.symbols) * len(payload.periods),
        success_count=success_count,
        cached_count=cached_count,
        refreshed_count=refreshed_count,
        failed_count=failed_count,
        items=items,
    )
    _last_kline_warmup_result = result
    return result


def get_last_kline_warmup_result() -> KlineWarmupResult | None:
    return _last_kline_warmup_result


def _failed_item(symbol: str, period: str, exc: Exception) -> KlineWarmupItem:
    error_code = getattr(exc, "code", exc.__class__.__name__)
    message = getattr(exc, "message", str(exc))
    detail = getattr(exc, "detail", None)
    if isinstance(detail, dict) and detail:
        message = f"{message}: {_short_detail(detail)}"
    return KlineWarmupItem(
        symbol=symbol,
        period=period,
        status="failed",
        error_code=str(error_code),
        error_message=str(message),
    )


def _short_detail(detail: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in detail.items())
