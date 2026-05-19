# 预留限流中间件。
"""Rate limit middleware."""

from __future__ import annotations

from collections import defaultdict, deque
import time
from typing import Deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from qmt_data_api.core.config import get_settings
from qmt_data_api.core.response import request_id_from, server_time_iso


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)
        self._requests: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        if not settings.api_rate_limit_enabled:
            return await call_next(request)

        key = request.headers.get("X-API-Key") or (request.client.host if request.client else "unknown")
        now = time.monotonic()
        window_start = now - settings.api_rate_limit_window_seconds
        bucket = self._requests[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()
        if len(bucket) >= settings.api_rate_limit_requests:
            request.state.error_code = "RATE_LIMIT_EXCEEDED"
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "请求过于频繁",
                    "request_id": request_id_from(request),
                    "data": {
                        "limit": settings.api_rate_limit_requests,
                        "window_seconds": settings.api_rate_limit_window_seconds,
                    },
                    "meta": {"retryable": True, "server_time": server_time_iso()},
                },
            )
        bucket.append(now)
        return await call_next(request)
