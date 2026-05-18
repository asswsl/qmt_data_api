# 校验请求头中的 API Key。
"""API key authentication dependency."""

from __future__ import annotations

from http import HTTPStatus

from fastapi import Request

from qmt_data_api.core.config import get_settings
from qmt_data_api.core.constants import API_KEY_HEADER
from qmt_data_api.core.errors import AuthError, ErrorCode


async def require_api_key(request: Request) -> str | None:
    settings = get_settings()
    if not settings.api_key_enabled:
        return None

    api_key = request.headers.get(API_KEY_HEADER)
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

    request.state.api_key = api_key
    return api_key
