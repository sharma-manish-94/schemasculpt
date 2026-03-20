"""
AI Processing Router.

Core endpoints for AI-powered specification processing and generation.
These endpoints handle:
- Processing AI requests with streaming support
- Generating complete OpenAPI specifications using agentic workflows
"""

import json
import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import get_agent_manager, get_context_manager, get_llm_service
from app.core.logging import set_correlation_id
from app.schemas.ai_schemas import (
    AIRequest,
    AIResponse,
    GenerateSpecRequest,
    StreamingMode,
)

if TYPE_CHECKING:
    from app.services.agent_manager import AgentManager
    from app.services.context_manager import ContextManager
    from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Processing"])


@router.post("/process", response_model=AIResponse)
async def process_specification(
    request: AIRequest,
    llm_service: "LLMService" = Depends(get_llm_service),
    context_manager: "ContextManager" = Depends(get_context_manager),
) -> AIResponse:
    """
    Process an AI request with advanced features including streaming and JSON patching.

    This is the main entry point for AI-powered specification modifications.

    Args:
        request: The AI request containing spec text, prompt, and operation type.
        llm_service: Injected LLM service for AI operations.
        context_manager: Injected context manager for session tracking.

    Returns:
        AIResponse with the processed specification or streaming response.

    Raises:
        HTTPException: If processing fails.
    """
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
        # Get or create session
        session_id = (
            str(request.session_id)
            if request.session_id
            else context_manager.create_session(request.user_id)
        )

        # Add context to request
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
        logger.exception(f"AI processing failed: {str(e)}")
        # Add failed turn to context if session was created
        if "session_id" in locals():
            context_manager.add_conversation_turn(session_id, request, None, False)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "PROCESSING_FAILED",
                "message": f"Failed to process AI request: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.post("/generate", response_model=AIResponse)
async def generate_specification_agentic(
    request: GenerateSpecRequest,
    agent_manager: "AgentManager" = Depends(get_agent_manager),
) -> AIResponse:
    """
    Generate a complete OpenAPI specification using an agentic workflow.

    Uses multiple specialized agents to create a comprehensive API specification
    based on the provided domain and requirements.

    Args:
        request: Generation request with domain, complexity, and requirements.
        agent_manager: Injected agent manager for orchestrating the workflow.

    Returns:
        AIResponse containing the generated specification.

    Raises:
        HTTPException: If generation fails.
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
        logger.exception(f"Agentic spec generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "GENERATION_FAILED",
                "message": f"Failed to generate specification: {str(e)}",
                "correlation_id": correlation_id,
            },
        )
