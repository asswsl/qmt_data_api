# 定义缓存后端协议。
"""Cache backend protocol."""

from __future__ import annotations

from typing import Any, Protocol


class CacheBackend(Protocol):
    def get(self, key: str) -> Any | None:
        ...

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        ...

    def clear(self) -> None:
        ...
