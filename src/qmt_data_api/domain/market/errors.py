# 定义行情领域错误。
"""Market domain errors."""

from __future__ import annotations

from http import HTTPStatus

from qmt_data_api.core.errors import ErrorCode, MarketDataError


def invalid_symbol_error(symbols: list[str]) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.INVALID_SYMBOL,
        message="证券代码格式错误",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"symbols": symbols},
        retryable=False,
    )


def too_many_symbols_error(count: int, limit: int) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.TOO_MANY_SYMBOLS,
        message="单次请求证券代码数量超过限制",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"count": count, "limit": limit},
        retryable=False,
    )
