# 提供缓存状态 HTTP 查询接口。
"""Cache status HTTP routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request

from qmt_data_api.api.deps import get_app_settings
from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.cache.file_cache import get_kline_file_cache
from qmt_data_api.cache.memory import get_runtime_cache, get_snapshot_cache
from qmt_data_api.core.response import success_response
from qmt_data_api.tasks.warmup_cache import (
    KlineWarmupRequest,
    get_last_kline_warmup_result,
    run_kline_cache_warmup,
)

router = APIRouter(prefix="/api/v1/cache", dependencies=[Depends(require_api_key)])


def _cache_dir_status(cache_dir: str) -> dict[str, object]:
    path = Path(cache_dir)
    parent = path.parent
    return {
        "path": cache_dir,
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "parent_exists": parent.exists(),
        "ready_for_file_cache": path.exists() and path.is_dir(),
    }


@router.get("/status")
def cache_status(request: Request) -> dict[str, object]:
    settings = get_app_settings()
    memory_status = get_runtime_cache().status().to_dict()
    snapshot_status = get_snapshot_cache().status().to_dict()
    kline_status = get_kline_file_cache().status().to_dict()
    return success_response(
        request,
        data={
            "status": "ok",
            "enabled": True,
            "cache_dir": settings.cache_dir,
            "cache_dir_status": _cache_dir_status(settings.cache_dir),
            "layers": [
                {
                    "name": "runtime",
                    **memory_status,
                },
                {
                    "name": "market_snapshot",
                    **snapshot_status,
                },
                {
                    "name": "kline_file",
                    **kline_status,
                }
            ],
            "capabilities": [
                "memory_ttl_status",
                "hit_miss_statistics",
                "snapshot_cache_status",
                "kline_file_cache_status",
                "kline_cache_warmup",
            ],
            "notes": [
                "当前接口提供进程内缓存、快照缓存和历史 K 线文件缓存状态。",
            ],
        },
    )


@router.delete("/kline")
def clear_kline_cache(request: Request) -> dict[str, object]:
    kline_cache = get_kline_file_cache()
    removed_count = kline_cache.clear()
    return success_response(
        request,
        data={
            "removed_count": removed_count,
            "layer": {
                "name": "kline_file",
                **kline_cache.status().to_dict(),
            },
        },
    )


@router.post("/warmup/kline")
def warmup_kline_cache(request: Request, payload: KlineWarmupRequest) -> dict[str, object]:
    result = run_kline_cache_warmup(payload)
    return success_response(request, data=result.model_dump(mode="json"))


@router.get("/warmup/kline/status")
def kline_warmup_status(request: Request) -> dict[str, object]:
    result = get_last_kline_warmup_result()
    return success_response(
        request,
        data={
            "status": "not_started" if result is None else result.status,
            "last_result": None if result is None else result.model_dump(mode="json"),
        },
    )
