# 验证进程内缓存的 TTL 与状态统计行为。
from __future__ import annotations

from qmt_data_api.cache.memory import InMemoryCache


def test_memory_cache_tracks_hit_and_miss() -> None:
    cache = InMemoryCache()
    cache.set("snapshot:600519.SH", {"last_price": 1688.88}, ttl_seconds=10)

    assert cache.get("snapshot:600519.SH") == {"last_price": 1688.88}
    assert cache.get("snapshot:000001.SZ") is None

    status = cache.status()
    assert status.item_count == 1
    assert status.hit_count == 1
    assert status.miss_count == 1
    assert status.max_ttl_seconds == 10
    assert status.oldest_item_age_seconds is not None


def test_memory_cache_expires_items() -> None:
    cache = InMemoryCache()
    cache.set("short", "value", ttl_seconds=0)

    assert cache.get("short") is None

    status = cache.status()
    assert status.item_count == 0
    assert status.miss_count == 1
    assert status.expired_count == 1
