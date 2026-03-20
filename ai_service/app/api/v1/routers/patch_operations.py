"""
Patch Operations Router.

Provides endpoints for JSON Patch (RFC 6902) generation and application.
These endpoints enable precise, targeted fixes to OpenAPI specifications
without regenerating the entire spec.

Key features:
- JSON Patch generation from LLM analysis
- Patch application with validation
- Smart fix selection (patch vs full regeneration)
"""

import json
import logging
import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from prance import ResolvingParser

from app.api.deps import get_llm_service, get_patch_generator, get_smart_fix_service
from app.core.logging import set_correlation_id
from app.schemas.patch_schemas import (
    PatchApplicationRequest,
    PatchApplicationResponse,
    PatchGenerationRequest,
    PatchGenerationResponse,
    SmartAIFixRequest,
    SmartAIFixResponse,
)
from app.services.llm_service import LLMService
from app.services.patch_generator import PatchGenerator, apply_json_patch
from app.services.smart_fix_service import SmartFixService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/patch", tags=["Patch Operations"])


@router.post("/generate", response_model=PatchGenerationResponse)
async def generate_json_patch(
    request: PatchGenerationRequest,
    patch_generator: PatchGenerator = Depends(get_patch_generator),
) -> PatchGenerationResponse:
    """
    Generate JSON Patch (RFC 6902) operations for a specific fix.

    This endpoint uses LLM to generate precise patch operations instead of
    regenerating the entire spec, improving accuracy and token efficiency.

    The generated patches can be applied by the backend using standard JSON Patch libraries.

    Args:
        request: Patch generation request containing spec, rule_id, and context.
        patch_generator: Injected patch generator service.

    Returns:
        PatchGenerationResponse with patch operations and confidence score.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        f"Generating JSON Patch for rule: {request.rule_id}",
        extra={"correlation_id": correlation_id},
    )

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
            f"with confidence {patch_response.confidence}",
            extra={"correlation_id": correlation_id},
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


@router.post("/apply", response_model=PatchApplicationResponse)
async def apply_patch(
    request: PatchApplicationRequest,
) -> PatchApplicationResponse:
    """
    Apply JSON Patch operations to a specification.

    This is a utility endpoint for testing. In production, the backend
    (Spring Boot) should apply patches using its own JSON Patch library.

    Args:
        request: Patch application request containing spec and patches.

    Returns:
        PatchApplicationResponse with updated spec and validation results.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        f"Applying {len(request.patches)} patch operations",
        extra={"correlation_id": correlation_id},
    )

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


# Create a separate router for the smart fix endpoint (different prefix)
smart_fix_router = APIRouter(prefix="/ai/fix", tags=["Patch Operations"])


@smart_fix_router.post("/smart", response_model=SmartAIFixResponse)
async def smart_ai_fix(
    request: SmartAIFixRequest,
    smart_fix_service: SmartFixService = Depends(get_smart_fix_service),
) -> SmartAIFixResponse:
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

    Args:
        request: Smart fix request with prompt and spec.
        smart_fix_service: Injected smart fix service.

    Returns:
        SmartAIFixResponse with updated spec and method used.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        f"Smart AI fix request: {request.prompt[:100]}...",
        extra={"correlation_id": correlation_id},
    )

    try:
        response = await smart_fix_service.process_smart_fix(request)

        logger.info(
            f"Smart fix completed using {response.method_used} method in "
            f"{response.processing_time_ms:.0f}ms ({response.token_count} tokens)",
            extra={"correlation_id": correlation_id},
        )

        return response

    except ValueError as e:
        logger.error(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail={"error": "INVALID_REQUEST", "message": str(e)},
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
