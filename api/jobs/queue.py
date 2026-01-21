import os

try:
    from redis import Redis  # type: ignore
    from rq import Queue  # type: ignore
    REDIS_AVAILABLE = True
except Exception:  # pragma: no cover
    Redis = None  # type: ignore
    Queue = None  # type: ignore
    REDIS_AVAILABLE = False


def get_redis_raw() -> Redis:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not installed")
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    # RQ stores pickled payloads in Redis; decode_responses must be False.
    return Redis.from_url(url, decode_responses=False)  # type: ignore


def get_redis_text() -> Redis:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not installed")
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return Redis.from_url(url, decode_responses=True)  # type: ignore


def get_queue(name: str = "fandom") -> Queue:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not installed")
    return Queue(name, connection=get_redis_raw(), default_timeout=60 * 60 * 12)  # type: ignore # 12h
