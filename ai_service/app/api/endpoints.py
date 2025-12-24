"""
Enhanced API endpoints for SchemaSculpt AI Service.
Integrates advanced LLM service, agentic workflows, streaming, and comprehensive AI features.
"""

import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from prance import ResolvingParser

from ..core.config import settings
from ..core.exceptions import SchemaSculptException
from ..core.logging import get_logger, set_correlation_id
from ..schemas.ai_schemas import (
    AIRequest,
    AIResponse,
    GenerateSpecRequest,
    HealthResponse,
    LLMParameters,
    MockStartRequest,
    MockStartResponse,
    OperationType,
    StreamingMode,
)
from ..schemas.description_schemas import (
    DescriptionAnalysisRequest,
    DescriptionAnalysisResponse,
)
from ..schemas.meta_analysis_schemas import (
    AIMetaAnalysisRequest,
    AIMetaAnalysisResponse,
)
from ..schemas.patch_schemas import (
    PatchApplicationRequest,
    PatchApplicationResponse,
    PatchGenerationRequest,
    PatchGenerationResponse,
    SmartAIFixRequest,
    SmartAIFixResponse,
)
from ..schemas.security_schemas import SecurityAnalysisReport, SecurityAnalysisRequest
from ..services.agent_manager import AgentManager
from ..services.cache_service import cache_service
from ..services.context_manager import ContextManager
from ..services.description_analysis_service import DescriptionAnalysisService
from ..services.llm_adapter import LLMAdapter
from ..services.llm_service import LLMService
from ..services.meta_analysis_service import MetaAnalysisService
from ..services.mock_data_service import MockDataService
from ..services.patch_generator import PatchGenerator, apply_json_patch
from ..services.prompt_engine import PromptEngine
from ..services.rag_service import RAGService
from ..services.security import SecurityAnalysisWorkflow
from ..services.smart_fix_service import SmartFixService
from ..services.test_case_generator import TestCaseGeneratorService

# Initialize services
router = APIRouter()
logger = get_logger("api.endpoints")

# Service instances
llm_service = LLMService()
llm_adapter = LLMAdapter()
agent_manager = AgentManager(llm_service)
context_manager = ContextManager()
prompt_engine = PromptEngine()
rag_service = RAGService()
security_workflow = SecurityAnalysisWorkflow(llm_service)
patch_generator = PatchGenerator(llm_service)
smart_fix_service = SmartFixService(llm_service)
meta_analysis_service = MetaAnalysisService(llm_service)
description_analysis_service = DescriptionAnalysisService(llm_adapter)
mock_data_service = MockDataService(llm_service)
test_case_generator = TestCaseGeneratorService(llm_service)

# Mock server storage
MOCKED_APIS: Dict[str, Dict[str, Any]] = {}

# Security analysis cache (TTL: 24 hours)
SECURITY_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}
SECURITY_CACHE_TTL = timedelta(hours=24)

# Explanation cache
EXPLANATION_CACHE: Dict[str, Dict[str, Any]] = {}
EXPLANATION_CACHE_TTL = timedelta(hours=settings.explanation_cache_ttl_hours)


# Dependency for error handling
async def handle_exceptions():
    """Global exception handler dependency."""
    try:
        yield
    except SchemaSculptException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"error": e.error_code, "message": e.message, "details": e.details},
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"original_error": str(e)},
            },
        )


@router.post("/ai/process", response_model=AIResponse)
async def process_specification(
    request: AIRequest, _: None = Depends(handle_exceptions)
):
    """
    Process AI request with advanced features including streaming and JSON patching.
    """
    # Set correlation ID for tracking
    correlation_id = set_correlation_id()

    logger.info(
        f"Processing AI request: {request.operation_type}",
        extra={
            "correlation_id": correlation_id,
            "operation_type": request.operation_type,
            "streaming": request.streaming != StreamingMode.DISABLED,
            "has_patches": bool(request.json_patches),
        },
    )

    try:
        # Get context for the request
        session_id = (
            str(request.session_id)
            if request.session_id
            else context_manager.create_session(request.user_id)
        )
        request.context = context_manager.get_context_for_request(session_id, request)

        # Process the request
        result = await llm_service.process_ai_request(request)

        # Handle streaming response
        if request.streaming != StreamingMode.DISABLED:

            async def stream_generator():
                async for chunk in result:
                    yield f"data: {json.dumps(chunk.model_dump())}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
            )

        # Add conversation turn to context
        context_manager.add_conversation_turn(session_id, request, result, True)

        return result

    except Exception as e:
        logger.error(f"AI processing failed: {str(e)}")
        # Add failed turn to context
        if "session_id" in locals():
            context_manager.add_conversation_turn(session_id, request, None, False)
        raise


@router.post("/ai/generate", response_model=AIResponse)
async def generate_specification_agentic(
    request: GenerateSpecRequest, _: None = Depends(handle_exceptions)
):
    """
    Generate complete OpenAPI specification using agentic workflow.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting agentic spec generation",
        extra={
            "correlation_id": correlation_id,
            "domain": request.domain,
            "complexity": request.complexity_level,
            "streaming": request.streaming != StreamingMode.DISABLED,
        },
    )

    try:
        result = await agent_manager.execute_complete_spec_generation(request)
        return result

    except Exception as e:
        logger.error(f"Agentic spec generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "GENERATION_FAILED",
                "message": f"Failed to generate specification: {str(e)}",
            },
        )


@router.post("/ai/workflow/{workflow_name}")
async def execute_predefined_workflow(
    workflow_name: str, input_data: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Execute a predefined workflow with custom input data.
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Executing workflow: {workflow_name}",
        extra={"correlation_id": correlation_id, "workflow": workflow_name},
    )

    try:
        result = await agent_manager.execute_custom_workflow(workflow_name, input_data)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail={"error": "INVALID_WORKFLOW", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "WORKFLOW_FAILED",
                "message": f"Workflow execution failed: {str(e)}",
            },
        )


@router.post("/ai/workflow/custom")
async def execute_custom_workflow(
    workflow_definition: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Execute a custom ad-hoc workflow.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Executing custom workflow",
        extra={
            "correlation_id": correlation_id,
            "workflow_type": workflow_definition.get("workflow_type", "unknown"),
        },
    )

    try:
        result = await agent_manager.execute_ad_hoc_workflow(workflow_definition)
        return result

    except Exception as e:
        logger.error(f"Custom workflow execution failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CUSTOM_WORKFLOW_FAILED",
                "message": f"Custom workflow execution failed: {str(e)}",
            },
        )


@router.get("/ai/workflows")
async def get_available_workflows():
    """
    Get list of available predefined workflows.
    """
    context_stats = context_manager.get_context_statistics()
    return {
        "workflows": agent_manager.get_available_workflows(),
        "timestamp": context_stats.get("timestamp") if context_stats else None,
    }


@router.post("/ai/context/session")
async def create_session(user_id: Optional[str] = None):
    """
    Create a new conversation session.
    """
    session_id = context_manager.create_session(user_id)
    return {
        "session_id": session_id,
        "user_id": user_id,
        "created_at": datetime.utcnow(),
    }


@router.get("/ai/context/session/{session_id}")
async def get_session_summary(session_id: str):
    """
    Get summary of a conversation session.
    """
    try:
        summary = context_manager.get_session_summary(session_id)
        suggestions = context_manager.get_intelligent_suggestions(session_id, None)

        return {"session_summary": summary, "suggestions": suggestions}
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "SESSION_NOT_FOUND",
                "message": f"Session {session_id} not found",
            },
        )


@router.get("/ai/context/statistics")
async def get_context_statistics():
    """
    Get context management statistics.
    """
    return context_manager.get_context_statistics()


@router.post("/ai/prompt/generate")
async def generate_intelligent_prompt(
    request_data: Dict[str, Any], context_id: Optional[str] = None
):
    """
    Generate intelligent prompts using the prompt engine.
    """
    try:
        # Create a mock AIRequest for prompt generation
        ai_request = AIRequest(
            spec_text=request_data.get("spec_text", ""),
            prompt=request_data.get("prompt", ""),
            operation_type=OperationType(request_data.get("operation_type", "modify")),
        )

        system_prompt, user_prompt = prompt_engine.generate_intelligent_prompt(
            ai_request, context_id
        )

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "context_id": context_id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PROMPT_GENERATION_FAILED",
                "message": f"Failed to generate prompt: {str(e)}",
            },
        )


@router.get("/ai/prompt/statistics")
async def get_prompt_statistics():
    """
    Get prompt engine statistics.
    """
    return prompt_engine.get_prompt_statistics()


@router.get("/ai/agents/status")
async def get_agents_status():
    """
    Get status of all AI agents.
    """
    return agent_manager.get_agent_status()


@router.get("/ai/health")
async def health_check():
    """
    Comprehensive health check for all AI services.
    """
    try:
        agent_health = await agent_manager.health_check()
        context_stats = context_manager.get_context_statistics()

        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            uptime_seconds=0,  # TODO: Implement uptime tracking
            dependencies={
                "ollama": "healthy",  # TODO: Check actual Ollama status
                "agents": agent_health["overall_status"],
                "context_manager": "healthy",
            },
            total_requests=context_stats.get("total_conversation_turns", 0),
            average_response_time_ms=context_stats.get("average_response_time", 0.0),
            error_rate=1.0 - context_stats.get("average_success_rate", 1.0),
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy", version=settings.app_version, uptime_seconds=0
        )


# Mock server endpoints (enhanced)
@router.post("/mock/start", response_model=MockStartResponse)
async def start_mock_server(
    request: MockStartRequest, _: None = Depends(handle_exceptions)
):
    """
    Start a mock server with enhanced AI-powered response generation.
    """
    mock_id = str(uuid.uuid4())

    try:
        # Parse and validate the specification
        parser = ResolvingParser(
            spec_string=request.spec_text, backend="openapi-spec-validator"
        )
        MOCKED_APIS[mock_id] = {
            "specification": parser.specification,
            "config": request.model_dump(),
            "created_at": datetime.utcnow(),
        }

        spec_info = parser.specification.get("info", {})
        paths = parser.specification.get("paths", {})

        return MockStartResponse(
            mock_id=mock_id,
            base_url=f"/mock/{mock_id}",
            host=request.host,
            port=request.port or 8000,
            available_endpoints=list(paths.keys()),
            total_endpoints=len(paths),
            created_at=MOCKED_APIS[mock_id]["created_at"],
        )

    except Exception as e:
        logger.error(f"Mock server creation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPEC",
                "message": f"Invalid OpenAPI specification: {str(e)}",
            },
        )


@router.put("/mock/{mock_id}")
async def update_mock_server(
    mock_id: str, request: MockStartRequest, _: None = Depends(handle_exceptions)
):
    """
    Update the specification for an existing mock server.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    try:
        parser = ResolvingParser(
            spec_string=request.spec_text, backend="openapi-spec-validator"
        )
        MOCKED_APIS[mock_id]["specification"] = parser.specification
        MOCKED_APIS[mock_id]["config"] = request.model_dump()

        return {
            "message": f"Mock server {mock_id} updated successfully",
            "updated_at": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Mock server update failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPEC",
                "message": f"Invalid OpenAPI specification: {str(e)}",
            },
        )


