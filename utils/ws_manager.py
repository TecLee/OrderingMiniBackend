"""Simple WebSocket manager for broadcasting order updates to kitchen boards."""
import asyncio
import json
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger("ws_manager")


class WSManager:
    """Manages WebSocket connections for real-time kitchen updates."""

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.add(ws)
        self._loop = asyncio.get_running_loop()
        logger.info(f"Kitchen WS connected (total: {len(self._connections)})")

    def disconnect(self, ws: WebSocket):
        self._connections.discard(ws)
        logger.info(f"Kitchen WS disconnected (total: {len(self._connections)})")

    async def broadcast(self, event: str, data: dict):
        """Push an event to all connected kitchen boards."""
        if not self._connections:
            return
        message = json.dumps({"event": event, "data": data})
        dead: Set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        self._connections -= dead

    def notify(self, event: str, data: dict):
        """Thread-safe: schedule broadcast from sync code."""
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(event, data), self._loop
            )

    @property
    def active_count(self) -> int:
        return len(self._connections)


# Singleton
kitchen_ws = WSManager()
