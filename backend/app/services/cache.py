import json
import logging
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.core.config import settings

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.client = None
        if settings.ENABLE_REDIS_CACHE and settings.REDIS_URL.startswith("rediss://"):
            try:
                self.client = Redis.from_url(settings.REDIS_URL, decode_responses=True,
                    socket_connect_timeout=2, socket_timeout=2, ssl_cert_reqs="required")
            except (ValueError, RedisError):
                logger.warning("Redis configuration invalid; cache disabled")
        elif settings.ENABLE_REDIS_CACHE:
            logger.warning("Redis cache requires a rediss:// URL")

    async def get(self, key):
        if self.client is None:
            return None, "BYPASS"
        try:
            value = await self.client.get(key)
            return (json.loads(value), "HIT") if value is not None else (None, "MISS")
        except (RedisError, ValueError, OSError):
            logger.warning("Redis read failed; using PostgreSQL")
            return None, "BYPASS"

    async def set(self, key, value):
        if self.client is None:
            return
        try:
            await self.client.set(key, json.dumps(value), ex=max(1, settings.REDIS_CACHE_TTL_SECONDS))
        except (RedisError, ValueError, OSError):
            logger.warning("Redis write failed; continuing without cache")

    async def close(self):
        if self.client is not None:
            await self.client.aclose()