@router.get("/mock/{mock_id}")
async def get_mock_server_info(mock_id: str):
    """
    Get information about a mock server.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    mock_data = MOCKED_APIS[mock_id]
    spec_info = mock_data["specification"].get("info", {})

    return {
        "mock_id": mock_id,
        "title": spec_info.get("title", "Untitled API"),
        "version": spec_info.get("version", "1.0.0"),
        "description": spec_info.get("description", "No description"),
        "total_endpoints": len(mock_data["specification"].get("paths", {})),
        "created_at": mock_data.get("created_at"),
        "config": mock_data.get("config", {}),
        "message": "Mock server is running",
        "docs": "Append a valid path from your specification to this URL to get mock responses",
    }


@router.api_route(
    "/mock/{mock_id}/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def handle_mock_request(mock_id: str, full_path: str, request: Request):
    """
    Enhanced mock request handler with AI-powered response generation.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    mock_data = MOCKED_APIS[mock_id]
    spec = mock_data["specification"]
    config = mock_data.get("config", {})
    http_method = request.method.lower()

    # Add artificial delay if configured
    if config.get("response_delay_ms", 0) > 0:
        await asyncio.sleep(config["response_delay_ms"] / 1000)

    # Simulate error rate if configured
    import random

    if random.random() < config.get("error_rate", 0.0):
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SIMULATED_ERROR",
                "message": "Simulated error for testing purposes",
            },
        )

    path_to_lookup = f"/{full_path}"
    path_spec = spec.get("paths", {}).get(path_to_lookup)

    if not path_spec or http_method not in path_spec:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "ENDPOINT_NOT_FOUND",
                "message": f"Endpoint {http_method.upper()} {path_to_lookup} not found in specification",
            },
        )

    operation_spec = path_spec[http_method]

    # Try to get response schema
    try:
        response_schema = operation_spec["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
    except KeyError:
        return JSONResponse(content={"message": "OK"}, status_code=200)

    # Generate AI-powered response if enabled
    if config.get("use_ai_responses", True):
        try:
            # Use MockDataService for proper mock data generation
            mock_response = await mock_data_service.generate_mock_response(
                operation_spec=operation_spec,
                response_schema=response_schema,
                spec_context=spec,
                variation=random.randint(1, config.get("response_variety", 3)),
                use_ai=True,
            )
            return JSONResponse(content=mock_response)

        except Exception as e:
            logger.warning(
                f"AI response generation failed: {str(e)}, falling back to simple response"
            )
            return JSONResponse(content={"message": "OK", "mock_id": mock_id})

    return JSONResponse(content={"message": "OK", "mock_id": mock_id})


# Backward compatibility endpoints
@router.post("/process", response_model=AIResponse)
async def process_specification_legacy(request: AIRequest):
    """Legacy endpoint for backward compatibility."""
    return await process_specification(request)


@router.post("/specifications/generate")
async def generate_specification_legacy(request: GenerateSpecRequest):
    """Legacy endpoint for backward compatibility."""
    return await generate_specification_agentic(request)


@router.post("/ai/meta-analysis", response_model=AIMetaAnalysisResponse)
async def perform_meta_analysis(
    request: AIMetaAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Perform AI meta-analysis on linter findings to detect higher-order patterns.

    This is the "linter-augmented AI analyst" feature. It takes the results from
    deterministic linters and uses AI to find patterns, combinations, and higher-level
    issues that individual linter rules cannot detect.
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Performing meta-analysis with {len(request.errors)} errors, "
        f"{len(request.suggestions)} suggestions",
        extra={
            "correlation_id": correlation_id,
            "error_count": len(request.errors),
            "suggestion_count": len(request.suggestions),
        },
    )

    try:
        result = await meta_analysis_service.analyze(request)

        logger.info(
            f"Meta-analysis completed with {len(result.insights)} insights",
            extra={
                "correlation_id": correlation_id,
                "insight_count": len(result.insights),
                "confidence": result.confidenceScore,
            },
        )

        return result

    except Exception as e:
        logger.error(
            f"Meta-analysis failed: {str(e)}", extra={"correlation_id": correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "META_ANALYSIS_FAILED",
                "message": "Failed to perform meta-analysis",
                "details": {"original_error": str(e)},
            },
        )


@router.post("/ai/analyze-descriptions", response_model=DescriptionAnalysisResponse)
async def analyze_descriptions(
    request: DescriptionAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Analyze description quality using AI.

    This endpoint:
    - Accepts ONLY descriptions + minimal context (NOT entire spec)
    - Analyzes quality (completeness, clarity, accuracy, best practices)
    - Returns quality scores + JSON Patch operations for improvements
    - Batches multiple descriptions in a single LLM call for efficiency
    """
    correlation_id = set_correlation_id()

    logger.info(
        f"Analyzing {len(request.items)} descriptions",
        extra={"correlation_id": correlation_id, "item_count": len(request.items)},
    )

    try:
        result = await description_analysis_service.analyze(request)

        logger.info(
            f"Description analysis completed with overall score: {result.overall_score}",
            extra={
                "correlation_id": correlation_id,
                "overall_score": result.overall_score,
                "patches_count": len(result.patches),
            },
        )

        return result

    except Exception as e:
        logger.error(
            f"Description analysis failed: {str(e)}",
            extra={"correlation_id": correlation_id},
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DESCRIPTION_ANALYSIS_FAILED",
                "message": "Failed to analyze description quality",
                "details": {"original_error": str(e)},
            },
        )


def _get_cache_key(spec_text: str, prompt: str) -> str:
    """Generate cache key for security analysis."""
    content = f"{spec_text}{prompt}"
    return hashlib.md5(content.encode()).hexdigest()


def _is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """Check if cache entry is still valid (1 hour TTL)."""
    if "timestamp" not in cache_entry:
        return False
    cache_time = datetime.fromisoformat(cache_entry["timestamp"])
    return datetime.now() - cache_time < timedelta(hours=1)


@router.post("/ai/analyze/security", response_model=AIResponse)
async def analyze_security(request: AIRequest, _: None = Depends(handle_exceptions)):
    """
    Perform RAG-enhanced security analysis of OpenAPI specifications.
    Retrieves relevant security context from knowledge base and generates comprehensive analysis.
    Includes response caching for better performance.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting security analysis",
        extra={
            "correlation_id": correlation_id,
            "operation_type": "security_analysis",
            "has_spec": bool(request.spec_text),
        },
    )

    try:
        # Check cache first
        cache_key = _get_cache_key(request.spec_text, request.prompt)
        if cache_key in SECURITY_ANALYSIS_CACHE:
            cache_entry = SECURITY_ANALYSIS_CACHE[cache_key]
            if _is_cache_valid(cache_entry):
                logger.info("Returning cached security analysis result")
                return cache_entry["result"]
            else:
                # Remove expired cache entry
                del SECURITY_ANALYSIS_CACHE[cache_key]

        # Get session context
        session_id = (
            str(request.session_id)
            if request.session_id
            else context_manager.create_session(request.user_id)
        )

        # Retrieve relevant security context from RAG knowledge base (limit results for performance)
        security_query = f"Security analysis OpenAPI specification vulnerabilities authentication authorization: {request.spec_text[:300]}"
        context_data = await rag_service.retrieve_security_context(
            security_query, n_results=3
        )

        # Streamlined security analysis prompt for better performance
        context_summary = context_data.get("context", "No additional context available")
        if len(context_summary) > 1000:
            context_summary = context_summary[:1000] + "..."

        enhanced_prompt = f"""Analyze this OpenAPI spec for security vulnerabilities:

CONTEXT: {context_summary}

USER REQUEST: {request.prompt}

FOCUS: Authentication, authorization, input validation, data exposure, rate limiting, HTTPS/TLS, CORS, error handling.

Provide specific, actionable recommendations."""

        # Create enhanced request for LLM processing
        security_request = AIRequest(
            spec_text=request.spec_text,
            prompt=enhanced_prompt,
            operation_type=OperationType.VALIDATE,  # Use validate for analysis
            streaming=request.streaming,
            response_format=request.response_format,
            llm_parameters=request.llm_parameters,
            context=request.context,
            validate_output=False,  # Don't validate since this is analysis, not modification
            user_id=request.user_id,
            session_id=request.session_id,
            tags=request.tags + ["security_analysis", "rag_enhanced"],
        )

        # Process through LLM service
        result = await llm_service.process_ai_request(security_request)

        # Enhance result with RAG metadata
        if hasattr(result, "metadata"):
            result.metadata.update(
                {
                    "rag_sources": context_data.get("sources", []),
                    "rag_relevance_scores": context_data.get("relevance_scores", []),
                    "knowledge_base_available": rag_service.is_available(),
                    "analysis_type": "security_rag_enhanced",
                }
            )

        # Add conversation turn to context
        context_manager.add_conversation_turn(
            session_id, security_request, result, True
        )

        # Cache the result for future requests
        SECURITY_ANALYSIS_CACHE[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Security analysis completed with {len(context_data.get('sources', []))} knowledge sources"
        )

        return result

    except Exception as e:
        logger.error(f"Security analysis failed: {str(e)}")
        if "session_id" in locals():
            context_manager.add_conversation_turn(session_id, request, None, False)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SECURITY_ANALYSIS_FAILED",
                "message": f"Security analysis failed: {str(e)}",
                "rag_available": rag_service.is_available(),
            },
        )


def _generate_explanation_cache_key(rule_id: str, message: str, category: str) -> str:
    """Generate cache key for explanation."""
    key_data = f"{rule_id}:{category}:{message}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached_explanation(
    rule_id: str, message: str, category: str
) -> Optional[Dict[str, Any]]:
    """Get cached explanation if available and not expired."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    cached = EXPLANATION_CACHE.get(cache_key)

    if not cached:
        return None

    # Check if expired
    if datetime.utcnow() - cached["timestamp"] > EXPLANATION_CACHE_TTL:
        del EXPLANATION_CACHE[cache_key]
        return None

    logger.info(f"Returning cached explanation for rule {rule_id}")
    return cached["data"]


def _cache_explanation(rule_id: str, message: str, category: str, data: Dict[str, Any]):
    """Store explanation in cache."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    EXPLANATION_CACHE[cache_key] = {"data": data, "timestamp": datetime.utcnow()}


