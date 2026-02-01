"""
API v1 Router Aggregation.

This module aggregates all v1 routers into a single FastAPI APIRouter.
The aggregated router is then included in the main FastAPI application.

Architecture:
    main.py
        └── v1/api.py (this file)
            ├── routers/health.py          - Health checks and monitoring
            ├── routers/ai_processing.py   - Core AI processing (/ai/process, /ai/generate)
            ├── routers/workflow.py        - Workflow management
            ├── routers/context.py         - Session/context management
            ├── routers/prompt.py          - Prompt engine
            ├── routers/explanation.py     - AI explanations with RAG
            ├── routers/meta_analysis.py   - Meta-analysis and description quality
            ├── routers/security_analysis.py - Security analysis and attack paths
            ├── routers/spec_analysis.py   - Taint analysis, authz matrix, etc.
            ├── routers/test_generation.py - Test case generation
            ├── routers/mock_server.py     - Mock server management
            ├── routers/patch_operations.py - JSON patch operations
            ├── routers/rag_knowledge.py   - RAG knowledge base (deprecated, use explanation.py)
            ├── routers/cache_management.py - Cache statistics and management
            ├── endpoints.py               - Legacy endpoints (deprecated)
            └── repository_endpoints.py    - Repository/MCP client endpoints

Migration Status:
    ✅ Phase 1: Critical bug fixes completed
    ✅ Phase 2: New domain routers created
    ✅ Phase 3: Dependency injection migrated
    ✅ Phase 4: Global caches migrated to ICacheRepository
    ✅ Phase 5: Router aggregation updated
    🔄 Phase 6: Final cleanup in progress

Router Categories:
    - Health & Monitoring: Health checks, agent status
    - AI Processing: Core AI operations, spec generation
    - Workflow: Predefined and custom workflows
    - Context: Session management, context statistics
    - Prompt: Intelligent prompt generation
    - Explanation: AI explanations with RAG context
    - Meta Analysis: Higher-order pattern detection
    - Security: Security analysis, attack path simulation, OWASP compliance
    - Analysis: Taint analysis, authz matrix, schema similarity, zombie APIs
    - Testing: Test case and test suite generation
    - Mock Server: Mock server management, mock data generation
    - Patch Operations: JSON patch generation, application, smart fixes
    - Cache: Cache statistics and management
    - Legacy: Backward-compatible endpoints (to be removed)
"""

from fastapi import APIRouter

# Legacy routers - to be fully decomposed in future phases
from app.api.v1.endpoints import router as legacy_endpoints_router
from app.api.v1.repository_endpoints import router as repository_router

# New domain-specific routers (Phase 2)
from app.api.v1.routers.ai_processing import router as ai_processing_router

# Existing domain routers
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
from app.api.v1.routers.remediation import router as remediation_router
from app.api.v1.routers.security_analysis import router as security_router
from app.api.v1.routers.spec_analysis import router as analysis_router
from app.api.v1.routers.test_generation import router as testing_router
from app.api.v1.routers.workflow import router as workflow_router
from app.api.v1.routers.workflow import workflows_list_router

# Create the aggregated v1 router
api_router = APIRouter()

# =============================================================================
# New Domain-Specific Routers (Recommended)
# =============================================================================

# Health & Monitoring
api_router.include_router(health_router)

# AI Processing (core AI operations)
api_router.include_router(ai_processing_router)

# Workflow Management
api_router.include_router(workflow_router)
api_router.include_router(workflows_list_router)

# Context Management
api_router.include_router(context_router)

# Prompt Engine
api_router.include_router(prompt_router)

# Explanation & RAG
api_router.include_router(explanation_router)

# Meta Analysis
api_router.include_router(meta_analysis_router)

# Security Analysis
api_router.include_router(security_router)

# Remediation
api_router.include_router(remediation_router)

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
        "router": "routers/health.py",
        "endpoints": ["/health", "/ai/health", "/ai/agents/status"],
    },
    "ai_processing": {
        "description": "Core AI processing operations",
        "router": "routers/ai_processing.py",
        "endpoints": ["/ai/process", "/ai/generate"],
    },
    "workflow": {
        "description": "Workflow management and execution",
        "router": "routers/workflow.py",
        "endpoints": [
            "/ai/workflow/{workflow_name}",
            "/ai/workflow/custom",
            "/ai/workflows",
        ],
    },
    "context": {
        "description": "Session and context management",
        "router": "routers/context.py",
        "endpoints": [
            "/ai/context/session",
            "/ai/context/session/{session_id}",
            "/ai/context/statistics",
        ],
    },
    "prompt": {
        "description": "Intelligent prompt generation",
        "router": "routers/prompt.py",
        "endpoints": ["/ai/prompt/generate", "/ai/prompt/statistics"],
    },
    "explanation": {
        "description": "AI explanations with RAG context (authoritative)",
        "router": "routers/explanation.py",
        "endpoints": ["/ai/explain", "/ai/rag/status"],
    },
    "meta_analysis": {
        "description": "Meta-analysis and description quality assessment",
        "router": "routers/meta_analysis.py",
        "endpoints": ["/ai/meta-analysis", "/ai/analyze-descriptions"],
    },
    "security": {
        "description": "Security analysis, attack path simulation, OWASP compliance",
        "router": "routers/security_analysis.py",
        "endpoints": [
            "/ai/security/analyze",
            "/ai/security/analyze/authentication",
            "/ai/security/analyze/authorization",
            "/ai/security/analyze/data-exposure",
            "/ai/security/report/{spec_hash}",
            "/ai/security/attack-path-simulation",
            "/ai/security/attack-path-findings",
            "/ai/security/analyze-with-knowledge-base",
        ],
    },
    "analysis": {
        "description": "AI-powered OpenAPI specification analysis",
        "router": "routers/spec_analysis.py",
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
        "router": "routers/test_generation.py",
        "endpoints": [
            "/ai/test-cases/generate",
            "/ai/test-suite/generate",
            "/tests/generate",
            "/tests/generate/all",
        ],
    },
    "mock": {
        "description": "Mock server management and data generation",
        "router": "routers/mock_server.py",
        "endpoints": [
            "/mock/start",
            "/mock/{mock_id}",
            "/mock/generate-data",
            "/mock/generate-variations",
        ],
    },
    "patch": {
        "description": "JSON patch generation and application",
        "router": "routers/patch_operations.py",
        "endpoints": [
            "/ai/patch/generate",
            "/ai/patch/apply",
            "/ai/fix/smart",
        ],
    },
    "rag_knowledge": {
        "description": "RAG knowledge base (DEPRECATED - use explanation router)",
        "router": "routers/rag_knowledge.py",
        "deprecated": True,
        "endpoints": ["/ai/rag/status", "/ai/explain"],
    },
    "cache": {
        "description": "Cache statistics and management",
        "router": "routers/cache_management.py",
        "endpoints": [
            "/cache/stats",
            "/cache/clear",
            "/cache/invalidate",
            "/ai/cache/stats",
            "/ai/cache/clear",
            "/ai/security/cache/stats",
            "/ai/security/cache/clear",
        ],
    },
    "legacy": {
        "description": "Legacy endpoints (DEPRECATED - kept for backward compatibility)",
        "router": "endpoints.py",
        "deprecated": True,
        "endpoints": ["/process", "/specifications/generate"],
    },
}
