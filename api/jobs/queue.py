import os

try:
    from redis import Redis  # type: ignore
    from rq import Queue  # type: ignore
    REDIS_IMPORTS_AVAILABLE = True
except Exception:  # pragma: no cover
    Redis = None  # type: ignore
    Queue = None  # type: ignore
    REDIS_IMPORTS_AVAILABLE = False


def _redis_url() -> str:
    return os.getenv("REDIS_URL", "redis://localhost:6379/0")


def job_queue_enabled() -> bool:
    return os.getenv("FANDOM_ENABLE_JOB_QUEUE", "").lower() in {"1", "true", "yes", "on"}


def _redis_is_reachable() -> bool:
    if not job_queue_enabled() or not REDIS_IMPORTS_AVAILABLE:
        return False
    try:
        client = Redis.from_url(  # type: ignore
            _redis_url(),
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            decode_responses=True,
        )
        return bool(client.ping())
    except Exception:
        return False


REDIS_AVAILABLE = _redis_is_reachable()


def get_redis_raw() -> Redis:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not available")
    # RQ stores pickled payloads in Redis; decode_responses must be False.
    return Redis.from_url(_redis_url(), decode_responses=False)  # type: ignore


def get_redis_text() -> Redis:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not available")
    return Redis.from_url(_redis_url(), decode_responses=True)  # type: ignore


def get_queue(name: str = "fandom") -> Queue:
    if not REDIS_AVAILABLE:
        raise RuntimeError("Redis/RQ not installed")
    return Queue(name, connection=get_redis_raw(), default_timeout=60 * 60 * 12)  # type: ignore # 12h
