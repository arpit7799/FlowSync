"""WebSocket connection manager for real-time dashboard streaming."""

import json
import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("flowsync.websocket")


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts live updates."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket client connected. Active: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Active: %d", len(self.active_connections))

    async def broadcast(self, message: dict):
        """Broadcast JSON message to all active clients."""
        if not self.active_connections:
            return

        payload = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as exc:
                logger.error("Error sending WebSocket message: %s", exc)
                self.disconnect(connection)


ws_manager = ConnectionManager()