@router.post("/ai/explain")
async def explain_validation_issue(
    request_data: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Provide detailed AI-powered explanations for validation issues and suggestions.
    Uses RAG to find relevant context and best practices.
    Responses are cached for 24 hours to improve performance.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Generating explanation for validation issue",
        extra={
            "correlation_id": correlation_id,
            "rule_id": request_data.get("rule_id", "unknown"),
            "category": request_data.get("category", "general"),
        },
    )

    try:
        rule_id = request_data.get("rule_id", "")
        message = request_data.get("message", "")
        category = request_data.get("category", "general")

        # Check cache first
        cached_explanation = _get_cached_explanation(rule_id, message, category)
        if cached_explanation:
            return cached_explanation

        spec_text = request_data.get("spec_text", "")
        context = request_data.get("context", {})

        # Create query for RAG knowledge base
        rag_query = f"OpenAPI best practices validation {rule_id} {category} {message}"

        # Retrieve relevant context from knowledge base
        context_data = await rag_service.retrieve_security_context(
            rag_query, n_results=3
        )

        # Build comprehensive explanation prompt
        knowledge_context = context_data.get(
            "context", "No additional context available"
        )
        if len(knowledge_context) > 800:
            knowledge_context = knowledge_context[:800] + "..."

        explanation_prompt = f"""You are an OpenAPI expert. Explain this validation issue concisely and professionally.

VALIDATION ISSUE:
- Rule: {rule_id}
- Category: {category}
- Message: {message}
- Context: {json.dumps(context, indent=2) if context else "None"}

KNOWLEDGE BASE:
{knowledge_context}

SPEC EXCERPT:
{spec_text[:500] if spec_text else "No specification provided"}

INSTRUCTIONS:
1. Provide a clear explanation of why this is an issue (2-3 sentences)
2. List 2-3 related best practices
3. Provide 1-2 specific example solutions
4. Suggest relevant resources (optional)

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON.

{{
  "explanation": "Brief explanation of the issue and its impact",
  "severity": "info",
  "related_best_practices": [
    "First best practice",
    "Second best practice"
  ],
  "example_solutions": [
    "First solution approach",
    "Second solution approach"
  ],
  "additional_resources": [
    "Resource 1",
    "Resource 2"
  ]
}}"""

        # Use direct LLM call instead of process_ai_request for text generation
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an OpenAPI expert. Always respond with valid JSON only, no additional text.",
                },
                {"role": "user", "content": explanation_prompt},
            ],
            "stream": False,
            "format": "json",  # Force JSON output
            "options": {"temperature": 0.3, "num_predict": 2048},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"LLM request failed: {response.status_code} - {response.text}",
            )

        # Extract response text
        response_data = response.json()
        llm_response = response_data.get("message", {}).get("content", "").strip()

        # Log raw response for debugging
        logger.debug(f"Raw LLM response: {llm_response[:200]}...")

        # Try to parse structured response, fallback to plain text
        structured_response = None
        try:
            # Try to extract JSON from response (in case LLM includes extra text)
            json_start = llm_response.find("{")
            json_end = llm_response.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]

                # Clean up common JSON issues
                import re

                # Fix trailing commas in arrays and objects
                json_str = re.sub(r",\s*]", "]", json_str)
                json_str = re.sub(r",\s*}", "}", json_str)

                # Fix missing commas between array elements
                json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)

                # Try to parse
                structured_response = json.loads(json_str)

                if not isinstance(structured_response, dict):
                    raise ValueError("Response is not a dictionary")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                f"Failed to parse JSON: {str(e)}, attempting manual extraction"
            )

            # Try manual extraction as last resort
            try:
                import re

                structured_response = {
                    "explanation": "",
                    "severity": "info",
                    "related_best_practices": [],
                    "example_solutions": [],
                    "additional_resources": [],
                }

                # Extract explanation - handle multiline and escaped quotes
                expl_match = re.search(
                    r'"explanation"\s*:\s*"((?:[^"\\]|\\["\\])*)"',
                    llm_response,
                    re.DOTALL,
                )
                if expl_match:
                    structured_response["explanation"] = (
                        expl_match.group(1).replace('\\"', '"').replace("\\n", "\n")
                    )

                # Extract severity
                sev_match = re.search(r'"severity"\s*:\s*"(\w+)"', llm_response)
                if sev_match:
                    structured_response["severity"] = sev_match.group(1)

                # Extract arrays
                def extract_array(field_name):
                    array_match = re.search(
                        rf'"{field_name}"\s*:\s*\[(.*?)\]', llm_response, re.DOTALL
                    )
                    if array_match:
                        items_str = array_match.group(1)
                        # Extract quoted strings
                        items = re.findall(r'"((?:[^"\\]|\\.)*)"', items_str)
                        return [item.replace('\\"', '"') for item in items]
                    return []

                structured_response["related_best_practices"] = extract_array(
                    "related_best_practices"
                )
                structured_response["example_solutions"] = extract_array(
                    "example_solutions"
                )
                structured_response["additional_resources"] = extract_array(
                    "additional_resources"
                )

                # If we couldn't extract explanation, use the whole response
                if not structured_response["explanation"]:
                    structured_response["explanation"] = llm_response

            except Exception as inner_e:
                logger.error(f"Manual extraction also failed: {str(inner_e)}")
                # Last resort - just use the raw text
                structured_response = {
                    "explanation": llm_response,
                    "severity": "info",
                    "related_best_practices": [],
                    "example_solutions": [],
                    "additional_resources": [],
                }

        # Build final response
        if structured_response:
            explanation_response = {
                "explanation": structured_response.get(
                    "explanation", "Unable to generate explanation"
                ),
                "severity": structured_response.get("severity", "info"),
                "category": category,
                "related_best_practices": structured_response.get(
                    "related_best_practices", []
                ),
                "example_solutions": structured_response.get("example_solutions", []),
                "additional_resources": structured_response.get(
                    "additional_resources", []
                ),
                "metadata": {
                    "rule_id": rule_id,
                    "rag_sources": context_data.get("sources", []),
                    "knowledge_base_available": rag_service.is_available(),
                    "generated_at": datetime.utcnow().isoformat(),
                },
            }
        else:
            # Complete fallback
            logger.warning("Using complete fallback for explanation")
            explanation_response = {
                "explanation": (
                    llm_response if llm_response else "Unable to generate explanation"
                ),
                "severity": "info",
                "category": category,
                "related_best_practices": [],
                "example_solutions": [],
                "additional_resources": [],
                "metadata": {
                    "rule_id": rule_id,
                    "rag_sources": context_data.get("sources", []),
                    "knowledge_base_available": rag_service.is_available(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback_format": True,
                },
            }

        # Cache the explanation
        _cache_explanation(rule_id, message, category, explanation_response)

        logger.info(f"Generated explanation for rule {rule_id}")
        return explanation_response

    except Exception as e:
        logger.error(f"Explanation generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "EXPLANATION_FAILED",
                "message": f"Failed to generate explanation: {str(e)}",
                "rag_available": rag_service.is_available(),
            },
        )


