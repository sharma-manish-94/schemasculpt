"""
Dependency Injection Container for SchemaSculpt AI Service.

This module provides FastAPI dependencies for injecting services and infrastructure
components. All dependencies follow the Dependency Inversion Principle - they depend
on interfaces, not concrete implementations.

Usage:
    @router.post("/analyze")
    async def analyze(
        request: Request,
        llm: ILLMProvider = Depends(get_llm_provider),
        cache: ICacheRepository = Depends(get_cache_repository)
    ):
        ...
"""

import logging
from datetime import timedelta
from functools import lru_cache
from typing import TYPE_CHECKING, Optional

from fastapi import Depends, Request

from app.core.config import get_settings, settings
from app.domain.interfaces.cache_repository import ICacheRepository
from app.domain.interfaces.llm_provider import ILLMProvider
from app.domain.interfaces.rag_repository import IRAGRepository
from app.domain.interfaces.spec_validator import ISpecValidator

if TYPE_CHECKING:
    from app.services.agent_manager import AgentManager
    from app.services.description_analysis_service import DescriptionAnalysisService
    from app.services.llm_service import LLMService
    from app.services.meta_analysis_service import MetaAnalysisService
    from app.services.mock_data_service import MockDataService
    from app.services.patch_generator import PatchGenerator
    from app.services.rag_service import RAGService
    from app.services.security.security_workflow import SecurityAnalysisWorkflow
    from app.services.smart_fix_service import SmartFixService
    from app.services.test_case_generator import TestCaseGeneratorService

logger = logging.getLogger(__name__)

# =============================================================================
# Singleton State Management
# =============================================================================

# These hold singleton instances - initialized lazily on first access
_llm_provider: Optional[ILLMProvider] = None
_cache_repository: Optional[ICacheRepository] = None
_rag_repository: Optional[IRAGRepository] = None
_spec_validator: Optional[ISpecValidator] = None


async def _initialize_llm_provider() -> ILLMProvider:
    """Initialize the LLM provider based on configuration."""
    from app.infrastructure.llm.provider_factory import create_provider

    provider_type = settings.llm_provider
    provider_config = settings.get_provider_config()

    logger.info(f"Initializing LLM provider: {provider_type}")

    provider = await create_provider(provider_type, provider_config)

    # Verify provider health
    try:
        is_healthy = await provider.health_check()
        if is_healthy:
            logger.info(f"LLM provider {provider_type} initialized successfully")
        else:
            logger.warning(f"LLM provider {provider_type} health check failed")
    except Exception as e:
        logger.warning(f"LLM provider health check error: {e}")

    return provider


async def _initialize_cache_repository() -> ICacheRepository:
    """Initialize the cache repository (Redis with in-memory fallback)."""
    from app.infrastructure.cache.cache_factory import create_cache_repository

    redis_url = settings.redis_url
    default_ttl = timedelta(seconds=settings.cache_ttl)

    logger.info(f"Initializing cache repository (Redis URL: {redis_url})")

    cache = await create_cache_repository(
        redis_url=redis_url,
        default_ttl=default_ttl,
        fallback_to_memory=True,  # Fall back to in-memory if Redis unavailable
    )

    # Verify cache health
    try:
        is_healthy = await cache.health_check()
        if is_healthy:
            logger.info("Cache repository initialized successfully")
        else:
            logger.warning("Cache repository health check failed, using fallback")
    except Exception as e:
        logger.warning(f"Cache health check error: {e}")

    return cache


async def _initialize_rag_repository() -> Optional[IRAGRepository]:
    """Initialize the RAG repository (ChromaDB)."""
    from app.infrastructure.rag.chromadb_repository import ChromaDBRepository

    try:
        logger.info("Initializing RAG repository")
        rag = ChromaDBRepository(
            persist_directory=f"{settings.ai_service_data_dir}/chroma_db"
        )

        if rag.is_available():
            logger.info("RAG repository initialized successfully")
            return rag
        else:
            logger.warning("RAG repository not available")
            return None

    except Exception as e:
        logger.warning(f"RAG repository initialization failed: {e}")
        return None


async def _initialize_spec_validator() -> ISpecValidator:
    """Initialize the spec validator."""
    from app.infrastructure.validation.prance_validator import PranceSpecValidator

    logger.info("Initializing spec validator")
    return PranceSpecValidator()


# =============================================================================
# Core Infrastructure Dependencies
# =============================================================================


async def get_llm_provider() -> ILLMProvider:
    """
    Get the configured LLM provider (singleton).

    The provider is initialized lazily on first access and reused for
    subsequent requests.

    Returns:
        ILLMProvider: The configured LLM provider instance.
    """
    global _llm_provider
    if _llm_provider is None:
        _llm_provider = await _initialize_llm_provider()
    return _llm_provider


