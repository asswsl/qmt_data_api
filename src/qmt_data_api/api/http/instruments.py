# 预留证券基础信息 HTTP 接口。
"""Instrument metadata HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.response import success_response
from qmt_data_api.domain.instrument.schemas import InstrumentRequest
from qmt_data_api.domain.instrument.service import get_instruments

router = APIRouter(prefix="/api/v1/instruments", dependencies=[Depends(require_api_key)])


def _split_csv(value: str | None) -> list[str]:
    if value is None:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


@router.get(
    "",
    summary="查询证券基础信息",
    description="按证券代码查询名称、市场、类型、上市状态等基础信息。",
)
def get_instrument_metadata(
    request: Request,
    symbols: str = Query(min_length=1),
    source: str = "auto",
    include_raw: bool = False,
) -> dict[str, object]:
    result = get_instruments(_split_csv(symbols), source)
    return success_response(
        request,
        data=[
            item.model_dump(exclude_none=True, exclude=set() if include_raw else {"raw"})
            for item in result.items
        ],
        meta={"missing_symbols": result.missing_symbols, "source": result.source},
    )


@router.post(
    "",
    summary="批量查询证券基础信息",
    description="使用 JSON 请求体批量查询证券基础信息。",
)
def post_instrument_metadata(
    request: Request,
    payload: InstrumentRequest,
    include_raw: bool = False,
) -> dict[str, object]:
    result = get_instruments(payload.symbols, payload.source)
    return success_response(
        request,
        data=[
            item.model_dump(exclude_none=True, exclude=set() if include_raw else {"raw"})
            for item in result.items
        ],
        meta={"missing_symbols": result.missing_symbols, "source": result.source},
    )
