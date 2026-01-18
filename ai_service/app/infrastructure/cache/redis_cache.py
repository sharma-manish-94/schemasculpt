"""
Redis Cache Repository.

Provides a Redis implementation of ICacheRepository.
This is the primary cache backend for production use.
"""

import json
import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.domain.interfaces.cache_repository import ICacheRepository

logger = logging.getLogger(__name__)


class RedisCacheRepository(ICacheRepository):
    """
    Redis implementation of ICacheRepository.

    Features:
    - Distributed caching across multiple instances
    - TTL-based expiration (handled by Redis)
    - Pattern-based key matching
    - JSON serialization for complex values

    Usage:
        cache = RedisCacheRepository(
            redis_url="redis://localhost:6379/0",
            default_ttl=timedelta(hours=1)
        )
        await cache.set("key", {"data": "value"})
        value = await cache.get("key")
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: timedelta = timedelta(hours=1),
        key_prefix: str = "schemasculpt:",
    ):
        """
        Initialize the Redis cache.

        Args:
            redis_url: Redis connection URL.
            default_ttl: Default time-to-live for cached values.
            key_prefix: Prefix for all cache keys.
        """
        self._redis_url = redis_url
        self._default_ttl = default_ttl
        self._key_prefix = key_prefix
        self._redis: Optional[Any] = None

    async def _get_redis(self):
        """Get or create Redis connection."""
        if self._redis is None:
            try:
                import redis.asyncio as redis

                self._redis = redis.from_url(
                    self._redis_url, encoding="utf-8", decode_responses=True
                )
            except ImportError:
                raise RuntimeError(
                    "redis package not installed. Install with: pip install redis"
                )
        return self._redis

    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self._key_prefix}{key}"

    def _serialize(self, value: Any) -> str:
        """Serialize value to JSON string."""
        return json.dumps(value)

    def _deserialize(self, data: str) -> Any:
        """Deserialize JSON string to value."""
        return json.loads(data)

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            data = await redis.get(full_key)

            if data is None:
                return None

            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Store a value in the cache."""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            data = self._serialize(value)
            actual_ttl = ttl or self._default_ttl

            await redis.setex(full_key, int(actual_ttl.total_seconds()), data)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            result = await redis.delete(full_key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        try:
            redis = await self._get_redis()
            full_key = self._make_key(key)
            return await redis.exists(full_key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries."""
        try:
            redis = await self._get_redis()

            if pattern is None:
                # Clear all keys with our prefix
                search_pattern = f"{self._key_prefix}*"
            else:
                search_pattern = self._make_key(pattern)

            # Use SCAN to find keys (safer than KEYS for large datasets)
            keys_deleted = 0
            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=search_pattern, count=100)
                if keys:
                    await redis.delete(*keys)
                    keys_deleted += len(keys)
                if cursor == 0:
                    break

            return keys_deleted if pattern else -1
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values from the cache."""
        try:
            redis = await self._get_redis()
            full_keys = [self._make_key(k) for k in keys]
            values = await redis.mget(full_keys)

            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Redis mget error: {e}")
            return {}

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Store multiple values in the cache."""
        try:
            redis = await self._get_redis()
            actual_ttl = ttl or self._default_ttl
            pipe = redis.pipeline()

            for key, value in items.items():
                full_key = self._make_key(key)
                data = self._serialize(value)
                pipe.setex(full_key, int(actual_ttl.total_seconds()), data)

            await pipe.execute()
        except Exception as e:
            logger.error(f"Redis mset error: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis = await self._get_redis()
            info = await redis.info("stats")
            memory = await redis.info("memory")

            # Count keys with our prefix
            key_count = 0
            cursor = 0
            while True:
                cursor, keys = await redis.scan(
                    cursor, match=f"{self._key_prefix}*", count=100
                )
                key_count += len(keys)
                if cursor == 0:
                    break

            return {
                "type": "redis",
                "size": key_count,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "memory_used_bytes": memory.get("used_memory", 0),
                "memory_used_human": memory.get("used_memory_human", "0B"),
                "connected": True,
            }
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {
                "type": "redis",
                "size": 0,
                "connected": False,
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            redis = await self._get_redis()
            await redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None
