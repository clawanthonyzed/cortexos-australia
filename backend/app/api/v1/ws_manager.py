"""WebSocket connection manager — broadcast to all authenticated clients."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import structlog
from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}  # client_id → socket
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[client_id] = websocket
        logger.info("WS client connected", client_id=client_id, total=len(self._connections))

    async def disconnect(self, client_id: str) -> None:
        async with self._lock:
            self._connections.pop(client_id, None)
        logger.info("WS client disconnected", client_id=client_id, total=len(self._connections))

    async def send(self, client_id: str, message: dict[str, Any]) -> None:
        async with self._lock:
            ws = self._connections.get(client_id)
        if ws:
            try:
                await ws.send_text(json.dumps(message))
            except Exception as exc:
                logger.warning("WS send failed", client_id=client_id, error=str(exc))
                await self.disconnect(client_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._connections.items())
        dead: list[str] = []
        payload = json.dumps(message)
        for cid, ws in targets:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(cid)
        for cid in dead:
            await self.disconnect(cid)

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Singleton used by both the WebSocket endpoint and background tasks
manager = ConnectionManager()
