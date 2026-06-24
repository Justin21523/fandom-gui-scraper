from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional

try:
    import redis.asyncio as aioredis  # type: ignore
    REDIS_AVAILABLE = True
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore
    REDIS_AVAILABLE = False

from api.jobs.events import EVENT_CHANNEL
from api.jobs.queue import job_queue_enabled
from api.websocket.manager import manager

logger = logging.getLogger(__name__)


async def run_event_listener(stop_event: asyncio.Event) -> None:
    if not job_queue_enabled() or not REDIS_AVAILABLE:
        await stop_event.wait()
        return
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis = aioredis.from_url(url, decode_responses=True)
    pubsub = redis.pubsub()

    await pubsub.subscribe(EVENT_CHANNEL)
    logger.info(f"Subscribed to Redis channel: {EVENT_CHANNEL}")

    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if not message:
                continue

            raw = message.get("data")
            if not raw:
                continue

            try:
                payload = json.loads(raw)
            except Exception:
                continue

            channel = payload.get("channel") or "scraping"
            await manager.broadcast_to_channel(channel, payload)
    finally:
        try:
            await pubsub.unsubscribe(EVENT_CHANNEL)
            await pubsub.close()
        except Exception:
            pass
        try:
            await redis.close()
        except Exception:
            pass


def start_event_listener() -> tuple[asyncio.Event, asyncio.Task]:
    stop_event = asyncio.Event()
    task = asyncio.create_task(run_event_listener(stop_event))
    return stop_event, task
