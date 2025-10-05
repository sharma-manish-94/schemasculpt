"""
Enhanced API endpoints for SchemaSculpt AI Service.
Integrates advanced LLM service, agentic workflows, streaming, and comprehensive AI features.
"""

import asyncio
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from prance import ResolvingParser

from ..core.config import settings
from ..core.exceptions import SchemaSculptException
from ..core.logging import get_logger, set_correlation_id
from ..schemas.ai_schemas import (
    AIRequest, AIResponse, MockStartRequest, MockStartResponse,
    GenerateSpecRequest, HealthResponse, OperationType, StreamingMode,
    LLMParameters
)
from ..schemas.security_schemas import (
    SecurityAnalysisRequest, SecurityAnalysisReport
)
from ..schemas.patch_schemas import (
    PatchGenerationRequest, PatchGenerationResponse,
    PatchApplicationRequest, PatchApplicationResponse,
    SmartAIFixRequest, SmartAIFixResponse
)
from ..schemas.meta_analysis_schemas import (
    AIMetaAnalysisRequest, AIMetaAnalysisResponse
)
from ..schemas.description_schemas import (
    DescriptionAnalysisRequest, DescriptionAnalysisResponse
)
from ..services.agent_manager import AgentManager
from ..services.context_manager import ContextManager
from ..services.llm_service import LLMService
from ..services.prompt_engine import PromptEngine
from ..services.rag_service import RAGService
from ..services.security import SecurityAnalysisWorkflow
from ..services.patch_generator import PatchGenerator, apply_json_patch
from ..services.smart_fix_service import SmartFixService
from ..services.meta_analysis_service import MetaAnalysisService
from ..services.description_analysis_service import DescriptionAnalysisService
from ..services.llm_adapter import LLMAdapter
from ..services.mock_data_service import MockDataService
from ..services.test_case_generator import TestCaseGeneratorService
from ..services.cache_service import cache_service

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
        raise HTTPException(status_code=e.status_code, detail={
            "error": e.error_code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "details": {"original_error": str(e)}
        })


@router.post("/ai/process", response_model=AIResponse)
async def process_specification(request: AIRequest, _: None = Depends(handle_exceptions)):
    """
    Process AI request with advanced features including streaming and JSON patching.
    """
    # Set correlation ID for tracking
    correlation_id = set_correlation_id()

    logger.info(f"Processing AI request: {request.operation_type}", extra={
        "correlation_id": correlation_id,
        "operation_type": request.operation_type,
        "streaming": request.streaming != StreamingMode.DISABLED,
        "has_patches": bool(request.json_patches)
    })

    try:
        # Get context for the request
        session_id = str(request.session_id) if request.session_id else context_manager.create_session(request.user_id)
        request.context = context_manager.get_context_for_request(session_id, request)

        # Process the request
        result = await llm_service.process_ai_request(request)

        # Handle streaming response
        if request.streaming != StreamingMode.DISABLED:
            async def stream_generator():
                async for chunk in result:
                    yield f"data: {json.dumps(chunk.dict())}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/plain",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )

        # Add conversation turn to context
        context_manager.add_conversation_turn(session_id, request, result, True)

        return result

    except Exception as e:
        logger.error(f"AI processing failed: {str(e)}")
        # Add failed turn to context
        if 'session_id' in locals():
            context_manager.add_conversation_turn(session_id, request, None, False)
        raise


@router.post("/ai/generate", response_model=AIResponse)
async def generate_specification_agentic(request: GenerateSpecRequest, _: None = Depends(handle_exceptions)):
    """
    Generate complete OpenAPI specification using agentic workflow.
    """
    correlation_id = set_correlation_id()

    logger.info("Starting agentic spec generation", extra={
        "correlation_id": correlation_id,
        "domain": request.domain,
        "complexity": request.complexity_level,
        "streaming": request.streaming != StreamingMode.DISABLED
    })

    try:
        result = await agent_manager.execute_complete_spec_generation(request)
        return result

    except Exception as e:
        logger.error(f"Agentic spec generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "GENERATION_FAILED",
            "message": f"Failed to generate specification: {str(e)}"
        })


@router.post("/ai/workflow/{workflow_name}")
async def execute_predefined_workflow(
    workflow_name: str,
    input_data: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Execute a predefined workflow with custom input data.
    """
    correlation_id = set_correlation_id()

    logger.info(f"Executing workflow: {workflow_name}", extra={
        "correlation_id": correlation_id,
        "workflow": workflow_name
    })

    try:
        result = await agent_manager.execute_custom_workflow(workflow_name, input_data)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_WORKFLOW",
            "message": str(e)
        })
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "WORKFLOW_FAILED",
            "message": f"Workflow execution failed: {str(e)}"
        })


@router.post("/ai/workflow/custom")
async def execute_custom_workflow(
    workflow_definition: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Execute a custom ad-hoc workflow.
    """
    correlation_id = set_correlation_id()

    logger.info("Executing custom workflow", extra={
        "correlation_id": correlation_id,
        "workflow_type": workflow_definition.get("workflow_type", "unknown")
    })

    try:
        result = await agent_manager.execute_ad_hoc_workflow(workflow_definition)
        return result

    except Exception as e:
        logger.error(f"Custom workflow execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "CUSTOM_WORKFLOW_FAILED",
            "message": f"Custom workflow execution failed: {str(e)}"
        })


@router.get("/ai/workflows")
async def get_available_workflows():
    """
    Get list of available predefined workflows.
    """
    context_stats = context_manager.get_context_statistics()
    return {
        "workflows": agent_manager.get_available_workflows(),
        "timestamp": context_stats.get("timestamp") if context_stats else None
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
        "created_at": datetime.utcnow()
    }


