# 聚合 QMT Data API 顶层路由。
"""Top-level API router."""

from fastapi import APIRouter

from qmt_data_api.api.http.cache import router as cache_router
from qmt_data_api.api.http.calendar import router as calendar_router
from qmt_data_api.api.http.health import router as health_router
from qmt_data_api.api.http.instruments import router as instruments_router
from qmt_data_api.api.http.market import router as market_router
from qmt_data_api.api.http.system import router as system_router

api_router = APIRouter()
api_router.include_router(cache_router, tags=["cache"])
api_router.include_router(calendar_router, tags=["calendar"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(instruments_router, tags=["instruments"])
api_router.include_router(market_router, tags=["market"])
api_router.include_router(system_router, tags=["system"])
