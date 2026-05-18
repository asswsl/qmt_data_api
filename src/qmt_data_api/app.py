# 创建并配置 FastAPI 应用实例。
"""FastAPI application factory."""

from fastapi import FastAPI

from qmt_data_api.api.router import api_router
from qmt_data_api.core.constants import APP_NAME, APP_VERSION
from qmt_data_api.middleware.error_handler import register_exception_handlers
from qmt_data_api.middleware.request_id import RequestIdMiddleware


def create_app() -> FastAPI:
    app = FastAPI(title=APP_NAME, version=APP_VERSION)
    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router)
    return app
