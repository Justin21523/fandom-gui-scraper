# api/websocket/__init__.py
"""
WebSocket support for real-time updates.
"""

from api.websocket.manager import ConnectionManager, manager

__all__ = ["ConnectionManager", "manager"]
