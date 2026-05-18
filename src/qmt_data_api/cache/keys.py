# 生成缓存键命名规则。
"""Cache key conventions."""

from __future__ import annotations


def snapshot_key(symbol: str) -> str:
    return f"market:snapshot:{symbol}"
