# api/websocket/manager.py
"""
WebSocket connection manager for real-time updates.

This module provides a connection manager for handling multiple WebSocket
connections and broadcasting messages to connected clients.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a WebSocket connection."""

    websocket: WebSocket
    client_id: str
    connected_at: datetime = field(default_factory=datetime.utcnow)
    subscriptions: List[str] = field(default_factory=list)


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting.

    Supports:
    - Multiple concurrent connections
    - Channel-based subscriptions
    - Broadcast to all or specific clients
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, Connection] = {}
        self._connection_counter = 0

    def _generate_client_id(self) -> str:
        """Generate a unique client ID."""
        self._connection_counter += 1
        return f"client_{self._connection_counter}"

    async def connect(
        self,
        websocket: WebSocket,
        client_id: Optional[str] = None,
    ) -> str:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection
            client_id: Optional custom client ID

        Returns:
            The client ID for this connection
        """
        await websocket.accept()

        if client_id is None:
            client_id = self._generate_client_id()

        connection = Connection(
            websocket=websocket,
            client_id=client_id,
        )
        self.active_connections[client_id] = connection

        logger.info(f"WebSocket client connected: {client_id}")
        return client_id

    def disconnect(self, client_id: str):
        """
        Remove a WebSocket connection.

        Args:
            client_id: The client ID to disconnect
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket client disconnected: {client_id}")

    def subscribe(self, client_id: str, channel: str):
        """
        Subscribe a client to a channel.

        Args:
            client_id: The client ID
            channel: The channel to subscribe to
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            if channel not in connection.subscriptions:
                connection.subscriptions.append(channel)
                logger.debug(f"Client {client_id} subscribed to {channel}")

    def unsubscribe(self, client_id: str, channel: str):
        """
        Unsubscribe a client from a channel.

        Args:
            client_id: The client ID
            channel: The channel to unsubscribe from
        """
        if client_id in self.active_connections:
            connection = self.active_connections[client_id]
            if channel in connection.subscriptions:
                connection.subscriptions.remove(channel)
                logger.debug(f"Client {client_id} unsubscribed from {channel}")

    async def send_personal_message(self, message: Dict[str, Any], client_id: str):
        """
        Send a message to a specific client.

        Args:
            message: The message to send
            client_id: The target client ID
        """
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id].websocket
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message to broadcast
        """
        disconnected = []

        for client_id, connection in self.active_connections.items():
            try:
                await connection.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """
        Broadcast a message to all clients subscribed to a channel.

        Args:
            channel: The channel name
            message: The message to broadcast
        """
        disconnected = []

        for client_id, connection in self.active_connections.items():
            if channel in connection.subscriptions:
                try:
                    await connection.websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to {client_id} on {channel}: {e}")
                    disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)

    def get_connection_info(self) -> List[Dict[str, Any]]:
        """Get information about all active connections."""
        return [
            {
                "client_id": conn.client_id,
                "connected_at": conn.connected_at.isoformat(),
                "subscriptions": conn.subscriptions,
            }
            for conn in self.active_connections.values()
        ]


# Global connection manager instance
manager = ConnectionManager()
