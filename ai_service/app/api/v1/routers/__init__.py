"""
API Routers for SchemaSculpt AI Service.

This package contains domain-specific routers that handle API endpoints.
Each router focuses on a single domain following Single Responsibility Principle.

Router Architecture:
    Each router is responsible for:
    - Defining endpoints for a specific domain
    - Input validation and error handling
    - Calling appropriate services
    - Formatting responses

    Routers do NOT:
    - Contain business logic (that belongs in services)
    - Access databases directly (use repositories)
    - Hold state between requests (stateless design)

Available Routers:
    - health: Health checks and service status (Kubernetes probes, monitoring)
    - security_analysis: Security scanning, attack path simulation, OWASP compliance
    - spec_analysis: OpenAPI specification analysis (taint, authz, similarity, zombies)
    - test_generation: Test case and test suite generation
    - mock_server: Mock server management and data generation
    - patch_operations: JSON patch generation, application, and smart fixes
    - rag_knowledge: RAG knowledge base status and explanations
    - cache_management: Cache statistics and management operations
    - ai_processing: Core AI processing and generation
    - workflows: Workflow execution and context management
    - context: Maintain context in chat and sessions
    - explanation: AI powered explanation of validation errors and suggestions
    - meta_analysis: Meta Analysis of OpenAPI specification
    - prompt: Intelligent prompt generation and prompt engine statistics

Usage:
    from app.api.v1.routers import health_router, security_router
    api_router.include_router(health_router)
    api_router.include_router(security_router)
"""

from app.api.v1.routers.ai_processing import router as ai_processing_router
from app.api.v1.routers.cache_management import router as cache_router
from app.api.v1.routers.context import router as context_router
from app.api.v1.routers.explanation import router as explanation_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.meta_analysis import router as meta_analysis_router
from app.api.v1.routers.mock_server import router as mock_router
from app.api.v1.routers.patch_operations import router as patch_router
from app.api.v1.routers.patch_operations import smart_fix_router
from app.api.v1.routers.prompt import router as prompt_router
from app.api.v1.routers.rag_knowledge import router as rag_router
from app.api.v1.routers.security_analysis import router as security_router
from app.api.v1.routers.spec_analysis import router as analysis_router
from app.api.v1.routers.test_generation import router as testing_router
from app.api.v1.routers.workflow import router as workflow_router

__all__ = [
    "health_router",
    "security_router",
    "analysis_router",
    "testing_router",
    "mock_router",
    "patch_router",
    "smart_fix_router",
    "rag_router",
    "cache_router",
    "testing_router",
    "meta_analysis_router",
    "prompt_router",
    "context_router",
    "explanation_router",
    "ai_processing_router",
    "workflow_router",
]