@router.get("/ai/context/session/{session_id}")
async def get_session_summary(session_id: str):
    """
    Get summary of a conversation session.
    """
    try:
        summary = context_manager.get_session_summary(session_id)
        suggestions = context_manager.get_intelligent_suggestions(session_id, None)

        return {
            "session_summary": summary,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail={
            "error": "SESSION_NOT_FOUND",
            "message": f"Session {session_id} not found"
        })


@router.get("/ai/context/statistics")
async def get_context_statistics():
    """
    Get context management statistics.
    """
    return context_manager.get_context_statistics()


@router.post("/ai/prompt/generate")
async def generate_intelligent_prompt(
    request_data: Dict[str, Any],
    context_id: Optional[str] = None
):
    """
    Generate intelligent prompts using the prompt engine.
    """
    try:
        # Create a mock AIRequest for prompt generation
        ai_request = AIRequest(
            spec_text=request_data.get("spec_text", ""),
            prompt=request_data.get("prompt", ""),
            operation_type=OperationType(request_data.get("operation_type", "modify"))
        )

        system_prompt, user_prompt = prompt_engine.generate_intelligent_prompt(ai_request, context_id)

        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "context_id": context_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail={
            "error": "PROMPT_GENERATION_FAILED",
            "message": f"Failed to generate prompt: {str(e)}"
        })


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
                "context_manager": "healthy"
            },
            total_requests=context_stats.get("total_conversation_turns", 0),
            average_response_time_ms=context_stats.get("average_response_time", 0.0),
            error_rate=1.0 - context_stats.get("average_success_rate", 1.0)
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return HealthResponse(
            status="unhealthy",
            version=settings.app_version,
            uptime_seconds=0
        )


# Mock server endpoints (enhanced)
@router.post("/mock/start", response_model=MockStartResponse)
async def start_mock_server(request: MockStartRequest, _: None = Depends(handle_exceptions)):
    """
    Start a mock server with enhanced AI-powered response generation.
    """
    mock_id = str(uuid.uuid4())

    try:
        # Parse and validate the specification
        parser = ResolvingParser(spec_string=request.spec_text, backend='openapi-spec-validator')
        MOCKED_APIS[mock_id] = {
            "specification": parser.specification,
            "config": request.dict(),
            "created_at": datetime.utcnow()
        }

        spec_info = parser.specification.get('info', {})
        paths = parser.specification.get('paths', {})

        return MockStartResponse(
            mock_id=mock_id,
            base_url=f"/mock/{mock_id}",
            host=request.host,
            port=request.port or 8000,
            available_endpoints=list(paths.keys()),
            total_endpoints=len(paths),
            created_at=MOCKED_APIS[mock_id]["created_at"]
        )

    except Exception as e:
        logger.error(f"Mock server creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_SPEC",
            "message": f"Invalid OpenAPI specification: {str(e)}"
        })


@router.put("/mock/{mock_id}")
async def update_mock_server(mock_id: str, request: MockStartRequest, _: None = Depends(handle_exceptions)):
    """
    Update the specification for an existing mock server.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail={
            "error": "MOCK_NOT_FOUND",
            "message": f"Mock server {mock_id} not found"
        })

    try:
        parser = ResolvingParser(spec_string=request.spec_text, backend='openapi-spec-validator')
        MOCKED_APIS[mock_id]["specification"] = parser.specification
        MOCKED_APIS[mock_id]["config"] = request.dict()

        return {
            "message": f"Mock server {mock_id} updated successfully",
            "updated_at": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Mock server update failed: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_SPEC",
            "message": f"Invalid OpenAPI specification: {str(e)}"
        })


@router.get("/mock/{mock_id}")
async def get_mock_server_info(mock_id: str):
    """
    Get information about a mock server.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail={
            "error": "MOCK_NOT_FOUND",
            "message": f"Mock server {mock_id} not found"
        })

    mock_data = MOCKED_APIS[mock_id]
    spec_info = mock_data["specification"].get('info', {})

    return {
        "mock_id": mock_id,
        "title": spec_info.get('title', 'Untitled API'),
        "version": spec_info.get('version', '1.0.0'),
        "description": spec_info.get('description', 'No description'),
        "total_endpoints": len(mock_data["specification"].get('paths', {})),
        "created_at": mock_data.get("created_at"),
        "config": mock_data.get("config", {}),
        "message": "Mock server is running",
        "docs": "Append a valid path from your specification to this URL to get mock responses"
    }


