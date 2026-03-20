"""
Prompt Engine Router.

Endpoints for intelligent prompt generation and prompt engine statistics.
The prompt engine analyzes requests and generates optimized prompts
for the underlying LLM.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_prompt_engine
from app.schemas.ai_schemas import AIRequest, OperationType

if TYPE_CHECKING:
    from app.services.prompt_engine import PromptEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/prompt", tags=["Prompt Engine"])


@router.post("/generate")
async def generate_intelligent_prompt(
    request_data: Dict[str, Any],
    context_id: Optional[str] = None,
    prompt_engine: "PromptEngine" = Depends(get_prompt_engine),
) -> Dict[str, Any]:
    """
    Generate intelligent prompts using the prompt engine.

    Analyzes the request and generates optimized system and user prompts
    tailored to the operation type and context.

    Args:
        request_data: Dictionary containing spec_text, prompt, and operation_type.
        context_id: Optional context ID for context-aware prompt generation.
        prompt_engine: Injected prompt engine.

    Returns:
        Dictionary containing generated system and user prompts.

    Raises:
        HTTPException: 400 if prompt generation fails.
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
        logger.exception(f"Prompt generation failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={
                "error": "PROMPT_GENERATION_FAILED",
                "message": f"Failed to generate prompt: {str(e)}",
            },
        )


@router.get("/statistics")
async def get_prompt_statistics(
    prompt_engine: "PromptEngine" = Depends(get_prompt_engine),
) -> Dict[str, Any]:
    """
    Get prompt engine statistics.

    Returns metrics about prompt generation performance,
    including usage patterns and optimization metrics.

    Returns:
        Dictionary containing prompt engine statistics.
    """
    return prompt_engine.get_prompt_statistics()
