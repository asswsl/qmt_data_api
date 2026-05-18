# 聚合 QMT Data API 顶层路由。
"""Top-level API router."""

from fastapi import APIRouter

from qmt_data_api.api.http.health import router as health_router
from qmt_data_api.api.http.system import router as system_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(system_router, tags=["system"])
