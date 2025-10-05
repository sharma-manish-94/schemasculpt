"""
Caching service for improving performance of test and mock generation.

Implements multi-level caching:
1. Spec parsing cache - Avoid re-parsing the same OpenAPI specs
2. Test case cache - Cache generated test cases by endpoint
3. Mock data cache - Cache generated mock data patterns
"""

import hashlib
import json
from typing import Any, Dict, Optional, List
from functools import lru_cache
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """
    In-memory cache service with TTL support.

    Uses a combination of:
    - LRU cache for frequently accessed items
    - TTL-based expiration for data freshness
    - Hash-based keys for efficient lookups
    """

    def __init__(self, default_ttl_minutes: int = 30, max_cache_size: int = 1000):
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.max_cache_size = max_cache_size

        # Separate caches for different data types
        self._spec_cache: Dict[str, Dict[str, Any]] = {}
        self._test_cache: Dict[str, Dict[str, Any]] = {}
        self._mock_cache: Dict[str, Dict[str, Any]] = {}

        # Cache metadata
        self._cache_stats = {
            "spec_hits": 0,
            "spec_misses": 0,
            "test_hits": 0,
            "test_misses": 0,
            "mock_hits": 0,
            "mock_misses": 0,
        }

    @staticmethod
    def _generate_cache_key(data: Any) -> str:
        """Generate a consistent hash key for any data."""
        if isinstance(data, dict):
            # Sort dict keys for consistency
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _is_expired(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if a cache entry has expired."""
        if "expires_at" not in cache_entry:
            return True
        return datetime.utcnow() > cache_entry["expires_at"]

    def _evict_expired(self, cache: Dict[str, Dict[str, Any]]) -> None:
        """Remove expired entries from cache."""
        expired_keys = [
            key for key, entry in cache.items()
            if self._is_expired(entry)
        ]
        for key in expired_keys:
            del cache[key]

    def _evict_lru(self, cache: Dict[str, Dict[str, Any]]) -> None:
        """Evict least recently used items if cache is too large."""
        if len(cache) > self.max_cache_size:
            # Sort by last accessed time and remove oldest
            sorted_items = sorted(
                cache.items(),
                key=lambda x: x[1].get("last_accessed", datetime.min)
            )
            items_to_remove = len(cache) - self.max_cache_size
            for key, _ in sorted_items[:items_to_remove]:
                del cache[key]

    # ==================== Spec Parsing Cache ====================

    def get_parsed_spec(self, spec_text: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached parsed specification."""
        cache_key = self._generate_cache_key(spec_text)

        self._evict_expired(self._spec_cache)

        if cache_key in self._spec_cache:
            entry = self._spec_cache[cache_key]
            if not self._is_expired(entry):
                entry["last_accessed"] = datetime.utcnow()
                self._cache_stats["spec_hits"] += 1
                logger.debug(f"Spec cache HIT for key {cache_key}")
                return entry["data"]

        self._cache_stats["spec_misses"] += 1
        logger.debug(f"Spec cache MISS for key {cache_key}")
        return None

    def cache_parsed_spec(
        self,
        spec_text: str,
        parsed_spec: Dict[str, Any],
        ttl_minutes: Optional[int] = None
    ) -> None:
        """Cache a parsed specification."""
        cache_key = self._generate_cache_key(spec_text)
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl

        self._spec_cache[cache_key] = {
            "data": parsed_spec,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + ttl,
            "last_accessed": datetime.utcnow()
        }

        self._evict_lru(self._spec_cache)
        logger.debug(f"Cached parsed spec with key {cache_key}")

    # ==================== Test Case Cache ====================

    def get_test_cases(
        self,
        spec_text: str,
        path: str,
        method: str,
        include_ai_tests: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached test cases for an endpoint."""
        cache_key = self._generate_cache_key({
            "spec": self._generate_cache_key(spec_text),  # Use spec hash
            "path": path,
            "method": method,
            "include_ai": include_ai_tests
        })

        self._evict_expired(self._test_cache)

        if cache_key in self._test_cache:
            entry = self._test_cache[cache_key]
            if not self._is_expired(entry):
                entry["last_accessed"] = datetime.utcnow()
                self._cache_stats["test_hits"] += 1
                logger.debug(f"Test cache HIT for {method} {path}")
                return entry["data"]

        self._cache_stats["test_misses"] += 1
        logger.debug(f"Test cache MISS for {method} {path}")
        return None

    def cache_test_cases(
        self,
        spec_text: str,
        path: str,
        method: str,
        include_ai_tests: bool,
        test_cases: Dict[str, Any],
        ttl_minutes: Optional[int] = None
    ) -> None:
        """Cache generated test cases."""
        cache_key = self._generate_cache_key({
            "spec": self._generate_cache_key(spec_text),
            "path": path,
            "method": method,
            "include_ai": include_ai_tests
        })
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl

        self._test_cache[cache_key] = {
            "data": test_cases,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + ttl,
            "last_accessed": datetime.utcnow()
        }

        self._evict_lru(self._test_cache)
        logger.debug(f"Cached test cases for {method} {path}")

    # ==================== Mock Data Cache ====================

    def get_mock_data(
        self,
        spec_text: str,
        path: str,
        method: str,
        response_code: str,
        count: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Retrieve cached mock data variations."""
        cache_key = self._generate_cache_key({
            "spec": self._generate_cache_key(spec_text),
            "path": path,
            "method": method,
            "code": response_code,
            "count": count
        })

        self._evict_expired(self._mock_cache)

        if cache_key in self._mock_cache:
            entry = self._mock_cache[cache_key]
            if not self._is_expired(entry):
                entry["last_accessed"] = datetime.utcnow()
                self._cache_stats["mock_hits"] += 1
                logger.debug(f"Mock cache HIT for {method} {path} ({response_code})")
                return entry["data"]

        self._cache_stats["mock_misses"] += 1
        logger.debug(f"Mock cache MISS for {method} {path} ({response_code})")
        return None

    def cache_mock_data(
        self,
        spec_text: str,
        path: str,
        method: str,
        response_code: str,
        count: int,
        mock_data: List[Dict[str, Any]],
        ttl_minutes: Optional[int] = None
    ) -> None:
        """Cache generated mock data."""
        cache_key = self._generate_cache_key({
            "spec": self._generate_cache_key(spec_text),
            "path": path,
            "method": method,
            "code": response_code,
            "count": count
        })
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl

        self._mock_cache[cache_key] = {
            "data": mock_data,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + ttl,
            "last_accessed": datetime.utcnow()
        }

        self._evict_lru(self._mock_cache)
        logger.debug(f"Cached mock data for {method} {path} ({response_code})")

    # ==================== Cache Management ====================

    def invalidate_spec_cache(self, spec_text: str) -> None:
        """Invalidate all cache entries related to a specific spec."""
        spec_key = self._generate_cache_key(spec_text)

        # Remove from spec cache
        if spec_key in self._spec_cache:
            del self._spec_cache[spec_key]

        # Remove related test and mock caches
        self._test_cache = {
            k: v for k, v in self._test_cache.items()
            if not k.startswith(spec_key)
        }
        self._mock_cache = {
            k: v for k, v in self._mock_cache.items()
            if not k.startswith(spec_key)
        }

        logger.info(f"Invalidated cache for spec {spec_key}")

    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """Clear specified cache or all caches."""
        if cache_type == "spec":
            self._spec_cache.clear()
        elif cache_type == "test":
            self._test_cache.clear()
        elif cache_type == "mock":
            self._mock_cache.clear()
        else:
            self._spec_cache.clear()
            self._test_cache.clear()
            self._mock_cache.clear()

        logger.info(f"Cleared {cache_type or 'all'} cache(s)")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and metrics."""
        total_hits = (
            self._cache_stats["spec_hits"] +
            self._cache_stats["test_hits"] +
            self._cache_stats["mock_hits"]
        )
        total_misses = (
            self._cache_stats["spec_misses"] +
            self._cache_stats["test_misses"] +
            self._cache_stats["mock_misses"]
        )
        total_requests = total_hits + total_misses

        hit_rate = (total_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_sizes": {
                "spec_cache": len(self._spec_cache),
                "test_cache": len(self._test_cache),
                "mock_cache": len(self._mock_cache),
                "total": len(self._spec_cache) + len(self._test_cache) + len(self._mock_cache)
            },
            "stats": self._cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_requests": total_requests
        }


# Global cache instance
cache_service = CacheService(default_ttl_minutes=30, max_cache_size=1000)
