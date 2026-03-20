"""
Cache Repository Interface.

Defines the contract for cache implementations (Redis, in-memory, etc.).
This abstraction allows swapping cache backends without changing service code.
"""

from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any, Dict, List, Optional


class ICacheRepository(ABC):
    """
    Abstract interface for cache repositories.

    All cache implementations (Redis, in-memory, etc.) must implement this interface.
    This follows the Repository Pattern and Dependency Inversion Principle.

    Usage:
        # In service layer
        class SecurityService:
            def __init__(self, cache: ICacheRepository):
                self._cache = cache

            async def analyze(self, spec_hash: str) -> dict:
                # Check cache first
                cached = await self._cache.get(f"security:{spec_hash}")
                if cached:
                    return cached

                # Compute result
                result = await self._compute_analysis()

                # Cache result
                await self._cache.set(f"security:{spec_hash}", result, ttl=timedelta(hours=24))
                return result
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: The cache key.

        Returns:
            The cached value if found, None otherwise.
        """

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
    ) -> None:
        """
        Store a value in the cache.

        Args:
            key: The cache key.
            value: The value to cache (must be JSON-serializable).
            ttl: Time-to-live for the cached value. None = use default TTL.
        """

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.

        Args:
            key: The cache key to delete.

        Returns:
            True if the key was deleted, False if it didn't exist.
        """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: The cache key to check.

        Returns:
            True if the key exists, False otherwise.
        """

    @abstractmethod
    async def clear(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            pattern: Optional glob pattern to match keys (e.g., "security:*").
                     If None, clears all entries.

        Returns:
            Number of keys deleted, or -1 if full flush was performed.
        """

    @abstractmethod
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Retrieve multiple values from the cache.

        Args:
            keys: List of cache keys.

        Returns:
            Dictionary mapping keys to their values. Missing keys are omitted.
        """

    @abstractmethod
    async def set_many(
        self,
        items: Dict[str, Any],
        ttl: Optional[timedelta] = None,
    ) -> None:
        """
        Store multiple values in the cache.

        Args:
            items: Dictionary mapping keys to values.
            ttl: Time-to-live for all cached values.
        """

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics (size, hits, misses, etc.).
        """

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the cache backend is healthy.

        Returns:
            True if healthy, False otherwise.
        """
