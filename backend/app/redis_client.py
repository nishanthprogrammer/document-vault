import uuid

import redis

from app.config import get_settings


_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(get_settings().redis_url, decode_responses=True)
    return _redis_client


def set_redis_client(client: redis.Redis) -> None:
    global _redis_client
    _redis_client = client


def reset_redis_client() -> None:
    global _redis_client
    _redis_client = None


def check_rate_limit(user_id: uuid.UUID) -> bool:
    """Return True if upload is allowed, False if rate limit exceeded."""
    settings = get_settings()
    client = get_redis()
    key = f"rate:upload:{user_id}"
    count = client.incr(key)
    if count == 1:
        client.expire(key, settings.upload_rate_window_seconds)
    return count <= settings.upload_rate_limit
