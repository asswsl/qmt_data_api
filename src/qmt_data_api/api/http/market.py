# 提供行情快照 HTTP 接口。
"""Market data HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.response import success_response
from qmt_data_api.domain.market.schemas import SnapshotRequest
from qmt_data_api.domain.market.service import get_market_klines, get_market_snapshots

router = APIRouter(prefix="/api/v1/market", dependencies=[Depends(require_api_key)])


def _split_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get("/snapshot")
def get_snapshot(
    request: Request,
    symbols: str = Query(min_length=1),
    fields: str | None = None,
    source: str = "auto",
) -> dict[str, object]:
    result = get_market_snapshots(_split_csv(symbols) or [], _split_csv(fields), source)
    return success_response(
        request,
        data=[item.model_dump(exclude_none=True, exclude={"raw"}) for item in result.items],
        meta={
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
            "source": result.source,
            "cache": result.cache,
        },
    )


@router.post("/snapshot")
def post_snapshot(request: Request, payload: SnapshotRequest) -> dict[str, object]:
    result = get_market_snapshots(payload.symbols, payload.fields, payload.source)
    return success_response(
        request,
        data=[item.model_dump(exclude_none=True, exclude={"raw"}) for item in result.items],
        meta={
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
            "source": result.source,
            "cache": result.cache,
        },
    )


@router.get("/kline")
def get_kline(
    request: Request,
    symbol: str = Query(min_length=1),
    period: str = "1d",
    start: str = Query(min_length=8),
    end: str = Query(min_length=8),
    adjust: str = "none",
    source: str = "auto",
    limit: int | None = Query(default=None, ge=1),
) -> dict[str, object]:
    result = get_market_klines(symbol, period, start, end, adjust, source, limit)
    return success_response(
        request,
        data={
            "symbol": result.symbol,
            "period": result.period,
            "adjust": result.adjust,
            "bars": [bar.model_dump(exclude_none=True) for bar in result.bars],
        },
        meta={
            "source": result.source,
            "count": len(result.bars),
        },
    )
