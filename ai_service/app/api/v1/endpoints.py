"""
Legacy API endpoints for backward compatibility.

DEPRECATED: This module is retained only for backward compatibility.
New clients should use the domain-specific routers instead:
  - /ai/process -> app/api/v1/routers/ai_processing.py
  - /ai/generate -> app/api/v1/routers/ai_processing.py

This module provides:
  - /process - Legacy endpoint forwarding to /ai/process
  - /specifications/generate - Legacy endpoint forwarding to /ai/generate
  - sanitize_openapi_spec() - Helper function for test generation

Migration Guide:
  - Replace POST /process with POST /ai/process
  - Replace POST /specifications/generate with POST /ai/generate
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Dict

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

# Router with deprecation notice in tags
router = APIRouter(tags=["Legacy Endpoints (Deprecated)"])


# =============================================================================
# Helper Functions (Kept for imports by other modules)
# =============================================================================


def sanitize_openapi_spec(spec_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively sanitize OpenAPI spec by replacing None/null schema values with {}.

    This prevents validation errors when parsing specs with missing schemas.
    This function is imported by routers/test_generation.py.

    Args:
        spec_dict: The OpenAPI specification dictionary to sanitize.

    Returns:
        Sanitized specification with None schemas replaced by empty dicts.
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


# =============================================================================
# Legacy Endpoints (Deprecated - kept for backward compatibility)
# =============================================================================


@router.post("/process", response_model=AIResponse, deprecated=True)
async def process_specification_legacy(
    request: AIRequest,
    llm_service: "LLMService" = Depends(get_llm_service),
    context_manager: "ContextManager" = Depends(get_context_manager),
) -> AIResponse:
    """
    DEPRECATED: Legacy endpoint for processing AI requests.

    Use POST /ai/process instead.

    This endpoint is maintained only for backward compatibility with
    existing clients that haven't migrated to the new API structure.
    """
    correlation_id = set_correlation_id()

    logger.warning(
        f"Deprecated /process endpoint called - migrate to /ai/process",
        extra={
            "correlation_id": correlation_id,
            "operation_type": request.operation_type,
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
        logger.exception(f"Legacy /process endpoint failed: {str(e)}")
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


@router.post("/specifications/generate", deprecated=True)
async def generate_specification_legacy(
    request: GenerateSpecRequest,
    agent_manager: "AgentManager" = Depends(get_agent_manager),
) -> AIResponse:
    """
    DEPRECATED: Legacy endpoint for generating specifications.

    Use POST /ai/generate instead.

    This endpoint is maintained only for backward compatibility with
    existing clients that haven't migrated to the new API structure.
    """
    correlation_id = set_correlation_id()

    logger.warning(
        f"Deprecated /specifications/generate endpoint called - migrate to /ai/generate",
        extra={
            "correlation_id": correlation_id,
            "domain": request.domain,
            "complexity": request.complexity_level,
        },
    )

    try:
        result = await agent_manager.execute_complete_spec_generation(request)
        return result

    except Exception as e:
        logger.exception(f"Legacy /specifications/generate endpoint failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "GENERATION_FAILED",
                "message": f"Failed to generate specification: {str(e)}",
                "correlation_id": correlation_id,
            },
        )
