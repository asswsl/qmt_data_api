# 提供系统和 QMT 状态接口。
"""System status HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from qmt_data_api import __version__
from qmt_data_api.api.deps import get_app_settings
from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.core.errors import AppError
from qmt_data_api.core.response import success_response
from qmt_data_api.providers.qmt.xtdata_client import probe_xtdata_status

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])


@router.get("/status")
def service_status(request: Request) -> dict[str, object]:
    settings = get_app_settings()
    try:
        qmt_status = probe_xtdata_status()
        service_status_value = "ok" if qmt_status["connected"] else "degraded"
    except AppError as exc:
        qmt_status = {
            "status": "error",
            "code": exc.code,
            "message": exc.message,
            "retryable": exc.retryable,
        }
        service_status_value = "degraded"

    return success_response(
        request,
        data={
            "service": "qmt-data-api",
            "version": __version__,
            "environment": settings.app_env,
            "status": service_status_value,
            "qmt": qmt_status,
        },
    )


@router.get("/status/qmt")
def qmt_status(request: Request) -> dict[str, object]:
    return success_response(request, data=probe_xtdata_status())
