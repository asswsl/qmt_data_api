# 管理 WebSocket 活跃连接集合。
"""WebSocket connection registry."""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import WebSocket


@dataclass(slots=True)
class WebSocketConnectionManager:
    active_connections: set[WebSocket] = field(default_factory=set)

    def connect(self, websocket: WebSocket) -> None:
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    @property
    def active_count(self) -> int:
        return len(self.active_connections)


connection_manager = WebSocketConnectionManager()
