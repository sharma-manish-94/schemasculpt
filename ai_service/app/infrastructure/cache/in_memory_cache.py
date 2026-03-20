"""
In-Memory Cache Repository.

Provides an in-memory implementation of ICacheRepository.
This is used as a fallback when Redis is not available.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.domain.interfaces.cache_repository import ICacheRepository

logger = logging.getLogger(__name__)


class CacheEntry:
    """Internal representation of a cached value."""

    def __init__(
        self,
        value: Any,
        expires_at: Optional[datetime] = None,
    ):
        self.value = value
        self.created_at = datetime.utcnow()
        self.expires_at = expires_at
        self.last_accessed = datetime.utcnow()
        self.hit_count = 0

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def access(self) -> Any:
        """Record access and return value."""
        self.last_accessed = datetime.utcnow()
        self.hit_count += 1
        return self.value


class InMemoryCacheRepository(ICacheRepository):
    """
    In-memory implementation of ICacheRepository.

    Features:
    - TTL-based expiration
    - LRU eviction when max size is reached
    - Thread-safe with asyncio locks
    - Pattern-based key matching for clear operations

    Usage:
        cache = InMemoryCacheRepository(default_ttl=timedelta(hours=1), max_size=10000)
        await cache.set("key", {"data": "value"})
        value = await cache.get("key")
    """

    def __init__(
        self,
        default_ttl: timedelta = timedelta(hours=1),
        max_size: int = 10000,
    ):
        """
        Initialize the in-memory cache.

        Args:
            default_ttl: Default time-to-live for cached values.
            max_size: Maximum number of entries before LRU eviction.
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = asyncio.Lock()

        # Statistics
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        async with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None

            self._hits += 1
            return entry.access()

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Store a value in the cache."""
        actual_ttl = ttl or self._default_ttl
        expires_at = datetime.utcnow() + actual_ttl

        async with self._lock:
            self._cache[key] = CacheEntry(value, expires_at)
            await self._evict_if_needed()

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                del self._cache[key]
                return False
            return True

    async def clear(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries."""
        async with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                return -1 if count > 0 else 0

            # Pattern matching (simple glob-style)
            import fnmatch

            keys_to_delete = [
                k for k in self._cache.keys() if fnmatch.fnmatch(k, pattern)
            ]
            for key in keys_to_delete:
                del self._cache[key]
            return len(keys_to_delete)

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Retrieve multiple values from the cache."""
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result

    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[timedelta] = None,
    ) -> None:
        """Store multiple values in the cache."""
        for key, value in items.items():
            await self.set(key, value, ttl)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

            return {
                "type": "in_memory",
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests,
            }

    async def health_check(self) -> bool:
        """In-memory cache is always healthy."""
        return True

    async def _evict_if_needed(self) -> None:
        """Evict entries if cache is too large (LRU eviction)."""
        # First, remove expired entries
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]

        # If still too large, remove LRU entries
        if len(self._cache) > self._max_size:
            # Sort by last_accessed (oldest first)
            sorted_entries = sorted(
                self._cache.items(), key=lambda x: x[1].last_accessed
            )
            entries_to_remove = len(self._cache) - self._max_size
            for key, _ in sorted_entries[:entries_to_remove]:
                del self._cache[key]
            logger.debug(f"Evicted {entries_to_remove} LRU entries from cache")
