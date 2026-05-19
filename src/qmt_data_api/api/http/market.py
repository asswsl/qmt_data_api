# 提供行情快照 HTTP 接口。
"""Market data HTTP routes."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.constants import DEFAULT_TIMEZONE
from qmt_data_api.core.response import success_response
from qmt_data_api.domain.market.schemas import KlineBatchRequest, SnapshotRequest
from qmt_data_api.domain.market.service import (
    get_market_klines,
    get_market_klines_batch,
    get_market_snapshots,
)

router = APIRouter(prefix="/api/v1/market", dependencies=[Depends(require_api_key)])


def _split_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _dump_kline_bars(result, fields: list[str] | None = None) -> list[dict[str, object]]:
    allowed = set(fields or [])
    bars = []
    for bar in result.bars:
        item = bar.model_dump(exclude_none=True)
        if allowed:
            item = {key: value for key, value in item.items() if key in allowed}
        bars.append(item)
    return bars


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


@router.get(
    "/kline",
    summary="查询单证券历史 K 线",
    description="查询单只证券的历史 K 线，支持 QMT 回源、文件缓存和字段裁剪。",
)
def get_kline(
    request: Request,
    symbol: str = Query(min_length=1),
    period: str = "1d",
    start: str = Query(min_length=8),
    end: str = Query(min_length=8),
    adjust: str = "none",
    source: str = "auto",
    limit: int | None = Query(default=None, ge=1),
    fields: str | None = None,
) -> dict[str, object]:
    result = get_market_klines(symbol, period, start, end, adjust, source, limit)
    requested_fields = _split_csv(fields)
    return success_response(
        request,
        data={
            "symbol": result.symbol,
            "period": result.period,
            "adjust": result.adjust,
            "bars": _dump_kline_bars(result, requested_fields),
        },
        meta={
            "source": result.source,
            "cache": result.cache,
            "fields": requested_fields,
            "count": len(result.bars),
        },
    )


@router.post(
    "/klines",
    summary="批量查询历史 K 线",
    description="一次查询多只证券的历史 K 线，适合远程客户端批量拉取主机 QMT 数据。",
)
def post_klines(request: Request, payload: KlineBatchRequest) -> dict[str, object]:
    result = get_market_klines_batch(
        payload.symbols,
        payload.period,
        payload.start,
        payload.end,
        payload.adjust,
        payload.source,
        payload.limit,
        payload.fields,
    )
    return success_response(
        request,
        data=[
            {
                "symbol": item.symbol,
                "period": item.period,
                "adjust": item.adjust,
                "bars": _dump_kline_bars(item, result.fields),
            }
            for item in result.items
        ],
        meta={
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
            "source": result.source,
            "cache": result.cache,
            "count": sum(len(item.bars) for item in result.items),
        },
    )


@router.get(
    "/kline/latest",
    summary="查询最近 K 线",
    description="按 count 查询单证券最近 K 线，适合准实时刷新。",
)
def get_latest_kline(
    request: Request,
    symbol: str = Query(min_length=1),
    period: str = "1m",
    count: int = Query(default=240, ge=1),
    adjust: str = "none",
    source: str = "auto",
    fields: str | None = None,
) -> dict[str, object]:
    end = datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d")
    result = get_market_klines(symbol, period, "19700101", end, adjust, source, count)
    requested_fields = _split_csv(fields)
    return success_response(
        request,
        data={
            "symbol": result.symbol,
            "period": result.period,
            "adjust": result.adjust,
            "bars": _dump_kline_bars(result, requested_fields),
        },
        meta={
            "source": result.source,
            "cache": result.cache,
            "fields": requested_fields,
            "count": len(result.bars),
        },
    )