@router.api_route("/mock/{mock_id}/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def handle_mock_request(mock_id: str, full_path: str, request: Request):
    """
    Enhanced mock request handler with AI-powered response generation.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(status_code=404, detail={
            "error": "MOCK_NOT_FOUND",
            "message": f"Mock server {mock_id} not found"
        })

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
        raise HTTPException(status_code=500, detail={
            "error": "SIMULATED_ERROR",
            "message": "Simulated error for testing purposes"
        })

    path_to_lookup = f'/{full_path}'
    path_spec = spec.get('paths', {}).get(path_to_lookup)

    if not path_spec or http_method not in path_spec:
        raise HTTPException(status_code=404, detail={
            "error": "ENDPOINT_NOT_FOUND",
            "message": f"Endpoint {http_method.upper()} {path_to_lookup} not found in specification"
        })

    operation_spec = path_spec[http_method]

    # Try to get response schema
    try:
        response_schema = operation_spec['responses']['200']['content']['application/json']['schema']
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
                variation=random.randint(1, config.get('response_variety', 3)),
                use_ai=True
            )
            return JSONResponse(content=mock_response)

        except Exception as e:
            logger.warning(f"AI response generation failed: {str(e)}, falling back to simple response")
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
async def perform_meta_analysis(request: AIMetaAnalysisRequest, _: None = Depends(handle_exceptions)):
    """
    Perform AI meta-analysis on linter findings to detect higher-order patterns.

    This is the "linter-augmented AI analyst" feature. It takes the results from
    deterministic linters and uses AI to find patterns, combinations, and higher-level
    issues that individual linter rules cannot detect.
    """
    correlation_id = set_correlation_id()

    logger.info(f"Performing meta-analysis with {len(request.errors)} errors, "
                f"{len(request.suggestions)} suggestions", extra={
        "correlation_id": correlation_id,
        "error_count": len(request.errors),
        "suggestion_count": len(request.suggestions)
    })

    try:
        result = await meta_analysis_service.analyze(request)

        logger.info(f"Meta-analysis completed with {len(result.insights)} insights", extra={
            "correlation_id": correlation_id,
            "insight_count": len(result.insights),
            "confidence": result.confidenceScore
        })

        return result

    except Exception as e:
        logger.error(f"Meta-analysis failed: {str(e)}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail={
            "error": "META_ANALYSIS_FAILED",
            "message": "Failed to perform meta-analysis",
            "details": {"original_error": str(e)}
        })


@router.post("/ai/analyze-descriptions", response_model=DescriptionAnalysisResponse)
async def analyze_descriptions(request: DescriptionAnalysisRequest, _: None = Depends(handle_exceptions)):
    """
    Analyze description quality using AI.

    This endpoint:
    - Accepts ONLY descriptions + minimal context (NOT entire spec)
    - Analyzes quality (completeness, clarity, accuracy, best practices)
    - Returns quality scores + JSON Patch operations for improvements
    - Batches multiple descriptions in a single LLM call for efficiency
    """
    correlation_id = set_correlation_id()

    logger.info(f"Analyzing {len(request.items)} descriptions", extra={
        "correlation_id": correlation_id,
        "item_count": len(request.items)
    })

    try:
        result = await description_analysis_service.analyze(request)

        logger.info(f"Description analysis completed with overall score: {result.overall_score}", extra={
            "correlation_id": correlation_id,
            "overall_score": result.overall_score,
            "patches_count": len(result.patches)
        })

        return result

    except Exception as e:
        logger.error(f"Description analysis failed: {str(e)}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail={
            "error": "DESCRIPTION_ANALYSIS_FAILED",
            "message": "Failed to analyze description quality",
            "details": {"original_error": str(e)}
        })


def _get_cache_key(spec_text: str, prompt: str) -> str:
    """Generate cache key for security analysis."""
    content = f"{spec_text}{prompt}"
    return hashlib.md5(content.encode()).hexdigest()

def _is_cache_valid(cache_entry: Dict[str, Any]) -> bool:
    """Check if cache entry is still valid (1 hour TTL)."""
    if 'timestamp' not in cache_entry:
        return False
    cache_time = datetime.fromisoformat(cache_entry['timestamp'])
    return datetime.now() - cache_time < timedelta(hours=1)

@router.post("/ai/analyze/security", response_model=AIResponse)
async def analyze_security(request: AIRequest, _: None = Depends(handle_exceptions)):
    """
    Perform RAG-enhanced security analysis of OpenAPI specifications.
    Retrieves relevant security context from knowledge base and generates comprehensive analysis.
    Includes response caching for better performance.
    """
    correlation_id = set_correlation_id()

    logger.info("Starting security analysis", extra={
        "correlation_id": correlation_id,
        "operation_type": "security_analysis",
        "has_spec": bool(request.spec_text)
    })

    try:
        # Check cache first
        cache_key = _get_cache_key(request.spec_text, request.prompt)
        if cache_key in SECURITY_ANALYSIS_CACHE:
            cache_entry = SECURITY_ANALYSIS_CACHE[cache_key]
            if _is_cache_valid(cache_entry):
                logger.info("Returning cached security analysis result")
                return cache_entry['result']
            else:
                # Remove expired cache entry
                del SECURITY_ANALYSIS_CACHE[cache_key]

        # Get session context
        session_id = str(request.session_id) if request.session_id else context_manager.create_session(request.user_id)

        # Retrieve relevant security context from RAG knowledge base (limit results for performance)
        security_query = f"Security analysis OpenAPI specification vulnerabilities authentication authorization: {request.spec_text[:300]}"
        context_data = await rag_service.retrieve_security_context(security_query, n_results=3)

        # Streamlined security analysis prompt for better performance
        context_summary = context_data.get('context', 'No additional context available')
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
            tags=request.tags + ["security_analysis", "rag_enhanced"]
        )

        # Process through LLM service
        result = await llm_service.process_ai_request(security_request)

        # Enhance result with RAG metadata
        if hasattr(result, 'metadata'):
            result.metadata.update({
                "rag_sources": context_data.get('sources', []),
                "rag_relevance_scores": context_data.get('relevance_scores', []),
                "knowledge_base_available": rag_service.is_available(),
                "analysis_type": "security_rag_enhanced"
            })

        # Add conversation turn to context
        context_manager.add_conversation_turn(session_id, security_request, result, True)

        # Cache the result for future requests
        SECURITY_ANALYSIS_CACHE[cache_key] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }

        logger.info(f"Security analysis completed with {len(context_data.get('sources', []))} knowledge sources")

        return result

    except Exception as e:
        logger.error(f"Security analysis failed: {str(e)}")
        if 'session_id' in locals():
            context_manager.add_conversation_turn(session_id, request, None, False)
        raise HTTPException(status_code=500, detail={
            "error": "SECURITY_ANALYSIS_FAILED",
            "message": f"Security analysis failed: {str(e)}",
            "rag_available": rag_service.is_available()
        })


def _generate_explanation_cache_key(rule_id: str, message: str, category: str) -> str:
    """Generate cache key for explanation."""
    key_data = f"{rule_id}:{category}:{message}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cached_explanation(rule_id: str, message: str, category: str) -> Optional[Dict[str, Any]]:
    """Get cached explanation if available and not expired."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    cached = EXPLANATION_CACHE.get(cache_key)

    if not cached:
        return None

    # Check if expired
    if datetime.utcnow() - cached['timestamp'] > EXPLANATION_CACHE_TTL:
        del EXPLANATION_CACHE[cache_key]
        return None

    logger.info(f"Returning cached explanation for rule {rule_id}")
    return cached['data']


def _cache_explanation(rule_id: str, message: str, category: str, data: Dict[str, Any]):
    """Store explanation in cache."""
    cache_key = _generate_explanation_cache_key(rule_id, message, category)
    EXPLANATION_CACHE[cache_key] = {
        'data': data,
        'timestamp': datetime.utcnow()
    }


@router.post("/ai/explain")
async def explain_validation_issue(
    request_data: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Provide detailed AI-powered explanations for validation issues and suggestions.
    Uses RAG to find relevant context and best practices.
    Responses are cached for 24 hours to improve performance.
    """
    correlation_id = set_correlation_id()

    logger.info("Generating explanation for validation issue", extra={
        "correlation_id": correlation_id,
        "rule_id": request_data.get("rule_id", "unknown"),
        "category": request_data.get("category", "general")
    })

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
        context_data = await rag_service.retrieve_security_context(rag_query, n_results=3)

        # Build comprehensive explanation prompt
        knowledge_context = context_data.get('context', 'No additional context available')
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
            "messages": [{
                "role": "system",
                "content": "You are an OpenAPI expert. Always respond with valid JSON only, no additional text."
            }, {
                "role": "user",
                "content": explanation_prompt
            }],
            "stream": False,
            "format": "json",  # Force JSON output
            "options": {
                "temperature": 0.3,
                "num_predict": 2048
            }
        }

        response = await llm_service.client.post(llm_service.chat_endpoint, json=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=500,
                detail=f"LLM request failed: {response.status_code} - {response.text}"
            )

        # Extract response text
        response_data = response.json()
        llm_response = response_data.get('message', {}).get('content', '').strip()

        # Log raw response for debugging
        logger.debug(f"Raw LLM response: {llm_response[:200]}...")

        # Try to parse structured response, fallback to plain text
        structured_response = None
        try:
            # Try to extract JSON from response (in case LLM includes extra text)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1

            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]

                # Clean up common JSON issues
                import re

                # Fix trailing commas in arrays and objects
                json_str = re.sub(r',\s*]', ']', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)

                # Fix missing commas between array elements
                json_str = re.sub(r'"\s*\n\s*"', '",\n"', json_str)

                # Try to parse
                structured_response = json.loads(json_str)

                if not isinstance(structured_response, dict):
                    raise ValueError("Response is not a dictionary")

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse JSON: {str(e)}, attempting manual extraction")

            # Try manual extraction as last resort
            try:
                import re

                structured_response = {
                    "explanation": "",
                    "severity": "info",
                    "related_best_practices": [],
                    "example_solutions": [],
                    "additional_resources": []
                }

                # Extract explanation - handle multiline and escaped quotes
                expl_match = re.search(r'"explanation"\s*:\s*"((?:[^"\\]|\\["\\])*)"', llm_response, re.DOTALL)
                if expl_match:
                    structured_response["explanation"] = expl_match.group(1).replace('\\"', '"').replace('\\n', '\n')

                # Extract severity
                sev_match = re.search(r'"severity"\s*:\s*"(\w+)"', llm_response)
                if sev_match:
                    structured_response["severity"] = sev_match.group(1)

                # Extract arrays
                def extract_array(field_name):
                    array_match = re.search(rf'"{field_name}"\s*:\s*\[(.*?)\]', llm_response, re.DOTALL)
                    if array_match:
                        items_str = array_match.group(1)
                        # Extract quoted strings
                        items = re.findall(r'"((?:[^"\\]|\\.)*)"', items_str)
                        return [item.replace('\\"', '"') for item in items]
                    return []

                structured_response["related_best_practices"] = extract_array("related_best_practices")
                structured_response["example_solutions"] = extract_array("example_solutions")
                structured_response["additional_resources"] = extract_array("additional_resources")

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
                    "additional_resources": []
                }

        # Build final response
        if structured_response:
            explanation_response = {
                "explanation": structured_response.get("explanation", "Unable to generate explanation"),
                "severity": structured_response.get("severity", "info"),
                "category": category,
                "related_best_practices": structured_response.get("related_best_practices", []),
                "example_solutions": structured_response.get("example_solutions", []),
                "additional_resources": structured_response.get("additional_resources", []),
                "metadata": {
                    "rule_id": rule_id,
                    "rag_sources": context_data.get('sources', []),
                    "knowledge_base_available": rag_service.is_available(),
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
        else:
            # Complete fallback
            logger.warning("Using complete fallback for explanation")
            explanation_response = {
                "explanation": llm_response if llm_response else "Unable to generate explanation",
                "severity": "info",
                "category": category,
                "related_best_practices": [],
                "example_solutions": [],
                "additional_resources": [],
                "metadata": {
                    "rule_id": rule_id,
                    "rag_sources": context_data.get('sources', []),
                    "knowledge_base_available": rag_service.is_available(),
                    "generated_at": datetime.utcnow().isoformat(),
                    "fallback_format": True
                }
            }

        # Cache the explanation
        _cache_explanation(rule_id, message, category, explanation_response)

        logger.info(f"Generated explanation for rule {rule_id}")
        return explanation_response

    except Exception as e:
        logger.error(f"Explanation generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "EXPLANATION_FAILED",
            "message": f"Failed to generate explanation: {str(e)}",
            "rag_available": rag_service.is_available()
        })


@router.get("/ai/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for explanations.
    """
    # Clean up expired entries
    expired_count = 0
    now = datetime.utcnow()
    expired_keys = [
        key for key, value in EXPLANATION_CACHE.items()
        if now - value['timestamp'] > EXPLANATION_CACHE_TTL
    ]

    for key in expired_keys:
        del EXPLANATION_CACHE[key]
        expired_count += 1

    return {
        "cache_size": len(EXPLANATION_CACHE),
        "expired_entries_cleaned": expired_count,
        "ttl_hours": EXPLANATION_CACHE_TTL.total_seconds() / 3600,
        "timestamp": now.isoformat()
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
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/ai/rag/status")
async def get_rag_status():
    """
    Get status and statistics of the RAG knowledge base.
    """
    try:
        stats = await rag_service.get_knowledge_base_stats()
        return {
            "rag_service": stats,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Failed to get RAG status: {str(e)}")
        return {
            "rag_service": {
                "available": False,
                "error": str(e)
            },
            "timestamp": datetime.utcnow()
        }


@router.post("/ai/test-cases/generate")
async def generate_test_cases(
    request_data: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Generate comprehensive test cases for API operations using AI.
    Creates both positive and negative test scenarios with realistic data.
    """
    correlation_id = set_correlation_id()

    logger.info("Generating test cases for API operation", extra={
        "correlation_id": correlation_id,
        "operation": request_data.get("operation_summary", "unknown")
    })

    try:
        spec_text = request_data.get("spec_text", "")
        operation_path = request_data.get("path", "")
        operation_method = request_data.get("method", "")
        operation_summary = request_data.get("operation_summary", "")
        test_types = request_data.get("test_types", ["positive", "negative", "edge_cases"])

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
                temperature=0.4,  # Moderate creativity for test variety
                max_tokens=3000
            ),
            validate_output=False,
            tags=["test_generation", "quality_assurance"]
        )

        # Get test cases from LLM
        result = await llm_service.process_ai_request(ai_request)

        # Try to parse the JSON response
        try:
            test_cases_data = json.loads(result.updated_spec_text)
            if not isinstance(test_cases_data, dict) or 'test_cases' not in test_cases_data:
                raise ValueError("Invalid test cases format")

            # Enhance test cases with additional metadata
            enhanced_test_cases = []
            for i, test_case in enumerate(test_cases_data['test_cases']):
                enhanced_test_case = {
                    **test_case,
                    "id": f"test_{i+1}",
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                    "priority": _get_test_priority(test_case.get("type", "positive")),
                    "estimated_execution_time": "< 1s"
                }
                enhanced_test_cases.append(enhanced_test_case)

            response = {
                "test_cases": enhanced_test_cases,
                "summary": {
                    "total_tests": len(enhanced_test_cases),
                    "positive_tests": len([tc for tc in enhanced_test_cases if tc.get("type") == "positive"]),
                    "negative_tests": len([tc for tc in enhanced_test_cases if tc.get("type") == "negative"]),
                    "edge_case_tests": len([tc for tc in enhanced_test_cases if tc.get("type") == "edge_case"]),
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat()
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered",
                    "llm_model": "mistral",
                    "test_framework_compatible": ["jest", "postman", "newman", "python-requests"]
                }
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
                    "body": {}
                },
                "expected_response": {
                    "status_code": 200,
                    "body": {}
                },
                "assertions": ["Response status should be successful"],
                "operation": f"{operation_method.upper()} {operation_path}",
                "generated_at": datetime.utcnow().isoformat(),
                "priority": "medium",
                "notes": "Fallback test case - original AI response was not parseable"
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
                    "fallback_mode": True
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered_fallback",
                    "original_response": result.updated_spec_text[:500]
                }
            }

        logger.info(f"Generated {len(response['test_cases'])} test cases for {operation_method.upper()} {operation_path}")
        return response

    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "TEST_GENERATION_FAILED",
            "message": f"Failed to generate test cases: {str(e)}",
            "operation": f"{request_data.get('method', '')} {request_data.get('path', '')}"
        })


def _get_test_priority(test_type: str) -> str:
    """Determine test priority based on test type."""
    priority_map = {
        "positive": "high",
        "negative": "medium",
        "edge_case": "low"
    }
    return priority_map.get(test_type, "medium")


@router.post("/ai/test-suite/generate")
async def generate_test_suite(
    request_data: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Generate a complete test suite for an entire API specification.
    """
    correlation_id = set_correlation_id()

    logger.info("Generating complete test suite", extra={
        "correlation_id": correlation_id,
        "spec_size": len(request_data.get("spec_text", ""))
    })

    try:
        spec_text = request_data.get("spec_text", "")
        test_options = request_data.get("options", {})

        if not spec_text:
            raise ValueError("OpenAPI specification is required")

        # Parse the specification to extract operations
        try:
            from prance import ResolvingParser
            parser = ResolvingParser(spec_string=spec_text, backend='openapi-spec-validator')
            spec = parser.specification
        except Exception as e:
            raise ValueError(f"Invalid OpenAPI specification: {str(e)}")

        # Extract all operations
        operations = []
        paths = spec.get('paths', {})
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method.lower() in ['get', 'post', 'put', 'patch', 'delete', 'options', 'head']:
                    operations.append({
                        'path': path,
                        'method': method,
                        'summary': operation.get('summary', f'{method.upper()} {path}'),
                        'operation_id': operation.get('operationId', f'{method}_{path.replace("/", "_")}')
                    })

        # Generate test cases for each operation
        all_test_cases = []
        for operation in operations[:10]:  # Limit to first 10 operations for performance
            try:
                operation_request = {
                    "spec_text": spec_text,
                    "path": operation['path'],
                    "method": operation['method'],
                    "operation_summary": operation['summary'],
                    "test_types": test_options.get("test_types", ["positive", "negative"])
                }

                # Generate test cases for this operation
                operation_tests = await generate_test_cases(operation_request)

                # Add operation context to each test case
                for test_case in operation_tests['test_cases']:
                    test_case['operation_id'] = operation['operation_id']
                    all_test_cases.append(test_case)

            except Exception as e:
                logger.warning(f"Failed to generate tests for {operation['method']} {operation['path']}: {str(e)}")

        # Organize test suite
        test_suite = {
            "test_suite": {
                "name": f"API Test Suite - {spec.get('info', {}).get('title', 'Unknown API')}",
                "version": spec.get('info', {}).get('version', '1.0.0'),
                "description": f"Comprehensive test suite generated for {len(operations)} operations",
                "test_cases": all_test_cases,
                "collections": _organize_tests_by_collection(all_test_cases),
                "statistics": {
                    "total_operations": len(operations),
                    "total_tests": len(all_test_cases),
                    "coverage": f"{min(len(operations), 10)}/{len(operations)} operations",
                    "test_types": {
                        "positive": len([tc for tc in all_test_cases if tc.get("type") == "positive"]),
                        "negative": len([tc for tc in all_test_cases if tc.get("type") == "negative"]),
                        "edge_cases": len([tc for tc in all_test_cases if tc.get("type") == "edge_case"])
                    }
                }
            },
            "execution_plan": {
                "recommended_order": ["positive", "negative", "edge_case"],
                "parallel_execution": True,
                "estimated_duration": f"{len(all_test_cases) * 2}s"
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "correlation_id": correlation_id,
                "generation_method": "ai_powered_suite"
            }
        }

        logger.info(f"Generated complete test suite with {len(all_test_cases)} test cases for {len(operations)} operations")
        return test_suite

    except Exception as e:
        logger.error(f"Test suite generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "TEST_SUITE_GENERATION_FAILED",
            "message": f"Failed to generate test suite: {str(e)}"
        })


def _organize_tests_by_collection(test_cases: List[Dict]) -> Dict[str, List[Dict]]:
    """Organize test cases into logical collections."""
    collections = {}

    for test_case in test_cases:
        # Group by operation method
        method = test_case.get('request', {}).get('method', 'unknown')
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
        "expires_at": datetime.utcnow() + SECURITY_CACHE_TTL
    }
    logger.info(f"Cached security report: {cache_key}")


@router.post("/ai/security/analyze", response_model=Dict[str, Any])
async def analyze_security(request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)):
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

    logger.info("Starting comprehensive security analysis", extra={"correlation_id": correlation_id})

    try:
        # Check cache first
        cache_key = _generate_security_cache_key(request.spec_text)

        if not request.force_refresh:
            cached_report = _get_cached_security_report(cache_key)
            if cached_report:
                return {
                    "cached": True,
                    "report": cached_report,
                    "correlation_id": correlation_id
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
                    "category": s.category
                }
                for s in request.validation_suggestions
            ]

        # Run security analysis workflow
        report = await security_workflow.analyze(
            request.spec_text,
            validation_suggestions=validation_suggestions_dict
        )

        # Convert to dict for response
        report_dict = report.dict()

        # Cache the report
        _cache_security_report(cache_key, report_dict)

        logger.info(
            f"Security analysis complete. Score: {report.overall_score:.1f}, Risk: {report.risk_level.value}",
            extra={
                "correlation_id": correlation_id,
                "overall_score": report.overall_score,
                "risk_level": report.risk_level.value,
                "total_issues": len(report.all_issues)
            }
        )

        return {
            "cached": False,
            "report": report_dict,
            "correlation_id": correlation_id
        }

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in spec: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_SPEC_FORMAT",
            "message": "Invalid OpenAPI specification format",
            "details": str(e)
        })
    except Exception as e:
        logger.error(f"Security analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "SECURITY_ANALYSIS_FAILED",
            "message": f"Failed to analyze security: {str(e)}"
        })


