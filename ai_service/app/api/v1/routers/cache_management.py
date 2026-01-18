"""
Cache Management Router.

Provides endpoints for managing and monitoring caches:
- Explanation cache (AI explanations for validation issues)
- Security analysis cache (security scan results)
- General service cache (spec parsing, test cases, mock data)

These endpoints help with:
- Monitoring cache performance and hit rates
- Clearing stale data
- Debugging cache-related issues
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_cache_repository
from app.core.config import settings
from app.domain.interfaces.cache_repository import ICacheRepository
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cache Management"])

# Cache TTL configurations
EXPLANATION_CACHE_TTL = timedelta(hours=settings.explanation_cache_ttl_hours)
SECURITY_CACHE_TTL = timedelta(hours=24)


# =============================================================================
# General Cache Operations
# =============================================================================


@router.get("/cache/stats")
async def get_service_cache_statistics(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Get comprehensive cache statistics and performance metrics.

    Returns information about:
    - Cache sizes for different data types
    - Hit/miss rates
    - Overall cache performance

    Returns:
        Dictionary with cache statistics and timestamp.
    """
    logger.info("Retrieving service cache statistics")

    try:
        # Get stats from the legacy cache service
        legacy_cache_stats = cache_service.get_cache_stats()

        # Get stats from the new cache repository
        repository_cache_stats = await cache.get_stats()

        return {
            "legacy_cache": legacy_cache_stats,
            "repository_cache": repository_cache_stats,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as error:
        logger.error(f"Failed to get cache statistics: {error}")
        return {
            "error": "Failed to retrieve cache statistics",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.delete("/cache/clear")
async def clear_service_cache(
    cache_type: Optional[str] = Query(
        None,
        description="Type of cache to clear: 'spec', 'test', 'mock', or None for all",
    ),
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Clear specified cache or all caches.

    Args:
        cache_type: Optional type of cache to clear.
                   - 'spec': Clear specification parsing cache
                   - 'test': Clear test case cache
                   - 'mock': Clear mock data cache
                   - None: Clear all caches

    Returns:
        Confirmation message with timestamp.
    """
    cache_type_description = cache_type or "all"
    logger.info(f"Clearing {cache_type_description} cache(s)")

    try:
        # Clear legacy cache
        cache_service.clear_cache(cache_type)

        # Clear repository cache if clearing all
        if cache_type is None:
            await cache.clear()

        return {
            "success": True,
            "message": f"Successfully cleared {cache_type_description} cache(s)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as error:
        logger.error(f"Failed to clear cache: {error}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CACHE_CLEAR_FAILED",
                "message": "Failed to clear cache",
            },
        )


@router.post("/cache/invalidate")
async def invalidate_cache_for_specification(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Invalidate all cache entries related to a specific OpenAPI specification.

    When a specification is updated, this endpoint can be used to
    invalidate all cached data (parsed spec, test cases, mock data)
    associated with it.

    Request Body:
        spec_text (str): The OpenAPI specification text to invalidate.

    Returns:
        Confirmation message with timestamp.
    """
    spec_text = request.get("spec_text")

    if not spec_text:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "MISSING_SPECIFICATION",
                "message": "The 'spec_text' field is required in the request body",
            },
        )

    logger.info("Invalidating cache entries for specification")
    cache_service.invalidate_spec_cache(spec_text)

    return {
        "success": True,
        "message": "Cache invalidated for the provided specification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Explanation Cache Operations
# =============================================================================

# Cache key prefix for explanation cache
_EXPLANATION_CACHE_PREFIX = "explanation:"


@router.get("/ai/cache/stats")
async def get_explanation_cache_statistics(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Get statistics for the AI explanation cache.

    The explanation cache stores AI-generated explanations for
    validation issues to avoid redundant LLM calls.

    Args:
        cache: Injected cache repository.

    Returns:
        Cache size, TTL, and cleanup statistics.
    """
    current_time = datetime.now(timezone.utc)

    # Get overall cache stats (includes all cache types)
    cache_stats = await cache.get_stats()

    return {
        "cache_prefix": _EXPLANATION_CACHE_PREFIX,
        "ttl_hours": EXPLANATION_CACHE_TTL.total_seconds() / 3600,
        "repository_stats": cache_stats,
        "timestamp": current_time.isoformat(),
    }


@router.delete("/ai/cache/clear")
async def clear_explanation_cache(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Clear all cached AI explanations.

    Use this when:
    - Updating the explanation prompt template
    - Clearing memory during high load
    - Testing fresh explanations

    Args:
        cache: Injected cache repository.

    Returns:
        Number of entries cleared and timestamp.
    """
    # Clear all explanation cache entries using pattern matching
    entries_cleared = await cache.clear(f"{_EXPLANATION_CACHE_PREFIX}*")

    logger.info(f"Cleared {entries_cleared} cached explanations")

    return {
        "success": True,
        "cleared_entries": entries_cleared,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# =============================================================================
# Security Analysis Cache Operations
# =============================================================================

# Cache key prefixes for security caches
_SECURITY_CACHE_PREFIX = "security:"
_ATTACK_PATH_CACHE_PREFIX = "attack_path:"


@router.get("/ai/security/cache/stats")
async def get_security_analysis_cache_statistics(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Get statistics for the security analysis cache.

    The security cache stores completed security analysis reports
    to avoid redundant scans of unchanged specifications.

    Args:
        cache: Injected cache repository.

    Returns:
        Total entries, valid/expired counts, and entry details.
    """
    current_time = datetime.now(timezone.utc)

    # Get overall cache stats
    cache_stats = await cache.get_stats()

    return {
        "security_cache_prefix": _SECURITY_CACHE_PREFIX,
        "attack_path_cache_prefix": _ATTACK_PATH_CACHE_PREFIX,
        "ttl_hours": SECURITY_CACHE_TTL.total_seconds() / 3600,
        "repository_stats": cache_stats,
        "timestamp": current_time.isoformat(),
    }


@router.delete("/ai/security/cache/clear")
async def clear_security_analysis_cache(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> Dict[str, Any]:
    """
    Clear all cached security analysis reports.

    Use this when:
    - Security analysis logic has been updated
    - Forcing fresh analysis for all specifications
    - Clearing memory during high load

    Args:
        cache: Injected cache repository.

    Returns:
        Number of entries cleared and timestamp.
    """
    # Clear both security and attack path caches
    security_entries_cleared = await cache.clear(f"{_SECURITY_CACHE_PREFIX}*")
    attack_path_entries_cleared = await cache.clear(f"{_ATTACK_PATH_CACHE_PREFIX}*")
    total_cleared = security_entries_cleared + attack_path_entries_cleared

    logger.info(f"Cleared security analysis cache ({total_cleared} entries)")

    return {
        "success": True,
        "cleared_entries": total_cleared,
        "security_entries_cleared": security_entries_cleared,
        "attack_path_entries_cleared": attack_path_entries_cleared,
        "message": f"Cleared {total_cleared} cached security analysis reports",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
