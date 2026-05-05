"""
Redis client setup for caching and rate limiting.
"""

import redis.asyncio as redis

from app.config import get_settings

settings = get_settings()

redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis() -> redis.Redis:
    """Dependency that yields a Redis client."""
    return redis_client


async def close_redis():
    """Close the Redis connection."""
    await redis_client.close()
