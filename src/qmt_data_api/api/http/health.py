# 提供健康检查和基础服务状态接口。
"""Health and readiness routes."""

from fastapi import APIRouter, Request

from qmt_data_api import __version__
from qmt_data_api.api.deps import get_app_settings
from qmt_data_api.core.response import success_response

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    settings = get_app_settings()
    return success_response(
        request,
        data={
            "service": "qmt-data-api",
            "version": __version__,
            "status": "ok",
            "environment": settings.app_env,
        },
    )
