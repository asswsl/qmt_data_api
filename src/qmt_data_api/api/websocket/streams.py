# 生成 WebSocket 行情推送消息。
"""WebSocket stream payload builders."""

from __future__ import annotations

from typing import Any

from qmt_data_api.core.errors import AppError
from qmt_data_api.core.response import server_time_iso
from qmt_data_api.domain.market.schemas import SnapshotResult
from qmt_data_api.api.websocket.subscriptions import SnapshotSubscription


def snapshot_payload(
    request_id: str,
    result: SnapshotResult,
    subscription: SnapshotSubscription,
) -> dict[str, Any]:
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "request_id": request_id,
        "type": "market_snapshot",
        "data": [item.model_dump(exclude_none=True, exclude={"raw"}) for item in result.items],
        "meta": {
            "server_time": server_time_iso(),
            "missing_symbols": result.missing_symbols,
            "fields": result.fields,
            "source": result.source,
            "cache": result.cache,
            "interval_seconds": subscription.interval_seconds,
        },
    }


def error_payload(request_id: str, error: AppError) -> dict[str, Any]:
    return {
        "success": False,
        "code": error.code,
        "message": error.message,
        "request_id": request_id,
        "type": "error",
        "data": error.detail or None,
        "meta": {
            "retryable": error.retryable,
            "server_time": server_time_iso(),
        },
    }
