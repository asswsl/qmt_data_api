# 生成统一 API 响应结构。
"""Unified API response helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import Request
from fastapi.responses import JSONResponse

from qmt_data_api.core.constants import DEFAULT_TIMEZONE
from qmt_data_api.core.errors import AppError


def server_time_iso() -> str:
    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat(timespec="seconds")


def request_id_from(request: Request) -> str:
    return getattr(request.state, "request_id", "req_missing")


def success_response(
    request: Request,
    data: Any,
    *,
    code: str = "OK",
    message: str = "success",
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload_meta = {"server_time": server_time_iso()}
    if meta:
        payload_meta.update(meta)
    return {
        "success": True,
        "code": code,
        "message": message,
        "request_id": request_id_from(request),
        "data": data,
        "meta": payload_meta,
    }


def error_response(request: Request, error: AppError) -> JSONResponse:
    request.state.error_code = error.code
    payload = {
        "success": False,
        "code": error.code,
        "message": error.message,
        "request_id": request_id_from(request),
        "data": error.detail or None,
        "meta": {
            "retryable": error.retryable,
            "server_time": server_time_iso(),
        },
    }
    return JSONResponse(status_code=error.status_code, content=payload)
