# api/endpoints/ws.py
"""
WebSocket endpoints for real-time updates.

This module provides WebSocket endpoints for receiving real-time
notifications about data changes and scraping progress.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for receiving real-time updates.

    Clients can subscribe to channels:
    - "characters": Character data changes
    - "scraping": Scraping progress updates
    - "system": System notifications

    Message format for subscriptions:
    {"action": "subscribe", "channel": "characters"}
    {"action": "unsubscribe", "channel": "characters"}
    """
    client_id = await manager.connect(websocket)

    try:
        # Send welcome message
        await manager.send_personal_message(
            {
                "type": "connected",
                "client_id": client_id,
                "message": "Connected to updates WebSocket",
                "available_channels": ["characters", "scraping", "system"],
            },
            client_id,
        )
        # Frontend currently doesn't actively subscribe; default to scraping updates.
        manager.subscribe(client_id, "scraping")

        # Handle incoming messages
        while True:
            data = await websocket.receive_json()
            await handle_client_message(client_id, data)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info(f"Client {client_id} disconnected")


async def handle_client_message(client_id: str, data: Dict[str, Any]):
    """
    Handle incoming messages from WebSocket clients.

    Args:
        client_id: The client ID
        data: The message data
    """
    action = data.get("action") or data.get("type")
    channel = data.get("channel") or (data.get("data") or {}).get("channel")

    if action == "subscribe" and channel:
        manager.subscribe(client_id, channel)
        await manager.send_personal_message(
            {
                "type": "subscribed",
                "channel": channel,
                "message": f"Subscribed to {channel}",
            },
            client_id,
        )

    elif action == "unsubscribe" and channel:
        manager.unsubscribe(client_id, channel)
        await manager.send_personal_message(
            {
                "type": "unsubscribed",
                "channel": channel,
                "message": f"Unsubscribed from {channel}",
            },
            client_id,
        )

    elif action == "ping":
        await manager.send_personal_message(
            {"type": "pong"},
            client_id,
        )

    else:
        await manager.send_personal_message(
            {
                "type": "error",
                "message": f"Unknown action: {action}",
            },
            client_id,
        )


@router.get("/ws/status")
async def get_websocket_status():
    """
    Get WebSocket connection status.

    Returns information about active connections.
    """
    return {
        "active_connections": manager.get_connection_count(),
        "connections": manager.get_connection_info(),
    }