@router.get("/ai/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for explanations.
    """
    # Clean up expired entries
    expired_count = 0
    now = datetime.utcnow()
    expired_keys = [
        key
        for key, value in EXPLANATION_CACHE.items()
        if now - value["timestamp"] > EXPLANATION_CACHE_TTL
    ]

    for key in expired_keys:
        del EXPLANATION_CACHE[key]
        expired_count += 1

    return {
        "cache_size": len(EXPLANATION_CACHE),
        "expired_entries_cleaned": expired_count,
        "ttl_hours": EXPLANATION_CACHE_TTL.total_seconds() / 3600,
        "timestamp": now.isoformat(),
    }


@router.delete("/ai/cache/clear")
async def clear_explanation_cache():
    """
    Clear all cached explanations.
    """
    cache_size = len(EXPLANATION_CACHE)
    EXPLANATION_CACHE.clear()
    logger.info(f"Cleared {cache_size} cached explanations")

    return {
        "success": True,
        "cleared_entries": cache_size,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ai/rag/status")
async def get_rag_status():
    """
    Get status and statistics of the RAG knowledge base.
    """
    try:
        stats = await rag_service.get_knowledge_base_stats()
        return {"rag_service": stats, "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error(f"Failed to get RAG status: {str(e)}")
        return {
            "rag_service": {"available": False, "error": str(e)},
            "timestamp": datetime.utcnow(),
        }


@router.post("/ai/test-cases/generate")
async def generate_test_cases(
    request_data: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate comprehensive test cases for API operations using AI.
    Creates both positive and negative test scenarios with realistic data.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Generating test cases for API operation",
        extra={
            "correlation_id": correlation_id,
            "operation": request_data.get("operation_summary", "unknown"),
        },
    )

    try:
        spec_text = request_data.get("spec_text", "")
        operation_path = request_data.get("path", "")
        operation_method = request_data.get("method", "")
        operation_summary = request_data.get("operation_summary", "")
        test_types = request_data.get(
            "test_types", ["positive", "negative", "edge_cases"]
        )

        # Build comprehensive test generation prompt
        test_generation_prompt = f"""Generate comprehensive test cases for this API operation:

OPERATION: {operation_method.upper()} {operation_path}
SUMMARY: {operation_summary}

SPECIFICATION EXCERPT:
{spec_text[:1000] if spec_text else "No specification provided"}

TEST TYPES TO GENERATE: {', '.join(test_types)}

Generate test cases as a JSON array with the following structure:
{{
  "test_cases": [
    {{
      "name": "descriptive test name",
      "type": "positive|negative|edge_case",
      "description": "what this test validates",
      "request": {{
        "method": "HTTP_METHOD",
        "path": "/api/path",
        "headers": {{}},
        "query_params": {{}},
        "body": {{}}
      }},
      "expected_response": {{
        "status_code": 200,
        "headers": {{}},
        "body": {{}}
      }},
      "assertions": [
        "Response status should be 200",
        "Response should contain valid data"
      ]
    }}
  ]
}}

REQUIREMENTS:
1. Generate 5-10 test cases covering different scenarios
2. Include realistic test data
3. Cover validation failures, authentication issues, and success cases
4. Include edge cases like empty inputs, large inputs, special characters
5. Specify clear assertions for each test
6. Use appropriate HTTP status codes
7. Consider the operation's purpose and constraints

Return only the JSON structure, no explanations."""

        # Create AI request for test generation
        ai_request = AIRequest(
            spec_text=spec_text,
            prompt=test_generation_prompt,
            operation_type=OperationType.GENERATE,
            streaming=StreamingMode.DISABLED,
            llm_parameters=LLMParameters(
                temperature=0.4, max_tokens=3000  # Moderate creativity for test variety
            ),
            validate_output=False,
            tags=["test_generation", "quality_assurance"],
        )

        # Get test cases from LLM
        result = await llm_service.process_ai_request(ai_request)

        # Try to parse the JSON response
        try:
            test_cases_data = json.loads(result.updated_spec_text)
            if (
                not isinstance(test_cases_data, dict)
                or "test_cases" not in test_cases_data
            ):
                raise ValueError("Invalid test cases format")

            # Enhance test cases with additional metadata
            enhanced_test_cases = []
            for i, test_case in enumerate(test_cases_data["test_cases"]):
                enhanced_test_case = {
                    **test_case,
                    "id": f"test_{i+1}",
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                    "priority": _get_test_priority(test_case.get("type", "positive")),
                    "estimated_execution_time": "< 1s",
                }
                enhanced_test_cases.append(enhanced_test_case)

            response = {
                "test_cases": enhanced_test_cases,
                "summary": {
                    "total_tests": len(enhanced_test_cases),
                    "positive_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "positive"
                        ]
                    ),
                    "negative_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "negative"
                        ]
                    ),
                    "edge_case_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "edge_case"
                        ]
                    ),
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered",
                    "llm_model": "mistral",
                    "test_framework_compatible": [
                        "jest",
                        "postman",
                        "newman",
                        "python-requests",
                    ],
                },
            }

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse structured test cases: {str(e)}")
            # Fallback: create a simple test case from the text response
            fallback_test_case = {
                "id": "test_1",
                "name": f"Basic test for {operation_method.upper()} {operation_path}",
                "type": "positive",
                "description": "Generated test case",
                "request": {
                    "method": operation_method.upper(),
                    "path": operation_path,
                    "headers": {"Content-Type": "application/json"},
                    "body": {},
                },
                "expected_response": {"status_code": 200, "body": {}},
                "assertions": ["Response status should be successful"],
                "operation": f"{operation_method.upper()} {operation_path}",
                "generated_at": datetime.utcnow().isoformat(),
                "priority": "medium",
                "notes": "Fallback test case - original AI response was not parseable",
            }

            response = {
                "test_cases": [fallback_test_case],
                "summary": {
                    "total_tests": 1,
                    "positive_tests": 1,
                    "negative_tests": 0,
                    "edge_case_tests": 0,
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback_mode": True,
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered_fallback",
                    "original_response": result.updated_spec_text[:500],
                },
            }

        logger.info(
            f"Generated {len(response['test_cases'])} test cases for {operation_method.upper()} {operation_path}"
        )
        return response

    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_GENERATION_FAILED",
                "message": f"Failed to generate test cases: {str(e)}",
                "operation": f"{request_data.get('method', '')} {request_data.get('path', '')}",
            },
        )


def _get_test_priority(test_type: str) -> str:
    """Determine test priority based on test type."""
    priority_map = {"positive": "high", "negative": "medium", "edge_case": "low"}
    return priority_map.get(test_type, "medium")


@router.post("/ai/test-suite/generate")
async def generate_test_suite(
    request_data: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate a complete test suite for an entire API specification.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Generating complete test suite",
        extra={
            "correlation_id": correlation_id,
            "spec_size": len(request_data.get("spec_text", "")),
        },
    )

    try:
        spec_text = request_data.get("spec_text", "")
        test_options = request_data.get("options", {})

        if not spec_text:
            raise ValueError("OpenAPI specification is required")

        # Parse the specification to extract operations
        try:
            from prance import ResolvingParser

            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
        except Exception as e:
            raise ValueError(f"Invalid OpenAPI specification: {str(e)}")

        # Extract all operations
        operations = []
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "options",
                    "head",
                ]:
                    operations.append(
                        {
                            "path": path,
                            "method": method,
                            "summary": operation.get(
                                "summary", f"{method.upper()} {path}"
                            ),
                            "operation_id": operation.get(
                                "operationId", f'{method}_{path.replace("/", "_")}'
                            ),
                        }
                    )

        # Generate test cases for each operation
        all_test_cases = []
        for operation in operations[
            :10
        ]:  # Limit to first 10 operations for performance
            try:
                operation_request = {
                    "spec_text": spec_text,
                    "path": operation["path"],
                    "method": operation["method"],
                    "operation_summary": operation["summary"],
                    "test_types": test_options.get(
                        "test_types", ["positive", "negative"]
                    ),
                }

                # Generate test cases for this operation
                operation_tests = await generate_test_cases(operation_request)

                # Add operation context to each test case
                for test_case in operation_tests["test_cases"]:
                    test_case["operation_id"] = operation["operation_id"]
                    all_test_cases.append(test_case)

            except Exception as e:
                logger.warning(
                    f"Failed to generate tests for {operation['method']} {operation['path']}: {str(e)}"
                )

        # Organize test suite
        test_suite = {
            "test_suite": {
                "name": f"API Test Suite - {spec.get('info', {}).get('title', 'Unknown API')}",
                "version": spec.get("info", {}).get("version", "1.0.0"),
                "description": f"Comprehensive test suite generated for {len(operations)} operations",
                "test_cases": all_test_cases,
                "collections": _organize_tests_by_collection(all_test_cases),
                "statistics": {
                    "total_operations": len(operations),
                    "total_tests": len(all_test_cases),
                    "coverage": f"{min(len(operations), 10)}/{len(operations)} operations",
                    "test_types": {
                        "positive": len(
                            [
                                tc
                                for tc in all_test_cases
                                if tc.get("type") == "positive"
                            ]
                        ),
                        "negative": len(
                            [
                                tc
                                for tc in all_test_cases
                                if tc.get("type") == "negative"
                            ]
                        ),
                        "edge_cases": len(
                            [
                                tc
                                for tc in all_test_cases
                                if tc.get("type") == "edge_case"
                            ]
                        ),
                    },
                },
            },
            "execution_plan": {
                "recommended_order": ["positive", "negative", "edge_case"],
                "parallel_execution": True,
                "estimated_duration": f"{len(all_test_cases) * 2}s",
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id,
                "generation_method": "ai_powered_suite",
            },
        }

        logger.info(
            f"Generated complete test suite with {len(all_test_cases)} test cases for {len(operations)} operations"
        )
        return test_suite

    except Exception as e:
        logger.error(f"Test suite generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_SUITE_GENERATION_FAILED",
                "message": f"Failed to generate test suite: {str(e)}",
            },
        )


def _organize_tests_by_collection(test_cases: List[Dict]) -> Dict[str, List[Dict]]:
    """Organize test cases into logical collections."""
    collections = {}

    for test_case in test_cases:
        # Group by operation method
        method = test_case.get("request", {}).get("method", "unknown")
        collection_name = f"{method.upper()} Operations"

        if collection_name not in collections:
            collections[collection_name] = []

        collections[collection_name].append(test_case)

    return collections


# ================================================================================
# Security Analysis Endpoints
# ================================================================================


def _generate_security_cache_key(spec_text: str) -> str:
    """Generate cache key from spec content hash."""
    return hashlib.sha256(spec_text.encode()).hexdigest()[:16]


def _get_cached_security_report(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve cached security report if not expired."""
    if cache_key in SECURITY_ANALYSIS_CACHE:
        cached = SECURITY_ANALYSIS_CACHE[cache_key]
        if datetime.utcnow() < cached["expires_at"]:
            logger.info(f"Security report cache hit: {cache_key}")
            return cached["report"]
        else:
            # Remove expired entry
            del SECURITY_ANALYSIS_CACHE[cache_key]
            logger.info(f"Security report cache expired: {cache_key}")
    return None


def _cache_security_report(cache_key: str, report: Dict[str, Any]):
    """Store security report in cache with TTL."""
    SECURITY_ANALYSIS_CACHE[cache_key] = {
        "report": report,
        "cached_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL,
    }
    logger.info(f"Cached security report: {cache_key}")


@router.post("/ai/security/analyze", response_model=Dict[str, Any])
async def analyze_security(
    request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Comprehensive security analysis of OpenAPI specification.

    Runs multi-agent security analysis workflow covering:
    - Authentication mechanisms
    - Authorization controls (RBAC, BOLA, BFLA)
    - Data exposure and PII protection
    - OWASP API Security Top 10 compliance

    Returns detailed security report with findings, recommendations, and overall security score.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting comprehensive security analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Check cache first
        cache_key = _generate_security_cache_key(request.spec_text)

        if not request.force_refresh:
            cached_report = _get_cached_security_report(cache_key)
            if cached_report:
                return {
                    "cached": True,
                    "report": cached_report,
                    "correlation_id": correlation_id,
                }

        # Convert validation suggestions to dict format if provided
        validation_suggestions_dict = None
        if request.validation_suggestions:
            validation_suggestions_dict = [
                {
                    "rule_id": s.rule_id,
                    "message": s.message,
                    "severity": s.severity,
                    "path": s.path,
                    "category": s.category,
                }
                for s in request.validation_suggestions
            ]

        # Run security analysis workflow
        report = await security_workflow.analyze(
            request.spec_text, validation_suggestions=validation_suggestions_dict
        )

        # Convert to dict for response
        report_dict = report.model_dump()

        # Cache the report
        _cache_security_report(cache_key, report_dict)

        logger.info(
            f"Security analysis complete. Score: {report.overall_score:.1f}, Risk: {report.risk_level.value}",
            extra={
                "correlation_id": correlation_id,
                "overall_score": report.overall_score,
                "risk_level": report.risk_level.value,
                "total_issues": len(report.all_issues),
            },
        )

        return {
            "cached": False,
            "report": report_dict,
            "correlation_id": correlation_id,
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in spec: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPEC_FORMAT",
                "message": "Invalid OpenAPI specification format",
                "details": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Security analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SECURITY_ANALYSIS_FAILED",
                "message": f"Failed to analyze security: {str(e)}",
            },
        )


@router.post("/ai/security/analyze/authentication")
async def analyze_authentication(
    request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Authentication-only security analysis.

    Analyzes authentication mechanisms including:
    - Security schemes (OAuth2, API Key, Basic Auth)
    - Authentication weaknesses
    - Unprotected endpoints
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting authentication analysis", extra={"correlation_id": correlation_id}
    )

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import AuthenticationAnalyzer

        analyzer = AuthenticationAnalyzer()
        result = await analyzer.analyze(spec)

        return {"analysis": result.model_dump(), "correlation_id": correlation_id}

    except Exception as e:
        logger.error(f"Authentication analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHENTICATION_ANALYSIS_FAILED",
                "message": f"Failed to analyze authentication: {str(e)}",
            },
        )


@router.post("/ai/security/analyze/authorization")
async def analyze_authorization(
    request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Authorization-only security analysis.

    Analyzes authorization controls including:
    - RBAC implementation
    - Broken Object Level Authorization (BOLA)
    - Broken Function Level Authorization (BFLA)
    - Protected vs unprotected endpoints
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting authorization analysis", extra={"correlation_id": correlation_id}
    )

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import AuthorizationAnalyzer

        analyzer = AuthorizationAnalyzer()
        result = await analyzer.analyze(spec)

        return {"analysis": result.model_dump(), "correlation_id": correlation_id}

    except Exception as e:
        logger.error(f"Authorization analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHORIZATION_ANALYSIS_FAILED",
                "message": f"Failed to analyze authorization: {str(e)}",
            },
        )


@router.post("/ai/security/analyze/data-exposure")
async def analyze_data_exposure(
    request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)
):
    """
    Data exposure and PII protection analysis.

    Analyzes data security including:
    - PII field detection
    - Sensitive data exposure
    - Password field protection
    - HTTPS enforcement
    - Excessive data exposure
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Starting data exposure analysis", extra={"correlation_id": correlation_id}
    )

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import DataExposureAnalyzer

        analyzer = DataExposureAnalyzer()
        result = await analyzer.analyze(spec)

        return {"analysis": result.model_dump(), "correlation_id": correlation_id}

    except Exception as e:
        logger.error(f"Data exposure analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "DATA_EXPOSURE_ANALYSIS_FAILED",
                "message": f"Failed to analyze data exposure: {str(e)}",
            },
        )


@router.get("/ai/security/report/{spec_hash}")
async def get_security_report(spec_hash: str):
    """
    Retrieve cached security analysis report by spec hash.

    Returns cached report if available, otherwise 404.
    """
    logger.info(f"Retrieving cached security report: {spec_hash}")

    cached_report = _get_cached_security_report(spec_hash)

    if cached_report:
        return {"cached": True, "report": cached_report, "spec_hash": spec_hash}
    else:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "REPORT_NOT_FOUND",
                "message": f"No cached security report found for hash: {spec_hash}",
            },
        )


# ===========================
# JSON Patch Generation (RFC 6902)
# ===========================


@router.post("/ai/patch/generate", response_model=PatchGenerationResponse)
async def generate_json_patch(request: PatchGenerationRequest):
    """
    Generate JSON Patch (RFC 6902) operations for a specific fix.

    This endpoint uses LLM to generate precise patch operations instead of
    regenerating the entire spec, improving accuracy and token efficiency.

    The generated patches can be applied by the backend using standard JSON Patch libraries.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(f"Generating JSON Patch for rule: {request.rule_id}")

    try:
        # Parse the spec
        spec_dict = json.loads(request.spec_text)

        # Generate patch using LLM
        patch_response = await patch_generator.generate_patch(
            spec=spec_dict,
            rule_id=request.rule_id,
            context=request.context,
            suggestion_message=request.suggestion_message,
        )

        logger.info(
            f"Generated {len(patch_response.patches)} patch operations "
            f"with confidence {patch_response.confidence}"
        )

        return patch_response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON spec: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_JSON",
                "message": f"Invalid JSON specification: {str(e)}",
            },
        )
    except Exception as e:
        logger.error(f"Patch generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PATCH_GENERATION_FAILED",
                "message": f"Failed to generate patch: {str(e)}",
            },
        )


