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


def invalid_period_error(period: str) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.INVALID_PERIOD,
        message="K 线周期不支持",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"period": period},
        retryable=False,
    )


def invalid_adjust_error(adjust: str) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.INVALID_ADJUST,
        message="复权类型不支持",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"adjust": adjust},
        retryable=False,
    )


def invalid_time_range_error(start: str, end: str) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.INVALID_TIME_RANGE,
        message="时间范围错误",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"start": start, "end": end},
        retryable=False,
    )


def unsupported_source_error(source: str) -> MarketDataError:
    return MarketDataError(
        code=ErrorCode.UNSUPPORTED_SOURCE,
        message="数据来源暂不支持",
        status_code=HTTPStatus.BAD_REQUEST,
        detail={"source": source},
        retryable=False,
    )