async def get_cache_repository() -> ICacheRepository:
    """
    Get the cache repository (singleton).

    Uses Redis if available, falls back to in-memory cache otherwise.

    Returns:
        ICacheRepository: The cache repository instance.
    """
    global _cache_repository
    if _cache_repository is None:
        _cache_repository = await _initialize_cache_repository()
    return _cache_repository


async def get_rag_repository() -> Optional[IRAGRepository]:
    """
    Get the RAG repository (singleton).

    Returns None if RAG service is not available.

    Returns:
        Optional[IRAGRepository]: The RAG repository instance or None.
    """
    global _rag_repository
    if _rag_repository is None:
        _rag_repository = await _initialize_rag_repository()
    return _rag_repository


async def get_spec_validator() -> ISpecValidator:
    """
    Get the spec validator (singleton).

    Returns:
        ISpecValidator: The spec validator instance.
    """
    global _spec_validator
    if _spec_validator is None:
        _spec_validator = await _initialize_spec_validator()
    return _spec_validator


# =============================================================================
# Legacy Service Dependencies (for backward compatibility during migration)
# =============================================================================


@lru_cache()
def get_llm_service() -> "LLMService":
    """
    Get the LLMService instance (legacy).

    DEPRECATED: Use get_llm_provider() instead for new code.
    This is kept for backward compatibility during migration.
    """
    from app.services.llm_service import LLMService

    return LLMService()


async def get_agent_manager(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "AgentManager":
    """
    Get the AgentManager instance.

    Args:
        llm_service: The LLMService dependency.

    Returns:
        AgentManager: The agent manager instance.
    """
    from app.services.agent_manager import AgentManager

    return AgentManager(llm_service)


@lru_cache()
def get_rag_service() -> "RAGService":
    """
    Get the RAGService instance (legacy).

    DEPRECATED: Use get_rag_repository() instead for new code.
    """
    from app.services.rag_service import RAGService

    return RAGService()


# =============================================================================
# Domain Service Dependencies
# =============================================================================


async def get_security_workflow(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "SecurityAnalysisWorkflow":
    """Get the security analysis workflow service."""
    from app.services.security.security_workflow import SecurityAnalysisWorkflow

    return SecurityAnalysisWorkflow(llm_service)


async def get_patch_generator(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "PatchGenerator":
    """Get the patch generator service."""
    from app.services.patch_generator import PatchGenerator

    return PatchGenerator(llm_service)


async def get_smart_fix_service(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "SmartFixService":
    """Get the smart fix service."""
    from app.services.smart_fix_service import SmartFixService

    return SmartFixService(llm_service)


async def get_meta_analysis_service(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "MetaAnalysisService":
    """Get the meta-analysis service."""
    from app.services.meta_analysis_service import MetaAnalysisService

    return MetaAnalysisService(llm_service)


async def get_description_analysis_service() -> "DescriptionAnalysisService":
    """Get the description analysis service."""
    from app.services.description_analysis_service import DescriptionAnalysisService
    from app.services.llm_adapter import LLMAdapter

    llm_adapter = LLMAdapter()
    return DescriptionAnalysisService(llm_adapter)


async def get_mock_data_service(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "MockDataService":
    """Get the mock data service."""
    from app.services.mock_data_service import MockDataService

    return MockDataService(llm_service)


async def get_test_case_generator(
    llm_service: "LLMService" = Depends(get_llm_service),
) -> "TestCaseGeneratorService":
    """Get the test case generator service."""
    from app.services.test_case_generator import TestCaseGeneratorService

    return TestCaseGeneratorService(llm_service)


# =============================================================================
# Request Context Dependencies
# =============================================================================


async def get_correlation_id(request: Request) -> str:
    """
    Get or generate a correlation ID for the request.

    Looks for X-Correlation-ID header, generates one if not present.
    """
    import uuid

    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        correlation_id = str(uuid.uuid4())

    # Store in request state for later use
    request.state.correlation_id = correlation_id
    return correlation_id


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Get the current authenticated user from request state.

    Returns None if no user is authenticated.
    """
    return getattr(request.state, "user", None)


# =============================================================================
# Cleanup Functions
# =============================================================================


async def cleanup_dependencies() -> None:
    """
    Cleanup singleton instances on shutdown.

    Should be called during application shutdown.
    """
    global _llm_provider, _cache_repository, _rag_repository, _spec_validator

    logger.info("Cleaning up dependency singletons")

    # Reset all singletons
    _llm_provider = None
    _cache_repository = None
    _rag_repository = None
    _spec_validator = None


def reset_singletons_for_testing() -> None:
    """
    Reset singleton instances for testing.

    This allows tests to inject mock dependencies.
    """
    global _llm_provider, _cache_repository, _rag_repository, _spec_validator

    _llm_provider = None
    _cache_repository = None
    _rag_repository = None
    _spec_validator = None