@router.post("/ai/security/analyze/authentication")
async def analyze_authentication(request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)):
    """
    Authentication-only security analysis.

    Analyzes authentication mechanisms including:
    - Security schemes (OAuth2, API Key, Basic Auth)
    - Authentication weaknesses
    - Unprotected endpoints
    """
    correlation_id = set_correlation_id()

    logger.info("Starting authentication analysis", extra={"correlation_id": correlation_id})

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import AuthenticationAnalyzer
        analyzer = AuthenticationAnalyzer()
        result = await analyzer.analyze(spec)

        return {
            "analysis": result.dict(),
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Authentication analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "AUTHENTICATION_ANALYSIS_FAILED",
            "message": f"Failed to analyze authentication: {str(e)}"
        })


@router.post("/ai/security/analyze/authorization")
async def analyze_authorization(request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)):
    """
    Authorization-only security analysis.

    Analyzes authorization controls including:
    - RBAC implementation
    - Broken Object Level Authorization (BOLA)
    - Broken Function Level Authorization (BFLA)
    - Protected vs unprotected endpoints
    """
    correlation_id = set_correlation_id()

    logger.info("Starting authorization analysis", extra={"correlation_id": correlation_id})

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import AuthorizationAnalyzer
        analyzer = AuthorizationAnalyzer()
        result = await analyzer.analyze(spec)

        return {
            "analysis": result.dict(),
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Authorization analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "AUTHORIZATION_ANALYSIS_FAILED",
            "message": f"Failed to analyze authorization: {str(e)}"
        })


