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
    GenerateSpecRequest, HealthResponse, OperationType, StreamingMode
)
from ..services.agent_manager import AgentManager
from ..services.context_manager import ContextManager
from ..services.llm_service import LLMService
from ..services.prompt_engine import PromptEngine
from ..services.rag_service import RAGService

# Initialize services
router = APIRouter()
logger = get_logger("api.endpoints")

# Service instances
llm_service = LLMService()
agent_manager = AgentManager(llm_service)
context_manager = ContextManager()
prompt_engine = PromptEngine()
rag_service = RAGService()

# Mock server storage
MOCKED_APIS: Dict[str, Dict[str, Any]] = {}

# Response cache for security analysis (TTL: 1 hour)
SECURITY_ANALYSIS_CACHE: Dict[str, Dict[str, Any]] = {}


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
            # Create enhanced prompt for realistic data generation
            prompt = f"""Generate realistic JSON data that conforms to this OpenAPI schema.

Operation: {operation_spec.get('summary', 'API operation')}
Description: {operation_spec.get('description', 'No description')}

Schema:
{json.dumps(response_schema, indent=2)}

Requirements:
- Generate realistic, diverse data
- Follow the schema constraints exactly
- Use appropriate data types and formats
- Make the data contextually relevant to the operation
- Return only the JSON object, no explanations

Variation #{random.randint(1, config.get('response_variety', 3))}"""

            # Use the enhanced LLM service for better responses
            ai_request = AIRequest(
                spec_text=json.dumps(spec, indent=2),
                prompt=prompt,
                operation_type=OperationType.GENERATE
            )

            ai_result = await llm_service.process_ai_request(ai_request)

            try:
                generated_data = json.loads(ai_result.updated_spec_text)
                return JSONResponse(content=generated_data)
            except json.JSONDecodeError:
                # Fallback to simple response
                return JSONResponse(content={"message": "Generated response", "data": {}})

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


@router.post("/ai/explain")
async def explain_validation_issue(
    request_data: Dict[str, Any],
    _: None = Depends(handle_exceptions)
):
    """
    Provide detailed AI-powered explanations for validation issues and suggestions.
    Uses RAG to find relevant context and best practices.
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
        spec_text = request_data.get("spec_text", "")
        category = request_data.get("category", "general")
        context = request_data.get("context", {})

        # Create query for RAG knowledge base
        rag_query = f"OpenAPI best practices validation {rule_id} {category} {message}"

        # Retrieve relevant context from knowledge base
        context_data = await rag_service.retrieve_security_context(rag_query, n_results=3)

        # Build comprehensive explanation prompt
        knowledge_context = context_data.get('context', 'No additional context available')
        if len(knowledge_context) > 800:
            knowledge_context = knowledge_context[:800] + "..."

        explanation_prompt = f"""Explain this OpenAPI validation issue in detail:

ISSUE: {message}
RULE ID: {rule_id}
CATEGORY: {category}
CONTEXT: {json.dumps(context, indent=2)}

KNOWLEDGE BASE CONTEXT:
{knowledge_context}

SPEC EXCERPT:
{spec_text[:500] if spec_text else "No specification provided"}

Provide a comprehensive explanation that includes:
1. Why this is an issue (technical reasoning)
2. Potential problems it could cause
3. Best practice recommendations
4. Specific example solutions
5. Related concepts to understand

Format as structured JSON with: explanation, severity, related_best_practices, example_solutions, additional_resources"""

        # Create AI request for explanation
        ai_request = AIRequest(
            spec_text=spec_text,
            prompt=explanation_prompt,
            operation_type=OperationType.VALIDATE,
            streaming=StreamingMode.DISABLED,
            llm_parameters=LLMParameters(
                temperature=0.3,  # Lower temperature for more factual explanations
                max_tokens=2048
            ),
            validate_output=False,
            tags=["explanation", "educational", "rag_enhanced"]
        )

        # Get explanation from LLM
        result = await llm_service.process_ai_request(ai_request)

        # Try to parse structured response, fallback to plain text
        try:
            structured_response = json.loads(result.updated_spec_text)
            if not isinstance(structured_response, dict):
                raise ValueError("Response is not a dictionary")

            explanation_response = {
                "explanation": structured_response.get("explanation", result.updated_spec_text),
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
        except (json.JSONDecodeError, ValueError):
            # Fallback to plain text explanation
            explanation_response = {
                "explanation": result.updated_spec_text,
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

        logger.info(f"Generated explanation for rule {rule_id}")
        return explanation_response

    except Exception as e:
        logger.error(f"Explanation generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail={
            "error": "EXPLANATION_FAILED",
            "message": f"Failed to generate explanation: {str(e)}",
            "rag_available": rag_service.is_available()
        })


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