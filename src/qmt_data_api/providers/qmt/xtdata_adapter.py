# 封装 xtdata 行情快照读取。
"""Application-level xtdata adapter."""

from __future__ import annotations

from http import HTTPStatus

from qmt_data_api.core.errors import ErrorCode, QmtError
from qmt_data_api.domain.instrument.schemas import InstrumentInfo
from qmt_data_api.domain.market.schemas import KlineBar, SnapshotItem
from qmt_data_api.providers.qmt.xtdata_mappers import map_xtdata_kline_row, map_xtdata_snapshot


def fetch_xtdata_snapshots(symbols: list[str]) -> tuple[list[SnapshotItem], list[str]]:
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_IMPORT_FAILED,
            message="无法导入 xtquant.xtdata",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=False,
        ) from exc

    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False

    try:
        raw_snapshots = xtdata.get_full_tick(symbols)
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_MARKET_DATA_UNAVAILABLE,
            message="无法获取行情快照",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=True,
        ) from exc

    items: list[SnapshotItem] = []
    missing: list[str] = []
    for symbol in symbols:
        raw = raw_snapshots.get(symbol) if isinstance(raw_snapshots, dict) else None
        if not isinstance(raw, dict) or not raw:
            missing.append(symbol)
            continue
        items.append(map_xtdata_snapshot(symbol, raw))
    return items, missing


def fetch_xtdata_klines(
    symbol: str,
    period: str,
    start_time: str,
    end_time: str,
    adjust: str,
    limit: int | None,
) -> list[KlineBar]:
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_IMPORT_FAILED,
            message="无法导入 xtquant.xtdata",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=False,
        ) from exc

    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False

    try:
        raw_data = xtdata.get_market_data_ex(
            [],
            [symbol],
            period=period,
            start_time=start_time,
            end_time=end_time,
            count=limit or -1,
            dividend_type=adjust,
            fill_data=True,
        )
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_MARKET_DATA_UNAVAILABLE,
            message="无法获取历史 K 线",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=True,
        ) from exc

    frame = raw_data.get(symbol) if isinstance(raw_data, dict) else None
    if frame is None or not hasattr(frame, "iterrows"):
        return []
    return [map_xtdata_kline_row(index_value, row) for index_value, row in frame.iterrows()]


def fetch_xtdata_instruments(symbols: list[str]) -> tuple[list[InstrumentInfo], list[str]]:
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_IMPORT_FAILED,
            message="无法导入 xtquant.xtdata",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=False,
        ) from exc

    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False

    items: list[InstrumentInfo] = []
    missing: list[str] = []
    for symbol in symbols:
        try:
            raw = xtdata.get_instrument_detail(symbol)
        except Exception as exc:
            raise QmtError(
                code=ErrorCode.QMT_MARKET_DATA_UNAVAILABLE,
                message="无法获取证券基础信息",
                status_code=HTTPStatus.SERVICE_UNAVAILABLE,
                detail={"error": str(exc), "symbol": symbol},
                retryable=True,
            ) from exc
        if not isinstance(raw, dict) or not raw:
            missing.append(symbol)
            continue
        items.append(
            InstrumentInfo(
                symbol=symbol,
                name=raw.get("InstrumentName") or raw.get("name"),
                market=raw.get("ExchangeID") or symbol.split(".")[-1],
                instrument_type=raw.get("ProductID") or raw.get("instrument_type"),
                status=raw.get("InstrumentStatus") or raw.get("status"),
                listed_date=str(raw.get("OpenDate") or raw.get("listed_date") or "") or None,
                delisted_date=str(raw.get("ExpireDate") or raw.get("delisted_date") or "") or None,
                raw=raw,
            )
        )
    return items, missing


def fetch_xtdata_trading_days(market: str, start_time: str, end_time: str) -> list[str]:
    try:
        from xtquant import xtdata  # type: ignore
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_IMPORT_FAILED,
            message="无法导入 xtquant.xtdata",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=False,
        ) from exc

    if hasattr(xtdata, "enable_hello"):
        xtdata.enable_hello = False

    if not hasattr(xtdata, "get_trading_dates"):
        return []
    try:
        raw_days = xtdata.get_trading_dates(market, start_time, end_time)
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_MARKET_DATA_UNAVAILABLE,
            message="无法获取交易日历",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc), "market": market},
            retryable=True,
        ) from exc

    days: list[str] = []
    for item in raw_days or []:
        raw = str(item)
        if len(raw) >= 8:
            value = raw[:8]
            days.append(f"{value[:4]}-{value[4:6]}-{value[6:8]}")
    return days