@router.post("/ai/security/analyze/data-exposure")
async def analyze_data_exposure(request: SecurityAnalysisRequest, _: None = Depends(handle_exceptions)):
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

    logger.info("Starting data exposure analysis", extra={"correlation_id": correlation_id})

    try:
        spec = json.loads(request.spec_text)

        from ..services.security import DataExposureAnalyzer
        analyzer = DataExposureAnalyzer()
        result = await analyzer.analyze(spec)

        return {
            "analysis": result.dict(),
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Data exposure analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "DATA_EXPOSURE_ANALYSIS_FAILED",
            "message": f"Failed to analyze data exposure: {str(e)}"
        })


@router.get("/ai/security/report/{spec_hash}")
async def get_security_report(spec_hash: str):
    """
    Retrieve cached security analysis report by spec hash.

    Returns cached report if available, otherwise 404.
    """
    logger.info(f"Retrieving cached security report: {spec_hash}")

    cached_report = _get_cached_security_report(spec_hash)

    if cached_report:
        return {
            "cached": True,
            "report": cached_report,
            "spec_hash": spec_hash
        }
    else:
        raise HTTPException(status_code=404, detail={
            "error": "REPORT_NOT_FOUND",
            "message": f"No cached security report found for hash: {spec_hash}"
        })


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
            suggestion_message=request.suggestion_message
        )

        logger.info(
            f"Generated {len(patch_response.patches)} patch operations "
            f"with confidence {patch_response.confidence}"
        )

        return patch_response

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON spec: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_JSON",
            "message": f"Invalid JSON specification: {str(e)}"
        })
    except Exception as e:
        logger.error(f"Patch generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "PATCH_GENERATION_FAILED",
            "message": f"Failed to generate patch: {str(e)}"
        })


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
            validation_errors=validation_errors
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON spec: {str(e)}")
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_JSON",
            "message": f"Invalid JSON specification: {str(e)}"
        })
    except Exception as e:
        logger.error(f"Patch application failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "PATCH_APPLICATION_FAILED",
            "message": f"Failed to apply patch: {str(e)}"
        })


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
        raise HTTPException(status_code=400, detail={
            "error": "INVALID_REQUEST",
            "message": str(e)
        })
    except Exception as e:
        logger.error(f"Smart fix failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "SMART_FIX_FAILED",
            "message": f"Failed to process smart fix: {str(e)}"
        })


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
                "risk_level": data["report"].get("risk_level")
            }
            for key, data in SECURITY_ANALYSIS_CACHE.items()
        ]
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
        "message": f"Cleared {cache_size} cached security report(s)"
    }


