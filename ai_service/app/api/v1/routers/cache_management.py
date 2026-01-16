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
from datetime import datetime, timedelta
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
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as error:
        logger.error(f"Failed to get cache statistics: {error}")
        return {
            "error": str(error),
            "timestamp": datetime.utcnow().isoformat(),
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
            "timestamp": datetime.utcnow().isoformat(),
        }
    except Exception as error:
        logger.error(f"Failed to clear cache: {error}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CACHE_CLEAR_FAILED",
                "message": f"Failed to clear cache: {str(error)}",
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
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Explanation Cache Operations
# =============================================================================

# Note: During migration, this uses global dict. Will be migrated to ICacheRepository.
EXPLANATION_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/ai/cache/stats")
async def get_explanation_cache_statistics() -> Dict[str, Any]:
    """
    Get statistics for the AI explanation cache.

    The explanation cache stores AI-generated explanations for
    validation issues to avoid redundant LLM calls.

    Returns:
        Cache size, TTL, and cleanup statistics.
    """
    # Clean up expired entries while getting stats
    current_time = datetime.utcnow()
    expired_keys = [
        key
        for key, value in EXPLANATION_CACHE.items()
        if current_time - value["timestamp"] > EXPLANATION_CACHE_TTL
    ]

    expired_entries_cleaned = len(expired_keys)
    for key in expired_keys:
        del EXPLANATION_CACHE[key]

    return {
        "cache_size": len(EXPLANATION_CACHE),
        "expired_entries_cleaned": expired_entries_cleaned,
        "ttl_hours": EXPLANATION_CACHE_TTL.total_seconds() / 3600,
        "timestamp": current_time.isoformat(),
    }


@router.delete("/ai/cache/clear")
async def clear_explanation_cache() -> Dict[str, Any]:
    """
    Clear all cached AI explanations.

    Use this when:
    - Updating the explanation prompt template
    - Clearing memory during high load
    - Testing fresh explanations

    Returns:
        Number of entries cleared and timestamp.
    """
    entries_cleared = len(EXPLANATION_CACHE)
    EXPLANATION_CACHE.clear()

    logger.info(f"Cleared {entries_cleared} cached explanations")

    return {
        "success": True,
        "cleared_entries": entries_cleared,
        "timestamp": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Security Analysis Cache Operations
# =============================================================================

# Note: During migration, this uses global dict. Will be migrated to ICacheRepository.
SECURITY_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


@router.get("/ai/security/cache/stats")
async def get_security_analysis_cache_statistics() -> Dict[str, Any]:
    """
    Get statistics for the security analysis cache.

    The security cache stores completed security analysis reports
    to avoid redundant scans of unchanged specifications.

    Returns:
        Total entries, valid/expired counts, and entry details.
    """
    current_time = datetime.utcnow()

    valid_entries = 0
    expired_entries = 0

    for cached_data in SECURITY_ANALYSIS_CACHE.values():
        if current_time < cached_data["expires_at"]:
            valid_entries += 1
        else:
            expired_entries += 1

    cache_entry_details = [
        {
            "spec_hash": key,
            "cached_at": data["cached_at"].isoformat(),
            "expires_at": data["expires_at"].isoformat(),
            "is_expired": current_time >= data["expires_at"],
            "overall_score": data["report"].get("overall_score"),
            "risk_level": data["report"].get("risk_level"),
        }
        for key, data in SECURITY_ANALYSIS_CACHE.items()
    ]

    return {
        "total_entries": len(SECURITY_ANALYSIS_CACHE),
        "valid_entries": valid_entries,
        "expired_entries": expired_entries,
        "ttl_hours": SECURITY_CACHE_TTL.total_seconds() / 3600,
        "cache_details": cache_entry_details,
        "timestamp": current_time.isoformat(),
    }


@router.delete("/ai/security/cache/clear")
async def clear_security_analysis_cache() -> Dict[str, Any]:
    """
    Clear all cached security analysis reports.

    Use this when:
    - Security analysis logic has been updated
    - Forcing fresh analysis for all specifications
    - Clearing memory during high load

    Returns:
        Number of entries cleared and timestamp.
    """
    entries_cleared = len(SECURITY_ANALYSIS_CACHE)
    SECURITY_ANALYSIS_CACHE.clear()

    logger.info(f"Cleared security analysis cache ({entries_cleared} entries)")

    return {
        "success": True,
        "cleared_entries": entries_cleared,
        "message": f"Cleared {entries_cleared} cached security analysis reports",
        "timestamp": datetime.utcnow().isoformat(),
    }
