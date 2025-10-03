"""
JSON Patch generation service using LLM.
Generates precise RFC 6902 JSON Patch operations instead of full spec regeneration.
"""

import json
import logging
from typing import List, Dict, Any
from app.services.llm_service import LLMService
from app.schemas.patch_schemas import JsonPatchOperation, PatchGenerationResponse

logger = logging.getLogger("schemasculpt_ai.patch_generator")


class PatchGenerator:
    """Generates JSON Patch operations for OpenAPI spec fixes."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def generate_patch(
        self,
        spec: dict,
        rule_id: str,
        context: dict,
        suggestion_message: str = None
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
            max_tokens=1000  # Patches are much smaller than full specs
        )

        # Parse LLM response into patch operations
        try:
            response_data = json.loads(llm_response)

            # Convert to patch operations
            patches = [
                JsonPatchOperation(**patch_data)
                for patch_data in response_data.get("patches", [])
            ]

            return PatchGenerationResponse(
                patches=patches,
                explanation=response_data.get("explanation", "Applied fix"),
                rule_id=rule_id,
                confidence=response_data.get("confidence", 0.9),
                warnings=response_data.get("warnings", [])
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
                warnings=[f"Patch generation failed: {str(e)}"]
            )

    def _build_patch_prompt(
        self,
        spec: dict,
        rule_id: str,
        context: dict,
        suggestion_message: str = None
    ) -> str:
        """Build a focused prompt for JSON Patch generation."""

        # Extract relevant part of spec based on context
        relevant_spec = self._extract_relevant_spec(spec, context)

        prompt = f"""You are an OpenAPI specification expert. Generate JSON Patch (RFC 6902) operations to fix a specific issue.

**Rule to Fix**: {rule_id}
**Suggestion**: {suggestion_message or "Fix the issue identified by the rule"}
**Context**: {json.dumps(context, indent=2)}

**Relevant Spec Section**:
```json
{json.dumps(relevant_spec, indent=2)}
```

**Task**: Generate minimal JSON Patch operations to fix this issue.

**JSON Patch Operations**:
- "add": Add a new value (path must not exist)
- "replace": Replace existing value (path must exist)
- "remove": Remove a value (path must exist)
- "move": Move a value from one path to another
- "copy": Copy a value from one path to another
- "test": Test that a path has a specific value

**Response Format** (JSON only, no markdown):
{{
  "patches": [
    {{
      "op": "replace",
      "path": "/info/version",
      "value": "1.0.0"
    }}
  ],
  "explanation": "Brief explanation of what was fixed",
  "confidence": 0.95,
  "warnings": ["Optional warning messages"]
}}

**Important**:
1. Use JSON Pointer format for paths (e.g., "/paths/~1users~1{{id}}/get/summary")
2. Escape "/" as "~1" and "~" as "~0" in path segments
3. Generate MINIMAL patches - only what's necessary to fix the issue
4. Be precise - wrong paths will cause patch application to fail
5. Return ONLY valid JSON, no markdown code blocks

Generate the patch now:"""

        return prompt

    def _extract_relevant_spec(self, spec: dict, context: dict) -> dict:
        """
        Extract the relevant portion of the spec based on context.
        This reduces prompt size and improves LLM focus.
        """
        # If context has a specific path, extract that section
        if "path" in context:
            path = context["path"]
            try:
                # Navigate to the relevant part
                parts = path.strip("/").split("/")
                current = spec
                for part in parts:
                    if isinstance(current, dict):
                        current = current.get(part, {})
                    elif isinstance(current, list):
                        try:
                            current = current[int(part)]
                        except (ValueError, IndexError):
                            break

                # Return the extracted section with some context
                return {
                    "extracted_path": path,
                    "content": current,
                    "full_spec_available": True
                }
            except Exception as e:
                logger.warning(f"Could not extract path {path}: {e}")

        # For rules that affect specific sections
        if rule_id := context.get("ruleId"):
            if "security" in rule_id.lower():
                return {
                    "securitySchemes": spec.get("components", {}).get("securitySchemes", {}),
                    "security": spec.get("security", []),
                    "info": spec.get("info", {})
                }
            elif "server" in rule_id.lower():
                return {
                    "servers": spec.get("servers", []),
                    "info": spec.get("info", {})
                }
            elif "operation" in rule_id.lower():
                return {
                    "paths": spec.get("paths", {}),
                    "info": spec.get("info", {})
                }

        # Default: return a focused view of the spec
        return {
            "info": spec.get("info", {}),
            "servers": spec.get("servers", []),
            "paths": spec.get("paths", {}),
            "components": spec.get("components", {})
        }


async def apply_json_patch(spec: dict, patches: List[JsonPatchOperation]) -> Dict[str, Any]:
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

        return {
            "success": True,
            "result": result,
            "errors": []
        }
    except jsonpatch.JsonPatchException as e:
        logger.error(f"JSON Patch application failed: {e}")
        return {
            "success": False,
            "result": spec,  # Return original spec
            "errors": [str(e)]
        }
    except Exception as e:
        logger.error(f"Unexpected error applying patch: {e}")
        return {
            "success": False,
            "result": spec,
            "errors": [f"Unexpected error: {str(e)}"]
        }