# ============================================================================
# Test Case Generation Endpoints
# ============================================================================

@router.post("/tests/generate")
async def generate_test_cases(request: Dict[str, Any], _: None = Depends(handle_exceptions)):
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
        spec_text = request.get('spec_text')
        path = request.get('path')
        method = request.get('method', 'GET').upper()
        include_ai_tests = request.get('include_ai_tests', True)

        if not spec_text:
            raise HTTPException(status_code=400, detail={
                "error": "MISSING_SPEC",
                "message": "spec_text is required"
            })

        if not path:
            raise HTTPException(status_code=400, detail={
                "error": "MISSING_PATH",
                "message": "path is required"
            })

        # Check cache first
        cached_tests = cache_service.get_test_cases(spec_text, path, method, include_ai_tests)
        if cached_tests:
            logger.info(f"Returning cached test cases for {method} {path}")
            return {
                **cached_tests,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat()
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            try:
                parser = ResolvingParser(spec_string=spec_text, backend='openapi-spec-validator')
                spec = parser.specification
                cache_service.cache_parsed_spec(spec_text, spec)
            except Exception as e:
                logger.error(f"Invalid OpenAPI specification: {str(e)}")
                raise HTTPException(status_code=400, detail={
                    "error": "INVALID_SPEC",
                    "message": f"Failed to parse OpenAPI specification: {str(e)}"
                })

        # Validate path exists
        if path not in spec.get('paths', {}):
            raise HTTPException(status_code=404, detail={
                "error": "PATH_NOT_FOUND",
                "message": f"Path '{path}' not found in specification",
                "available_paths": list(spec.get('paths', {}).keys())
            })

        # Validate method exists
        method_lower = method.lower()
        if method_lower not in spec['paths'][path]:
            raise HTTPException(status_code=404, detail={
                "error": "METHOD_NOT_FOUND",
                "message": f"Method '{method}' not found for path '{path}'",
                "available_methods": list(spec['paths'][path].keys())
            })

        # Generate test cases
        result = await test_case_generator.generate_test_cases(
            spec=spec,
            path=path,
            method=method_lower,
            include_ai_tests=include_ai_tests
        )

        # Cache the results
        cache_service.cache_test_cases(spec_text, path, method_lower, include_ai_tests, result)

        logger.info(
            f"Generated {result['total_tests']} test cases for {method} {path}",
            extra={"correlation_id": correlation_id}
        )

        return {
            **result,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "TEST_GENERATION_FAILED",
            "message": str(e),
            "correlation_id": correlation_id
        })


