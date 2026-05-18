# 定义缓存后端协议和状态快照结构。
"""Cache backend protocols and status models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class CacheStatus:
    backend: str
    enabled: bool
    item_count: int
    hit_count: int
    miss_count: int
    evicted_count: int
    expired_count: int
    max_ttl_seconds: int | None
    oldest_item_age_seconds: float | None
    newest_item_age_seconds: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CacheBackend(Protocol):
    def status(self) -> CacheStatus:
        raise NotImplementedError
