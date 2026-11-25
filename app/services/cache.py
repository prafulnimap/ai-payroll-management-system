import hashlib
import json
import logging
import threading
import time
from datetime import date

from app.config import settings

logger = logging.getLogger(__name__)


def make_key(user_id: int, question: str) -> str:
    # Normalize so "What is my salary?" and "what is my  salary?" share one entry.
    normalized = " ".join(question.lower().split())
    # Today's date is included because "last month" means different things on different days.
    digest = hashlib.sha256(f"{date.today()}|{normalized}".encode()).hexdigest()[:32]
    return f"chat:{user_id}:{digest}"


class MemoryCache:
    """Simple dictionary cache with expiry. Lives inside the Python process."""

    def __init__(self):
        self._data: dict[str, tuple[float, dict]] = (
            {}
        )  # This is an empty dictionary when the application starts ,its structure is this :{"cache_key": (expiration_timestamp, cached_response)}
        self._lock = (
            threading.Lock()
        )  # FastAPI runs endpoints in multiple threads this lock ensures that only one thread can access the cache at a time, preventing race conditions.

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if not item:
                return None
            expires_at, value = item
            if expires_at < time.time():
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: dict, ttl: int):
        with self._lock:
            self._data[key] = (time.time() + ttl, value)

    def delete_prefix(self, prefix: str):
        with self._lock:
            for k in [k for k in self._data if k.startswith(prefix)]:
                del self._data[k]


class RedisCache:
    def __init__(self, url: str):
        import redis

        self.client = redis.Redis.from_url(url, decode_responses=True, socket_timeout=2)
        self.client.ping()  # fails immediately if Redis isn't running

    def get(self, key: str):
        raw = self.client.get(key)
        return json.loads(raw) if raw else None

    def set(self, key: str, value: dict, ttl: int):
        self.client.set(key, json.dumps(value), ex=ttl)

    def delete_prefix(self, prefix: str):
        for k in self.client.scan_iter(match=f"{prefix}*"):
            self.client.delete(k)


def _build_backend():
    if settings.REDIS_URL:
        try:
            backend = RedisCache(settings.REDIS_URL)
            logger.info("Cache backend: Redis")
            return backend
        except Exception as e:
            logger.warning(
                "Redis unavailable (%s). Falling back to in-memory cache.", e
            )
    logger.info("Cache backend: in-memory")
    return MemoryCache()


_cache = _build_backend()


# ---------- public functions used by the rest of the app ----------


def get_cached(user_id: int, question: str):
    try:
        return _cache.get(make_key(user_id, question))
    except Exception:
        logger.exception("Cache read failed")
        return None  # a broken cache must never break the app


def set_cached(user_id: int, question: str, value: dict):
    try:
        _cache.set(make_key(user_id, question), value, settings.CACHE_TTL_SECONDS)
    except Exception:
        logger.exception("Cache write failed")


def invalidate_user(user_id: int):
    """Called when a user's payslip changes."""
    try:
        _cache.delete_prefix(f"chat:{user_id}:")
    except Exception:
        logger.exception("Cache invalidation failed")


def clear_all():
    """Called when a policy changes, because policy answers are shared by everyone."""
    try:
        _cache.delete_prefix("chat:")
    except Exception:
        logger.exception("Cache clear failed")
