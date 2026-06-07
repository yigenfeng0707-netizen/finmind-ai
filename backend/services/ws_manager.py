from fastapi import WebSocket
from typing import Dict, Set, List, Any
import json
import logging
import asyncio

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "general"):
        """Accept a WebSocket connection and add to channel."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        logger.info(f"WebSocket connected to channel: {channel}")

    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        """Remove a WebSocket connection from channel."""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        logger.info(f"WebSocket disconnected from channel: {channel}")

    async def broadcast(self, channel: str, message: Dict[str, Any]):
        """Broadcast a message to all connections in a channel."""
        if channel not in self.active_connections:
            return

        disconnected = set()
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)

        for conn in disconnected:
            self.active_connections[channel].discard(conn)

    async def send_personal(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    async def send_agent_progress(
        self, symbol: str, agent_name: str, status: str, result: Any = None
    ):
        """Send agent execution progress update."""
        channel = f"analysis:{symbol}"
        message = {
            "type": "agent_progress",
            "symbol": symbol,
            "agent": agent_name,
            "status": status,
            "result": result,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        await self.broadcast(channel, message)

    async def send_analysis_complete(self, symbol: str, result: Dict[str, Any]):
        """Send analysis completion notification."""
        channel = f"analysis:{symbol}"
        message = {
            "type": "analysis_complete",
            "symbol": symbol,
            "result": result,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
        await self.broadcast(channel, message)


# Singleton instance
ws_manager = ConnectionManager()
