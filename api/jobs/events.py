from __future__ import annotations

import json
from typing import Any, Dict

from api.jobs.queue import get_redis_raw


EVENT_CHANNEL = "fandom:events"


def publish(message: Dict[str, Any]) -> None:
    """
    Publish an event message for the API process to forward to WebSocket clients.

    Expected format: {"type": "...", "channel": "scraping", "data": {...}}
    """
    get_redis_raw().publish(EVENT_CHANNEL, json.dumps(message, ensure_ascii=False))