@router.post("/ai/patch/apply", response_model=PatchApplicationResponse)
async def apply_patch(request: PatchApplicationRequest):
    """
    Apply JSON Patch operations to a specification.

    This is a utility endpoint for testing. In production, the backend
    (Spring Boot) should apply patches using its own JSON Patch library.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(f"Applying {len(request.patches)} patch operations")

    try:
        # Parse the spec
        spec_dict = json.loads(request.spec_text)

        # Apply patches
        result = await apply_json_patch(spec_dict, request.patches)

        validation_errors = []
        if request.validate_after and result["success"]:
            # Validate the patched spec
            try:
                spec_json = json.dumps(result["result"])
                parser = ResolvingParser(spec_string=spec_json)
                logger.info("Patched spec is valid")
            except Exception as e:
                validation_errors.append(f"Validation failed: {str(e)}")

        return PatchApplicationResponse(
            success=result["success"],
            updated_spec=result["result"] if result["success"] else None,
            errors=result["errors"],
            validation_errors=validation_errors,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON spec: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_JSON",
                "message": f"Invalid JSON specification: {str(e)}",
            },
        )
    except Exception as e:
        logger.error(f"Patch application failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PATCH_APPLICATION_FAILED",
                "message": f"Failed to apply patch: {str(e)}",
            },
        )


@router.post("/ai/fix/smart", response_model=SmartAIFixResponse)
async def smart_ai_fix(request: SmartAIFixRequest):
    """
    Smart AI fix that intelligently chooses between JSON patches and full spec regeneration.

    This endpoint optimizes performance by:
    - Using JSON patches for targeted fixes (faster, more accurate)
    - Using full regeneration only when necessary (broad changes)

    The decision is made based on:
    - Prompt analysis (targeted vs broad)
    - Target scope (specific operation vs entire spec)
    - Spec size (small specs can regenerate quickly)
    - Validation errors (targeted fixes use patches)

    Performance comparison:
    - Patch mode: ~2-5 seconds, ~100-500 tokens
    - Full regen: ~10-30 seconds, ~2000-8000 tokens
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(f"Smart AI fix request: {request.prompt[:100]}...")

    try:
        response = await smart_fix_service.process_smart_fix(request)

        logger.info(
            f"Smart fix completed using {response.method_used} method in "
            f"{response.processing_time_ms:.0f}ms ({response.token_count} tokens)"
        )

        return response

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400, detail={"error": "INVALID_REQUEST", "message": str(e)}
        )
    except Exception as e:
        logger.error(f"Smart fix failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SMART_FIX_FAILED",
                "message": f"Failed to process smart fix: {str(e)}",
            },
        )


@router.get("/ai/security/cache/stats")
async def get_security_cache_stats():
    """
    Get security analysis cache statistics.

    Returns information about cached reports and cache performance.
    """
    total_cached = len(SECURITY_ANALYSIS_CACHE)

    valid_count = 0
    expired_count = 0

    for cache_key, cached_data in SECURITY_ANALYSIS_CACHE.items():
        if datetime.utcnow() < cached_data["expires_at"]:
            valid_count += 1
        else:
            expired_count += 1

    return {
        "total_entries": total_cached,
        "valid_entries": valid_count,
        "expired_entries": expired_count,
        "ttl_hours": SECURITY_CACHE_TTL.total_seconds() / 3600,
        "cache_details": [
            {
                "spec_hash": key,
                "cached_at": data["cached_at"].isoformat(),
                "expires_at": data["expires_at"].isoformat(),
                "expired": datetime.utcnow() >= data["expires_at"],
                "overall_score": data["report"].get("overall_score"),
                "risk_level": data["report"].get("risk_level"),
            }
            for key, data in SECURITY_ANALYSIS_CACHE.items()
        ],
    }


@router.delete("/ai/security/cache/clear")
async def clear_security_cache():
    """
    Clear all cached security analysis reports.

    Useful for forcing fresh analysis or clearing memory.
    """
    cache_size = len(SECURITY_ANALYSIS_CACHE)
    SECURITY_ANALYSIS_CACHE.clear()

    logger.info(f"Cleared security analysis cache ({cache_size} entries)")

    return {
        "cleared": cache_size,
        "message": f"Cleared {cache_size} cached security report(s)",
    }


# ============================================================================
# Advanced Security: Attack Path Simulation
# ============================================================================


@router.post("/ai/security/attack-path-simulation")
async def run_attack_path_simulation(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    **The "Wow" Feature: AI Attack Path Simulation**

    Think like a hacker. This endpoint uses an agentic AI system to discover
    multi-step attack chains that real attackers could exploit. Unlike simple
    linting that finds isolated vulnerabilities, this feature:

    1. Finds individual vulnerabilities (Scanner Agent)
    2. Analyzes how they can be CHAINED together (Threat Modeling Agent)
    3. Generates executive-level security reports (Reporter Agent)

    **Example Attack Chain:**
    - Step 1: GET /users/{id} exposes sensitive 'role' field (Information Disclosure)
    - Step 2: PUT /users/{id} accepts 'role' in request body (Mass Assignment)
    - Result: Any user can escalate to admin privileges!

    **Request Body:**
    {
        "spec_text": "OpenAPI spec (JSON or YAML string)",
        "analysis_depth": "quick | standard | comprehensive | exhaustive",
        "max_chain_length": 5,  // Maximum steps in an attack chain
        "exclude_low_severity": false  // Skip low-severity chains
    }

    **Response:**
    {
        "report_id": "uuid",
        "risk_level": "CRITICAL | HIGH | MEDIUM | LOW",
        "overall_security_score": 0-100,
        "executive_summary": "Business-focused summary",
        "critical_chains": [...],  // CRITICAL attack chains
        "high_priority_chains": [...],  // HIGH severity chains
        "all_chains": [...],  // All discovered attack chains
        "top_3_risks": [...],  // Simplified explanations
        "immediate_actions": [...],  // Fix right now
        "short_term_actions": [...],  // Fix within 1-2 weeks
        "long_term_actions": [...]  // Architectural improvements
    }

    **Attack Chain Structure:**
    Each chain contains:
    - name: Descriptive attack name
    - attack_goal: What attacker achieves
    - severity: CRITICAL | HIGH | MEDIUM | LOW
    - complexity: How hard to execute
    - steps: Ordered list of exploitation steps
    - business_impact: Impact in business terms
    - remediation_steps: How to fix
    """
    from ..schemas.attack_path_schemas import AttackPathAnalysisRequest
    from ..services.agents.attack_path_orchestrator import AttackPathOrchestrator

    correlation_id = set_correlation_id()
    logger.info(
        "Starting attack path simulation", extra={"correlation_id": correlation_id}
    )

    try:
        # Parse and validate request
        spec_text = request.get("spec_text")
        if not spec_text:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_SPEC", "message": "spec_text is required"},
            )

        # Build analysis request
        analysis_request = AttackPathAnalysisRequest(
            spec_text=spec_text,
            analysis_depth=request.get("analysis_depth", "standard"),
            max_chain_length=request.get("max_chain_length", 5),
            exclude_low_severity=request.get("exclude_low_severity", False),
            focus_areas=request.get("focus_areas", []),
        )

        # Check cache first
        spec_hash = hashlib.sha256(spec_text.encode()).hexdigest()
        cache_key = f"attack_path_{spec_hash}_{analysis_request.analysis_depth}"

        if cache_key in SECURITY_ANALYSIS_CACHE:
            cached_data = SECURITY_ANALYSIS_CACHE[cache_key]
            if datetime.utcnow() < cached_data["expires_at"]:
                logger.info(f"Returning cached attack path report: {cache_key}")
                return cached_data["report"]

        # Run attack path simulation
        orchestrator = AttackPathOrchestrator(llm_service)
        report = await orchestrator.run_attack_path_analysis(analysis_request)

        # Convert to dict for response
        report_dict = report.model_dump()

        # Cache the report
        SECURITY_ANALYSIS_CACHE[cache_key] = {
            "report": report_dict,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL,
        }
        logger.info(f"Cached attack path report: {cache_key}")

        return report_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attack path simulation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ATTACK_PATH_SIMULATION_FAILED",
                "message": f"Failed to run attack path simulation: {str(e)}",
            },
        )


@router.post("/ai/security/attack-path-findings")
async def analyze_attack_chains_from_findings(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    **The "Linter-Augmented AI Analyst" - Attack Path Analysis from Findings**

    This endpoint implements the CORRECT, PROFESSIONAL approach to AI-powered security analysis:

    **The Problem with "On the Go" AI:**
    - Sending a 5MB spec to the AI on every run is SLOW and EXPENSIVE
    - LLMs are not 100% accurate at graph traversal
    - Wastes computational resources re-discovering the same facts

    **Our Solution (The Right Way):**
    1. Java extracts FACTUAL findings deterministically (100% accurate, blazing fast)
    2. Only those facts are sent to the AI (tiny payload, not 5MB)
    3. AI reasons about attack chains based on pre-processed facts

    **Request Body:**
    {
        "findings": [
            {
                "type": "PUBLIC_ENDPOINT",
                "endpoint": "GET /users/all",
                "description": "Endpoint GET /users/all has no security requirements",
                "metadata": {"method": "GET", "path": "/users/all"}
            },
            {
                "type": "ENDPOINT_RETURNS_SCHEMA",
                "endpoint": "GET /users/all",
                "description": "Endpoint GET /users/all returns schema 'User'",
                "metadata": {"schema": "User", "fields": ["id", "name", "role"]}
            },
            {
                "type": "SENSITIVE_FIELD",
                "description": "Schema 'User' contains sensitive field 'role'",
                "metadata": {"schema": "User", "field": "role"}
            },
            {
                "type": "ENDPOINT_ACCEPTS_SCHEMA",
                "endpoint": "PUT /users/{id}",
                "description": "Endpoint PUT /users/{id} accepts schema 'User'",
                "metadata": {"schema": "User", "fields": ["id", "name", "role"]}
            }
        ],
        "analysis_depth": "standard",
        "max_chain_length": 5,
        "exclude_low_severity": false
    }

    **AI's Analysis (What We Want It To Do):**
    "Critical Vulnerability Found: Privilege Escalation via Mass Assignment.

    Attack Chain:
    1. Attacker calls public GET /users/all (Finding 1)
    2. Attacker obtains User schema structure including 'role' field (Findings 2 & 3)
    3. Attacker modifies their user object, setting role=admin
    4. Attacker calls PUT /users/{id} with modified User object (Finding 4)
    5. Result: Privilege escalation to admin"

    **Response:** Same as /attack-path-simulation endpoint
    """
    correlation_id = set_correlation_id()
    logger.info(
        "Starting attack path analysis from findings",
        extra={"correlation_id": correlation_id},
    )

    try:
        # Parse and validate request
        findings = request.get("findings")
        if not findings or not isinstance(findings, list):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_FINDINGS",
                    "message": "findings list is required",
                },
            )

        analysis_depth = request.get("analysis_depth", "standard")
        max_chain_length = request.get("max_chain_length", 5)
        exclude_low_severity = request.get("exclude_low_severity", False)

        # Build prompt for AI to analyze attack chains
        findings_text = _format_findings_for_prompt(findings)

        # Check cache
        findings_hash = hashlib.sha256(
            json.dumps(findings, sort_keys=True).encode()
        ).hexdigest()
        cache_key = f"attack_path_findings_{findings_hash}_{analysis_depth}"

        if cache_key in SECURITY_ANALYSIS_CACHE:
            cached_data = SECURITY_ANALYSIS_CACHE[cache_key]
            if datetime.utcnow() < cached_data["expires_at"]:
                logger.info(
                    f"Returning cached findings-based attack path report: {cache_key}"
                )
                return cached_data["report"]

        # Use AI to reason about attack chains
        report = await _analyze_attack_chains_with_ai(
            findings_text,
            analysis_depth,
            max_chain_length,
            exclude_low_severity,
            findings,
        )

        # Add statistics and metadata
        report = _enrich_report_with_statistics(report, findings)

        # Cache the report
        SECURITY_ANALYSIS_CACHE[cache_key] = {
            "report": report,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL,
        }
        logger.info(f"Cached findings-based attack path report: {cache_key}")

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Findings-based attack path analysis failed: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "FINDINGS_ANALYSIS_FAILED",
                "message": f"Failed to analyze attack chains from findings: {str(e)}",
            },
        )


