# 提供健康检查和服务状态接口。
"""Health and readiness routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/api/v1/health")
def health() -> dict[str, object]:
    return {
        "success": True,
        "code": "OK",
        "message": "success",
        "data": {
            "service": "qmt-data-api",
            "version": "0.1.0",
            "status": "ok",
        },
    }
