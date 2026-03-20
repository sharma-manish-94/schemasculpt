"""
Smart AI fix service that intelligently chooses between JSON patches and full spec regeneration.
Optimizes for performance by using patches when possible.
"""

import json
import logging
import re
import time
from typing import Tuple

from app.schemas.ai_schemas import AIRequest, OperationType
from app.schemas.patch_schemas import (
    PatchGenerationRequest,
    SmartAIFixRequest,
    SmartAIFixResponse,
)
from app.services.llm_service import LLMService
from app.services.patch_generator import PatchGenerator, apply_json_patch

logger = logging.getLogger("schemasculpt_ai.smart_fix")


class SmartFixService:
    """
    Intelligently chooses between JSON patch and full spec regeneration
    based on the prompt complexity and target scope.
    """

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.patch_generator = PatchGenerator(llm_service)

    async def process_smart_fix(self, request: SmartAIFixRequest) -> SmartAIFixResponse:
        """
        Main entry point: intelligently processes fix using optimal method.

        Args:
            request: Smart AI fix request

        Returns:
            SmartAIFixResponse with method used and performance metrics
        """
        start_time = time.time()

        logger.info(f"Processing smart AI fix request: {request.prompt[:100]}...")

        # Parse spec
        try:
            spec = json.loads(request.spec_text)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON spec: {e}")
            raise ValueError(f"Invalid OpenAPI spec JSON: {e}")

        # Decide which method to use
        use_patches, reasoning = self._should_use_patches(request, spec)

        logger.info(
            f"Decision: {'PATCHES' if use_patches else 'FULL REGENERATION'} - {reasoning}"
        )

        if request.force_full_regeneration:
            logger.info("Force full regeneration requested by user")
            use_patches = False

        # Execute the appropriate method
        if use_patches:
            result = await self._apply_via_patches(request, spec, start_time)
        else:
            result = await self._apply_via_full_regeneration(request, spec, start_time)

        return result

    def _should_use_patches(
        self, request: SmartAIFixRequest, spec: dict
    ) -> Tuple[bool, str]:
        """
        Intelligently decide whether to use patches or full regeneration.

        Returns:
            (use_patches: bool, reasoning: str)
        """

        # Rule 1: If validation errors are provided, use patches (targeted fix)
        if request.validation_errors:
            return (
                True,
                f"Targeted validation fix ({len(request.validation_errors)} errors)",
            )

        # Rule 2: If target path/method specified, use patches (scoped to specific operation)
        if request.target_path or request.target_method:
            return (
                True,
                f"Scoped to specific operation: {request.target_method.upper() if request.target_method else 'ANY'} {request.target_path or 'any path'}",
            )

        # Rule 3: Analyze prompt for scope indicators
        prompt_lower = request.prompt.lower()

        # Indicators for patch-based approach (targeted fixes)
        patch_indicators = [
            "fix",
            "add security",
            "add response",
            "add operationid",
            "remove",
            "update",
            "modify",
            "change",
            "missing",
            "error",
            "issue",
            "problem",
        ]

        # Indicators for full regeneration (broad changes)
        regen_indicators = [
            "rewrite",
            "redesign",
            "refactor all",
            "add authentication to all",
            "change all",
            "update all",
            "transform",
            "convert",
            "generate",
            "create from scratch",
        ]

        # Check for specific path/method mentions in prompt
        has_path_mention = bool(re.search(r"/[\w\-/{}]+", request.prompt))
        has_method_mention = any(
            method in prompt_lower
            for method in [
                "get ",
                "post ",
                "put ",
                "delete ",
                "patch ",
                "options ",
                "head ",
            ]
        )

        if has_path_mention and has_method_mention:
            return True, "Prompt mentions specific path and method"

        # Count indicators
        patch_score = sum(
            1 for indicator in patch_indicators if indicator in prompt_lower
        )
        regen_score = sum(
            1 for indicator in regen_indicators if indicator in prompt_lower
        )

        if regen_score > patch_score:
            return False, f"Broad scope detected (regen indicators: {regen_score})"

        if patch_score > 0:
            return True, f"Targeted fix detected (patch indicators: {patch_score})"

        # Rule 4: Check spec size - small specs can use full regen efficiently
        spec_size = len(json.dumps(spec))
        if spec_size < 5000:  # < 5KB
            return False, f"Small spec ({spec_size} bytes), full regen is fast"

        # Rule 5: Default to patches for large specs with unclear intent
        return True, "Default to patches for large spec with unclear scope"

    async def _apply_via_patches(
        self, request: SmartAIFixRequest, spec: dict, start_time: float
    ) -> SmartAIFixResponse:
        """Apply fix using JSON Patch approach."""

        logger.info("Applying fix via JSON Patch method")

        # Extract context from request
        context = {}
        if request.target_path:
            context["path"] = request.target_path
        if request.target_method:
            context["method"] = request.target_method

        # If no explicit rule ID, infer from prompt
        rule_id = self._infer_rule_from_prompt(request.prompt)

        # Generate patches
        _ = PatchGenerationRequest(
            spec_text=request.spec_text,
            rule_id=rule_id,
            context=context,
            suggestion_message=request.prompt,
        )

        patch_response = await self.patch_generator.generate_patch(
            spec=spec,
            rule_id=rule_id,
            context=context,
            suggestion_message=request.prompt,
        )

        if not patch_response.patches:
            logger.warning("No patches generated, falling back to full regeneration")
            return await self._apply_via_full_regeneration(request, spec, start_time)

        # Apply patches
        patch_result = await apply_json_patch(spec, patch_response.patches)

        if not patch_result["success"]:
            logger.error(f"Patch application failed: {patch_result['errors']}")
            # Fall back to full regeneration
            logger.info("Falling back to full regeneration due to patch failure")
            return await self._apply_via_full_regeneration(request, spec, start_time)

        processing_time_ms = (time.time() - start_time) * 1000

        return SmartAIFixResponse(
            updated_spec_text=json.dumps(patch_result["result"], indent=2),
            method_used="patch",
            patches_applied=patch_response.patches,
            explanation=patch_response.explanation,
            confidence=patch_response.confidence,
            processing_time_ms=processing_time_ms,
            token_count=100,  # Approximate tokens for patch generation
            warnings=patch_response.warnings,
        )

    async def _apply_via_full_regeneration(
        self, request: SmartAIFixRequest, spec: dict, start_time: float
    ) -> SmartAIFixResponse:
        """Apply fix using full spec regeneration."""

        logger.info("Applying fix via full spec regeneration")

        # Create AI request
        ai_request = AIRequest(
            spec_text=request.spec_text,
            prompt=request.prompt,
            operation_type=OperationType.MODIFY,
        )

        # Process via LLM service
        ai_response = await self.llm_service.process_ai_request(ai_request)

        processing_time_ms = (time.time() - start_time) * 1000

        return SmartAIFixResponse(
            updated_spec_text=ai_response.updated_spec_text,
            method_used="full_regeneration",
            patches_applied=None,
            explanation=ai_response.changes_summary,
            confidence=ai_response.confidence_score,
            processing_time_ms=processing_time_ms,
            token_count=ai_response.performance.token_count,
            warnings=ai_response.validation.warnings if ai_response.validation else [],
        )

    def _infer_rule_from_prompt(self, prompt: str) -> str:
        """
        Infer a rule ID from the prompt for patch generation.
        """
        prompt_lower = prompt.lower()

        # Common fix patterns
        if (
            "security" in prompt_lower
            or "auth" in prompt_lower
            or "bearer" in prompt_lower
        ):
            return "add-operation-security"
        if "response" in prompt_lower and (
            "add" in prompt_lower or "missing" in prompt_lower
        ):
            return "add-success-response"
        if "operationid" in prompt_lower or "operation id" in prompt_lower:
            return "generate-operation-id"
        if "description" in prompt_lower and "missing" in prompt_lower:
            return "add-description"
        if "example" in prompt_lower and "add" in prompt_lower:
            return "add-example"

        # Generic fix
        return "ai-custom-fix"
