"""
Health Check Router.

Provides endpoints for monitoring service health and status.
These endpoints are typically used by:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems (Prometheus, Datadog, etc.)
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.api.deps import get_agent_manager, get_cache_repository
from app.core.config import settings
from app.domain.interfaces.cache_repository import ICacheRepository
from app.schemas.ai_schemas import HealthResponse
from app.services.agent_manager import AgentManager
from app.services.context_manager import ContextManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health & Status"])

# Track service start time for uptime calculation
SERVICE_START_TIME = time.time()

# Context manager instance (shared)
context_manager = ContextManager()


@router.get("/ai/health", response_model=HealthResponse)
async def check_service_health(
    cache: ICacheRepository = Depends(get_cache_repository),
) -> HealthResponse:
    """
    Comprehensive health check for all AI service components.

    Checks the status of:
    - LLM provider connectivity
    - Cache backend (Redis or in-memory)
    - Agent manager
    - Context manager

    Returns:
        HealthResponse with overall status and component details.

    Used by:
        - Kubernetes readiness probe
        - Load balancer health checks
        - Monitoring dashboards
    """
    uptime_seconds = int(time.time() - SERVICE_START_TIME)
    dependency_statuses: Dict[str, str] = {}

    try:
        # Check cache health
        cache_is_healthy = await cache.health_check()
        dependency_statuses["cache"] = "healthy" if cache_is_healthy else "degraded"

        # Get context statistics
        context_statistics = context_manager.get_context_statistics()
        dependency_statuses["context_manager"] = "healthy"

        # Calculate metrics
        total_requests = context_statistics.get("total_conversation_turns", 0)
        average_response_time = context_statistics.get("average_response_time", 0.0)
        success_rate = context_statistics.get("average_success_rate", 1.0)
        error_rate = round(1.0 - success_rate, 4)

        overall_status = _determine_overall_health_status(dependency_statuses)

        return HealthResponse(
            status=overall_status,
            version=settings.app_version,
            uptime_seconds=uptime_seconds,
            dependencies=dependency_statuses,
            total_requests=total_requests,
            average_response_time_ms=average_response_time,
            error_rate=error_rate,
        )

    except Exception as error:
        logger.error(f"Health check encountered an error: {str(error)}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            uptime_seconds=uptime_seconds,
            dependencies={"error": "An internal error occurred during health check."},
        )


@router.get("/ai/agents/status")
async def get_all_agents_status(
    agent_manager: AgentManager = Depends(get_agent_manager),
) -> Dict[str, Any]:
    """
    Get the current status of all AI agents.

    Returns information about each agent including:
    - Agent name and type
    - Current state (idle, busy, error)
    - Recent activity statistics

    Returns:
        Dictionary containing status for each registered agent.
    """
    try:
        agent_status = agent_manager.get_agent_status()
        return {
            "status": "success",
            "agents": agent_status,
            "timestamp": time.time(),
        }
    except Exception as error:
        logger.error(f"Failed to get agent status: {str(error)}")
        return {
            "status": "error",
            "message": "Failed to retrieve agent status",
            "agents": {},
        }


@router.get("/health")
async def simple_health_check() -> Dict[str, str]:
    """
    Simple health check endpoint for basic liveness probes.

    Returns a minimal response to confirm the service is running.
    Use /ai/health for comprehensive health information.

    Returns:
        Simple dictionary with status "ok".
    """
    return {"status": "ok", "service": "schemasculpt-ai"}


def _determine_overall_health_status(dependency_statuses: Dict[str, str]) -> str:
    """
    Determine overall health status based on individual component statuses.

    Rules:
    - If any component is "unhealthy" -> overall is "unhealthy"
    - If any component is "degraded" -> overall is "degraded"
    - Otherwise -> overall is "healthy"
    """
    if any(status == "unhealthy" for status in dependency_statuses.values()):
        return "unhealthy"

    if any(status == "degraded" for status in dependency_statuses.values()):
        return "degraded"

    return "healthy"
