# 提供缓存状态 HTTP 接口。
"""Cache status HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from qmt_data_api.auth.api_key import require_api_key
from qmt_data_api.cache.memory import snapshot_cache
from qmt_data_api.cache.policies import snapshot_ttl_seconds
from qmt_data_api.core.response import success_response

router = APIRouter(prefix="/api/v1/cache", dependencies=[Depends(require_api_key)])


@router.get("/status")
def cache_status(request: Request) -> dict[str, object]:
    stats = snapshot_cache.stats()
    return success_response(
        request,
        data={
            "market_snapshot": {
                "backend": "memory",
                "ttl_seconds": snapshot_ttl_seconds(),
                "size": stats.size,
                "hits": stats.hits,
                "misses": stats.misses,
                "sets": stats.sets,
                "evictions": stats.evictions,
            }
        },
    )
