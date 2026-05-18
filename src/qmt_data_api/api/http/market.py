# 提供行情快照 HTTP 接口。
"""Market data HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.response import success_response
from qmt_data_api.domain.market.schemas import SnapshotRequest
from qmt_data_api.domain.market.service import get_market_snapshots

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
) -> dict[str, object]:
    result = get_market_snapshots(_split_csv(symbols) or [], _split_csv(fields))
    return success_response(
        request,
        data=[item.model_dump(exclude_none=True, exclude={"raw"}) for item in result.items],
        meta={
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
        },
    )


@router.post("/snapshot")
def post_snapshot(request: Request, payload: SnapshotRequest) -> dict[str, object]:
    result = get_market_snapshots(payload.symbols, payload.fields)
    return success_response(
        request,
        data=[item.model_dump(exclude_none=True, exclude={"raw"}) for item in result.items],
        meta={
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
        },
    )