@router.post("/tests/generate/all")
async def generate_all_test_cases(request: Dict[str, Any], _: None = Depends(handle_exceptions)):
    """
    Generate test cases for all endpoints in an OpenAPI specification.

    Request body:
    - spec_text: OpenAPI specification (JSON/YAML string)
    - include_ai_tests: Whether to include AI-generated tests (default: false for performance)
    - max_endpoints: Maximum number of endpoints to process (default: 50)
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info("Generating test cases for all endpoints", extra={"correlation_id": correlation_id})

    try:
        spec_text = request.get('spec_text')
        include_ai_tests = request.get('include_ai_tests', False)
        max_endpoints = request.get('max_endpoints', 50)

        if not spec_text:
            raise HTTPException(status_code=400, detail={
                "error": "MISSING_SPEC",
                "message": "spec_text is required"
            })

        # Parse specification
        try:
            parser = ResolvingParser(spec_string=spec_text, backend='openapi-spec-validator')
            spec = parser.specification
        except Exception as e:
            raise HTTPException(status_code=400, detail={
                "error": "INVALID_SPEC",
                "message": f"Failed to parse OpenAPI specification: {str(e)}"
            })

        # Generate tests for all endpoints
        all_tests = {}
        total_test_count = 0
        endpoint_count = 0

        for path, path_item in spec.get('paths', {}).items():
            for method in ['get', 'post', 'put', 'patch', 'delete']:
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
                            include_ai_tests=include_ai_tests
                        )

                        endpoint_key = f"{method.upper()} {path}"
                        all_tests[endpoint_key] = result
                        total_test_count += result['total_tests']

                    except Exception as e:
                        logger.error(f"Failed to generate tests for {method.upper()} {path}: {e}")
                        all_tests[f"{method.upper()} {path}"] = {
                            "error": str(e),
                            "endpoint": f"{method.upper()} {path}"
                        }

            if endpoint_count > max_endpoints:
                break

        logger.info(
            f"Generated {total_test_count} tests across {endpoint_count} endpoints",
            extra={"correlation_id": correlation_id}
        )

        return {
            "endpoints": all_tests,
            "summary": {
                "total_endpoints": endpoint_count,
                "total_tests": total_test_count,
                "include_ai_tests": include_ai_tests
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk test generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "BULK_TEST_GENERATION_FAILED",
            "message": str(e),
            "correlation_id": correlation_id
        })


@router.post("/mock/generate-data")
async def generate_mock_data(request: Dict[str, Any], _: None = Depends(handle_exceptions)):
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
        spec_text = request.get('spec_text')
        path = request.get('path')
        method = request.get('method', 'GET').lower()
        response_code = request.get('response_code', '200')
        variation = request.get('variation', 1)
        use_ai = request.get('use_ai', True)

        if not spec_text or not path:
            raise HTTPException(status_code=400, detail={
                "error": "MISSING_PARAMETERS",
                "message": "spec_text and path are required"
            })

        # Parse specification
        parser = ResolvingParser(spec_string=spec_text, backend='openapi-spec-validator')
        spec = parser.specification

        # Get operation and response schema
        operation = spec['paths'][path][method]
        response_spec = operation.get('responses', {}).get(response_code)

        if not response_spec:
            raise HTTPException(status_code=404, detail={
                "error": "RESPONSE_NOT_FOUND",
                "message": f"Response {response_code} not found for {method.upper()} {path}"
            })

        # Extract schema
        response_schema = response_spec.get('content', {}).get('application/json', {}).get('schema')

        if not response_schema:
            raise HTTPException(status_code=400, detail={
                "error": "NO_SCHEMA",
                "message": "No JSON schema found for response"
            })

        # Generate mock data
        mock_data = await mock_data_service.generate_mock_response(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            variation=variation,
            use_ai=use_ai
        )

        logger.info("Mock data generated successfully", extra={"correlation_id": correlation_id})

        return {
            "mock_data": mock_data,
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "variation": variation,
            "used_ai": use_ai,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock data generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "MOCK_DATA_GENERATION_FAILED",
            "message": str(e),
            "correlation_id": correlation_id
        })


@router.post("/mock/generate-variations")
async def generate_mock_variations(request: Dict[str, Any], _: None = Depends(handle_exceptions)):
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

    logger.info("Generating mock data variations", extra={"correlation_id": correlation_id})

    try:
        spec_text = request.get('spec_text')
        path = request.get('path')
        method = request.get('method', 'GET').lower()
        response_code = request.get('response_code', '200')
        count = min(request.get('count', 3), 10)  # Cap at 10

        # Check cache first
        cached_mock_data = cache_service.get_mock_data(spec_text, path, method, response_code, count)
        if cached_mock_data:
            logger.info(f"Returning cached mock data for {method} {path}")
            return {
                "variations": cached_mock_data,
                "count": len(cached_mock_data),
                "endpoint": f"{method.upper()} {path}",
                "response_code": response_code,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat()
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            parser = ResolvingParser(spec_string=spec_text, backend='openapi-spec-validator')
            spec = parser.specification
            cache_service.cache_parsed_spec(spec_text, spec)

        # Get operation and response schema
        operation = spec['paths'][path][method]
        response_spec = operation.get('responses', {}).get(response_code)
        response_schema = response_spec.get('content', {}).get('application/json', {}).get('schema')

        # Generate variations
        variations = await mock_data_service.generate_test_variations(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            count=count
        )

        # Cache the results
        cache_service.cache_mock_data(spec_text, path, method, response_code, count, variations)

        logger.info(f"Generated {len(variations)} mock data variations", extra={"correlation_id": correlation_id})

        return {
            "variations": variations,
            "count": len(variations),
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Mock variations generation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail={
            "error": "MOCK_VARIATIONS_FAILED",
            "message": str(e),
            "correlation_id": correlation_id
        })


# ==================== Cache Management Endpoints ====================


@router.get("/cache/stats")
async def get_cache_stats(_: None = Depends(handle_exceptions)):
    """
    Get cache statistics and performance metrics.

    Returns hit rates, cache sizes, and overall performance data.
    """
    logger.info("Retrieving cache statistics")
    stats = cache_service.get_cache_stats()
    return {
        **stats,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.delete("/cache/clear")
async def clear_cache(
    cache_type: Optional[str] = None,
    _: None = Depends(handle_exceptions)
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
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/cache/invalidate")
async def invalidate_spec_cache(
    request: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Invalidate all cache entries related to a specific specification.

    Request body:
    - spec_text: The OpenAPI specification to invalidate
    """
    spec_text = request.get('spec_text')
    if not spec_text:
        raise HTTPException(status_code=400, detail={
            "error": "MISSING_SPEC",
            "message": "spec_text is required"
        })

    logger.info("Invalidating cache for specification")
    cache_service.invalidate_spec_cache(spec_text)
    return {
        "success": True,
        "message": "Cache invalidated for specification",
        "timestamp": datetime.utcnow().isoformat()
    }