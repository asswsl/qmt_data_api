# 提供交易日历 HTTP 接口。
"""Trading calendar HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.response import success_response
from qmt_data_api.domain.calendar.service import get_trading_calendar

router = APIRouter(prefix="/api/v1/calendar", dependencies=[Depends(require_api_key)])


@router.get(
    "/trading-days",
    summary="查询交易日历",
    description="返回指定市场和日期区间内的交易日列表，以及区间前后相邻交易日。",
)
def trading_days(
    request: Request,
    market: str = "SH",
    start: str = Query(min_length=8),
    end: str = Query(min_length=8),
    source: str = "auto",
) -> dict[str, object]:
    result = get_trading_calendar(market, start, end, source)
    return success_response(
        request,
        data=result.model_dump(),
        meta={"source": result.source, "count": len(result.trading_days)},
    )
