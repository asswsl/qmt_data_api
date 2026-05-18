# 注册统一异常处理逻辑。
"""Global exception handlers."""

from __future__ import annotations

from http import HTTPStatus
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError

from qmt_data_api.core.errors import AppError, ErrorCode
from qmt_data_api.core.response import error_response

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return error_response(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        error = AppError(
            code=ErrorCode.REQ_INVALID_PARAMS,
            message="请求参数错误",
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail={"errors": exc.errors()},
        )
        return error_response(request, error)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        error = AppError(
            code=ErrorCode.SYS_INTERNAL_ERROR,
            message="服务内部错误",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            retryable=False,
        )
        return error_response(request, error)
