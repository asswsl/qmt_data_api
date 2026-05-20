# 提供 WebSocket 实时行情路由。
"""WebSocket routes."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from uuid import uuid4

import anyio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from qmt_data_api.api.websocket.connections import connection_manager
from qmt_data_api.api.websocket.streams import error_payload, snapshot_payload
from qmt_data_api.api.websocket.subscriptions import build_snapshot_subscription
from qmt_data_api.core.config import get_settings
from qmt_data_api.core.constants import API_KEY_HEADER, REQUEST_ID_HEADER
from qmt_data_api.core.errors import AppError, AuthError, ErrorCode
from qmt_data_api.domain.market.service import get_market_snapshots

router = APIRouter()


def _request_id(websocket: WebSocket) -> str:
    return websocket.headers.get(REQUEST_ID_HEADER) or f"req_ws_{uuid4().hex}"


def _authenticate_websocket(websocket: WebSocket) -> str | None:
    settings = get_settings()
    if not settings.api_key_enabled:
        return None

    api_key = websocket.query_params.get("api_key") or websocket.headers.get(API_KEY_HEADER)
    if not api_key:
        raise AuthError(
            code=ErrorCode.AUTH_MISSING_API_KEY,
            message="缺少 API Key",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    if api_key not in settings.api_keys:
        raise AuthError(
            code=ErrorCode.AUTH_INVALID_API_KEY,
            message="API Key 无效",
            status_code=HTTPStatus.UNAUTHORIZED,
        )
    return api_key


@router.websocket("/ws/v1/market/snapshot")
async def stream_market_snapshot(
    websocket: WebSocket,
    symbols: str,
    fields: str | None = None,
    source: str = "auto",
    interval_seconds: float = 3.0,
) -> None:
    request_id = _request_id(websocket)
    await websocket.accept()

    try:
        _authenticate_websocket(websocket)
    except AuthError as exc:
        await websocket.send_json(error_payload(request_id, exc))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    subscription = build_snapshot_subscription(symbols, fields, source, interval_seconds)
    connection_manager.connect(websocket)
    try:
        while True:
            try:
                result = await anyio.to_thread.run_sync(
                    get_market_snapshots,
                    subscription.symbols,
                    subscription.fields,
                    subscription.source,
                )
                await websocket.send_json(snapshot_payload(request_id, result, subscription))
            except AppError as exc:
                await websocket.send_json(error_payload(request_id, exc))
                if not exc.retryable:
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    return
            await asyncio.sleep(subscription.interval_seconds)
    except WebSocketDisconnect:
        return
    finally:
        connection_manager.disconnect(websocket)
