# 实现进程内 TTL 缓存。
"""In-memory cache implementation."""

from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any


@dataclass(slots=True)
class CacheEntry:
    value: Any
    expires_at: float


@dataclass(frozen=True, slots=True)
class CacheStats:
    name: str
    size: int
    hits: int
    misses: int
    sets: int
    evictions: int


class MemoryTTLCache:
    def __init__(self, name: str) -> None:
        self.name = name
        self._items: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._evictions = 0

    def get(self, key: str) -> Any | None:
        entry = self._items.get(key)
        if entry is None:
            self._misses += 1
            return None
        if entry.expires_at <= monotonic():
            self._items.pop(key, None)
            self._misses += 1
            self._evictions += 1
            return None
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        self._items[key] = CacheEntry(value=value, expires_at=monotonic() + ttl_seconds)
        self._sets += 1

    def clear(self) -> None:
        self._items.clear()

    def stats(self) -> CacheStats:
        self._purge_expired()
        return CacheStats(
            name=self.name,
            size=len(self._items),
            hits=self._hits,
            misses=self._misses,
            sets=self._sets,
            evictions=self._evictions,
        )

    def _purge_expired(self) -> None:
        now = monotonic()
        expired_keys = [key for key, entry in self._items.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._items.pop(key, None)
            self._evictions += 1


snapshot_cache = MemoryTTLCache("market_snapshot")
