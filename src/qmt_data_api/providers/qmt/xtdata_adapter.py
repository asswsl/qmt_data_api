# 封装 xtdata 行情快照读取。
"""Application-level xtdata adapter."""

from __future__ import annotations

from http import HTTPStatus

from qmt_data_api.core.errors import ErrorCode, QmtError
from qmt_data_api.domain.market.schemas import SnapshotItem
from qmt_data_api.providers.qmt.xtdata_mappers import map_xtdata_snapshot


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
