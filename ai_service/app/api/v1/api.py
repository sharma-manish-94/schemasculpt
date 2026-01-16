"""
API v1 Router Aggregation.

This module aggregates all v1 routers into a single FastAPI APIRouter.
The aggregated router is then included in the main FastAPI application.

Architecture:
    main.py
        └── v1/api.py (this file)
            ├── routers/health.py
            ├── routers/security_analysis.py
            ├── routers/cache_management.py
            ├── routers/rag_knowledge.py
            ├── routers/spec_analysis.py
            ├── routers/test_generation.py
            ├── routers/mock_server.py
            ├── routers/patch_operations.py
            ├── endpoints.py (legacy endpoints - to be migrated)
            └── repository_endpoints.py

Migration Strategy:
    Phase 1 (current): All routers coexist with legacy endpoints.py
    Phase 2 (future): Gradually move endpoints from endpoints.py to domain routers
    Phase 3 (final): Remove endpoints.py entirely

Router Categories:
    - Health & Monitoring: Health checks, agent status
    - Security: Security analysis, attack path simulation, RAG-enhanced security
    - Analysis: Taint analysis, authz matrix, schema similarity, zombie APIs
    - Testing: Test case generation, test suite generation
    - Mock Server: Mock server management, mock data generation
    - Patch Operations: JSON patch generation, application, smart fixes
    - Legacy: Main endpoints (to be decomposed), repository endpoints
"""

from fastapi import APIRouter

# Legacy routers - to be decomposed in future phases
from app.api.v1.endpoints import router as legacy_endpoints_router
from app.api.v1.repository_endpoints import router as repository_router
from app.api.v1.routers.cache_management import router as cache_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.mock_server import router as mock_router
from app.api.v1.routers.patch_operations import router as patch_router
from app.api.v1.routers.patch_operations import smart_fix_router
from app.api.v1.routers.rag_knowledge import router as rag_router
from app.api.v1.routers.security_analysis import router as security_router
from app.api.v1.routers.spec_analysis import router as analysis_router
from app.api.v1.routers.test_generation import router as testing_router

# Create the aggregated v1 router
api_router = APIRouter()

# =============================================================================
# New Domain-Specific Routers (Recommended)
# =============================================================================

# Health & Monitoring
api_router.include_router(health_router)

# Security Analysis
api_router.include_router(security_router)

# OpenAPI Specification Analysis
api_router.include_router(analysis_router)

# Test Generation
api_router.include_router(testing_router)

# Mock Server Management
api_router.include_router(mock_router)

# Patch Operations
api_router.include_router(patch_router)
api_router.include_router(smart_fix_router)

# RAG Knowledge Base
api_router.include_router(rag_router)

# Cache Management
api_router.include_router(cache_router)

# =============================================================================
# Legacy Routers (To Be Decomposed)
# =============================================================================

# Legacy endpoints - contains main AI processing, workflow, context management
# These will gradually be moved to domain-specific routers
api_router.include_router(legacy_endpoints_router)

# Repository/MCP client endpoints
api_router.include_router(repository_router)


# =============================================================================
# Router Metadata for Documentation
# =============================================================================

ROUTER_METADATA = {
    "health": {
        "description": "Health checks and service status monitoring",
        "endpoints": ["/health", "/ai/health", "/ai/agents/status"],
    },
    "security": {
        "description": "Security analysis, attack path simulation, OWASP compliance",
        "endpoints": [
            "/ai/security/analyze",
            "/ai/security/attack-path-simulation",
            "/ai/security/analyze-with-knowledge-base",
        ],
    },
    "analysis": {
        "description": "AI-powered OpenAPI specification analysis",
        "endpoints": [
            "/ai/analyze/taint-analysis",
            "/ai/analyze/authz-matrix",
            "/ai/analyze/schema-similarity",
            "/ai/analyze/zombie-apis",
            "/ai/analyze/comprehensive-architecture",
        ],
    },
    "testing": {
        "description": "Test case and test suite generation",
        "endpoints": [
            "/ai/test-cases/generate",
            "/ai/test-suite/generate",
            "/tests/generate",
            "/tests/generate/all",
        ],
    },
    "mock": {
        "description": "Mock server management and data generation",
        "endpoints": [
            "/mock/start",
            "/mock/{mock_id}",
            "/mock/generate-data",
            "/mock/generate-variations",
        ],
    },
    "patch": {
        "description": "JSON patch generation and application",
        "endpoints": [
            "/ai/patch/generate",
            "/ai/patch/apply",
            "/ai/fix/smart",
        ],
    },
    "rag": {
        "description": "RAG knowledge base management",
        "endpoints": ["/ai/rag/status", "/ai/rag/explain"],
    },
    "cache": {
        "description": "Cache statistics and management",
        "endpoints": ["/ai/cache/stats", "/ai/cache/clear"],
    },
}
