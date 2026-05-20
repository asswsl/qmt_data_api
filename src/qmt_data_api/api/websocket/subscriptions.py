# 管理 WebSocket 行情订阅参数。
"""WebSocket subscription management."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SnapshotSubscription:
    symbols: list[str]
    fields: list[str] | None
    source: str
    interval_seconds: float


def split_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def build_snapshot_subscription(
    symbols: str,
    fields: str | None,
    source: str,
    interval_seconds: float,
) -> SnapshotSubscription:
    return SnapshotSubscription(
        symbols=split_csv(symbols) or [],
        fields=split_csv(fields),
        source=source,
        interval_seconds=max(interval_seconds, 0.2),
    )