def _enrich_report_with_statistics(
    report: Dict[str, Any], findings: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Enrich the attack path report with statistics and structured data for the UI.

    Adds:
    - total_chains_found: Number of attack chains discovered
    - total_vulnerabilities: Total number of findings analyzed
    - vulnerabilities_in_chains: Findings referenced in attack chains
    - isolated_vulnerabilities: Findings not part of any chain
    - Structured step data with endpoints parsed
    """

    # Count chains
    all_chains = report.get("attack_chains", [])
    report["total_chains_found"] = len(all_chains)

    # Total findings
    report["total_vulnerabilities"] = len(findings)

    # Find which findings are used in chains
    findings_in_chains = set()
    for chain in all_chains:
        finding_refs = chain.get("finding_refs", [])
        findings_in_chains.update(finding_refs)

    report["vulnerabilities_in_chains"] = len(findings_in_chains)
    report["isolated_vulnerabilities"] = len(findings) - len(findings_in_chains)

    # Parse steps to extract endpoint information for UI
    for idx, chain in enumerate(all_chains):
        # Add unique chain ID for UI
        if "chain_id" not in chain:
            chain["chain_id"] = f"chain-{idx + 1}"

        # Add defaults for UI
        if "likelihood" not in chain:
            chain["likelihood"] = 0.7  # Default moderate likelihood
        if "attacker_profile" not in chain:
            chain["attacker_profile"] = "Authenticated User"
        if "endpoints_involved" not in chain:
            chain["endpoints_involved"] = []
        if "impact_score" not in chain:
            # Calculate impact score based on severity
            severity = chain.get("severity", "MEDIUM")
            impact_map = {"CRITICAL": 9.0, "HIGH": 7.5, "MEDIUM": 5.0, "LOW": 3.0}
            chain["impact_score"] = impact_map.get(severity, 5.0)

        # Parse steps to extract structured endpoint data
        steps_text = chain.get("steps", [])
        structured_steps = []

        for step in steps_text:
            # Try to extract HTTP method and endpoint from step text
            # Example: "Step 1: Get user data via GET /users/all (Finding 1)"
            step_data = {
                "description": step,
                "http_method": "GET",  # Default
                "endpoint": "/",  # Default
            }

            # Parse for HTTP methods
            for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                if method in step.upper():
                    step_data["http_method"] = method
                    # Try to extract the path after the method
                    parts = step.split(method)
                    if len(parts) > 1:
                        # Extract path (everything between method and next space/parenthesis)
                        path_part = parts[1].strip()
                        # Get text until we hit a space or parenthesis
                        endpoint = ""
                        for char in path_part:
                            if char in [" ", "(", "\n"]:
                                break
                            endpoint += char
                        if endpoint.startswith("/"):
                            step_data["endpoint"] = endpoint
                    break

            structured_steps.append(step_data)

        # Replace steps with structured version (keep text in description)
        # Save original steps as steps_text for reference
        chain["steps_text"] = steps_text
        chain["steps"] = structured_steps

        # Extract unique endpoints from structured steps
        if not chain["endpoints_involved"]:
            endpoints = set()
            for step in structured_steps:
                if step["endpoint"] != "/":
                    endpoints.add(f"{step['http_method']} {step['endpoint']}")
            chain["endpoints_involved"] = list(endpoints)

    # Enhance executive summary if it's too generic
    if "attack chains" not in report.get("executive_summary", "").lower():
        critical_count = len(report.get("critical_chains", []))
        high_count = len(report.get("high_priority_chains", []))

        if critical_count > 0:
            first_chain = report.get("critical_chains", [{}])[0]
            chain_name = first_chain.get("name", "Unknown")
            endpoints = ", ".join(
                first_chain.get("endpoints_involved", ["multiple endpoints"])[:2]
            )
            report["executive_summary"] = (
                f"Found {report['total_chains_found']} attack chain(s): "
                f"{critical_count} critical, {high_count} high priority. "
                f"Most critical: {chain_name} affecting {endpoints}. "
                f"{report['vulnerabilities_in_chains']} of {report['total_vulnerabilities']} "
                f"vulnerabilities can be chained together. "
                f"{report.get('executive_summary', '')}"
            )

    return report


def _format_findings_for_prompt(findings: List[Dict[str, Any]]) -> str:
    """Format findings as a clear, numbered list for the AI prompt"""
    lines = []
    for i, finding in enumerate(findings, 1):
        finding_type = finding.get("type", "UNKNOWN")
        description = finding.get("description", "")
        endpoint = finding.get("endpoint", "")
        metadata = finding.get("metadata", {})

        line = f"{i}. {description}"
        if endpoint:
            line += f" [Endpoint: {endpoint}]"
        if metadata:
            meta_items = ", ".join([f"{k}={v}" for k, v in metadata.items()])
            line += f" (Details: {meta_items})"

        lines.append(line)

    return "\n".join(lines)


async def _analyze_attack_chains_with_ai(
    findings_text: str,
    analysis_depth: str,
    max_chain_length: int,
    exclude_low_severity: bool,
    findings_list: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Use AI to reason about attack chains based on factual findings"""

    prompt = f"""You are a security expert analyzing API vulnerabilities. You have been provided with a list of FACTUAL security findings extracted from an OpenAPI specification by deterministic analysis.

Your task is to identify ATTACK CHAINS where multiple findings can be COMBINED to create high-severity security vulnerabilities.

## Factual Findings:
{findings_text}

## Your Analysis:
1. Identify attack chains where these findings can be combined
2. For each attack chain, provide:
   - Name: A descriptive attack name (e.g., "Privilege Escalation via Mass Assignment")
   - Attack Goal: What the attacker achieves
   - Severity: CRITICAL, HIGH, MEDIUM, or LOW
   - Complexity: How difficult it is to execute (Easy, Medium, Hard)
   - Likelihood: Probability of exploitation (0.0-1.0)
   - Attacker Profile: Who could exploit this (e.g., "Unauthenticated Attacker", "Authenticated User")
   - Steps: Ordered list of exploitation steps with SPECIFIC API ENDPOINTS
     - Each step must include the HTTP method and path (e.g., "GET /users", "POST /user/{id}")
     - Reference finding numbers in each step
   - Endpoints Involved: List of API paths used in the attack (e.g., ["GET /users/all", "PUT /users/{id}"])
   - Business Impact: Impact in business terms
   - Remediation: How to fix it

3. Prioritize:
   - CRITICAL: Chains leading to privilege escalation, data breach, or complete system compromise
   - HIGH: Chains exposing sensitive data or allowing unauthorized actions
   - MEDIUM: Chains requiring additional vulnerabilities or limited impact
   - LOW: Theoretical chains requiring unlikely conditions

4. Create a detailed executive summary that includes:
   - Number of attack chains found
   - Most critical vulnerabilities
   - Specific API endpoints at risk
   - Brief description of the worst attack chain

Analysis Depth: {analysis_depth}
Max Chain Length: {max_chain_length}
Exclude Low Severity: {exclude_low_severity}

Please provide your analysis in JSON format:
{{
    "report_id": "uuid",
    "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
    "overall_security_score": 0-100,
    "executive_summary": "Detailed summary: Found X attack chains. Most critical: [attack name] affecting [endpoints]. This allows attackers to [impact].",
    "attack_chains": [
        {{
            "name": "Attack name",
            "attack_goal": "What attacker achieves",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "complexity": "Easy|Medium|Hard",
            "likelihood": 0.8,
            "attacker_profile": "Unauthenticated Attacker",
            "endpoints_involved": ["GET /path1", "POST /path2"],
            "steps": [
                "Step 1: [Action] via GET /endpoint (Finding 1)",
                "Step 2: [Action] via POST /endpoint (Finding 2)"
            ],
            "finding_refs": [1, 2, 3],
            "business_impact": "Business impact description",
            "remediation_steps": ["Fix 1", "Fix 2", ...]
        }}
    ],
    "immediate_actions": ["Action 1", "Action 2"],
    "short_term_actions": ["Action 1", "Action 2"],
    "long_term_actions": ["Action 1", "Action 2"]
}}"""

    # Call LLM
    result = await llm_service.generate(
        prompt=prompt,
        temperature=0.3,  # Lower temperature for more consistent security analysis
        max_tokens=4000,
    )
    response = result["response"]

    # Parse JSON response
    try:
        # Extract JSON from response (handle code blocks)
        response_text = response.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        report = json.loads(response_text)

        # Add report ID if missing
        if "report_id" not in report:
            report["report_id"] = str(uuid.uuid4())

        # Organize chains by severity
        report["critical_chains"] = [
            c
            for c in report.get("attack_chains", [])
            if c.get("severity") == "CRITICAL"
        ]
        report["high_priority_chains"] = [
            c for c in report.get("attack_chains", []) if c.get("severity") == "HIGH"
        ]
        report["all_chains"] = report.get("attack_chains", [])

        return report

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {str(e)}")
        # Return a fallback response without exposing internal error details
        return {
            "report_id": str(uuid.uuid4()),
            "risk_level": "UNKNOWN",
            "overall_security_score": 0,
            "executive_summary": "Failed to parse AI analysis. Please try again.",
            "attack_chains": [],
            "critical_chains": [],
            "high_priority_chains": [],
            "all_chains": [],
            "immediate_actions": ["Review findings manually"],
            "short_term_actions": [],
            "long_term_actions": [],
            "error": "FALLBACK_PARSING_ERROR",
        }


# ============================================================================
# Test Case Generation Endpoints
# ============================================================================


def sanitize_openapi_spec(spec_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize OpenAPI spec by replacing None/null schema values with {}.
    This prevents validation errors when parsing specs with missing schemas.
    """
    if isinstance(spec_dict, dict):
        sanitized = {}
        for key, value in spec_dict.items():
            # Replace None schemas with empty schema
            if key == "schema" and value is None:
                sanitized[key] = {}
            else:
                sanitized[key] = sanitize_openapi_spec(value)
        return sanitized
    elif isinstance(spec_dict, list):
        return [sanitize_openapi_spec(item) for item in spec_dict]
    else:
        return spec_dict


@router.post("/tests/generate")
async def generate_test_cases(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate comprehensive test cases for an OpenAPI endpoint.

    Creates happy path, sad path, edge cases, and AI-generated advanced tests.

    Request body:
    - spec_text: OpenAPI specification (JSON/YAML string)
    - path: API path to generate tests for (e.g., "/users/{id}")
    - method: HTTP method (GET, POST, PUT, DELETE, etc.)
    - include_ai_tests: Whether to include AI-generated tests (default: true)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info("Generating test cases", extra={"correlation_id": correlation_id})

    try:
        # Extract and validate request parameters
        spec_text = request.get("spec_text")
        path = request.get("path")
        method = request.get("method", "GET").upper()
        include_ai_tests = request.get("include_ai_tests", True)

        if not spec_text:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_SPEC", "message": "spec_text is required"},
            )

        if not path:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_PATH", "message": "path is required"},
            )

        # Check cache first
        cached_tests = cache_service.get_test_cases(
            spec_text, path, method, include_ai_tests
        )
        if cached_tests:
            logger.info(f"Returning cached test cases for {method} {path}")
            return {
                **cached_tests,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            try:
                # First, parse the spec text to dict and sanitize it
                try:
                    spec_dict = json.loads(spec_text)
                except json.JSONDecodeError:
                    spec_dict = yaml.safe_load(spec_text)

                # Sanitize the spec to replace None schemas with {}
                sanitized_spec = sanitize_openapi_spec(spec_dict)

                # Convert back to JSON string for ResolvingParser
                sanitized_spec_text = json.dumps(sanitized_spec)

                # Now parse with ResolvingParser
                parser = ResolvingParser(
                    spec_string=sanitized_spec_text, backend="openapi-spec-validator"
                )
                spec = parser.specification
                cache_service.cache_parsed_spec(spec_text, spec)
            except Exception as e:
                logger.error(f"Invalid OpenAPI specification: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "INVALID_SPEC",
                        "message": f"Failed to parse OpenAPI specification: {str(e)}",
                    },
                )

        # Validate path exists
        if path not in spec.get("paths", {}):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PATH_NOT_FOUND",
                    "message": f"Path '{path}' not found in specification",
                    "available_paths": list(spec.get("paths", {}).keys()),
                },
            )

        # Validate method exists
        method_lower = method.lower()
        if method_lower not in spec["paths"][path]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "METHOD_NOT_FOUND",
                    "message": f"Method '{method}' not found for path '{path}'",
                    "available_methods": list(spec["paths"][path].keys()),
                },
            )

        # Generate test cases
        result = await test_case_generator.generate_test_cases(
            spec=spec, path=path, method=method_lower, include_ai_tests=include_ai_tests
        )

        # Cache the results
        cache_service.cache_test_cases(
            spec_text, path, method_lower, include_ai_tests, result
        )

        logger.info(
            f"Generated {result['total_tests']} test cases for {method} {path}",
            extra={"correlation_id": correlation_id},
        )

        return {
            **result,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


@router.post("/tests/generate/all")
async def generate_all_test_cases(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate test cases for all endpoints in an OpenAPI specification.

    Request body:
    - spec_text: OpenAPI specification (JSON/YAML string)
    - include_ai_tests: Whether to include AI-generated tests (default: false for performance)
    - max_endpoints: Maximum number of endpoints to process (default: 50)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        "Generating test cases for all endpoints",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_text = request.get("spec_text")
        include_ai_tests = request.get("include_ai_tests", False)
        max_endpoints = request.get("max_endpoints", 50)

        if not spec_text:
            raise HTTPException(
                status_code=400,
                detail={"error": "MISSING_SPEC", "message": "spec_text is required"},
            )

        # Parse specification
        try:
            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_SPEC",
                    "message": f"Failed to parse OpenAPI specification: {str(e)}",
                },
            )

        # Generate tests for all endpoints
        all_tests = {}
        total_test_count = 0
        endpoint_count = 0

        for path, path_item in spec.get("paths", {}).items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    endpoint_count += 1

                    if endpoint_count > max_endpoints:
                        logger.warning(f"Reached max_endpoints limit ({max_endpoints})")
                        break

                    try:
                        result = await test_case_generator.generate_test_cases(
                            spec=spec,
                            path=path,
                            method=method,
                            include_ai_tests=include_ai_tests,
                        )

                        endpoint_key = f"{method.upper()} {path}"
                        all_tests[endpoint_key] = result
                        total_test_count += result["total_tests"]

                    except Exception as e:
                        logger.error(
                            f"Failed to generate tests for {method.upper()} {path}: {e}"
                        )
                        all_tests[f"{method.upper()} {path}"] = {
                            "error": str(e),
                            "endpoint": f"{method.upper()} {path}",
                        }

            if endpoint_count > max_endpoints:
                break

        logger.info(
            f"Generated {total_test_count} tests across {endpoint_count} endpoints",
            extra={"correlation_id": correlation_id},
        )

        return {
            "endpoints": all_tests,
            "summary": {
                "total_endpoints": endpoint_count,
                "total_tests": total_test_count,
                "include_ai_tests": include_ai_tests,
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk test generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "BULK_TEST_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


@router.post("/mock/generate-data")
async def generate_mock_data(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate realistic mock data for a specific response schema.

    Request body:
    - spec_text: OpenAPI specification
    - path: API path
    - method: HTTP method
    - response_code: Response code to generate data for (default: "200")
    - variation: Variation number for diversity (default: 1)
    - use_ai: Whether to use AI for generation (default: true)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info("Generating mock data", extra={"correlation_id": correlation_id})

    try:
        spec_text = request.get("spec_text")
        path = request.get("path")
        method = request.get("method", "GET").lower()
        response_code = request.get("response_code", "200")
        variation = request.get("variation", 1)
        use_ai = request.get("use_ai", True)

        if not spec_text or not path:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "MISSING_PARAMETERS",
                    "message": "spec_text and path are required",
                },
            )

        # Parse specification
        parser = ResolvingParser(
            spec_string=spec_text, backend="openapi-spec-validator"
        )
        spec = parser.specification

        # Get operation and response schema
        operation = spec["paths"][path][method]
        response_spec = operation.get("responses", {}).get(response_code)

        if not response_spec:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "RESPONSE_NOT_FOUND",
                    "message": f"Response {response_code} not found for {method.upper()} {path}",
                },
            )

        # Extract schema
        response_schema = (
            response_spec.get("content", {}).get("application/json", {}).get("schema")
        )

        if not response_schema:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NO_SCHEMA",
                    "message": "No JSON schema found for response",
                },
            )

        # Generate mock data
        mock_data = await mock_data_service.generate_mock_response(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            variation=variation,
            use_ai=use_ai,
        )

        logger.info(
            "Mock data generated successfully", extra={"correlation_id": correlation_id}
        )

        return {
            "mock_data": mock_data,
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "variation": variation,
            "used_ai": use_ai,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock data generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MOCK_DATA_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


@router.post("/mock/generate-variations")
async def generate_mock_variations(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Generate multiple variations of mock data for testing diversity.

    Request body:
    - spec_text: OpenAPI specification
    - path: API path
    - method: HTTP method
    - response_code: Response code (default: "200")
    - count: Number of variations (default: 3, max: 10)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        "Generating mock data variations", extra={"correlation_id": correlation_id}
    )

    try:
        spec_text = request.get("spec_text")
        path = request.get("path")
        method = request.get("method", "GET").lower()
        response_code = request.get("response_code", "200")
        count = min(request.get("count", 3), 10)  # Cap at 10

        # Check cache first
        cached_mock_data = cache_service.get_mock_data(
            spec_text, path, method, response_code, count
        )
        if cached_mock_data:
            logger.info(f"Returning cached mock data for {method} {path}")
            return {
                "variations": cached_mock_data,
                "count": len(cached_mock_data),
                "endpoint": f"{method.upper()} {path}",
                "response_code": response_code,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
            cache_service.cache_parsed_spec(spec_text, spec)

        # Get operation and response schema
        operation = spec["paths"][path][method]
        response_spec = operation.get("responses", {}).get(response_code)
        response_schema = (
            response_spec.get("content", {}).get("application/json", {}).get("schema")
        )

        # Generate variations
        variations = await mock_data_service.generate_test_variations(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            count=count,
        )

        # Cache the results
        cache_service.cache_mock_data(
            spec_text, path, method, response_code, count, variations
        )

        logger.info(
            f"Generated {len(variations)} mock data variations",
            extra={"correlation_id": correlation_id},
        )

        return {
            "variations": variations,
            "count": len(variations),
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Mock variations generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MOCK_VARIATIONS_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


# ==================== Cache Management Endpoints ====================


@router.get("/cache/stats")
async def get_cache_stats(_: None = Depends(handle_exceptions)):
    """
    Get cache statistics and performance metrics.

    Returns hit rates, cache sizes, and overall performance data.
    """
    logger.info("Retrieving cache statistics")
    stats = cache_service.get_cache_stats()
    return {**stats, "timestamp": datetime.utcnow().isoformat()}


@router.delete("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None, _: None = Depends(handle_exceptions)
):
    """
    Clear specified cache or all caches.

    Query Parameters:
    - cache_type: Type of cache to clear (spec, test, mock). If not specified, clears all.
    """
    logger.info(f"Clearing {cache_type or 'all'} cache(s)")
    cache_service.clear_cache(cache_type)
    return {
        "success": True,
        "message": f"Cleared {cache_type or 'all'} cache(s)",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/cache/invalidate")
async def invalidate_spec_cache(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Invalidate all cache entries related to a specific specification.

    Request body:
    - spec_text: The OpenAPI specification to invalidate
    """
    spec_text = request.get("spec_text")
    if not spec_text:
        raise HTTPException(
            status_code=400,
            detail={"error": "MISSING_SPEC", "message": "spec_text is required"},
        )

    logger.info("Invalidating cache for specification")
    cache_service.invalidate_spec_cache(spec_text)
    return {
        "success": True,
        "message": "Cache invalidated for specification",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Advanced Architectural Analyzer AI Interpretation Endpoints
# ============================================================================


@router.post("/ai/analyze/taint-analysis")
async def interpret_taint_analysis(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    AI-powered interpretation of Taint Analysis results.

    Takes the raw taint analysis data from the Java backend and provides:
    - Executive summary of data leakage risks
    - Business impact assessment
    - Prioritized remediation recommendations
    - Compliance implications (GDPR, PCI-DSS, HIPAA)

    Request body:
    - vulnerabilities: List of taint vulnerabilities from backend
    - spec_text: OpenAPI specification for context
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting taint analysis results", extra={"correlation_id": correlation_id}
    )

    try:
        vulnerabilities = request.get("vulnerabilities", [])
        spec_text = request.get("spec_text", "")

        if not vulnerabilities:
            return {
                "summary": "No taint vulnerabilities detected. Your API appears to have proper data flow controls.",
                "risk_level": "LOW",
                "recommendations": [],
                "correlation_id": correlation_id,
            }

        # Build AI prompt for taint analysis interpretation
        critical_vulns = [v for v in vulnerabilities if v.get("severity") == "CRITICAL"]
        warning_vulns = [v for v in vulnerabilities if v.get("severity") == "WARNING"]

        taint_prompt = f"""You are an API security expert analyzing taint analysis results.

TAINT ANALYSIS FINDINGS:
Total Vulnerabilities: {len(vulnerabilities)}
- CRITICAL (Public data leakage): {len(critical_vulns)}
- WARNING (Secured but needs review): {len(warning_vulns)}

CRITICAL VULNERABILITIES:
{json.dumps(critical_vulns, indent=2) if critical_vulns else "None"}

WARNING VULNERABILITIES:
{json.dumps(warning_vulns, indent=2) if warning_vulns else "None"}

Provide a comprehensive security analysis in JSON format:
{{
  "executive_summary": "Brief executive summary of the data leakage risks",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "business_impact": "Explanation of business/compliance impact",
  "top_issues": [
    {{
      "endpoint": "endpoint path",
      "issue": "description",
      "severity": "CRITICAL|WARNING",
      "leaked_data": "what sensitive data is exposed",
      "attack_scenario": "how an attacker could exploit this",
      "compliance_impact": "GDPR/PCI-DSS/HIPAA violations"
    }}
  ],
  "remediation_priorities": [
    {{
      "priority": "IMMEDIATE|HIGH|MEDIUM",
      "action": "specific fix to implement",
      "endpoints_affected": ["list of endpoints"],
      "estimated_effort": "hours/days"
    }}
  ],
  "compliance_recommendations": {{
    "gdpr": "GDPR-specific recommendations",
    "pci_dss": "PCI-DSS recommendations if credit card data involved",
    "hipaa": "HIPAA recommendations if health data involved"
  }}
}}"""

        # Call LLM for interpretation
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert API security analyst specializing in data protection and compliance. Respond only with valid JSON.",
                },
                {"role": "user", "content": taint_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 3000},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM request failed")

        llm_response = response.json().get("message", {}).get("content", "{}")
        interpretation = json.loads(llm_response)

        return {
            **interpretation,
            "total_vulnerabilities": len(vulnerabilities),
            "critical_count": len(critical_vulns),
            "warning_count": len(warning_vulns),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Taint analysis interpretation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TAINT_INTERPRETATION_FAILED",
                "message": f"Failed to interpret taint analysis: {str(e)}",
            },
        )


@router.post("/ai/analyze/authz-matrix")
async def interpret_authz_matrix(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    AI-powered interpretation of Authorization Matrix results.

    Analyzes RBAC configuration for security anomalies and misconfigurations.

    Request body:
    - scopes: List of all scopes/roles
    - matrix: Map of operations to their required scopes
    - spec_text: OpenAPI specification for context
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting authz matrix results", extra={"correlation_id": correlation_id}
    )

    try:
        scopes = request.get("scopes", [])
        matrix = request.get("matrix", {})

        if not matrix:
            return {
                "summary": "No authorization matrix data available.",
                "anomalies": [],
                "correlation_id": correlation_id,
            }

        # Analyze matrix for anomalies
        authz_prompt = f"""You are an API security expert analyzing RBAC authorization matrix.

AUTHORIZATION MATRIX:
Total Endpoints: {len(matrix)}
Available Scopes/Roles: {', '.join(scopes)}

MATRIX DATA:
{json.dumps(matrix, indent=2)[:3000]}

Analyze this authorization matrix for security anomalies. Look for:
1. Destructive operations (DELETE, PUT) accessible with read-only scopes
2. Admin operations accessible with regular user scopes
3. Public endpoints (no security) that should be protected
4. Overly permissive scopes (one scope grants access to too many operations)
5. Missing authorization on sensitive operations

Provide analysis in JSON format:
{{
  "executive_summary": "Brief summary of authorization security",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "anomalies_detected": [
    {{
      "type": "PRIVILEGE_ESCALATION|MISSING_AUTH|OVERLY_PERMISSIVE",
      "severity": "CRITICAL|HIGH|MEDIUM",
      "endpoint": "operation endpoint",
      "issue": "description of the issue",
      "current_scopes": ["list of scopes"],
      "attack_scenario": "how this could be exploited",
      "recommended_scopes": ["what scopes should be required"]
    }}
  ],
  "best_practice_violations": [
    "List of RBAC best practice violations found"
  ],
  "recommendations": [
    {{
      "priority": "IMMEDIATE|HIGH|MEDIUM",
      "recommendation": "specific action to take",
      "affected_endpoints": ["list of endpoints"]
    }}
  ]
}}"""

        # Call LLM
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in RBAC and authorization security. Respond only with valid JSON.",
                },
                {"role": "user", "content": authz_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 3000},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM request failed")

        llm_response = response.json().get("message", {}).get("content", "{}")
        interpretation = json.loads(llm_response)

        return {
            **interpretation,
            "total_endpoints": len(matrix),
            "total_scopes": len(scopes),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Authz matrix interpretation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "AUTHZ_INTERPRETATION_FAILED",
                "message": f"Failed to interpret authorization matrix: {str(e)}",
            },
        )


