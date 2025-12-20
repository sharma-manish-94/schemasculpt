"""
JSON Patch generation service using LLM.
Generates precise RFC 6902 JSON Patch operations instead of full spec regeneration.
"""

import json
import logging
from typing import Any, Dict, List

from app.schemas.patch_schemas import JsonPatchOperation, PatchGenerationResponse
from app.services.llm_service import LLMService

logger = logging.getLogger("schemasculpt_ai.patch_generator")


class PatchGenerator:
    """Generates JSON Patch operations for OpenAPI spec fixes."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def generate_patch(
        self, spec: dict, rule_id: str, context: dict, suggestion_message: str = None
    ) -> PatchGenerationResponse:
        """
        Generate JSON Patch operations for a specific fix.

        Args:
            spec: The OpenAPI specification as dict
            rule_id: The rule identifier to fix
            context: Additional context (path, current value, etc.)
            suggestion_message: The suggestion message

        Returns:
            PatchGenerationResponse with patch operations
        """
        logger.info(f"Generating JSON Patch for rule: {rule_id}")

        # Build focused prompt for patch generation
        prompt = self._build_patch_prompt(spec, rule_id, context, suggestion_message)

        # Get LLM response
        llm_response = await self.llm_service.generate_json_response(
            prompt=prompt,
            schema_description="JSON Patch RFC 6902 operations array with explanation",
            max_tokens=1000,  # Patches are much smaller than full specs
        )

        # Parse LLM response into patch operations
        try:
            response_data = json.loads(llm_response)

            # Convert to patch operations
            patches = [
                JsonPatchOperation(**patch_data)
                for patch_data in response_data.get("patches", [])
            ]

            # Validate and fix patches to ensure parent paths exist
            validated_patches = self._ensure_parent_paths_exist(
                patches, spec, rule_id, context
            )

            return PatchGenerationResponse(
                patches=validated_patches,
                explanation=response_data.get("explanation", "Applied fix"),
                rule_id=rule_id,
                confidence=response_data.get("confidence", 0.9),
                warnings=response_data.get("warnings", []),
            )

        except Exception as e:
            logger.error(f"Failed to parse patch response: {e}")
            logger.error(f"LLM response was: {llm_response}")

            # Return empty patch with error
            return PatchGenerationResponse(
                patches=[],
                explanation=f"Failed to generate patch: {str(e)}",
                rule_id=rule_id,
                confidence=0.0,
                warnings=[f"Patch generation failed: {str(e)}"],
            )

    def _build_patch_prompt(
        self, spec: dict, rule_id: str, context: dict, suggestion_message: str = None
    ) -> str:
        """Build a focused prompt for JSON Patch generation."""

        # Extract relevant part of spec based on context
        relevant_spec = self._extract_relevant_spec(spec, context)

        # Get the actual path and method from context
        api_path = context.get("path", "")
        api_method = context.get("method", "").lower()

        # Build path-specific guidance
        path_guidance = ""
        if api_path and api_method:
            # Escape the path for JSON Pointer
            escaped_path = api_path.replace("~", "~0").replace("/", "~1")
            json_pointer = f"/paths/{escaped_path}/{api_method}"

            path_guidance = f"""
**Target Location**:
- API Path: {api_path}
- Method: {api_method.upper()}
- JSON Pointer: {json_pointer}

**CRITICAL**: Use the exact JSON Pointer path above. For example:
- To add security: "{json_pointer}/security"
- To add response: "{json_pointer}/responses/200"
- To modify summary: "{json_pointer}/summary"
"""

        # Provide rule-specific examples
        rule_examples = self._get_rule_specific_examples(
            rule_id, api_path, api_method, spec
        )

        # Build example based on actual target
        example_patch_path = "/paths/~1example/get/summary"
        if api_path and api_method:
            escaped_path = api_path.replace("~", "~0").replace("/", "~1")
            # Use a generic property for the example to avoid confusion
            example_patch_path = f"/paths/{escaped_path}/{api_method.lower()}/tags"

        # Build concise prompt
        prompt = f"""Generate JSON Patch for OpenAPI spec fix.

