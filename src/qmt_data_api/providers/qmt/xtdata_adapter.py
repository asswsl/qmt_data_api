# 封装 xtdata 行情快照读取。
"""Application-level xtdata adapter."""

from __future__ import annotations

from http import HTTPStatus

from qmt_data_api.core.errors import ErrorCode, QmtError
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
