# 提供带 TTL 和统计信息的进程内缓存。
"""In-memory cache implementation."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
import time
from typing import Any

from qmt_data_api.cache.base import CacheStatus


@dataclass(slots=True)
class _CacheEntry:
    value: Any
    created_at: float
    expires_at: float | None


class InMemoryCache:
    def __init__(self, *, backend: str = "memory") -> None:
        self._backend = backend
        self._items: dict[str, _CacheEntry] = {}
        self._lock = RLock()
        self._hit_count = 0
        self._miss_count = 0
        self._evicted_count = 0
        self._expired_count = 0
        self._max_ttl_seconds: int | None = None

    def get(self, key: str) -> Any | None:
        now = time.time()
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                self._miss_count += 1
                return None
            if self._is_expired(entry, now):
                self._items.pop(key, None)
                self._miss_count += 1
                self._expired_count += 1
                return None
            self._hit_count += 1
            return entry.value

    def set(self, key: str, value: Any, *, ttl_seconds: int | None = None) -> None:
        now = time.time()
        expires_at = now + ttl_seconds if ttl_seconds is not None else None
        with self._lock:
            self._items[key] = _CacheEntry(value=value, created_at=now, expires_at=expires_at)
            if ttl_seconds is not None:
                self._max_ttl_seconds = max(self._max_ttl_seconds or 0, ttl_seconds)

    def delete(self, key: str) -> bool:
        with self._lock:
            removed = self._items.pop(key, None) is not None
            if removed:
                self._evicted_count += 1
            return removed

    def clear(self) -> None:
        with self._lock:
            self._evicted_count += len(self._items)
            self._items.clear()

    def status(self) -> CacheStatus:
        now = time.time()
        with self._lock:
            self._purge_expired(now)
            ages = [now - entry.created_at for entry in self._items.values()]
            return CacheStatus(
                backend=self._backend,
                enabled=True,
                item_count=len(self._items),
                hit_count=self._hit_count,
                miss_count=self._miss_count,
                evicted_count=self._evicted_count,
                expired_count=self._expired_count,
                max_ttl_seconds=self._max_ttl_seconds,
                oldest_item_age_seconds=round(max(ages), 3) if ages else None,
                newest_item_age_seconds=round(min(ages), 3) if ages else None,
            )

    @staticmethod
    def _is_expired(entry: _CacheEntry, now: float) -> bool:
        return entry.expires_at is not None and entry.expires_at <= now

    def _purge_expired(self, now: float) -> None:
        expired_keys = [
            key for key, entry in self._items.items() if self._is_expired(entry, now)
        ]
        for key in expired_keys:
            self._items.pop(key, None)
        self._expired_count += len(expired_keys)


runtime_cache = InMemoryCache()
snapshot_cache = InMemoryCache()


def get_runtime_cache() -> InMemoryCache:
    return runtime_cache


def get_snapshot_cache() -> InMemoryCache:
    return snapshot_cache