Rule: {rule_id}
{path_guidance}
Current spec:
{json.dumps(relevant_spec, indent=2)}

{rule_examples}

Return ONLY JSON (no markdown):
{{
  "patches": [
    {{"op": "add", "path": "{example_patch_path}", "value": ["example"]}}
  ],
  "explanation": "Description of changes",
  "confidence": 0.95,
  "warnings": []
}}

Rules:
- Escape "/" as "~1" in paths
- Use "add" if path doesn't exist, "replace" if it does
- Be precise with JSON Pointer paths
- Apply changes ONLY to the target location specified above"""

        return prompt

    def _ensure_parent_paths_exist(
        self, patches: List[JsonPatchOperation], spec: dict, rule_id: str, context: dict
    ) -> List[JsonPatchOperation]:
        """
        Ensure parent paths exist for all patch operations.
        Adds missing parent paths as needed.
        """
        additional_patches = []

        # Special handling for security-related patches
        if "security" in rule_id.lower():
            # Check if components exists
            if "components" not in spec:
                additional_patches.append(
                    JsonPatchOperation(op="add", path="/components", value={})
                )

            # Check if securitySchemes exists
            if "securitySchemes" not in spec.get("components", {}):
                additional_patches.append(
                    JsonPatchOperation(
                        op="add", path="/components/securitySchemes", value={}
                    )
                )

            # ONLY add a default security scheme if NO schemes exist at all
            existing_schemes = spec.get("components", {}).get("securitySchemes", {})
            if not existing_schemes:
                additional_patches.append(
                    JsonPatchOperation(
                        op="add",
                        path="/components/securitySchemes/bearerAuth",
                        value={
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                        },
                    )
                )

        # Check each patch for parent path existence
        for patch in patches:
            if patch.op == "add" and patch.path:
                # Get parent path
                path_parts = patch.path.rstrip("/").split("/")

                # For paths like /paths/~1user~1{username}/put/security
                # We need to ensure /paths/~1user~1{username}/put exists
                if len(path_parts) > 2:
                    # Build parent paths and check they exist
                    current_path = ""
                    for i, part in enumerate(
                        path_parts[1:-1], 1
                    ):  # Skip first empty and last part
                        current_path += "/" + part

                        # Navigate spec to check if path exists
                        if not self._path_exists_in_spec(current_path, spec):
                            # Add patch to create missing parent
                            logger.info(f"Adding missing parent path: {current_path}")
                            additional_patches.append(
                                JsonPatchOperation(
                                    op="add", path=current_path, value={}
                                )
                            )

        # Return additional patches first, then original patches
        return additional_patches + patches

    def _path_exists_in_spec(self, json_pointer: str, spec: dict) -> bool:
        """Check if a JSON Pointer path exists in the spec."""
        if not json_pointer or json_pointer == "/":
            return True

        # Parse JSON Pointer manually
        # Convert /paths/~1user/get to ["paths", "/user", "get"]
        parts = json_pointer.lstrip("/").split("/")
        current = spec

        for part in parts:
            # Unescape ~1 to / and ~0 to ~
            unescaped = part.replace("~1", "/").replace("~0", "~")

            if isinstance(current, dict):
                if unescaped not in current:
                    return False
                current = current[unescaped]
            elif isinstance(current, list):
                try:
                    index = int(unescaped)
                    if index >= len(current):
                        return False
                    current = current[index]
                except (ValueError, IndexError):
                    return False
            else:
                return False

        return True

    def _get_rule_specific_examples(
        self, rule_id: str, api_path: str, api_method: str, spec: dict
    ) -> str:
        """Get rule-specific examples to guide the LLM."""
        escaped_path = (
            api_path.replace("~", "~0").replace("/", "~1") if api_path else "~1users"
        )
        method = api_method.lower() if api_method else "get"

        # Get existing security schemes from spec
        existing_schemes = list(
            spec.get("components", {}).get("securitySchemes", {}).keys()
        )
        schemes_list = (
            ", ".join(existing_schemes) if existing_schemes else "none defined"
        )

        # Build example using first existing scheme or a generic one
        example_scheme = existing_schemes[0] if existing_schemes else "bearerAuth"

        examples = {
            "add-operation-security": f"""CRITICAL: Use EXISTING security schemes, do NOT create new ones!

