# 定义缓存 TTL 和刷新策略。
"""Cache TTL and refresh policies."""

from __future__ import annotations

from qmt_data_api.core.config import get_settings


def snapshot_ttl_seconds() -> int:
    return max(get_settings().market_snapshot_cache_ttl_seconds, 0)
