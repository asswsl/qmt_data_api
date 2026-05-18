# 定义 FastAPI 常用依赖函数。
"""FastAPI dependency helpers."""

from __future__ import annotations

from fastapi import Request

from qmt_data_api.core.config import Settings, get_settings
from qmt_data_api.core.response import request_id_from


def get_app_settings() -> Settings:
    return get_settings()


def get_request_id(request: Request) -> str:
    return request_id_from(request)