**Existing Security Schemes**: {schemes_list}

INSTRUCTIONS:
- If security schemes exist: Reference them in the operation's security array
- Do NOT create new security schemes
- Do NOT replace existing securitySchemes
- ONLY add security to the specific operation

Example (using existing scheme "{example_scheme}"):
"patches": [
  {{"op": "add", "path": "/paths/{escaped_path}/{method}/security", "value": [{{"{example_scheme}": []}}]}}
]

WRONG - DO NOT DO THIS:
- Do NOT use "example" as a scheme name
- Do NOT replace /components/securitySchemes
- Do NOT add new schemes unless they don't exist""",
            "add-success-response": f'Example path: "/paths/{escaped_path}/{method}/responses/200"',
            "generate-operation-id": f'Example path: "/paths/{escaped_path}/{method}/operationId"',
        }

        return examples.get(rule_id, "")

    def _extract_relevant_spec(self, spec: dict, context: dict) -> dict:
        """
        Extract the MINIMAL relevant portion of the spec based on context.
        This reduces prompt size and improves LLM focus and response time.
        """
        # If context has a specific path and method, extract ONLY that operation
        if "path" in context and "method" in context:
            api_path = context["path"]
            api_method = context["method"].lower()

            try:
                # Get the specific operation
                operation = spec.get("paths", {}).get(api_path, {}).get(api_method, {})

                # Return ONLY the relevant operation with minimal context
                return {
                    "target_path": api_path,
                    "target_method": api_method,
                    "operation": operation,
                    "components": {
                        "securitySchemes": spec.get("components", {}).get(
                            "securitySchemes", {}
                        )
                    },
                }
            except Exception as e:
                logger.warning(
                    f"Could not extract {api_method.upper()} {api_path}: {e}"
                )

        # For security rules, return minimal security context
        if rule_id := context.get("ruleId"):
            if "security" in rule_id.lower():
                return {
                    "securitySchemes": spec.get("components", {}).get(
                        "securitySchemes", {}
                    ),
                    "security": spec.get("security", []),
                }

        # Default: return minimal spec structure
        return {
            "info": {"title": spec.get("info", {}).get("title", "API")},
            "openapi": spec.get("openapi", "3.0.0"),
        }


async def apply_json_patch(
    spec: dict, patches: List[JsonPatchOperation]
) -> Dict[str, Any]:
    """
    Apply JSON Patch operations to a spec.
    Returns {"success": bool, "result": dict, "errors": list}
    """
    import jsonpatch

    try:
        # Convert patches to dict format for jsonpatch library
        patch_dicts = [
            {k: v for k, v in patch.dict(by_alias=True).items() if v is not None}
            for patch in patches
        ]

        # Create patch object
        patch = jsonpatch.JsonPatch(patch_dicts)

        # Apply patch
        result = patch.apply(spec)

        return {"success": True, "result": result, "errors": []}
    except jsonpatch.JsonPatchException as e:
        logger.error(f"JSON Patch application failed: {e}")
        return {
            "success": False,
            "result": spec,  # Return original spec
            "errors": [str(e)],
        }
    except Exception as e:
        logger.error(f"Unexpected error applying patch: {e}")
        return {
            "success": False,
            "result": spec,
            "errors": [f"Unexpected error: {str(e)}"],
        }
