"""
Enhanced API endpoints for SchemaSculpt AI Service.
Integrates advanced LLM service, agentic workflows, streaming, and comprehensive AI features.
"""

import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from prance import ResolvingParser

from ..schemas.ai_schemas import (
    AIRequest, AIResponse, MockStartRequest, MockStartResponse,
    GenerateSpecRequest, StreamingChunk, HealthResponse, ErrorResponse,
    OperationType, StreamingMode
)
from ..services.llm_service import LLMService
from ..services.agent_manager import AgentManager
from ..services.context_manager import ContextManager
from ..services.prompt_engine import PromptEngine
from ..core.config import settings
from ..core.logging import get_logger, set_correlation_id
from ..core.exceptions import SchemaSculptException, ValidationError, LLMError


# Initialize services
router = APIRouter()
logger = get_logger("api.endpoints")

# Service instances
llm_service = LLMService()
agent_manager = AgentManager(llm_service)
context_manager = ContextManager()
prompt_engine = PromptEngine()

# Mock server storage
MOCKED_APIS: Dict[str, Dict[str, Any]] = {}


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