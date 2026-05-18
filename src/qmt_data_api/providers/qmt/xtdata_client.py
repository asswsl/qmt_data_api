# 探测 xtdata 与 MiniQMT 连接状态。
"""QMT xtdata status helpers."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from qmt_data_api.core.errors import ErrorCode, QmtError


def _safe_call(target: object, method_name: str) -> Any | None:
    method = getattr(target, method_name, None)
    if not callable(method):
        return None
    try:
        return method()
    except Exception:
        return None


def probe_xtdata_status() -> dict[str, Any]:
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
        client = xtdata.get_client()
    except Exception as exc:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_UNAVAILABLE,
            message="xtdata 客户端不可用",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail={"error": str(exc)},
            retryable=True,
        ) from exc

    if client is None:
        raise QmtError(
            code=ErrorCode.QMT_XTDATA_UNAVAILABLE,
            message="未获取到 xtdata 客户端",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            retryable=True,
        )

    connected = bool(_safe_call(client, "is_connected"))
    peer_addr = _safe_call(client, "get_peer_addr")
    data_dir = _safe_call(client, "get_data_dir")

    quote_server_status = None
    quote_server_status_error = None
    quote_server_fn = getattr(xtdata, "get_quote_server_status", None)
    if callable(quote_server_fn):
        try:
            quote_server_status = quote_server_fn()
        except Exception as exc:  # pragma: no cover - depends on local client capability
            quote_server_status_error = str(exc)

    return {
        "status": "ok" if connected else "disconnected",
        "xtdata_imported": True,
        "qmt_running": connected,
        "connected": connected,
        "peer_addr": peer_addr,
        "data_dir": data_dir,
        "quote_server_status": quote_server_status,
        "quote_server_status_error": quote_server_status_error,
    }
