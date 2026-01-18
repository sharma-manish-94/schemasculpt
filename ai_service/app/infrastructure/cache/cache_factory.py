"""
Cache Factory.

Creates ICacheRepository instances with Redis and in-memory fallback support.
"""

import logging
from datetime import timedelta
from typing import Optional

from app.domain.interfaces.cache_repository import ICacheRepository

from .in_memory_cache import InMemoryCacheRepository
from .redis_cache import RedisCacheRepository

logger = logging.getLogger(__name__)


async def create_cache_repository(
    redis_url: Optional[str] = None,
    default_ttl: timedelta = timedelta(hours=1),
    max_memory_size: int = 10000,
    fallback_to_memory: bool = True,
) -> ICacheRepository:
    """
    Create a cache repository instance.

    Attempts to create a Redis cache if redis_url is provided.
    Falls back to in-memory cache if Redis is unavailable or not configured.

    Args:
        redis_url: Redis connection URL (e.g., "redis://localhost:6379/0").
        default_ttl: Default time-to-live for cached values.
        max_memory_size: Maximum entries for in-memory cache.
        fallback_to_memory: If True, fall back to in-memory if Redis unavailable.

    Returns:
        ICacheRepository: A cache repository instance.

    Example:
        # With Redis
        cache = await create_cache_repository(
            redis_url="redis://localhost:6379/0",
            fallback_to_memory=True
        )

        # In-memory only
        cache = await create_cache_repository(default_ttl=timedelta(minutes=30))
    """
    # If no Redis URL, use in-memory
    if not redis_url:
        logger.info("No Redis URL provided, using in-memory cache")
        return InMemoryCacheRepository(
            default_ttl=default_ttl, max_size=max_memory_size
        )

    # Try Redis
    try:
        redis_cache = RedisCacheRepository(redis_url=redis_url, default_ttl=default_ttl)

        # Test connection
        is_healthy = await redis_cache.health_check()

        if is_healthy:
            logger.info(f"Connected to Redis at {redis_url}")
            return redis_cache
        else:
            logger.warning("Redis health check failed")
            await redis_cache.close()

            if fallback_to_memory:
                logger.info("Falling back to in-memory cache")
                return InMemoryCacheRepository(
                    default_ttl=default_ttl, max_size=max_memory_size
                )
            else:
                raise RuntimeError("Redis unavailable and fallback disabled")

    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")

        if fallback_to_memory:
            logger.info("Falling back to in-memory cache")
            return InMemoryCacheRepository(
                default_ttl=default_ttl, max_size=max_memory_size
            )
        else:
            raise
