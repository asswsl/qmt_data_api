# 记录每次 HTTP 请求的结构化访问日志。
"""Access log middleware."""

from __future__ import annotations

import hashlib
import logging
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from qmt_data_api.core.constants import API_KEY_HEADER, REQUEST_ID_HEADER

ACCESS_LOGGER_NAME = "qmt_data_api.access"

logger = logging.getLogger(ACCESS_LOGGER_NAME)


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started_at = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration_ms = round((time.perf_counter() - started_at) * 1000, 3)
            self._write_log(request, status_code, duration_ms)

    def _write_log(self, request: Request, status_code: int, duration_ms: float) -> None:
        try:
            error_code = getattr(request.state, "error_code", None)
            logger.info(
                "http_access",
                extra={
                    "request_id": self._request_id(request),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": self._client_ip(request),
                    "error_code": error_code,
                    "api_key_fingerprint": self._api_key_fingerprint(request),
                },
            )
        except Exception:
            logger.exception("访问日志写入失败")

    @staticmethod
    def _request_id(request: Request) -> str:
        return getattr(request.state, "request_id", None) or request.headers.get(REQUEST_ID_HEADER, "req_missing")

    @staticmethod
    def _client_ip(request: Request) -> str | None:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",", maxsplit=1)[0].strip() or None
        if request.client:
            return request.client.host
        return None

    @staticmethod
    def _api_key_fingerprint(request: Request) -> str | None:
        api_key = request.headers.get(API_KEY_HEADER)
        if not api_key:
            return None
        digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
        return digest[:12]