@router.post("/ai/analyze/schema-similarity")
async def interpret_schema_similarity(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    AI-powered interpretation of Schema Similarity Clustering results.

    Provides refactoring recommendations for duplicate/similar schemas.

    Request body:
    - clusters: List of schema clusters with similarity scores
    - spec_text: OpenAPI specification for context
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting schema similarity results",
        extra={"correlation_id": correlation_id},
    )

    try:
        clusters = request.get("clusters", [])

        if not clusters:
            return {
                "summary": "No duplicate or similar schemas detected. Your schema design is well-organized.",
                "refactoring_opportunities": [],
                "correlation_id": correlation_id,
            }

        similarity_prompt = f"""You are an API design expert analyzing schema similarity clustering results.

SCHEMA SIMILARITY CLUSTERS:
Total Clusters Found: {len(clusters)}

CLUSTER DATA:
{json.dumps(clusters, indent=2)[:3000]}

Analyze these clusters and provide refactoring recommendations in JSON format:
{{
  "executive_summary": "Brief summary of schema duplication issues",
  "code_health_score": 0-100,
  "potential_savings": "estimated lines of code reduction",
  "refactoring_opportunities": [
    {{
      "cluster_id": "cluster identifier",
      "schema_names": ["list of similar schemas"],
      "similarity_score": 0.0-1.0,
      "issue": "description of duplication/similarity",
      "refactoring_strategy": "MERGE|BASE_SCHEMA_WITH_INHERITANCE|COMPOSITION",
      "implementation_steps": [
        "Step 1: Create base schema...",
        "Step 2: Apply allOf/oneOf...",
        "Step 3: Update references..."
      ],
      "estimated_effort": "hours",
      "benefits": "why this refactoring is valuable",
      "breaking_change_risk": "HIGH|MEDIUM|LOW"
    }}
  ],
  "quick_wins": [
    {{
      "schemas": ["schemas that can be quickly merged"],
      "effort": "15-30 minutes",
      "impact": "description of impact"
    }}
  ],
  "architectural_recommendations": [
    "High-level recommendations for schema organization"
  ]
}}"""

        # Call LLM
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in API design and schema architecture. Respond only with valid JSON.",
                },
                {"role": "user", "content": similarity_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 3000},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM request failed")

        llm_response = response.json().get("message", {}).get("content", "{}")
        interpretation = json.loads(llm_response)

        return {
            **interpretation,
            "total_clusters": len(clusters),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Schema similarity interpretation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SIMILARITY_INTERPRETATION_FAILED",
                "message": f"Failed to interpret schema similarity: {str(e)}",
            },
        )


