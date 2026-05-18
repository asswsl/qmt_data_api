# 提供缓存状态 HTTP 查询接口。
"""Cache status HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from qmt_data_api.api.deps import get_app_settings
from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.cache.memory import get_runtime_cache
from qmt_data_api.core.response import success_response

router = APIRouter(prefix="/api/v1/cache", dependencies=[Depends(require_api_key)])


@router.get("/status")
def cache_status(request: Request) -> dict[str, object]:
    settings = get_app_settings()
    memory_status = get_runtime_cache().status().to_dict()
    return success_response(
        request,
        data={
            "status": "ok",
            "enabled": True,
            "cache_dir": settings.cache_dir,
            "layers": [
                {
                    "name": "runtime",
                    **memory_status,
                }
            ],
            "capabilities": [
                "memory_ttl_status",
                "hit_miss_statistics",
            ],
            "notes": [
                "当前接口提供进程内缓存状态；文件缓存覆盖范围和预热任务状态将在后续功能接入。",
            ],
        },
    )