@router.post("/ai/analyze/zombie-apis")
async def interpret_zombie_apis(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    AI-powered interpretation of Zombie API Detection results.

    Analyzes unreachable, shadowed, and orphaned endpoints.

    Request body:
    - shadowed_endpoints: List of shadowed endpoints
    - orphaned_operations: List of orphaned operations
    - spec_text: OpenAPI specification for context
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Interpreting zombie API results", extra={"correlation_id": correlation_id}
    )

    try:
        shadowed = request.get("shadowedEndpoints", [])
        orphaned = request.get("orphanedOperations", [])

        if not shadowed and not orphaned:
            return {
                "summary": "No zombie APIs detected. All endpoints appear reachable and properly defined.",
                "cleanup_recommendations": [],
                "correlation_id": correlation_id,
            }

        zombie_prompt = f"""You are an API maintenance expert analyzing zombie API detection results.

ZOMBIE API FINDINGS:
Shadowed Endpoints: {len(shadowed)}
Orphaned Operations: {len(orphaned)}

SHADOWED ENDPOINTS (unreachable due to routing conflicts):
{json.dumps(shadowed, indent=2)[:2000]}

ORPHANED OPERATIONS (no params/body/response):
{json.dumps(orphaned, indent=2)[:1000]}

Analyze these zombie APIs and provide cleanup recommendations in JSON format:
{{
  "executive_summary": "Brief summary of API hygiene issues",
  "code_health_score": 0-100,
  "maintenance_burden": "description of technical debt",
  "shadowed_endpoint_analysis": [
    {{
      "shadowed_path": "unreachable endpoint",
      "shadowing_path": "conflicting endpoint",
      "reason": "why it's unreachable",
      "recommendation": "REORDER|RENAME|REMOVE|MERGE",
      "fix_instructions": "specific steps to fix",
      "breaking_change": "yes|no|maybe"
    }}
  ],
  "orphaned_operation_analysis": [
    {{
      "operation": "operation identifier",
      "reason": "why it's considered orphaned",
      "recommendation": "REMOVE|COMPLETE_IMPLEMENTATION|CONVERT_TO_HEALTH_CHECK",
      "rationale": "why this recommendation makes sense"
    }}
  ],
  "cleanup_priorities": [
    {{
      "priority": "HIGH|MEDIUM|LOW",
      "action": "specific cleanup action",
      "affected_endpoints": ["list of endpoints"],
      "estimated_effort": "hours"
    }}
  ],
  "architectural_improvements": [
    "Suggestions for preventing zombie APIs in the future"
  ]
}}"""

        # Call LLM
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert in API design and maintenance. Respond only with valid JSON.",
                },
                {"role": "user", "content": zombie_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 3000},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM request failed")

        llm_response = response.json().get("message", {}).get("content", "{}")
        interpretation = json.loads(llm_response)

        return {
            **interpretation,
            "total_shadowed": len(shadowed),
            "total_orphaned": len(orphaned),
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Zombie API interpretation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ZOMBIE_INTERPRETATION_FAILED",
                "message": f"Failed to interpret zombie API detection: {str(e)}",
            },
        )


@router.post("/ai/analyze/comprehensive-architecture")
async def comprehensive_architecture_analysis(
    request: Dict[str, Any], _: None = Depends(handle_exceptions)
):
    """
    Comprehensive architectural analysis combining all 4 advanced analyzers.

    This endpoint provides a holistic view of:
    - Security (Taint Analysis + Authz Matrix)
    - Code Quality (Schema Similarity + Zombie APIs)
    - Overall API health score
    - Executive summary with prioritized action items

    Request body:
    - taint_analysis: Results from taint analyzer
    - authz_matrix: Results from authz matrix analyzer
    - schema_similarity: Results from similarity analyzer
    - zombie_apis: Results from zombie API detector
    - spec_text: OpenAPI specification
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Performing comprehensive architecture analysis",
        extra={"correlation_id": correlation_id},
    )

    try:
        taint = request.get("taint_analysis", {})
        authz = request.get("authz_matrix", {})
        similarity = request.get("schema_similarity", {})
        zombie = request.get("zombie_apis", {})

        # Build comprehensive prompt
        comprehensive_prompt = f"""You are a senior API architect performing a comprehensive analysis.

ANALYSIS RESULTS:

1. TAINT ANALYSIS (Data Security):
Vulnerabilities: {len(taint.get('vulnerabilities', []))}
{json.dumps(taint, indent=2)[:1500]}

2. AUTHORIZATION MATRIX (Access Control):
Endpoints: {len(authz.get('matrix', {}))}
Scopes: {len(authz.get('scopes', []))}
{json.dumps(authz, indent=2)[:1500]}

3. SCHEMA SIMILARITY (Code Quality):
Duplicate Clusters: {len(similarity.get('clusters', []))}
{json.dumps(similarity, indent=2)[:1500]}

4. ZOMBIE API DETECTION (Maintenance):
Shadowed: {len(zombie.get('shadowedEndpoints', []))}
Orphaned: {len(zombie.get('orphanedOperations', []))}
{json.dumps(zombie, indent=2)[:1500]}

Provide a comprehensive executive report in JSON format:
{{
  "overall_health_score": 0-100,
  "health_breakdown": {{
    "security_score": 0-100,
    "access_control_score": 0-100,
    "code_quality_score": 0-100,
    "maintenance_score": 0-100
  }},
  "executive_summary": "High-level summary for business stakeholders",
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW",
  "top_3_critical_issues": [
    {{
      "category": "SECURITY|ACCESS_CONTROL|CODE_QUALITY|MAINTENANCE",
      "issue": "description",
      "business_impact": "impact on business",
      "urgency": "IMMEDIATE|URGENT|IMPORTANT"
    }}
  ],
  "immediate_action_items": [
    "Action items that must be addressed immediately"
  ],
  "short_term_roadmap": [
    "Items to address in next 1-2 weeks"
  ],
  "long_term_improvements": [
    "Architectural improvements for next quarter"
  ],
  "estimated_total_effort": "total hours/days to fix all issues",
  "roi_analysis": "expected benefits vs effort required"
}}"""

        # Call LLM
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a senior API architect and security expert. Respond only with valid JSON.",
                },
                {"role": "user", "content": comprehensive_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2, "num_predict": 4000},
        }

        response = await llm_service.client.post(
            llm_service.chat_endpoint, json=payload
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="LLM request failed")

        llm_response = response.json().get("message", {}).get("content", "{}")
        interpretation = json.loads(llm_response)

        return {
            **interpretation,
            "analyzer_summary": {
                "taint_vulnerabilities": len(taint.get("vulnerabilities", [])),
                "authz_endpoints": len(authz.get("matrix", {})),
                "duplicate_clusters": len(similarity.get("clusters", [])),
                "zombie_apis": len(zombie.get("shadowedEndpoints", []))
                + len(zombie.get("orphanedOperations", [])),
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Comprehensive analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "COMPREHENSIVE_ANALYSIS_FAILED",
                "message": f"Failed to perform comprehensive analysis: {str(e)}",
            },
        )
