"""
Advanced LLM Service for SchemaSculpt AI.
Provides streaming, JSON patching, agentic workflows, and intelligent prompt engineering.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Union

import httpx
import jsonpatch

from ..core.config import settings
from ..core.exceptions import LLMError, LLMTimeoutError, OpenAPIError, ValidationError
from ..core.logging import get_logger, set_correlation_id
from ..schemas.ai_schemas import (
    AIRequest,
    AIResponse,
    GenerateSpecRequest,
    JSONPatchOperation,
    LLMParameters,
    OperationType,
    PerformanceMetrics,
    StreamingChunk,
    StreamingMode,
    ValidationResult,
)
from .intelligent_workflow import IntelligentOpenAPIWorkflow


class LLMService:
    """
    Advanced LLM service with streaming, JSON patching, and agentic capabilities.
    """

    def __init__(self, auto_close_client: bool = False):
        self.logger = get_logger("llm_service")
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout),
            limits=httpx.Limits(max_connections=settings.max_concurrent_requests),
        )
        self.base_url = settings.ollama_base_url
        self.chat_endpoint = f"{self.base_url}{settings.ollama_chat_endpoint}"
        self.generate_endpoint = f"{self.base_url}{settings.ollama_generate_endpoint}"
        self._auto_close_client = auto_close_client

        # Cache for conversation context
        self._context_cache: Dict[str, Any] = {}

        # Initialize intelligent workflow
        self.intelligent_workflow = IntelligentOpenAPIWorkflow(self)

        # Prompt templates
        self._system_prompts = {
            "modify": self._get_modification_system_prompt(),
            "generate": self._get_generation_system_prompt(),
            "validate": self._get_validation_system_prompt(),
            "patch": self._get_patch_system_prompt(),
        }

        def run_security_analysis(self, spec_text: str, context: str) -> str:
            """Performs a security analysis of a spec using the provided RAG context."""
            messages = self._build_rag_security_prompt(spec_text, context)

            payload = {
                "model": "codellama:13b-instruct-q4_K_M",
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            response = requests.post(OLLAMA_URL, json=payload)

            if response.status_code == 200:
                return self._extract_generated_text(response.json())
            else:
                return f"Error from Ollama service: {response.status_code} - {response.text}"

        def _build_rag_security_prompt(self, spec: str, context: str) -> list:
            """Builds a prompt that includes the retrieved context."""
            system_prompt = "You are an expert API security auditor..."
            user_prompt = f"""Please analyze the following OpenAPI specification.
    <SPECIFICATION>
    {spec}
    </SPECIFICATION>

    Use the following security best practices as your primary reference.
    <CONTEXT>
    {context}
    </CONTEXT>

    Based ONLY on the provided context, list any potential security issues in the specification."""

            return [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

    async def process_ai_request(
        self, request: AIRequest
    ) -> Union[AIResponse, AsyncGenerator[StreamingChunk, None]]:
        """
        Process AI request with advanced features including streaming and JSON patching.
        """
        start_time = time.time()
        set_correlation_id(
            str(request.context.conversation_id)
            if request.context.conversation_id
            else None
        )

        self.logger.info(
            f"Processing AI request: {request.operation_type}",
            extra={
                "operation_type": request.operation_type,
                "streaming": request.streaming != StreamingMode.DISABLED,
                "has_patches": bool(request.json_patches),
            },
        )

        try:
            # Validate input spec
            if request.validate_output:
                validation_result = await self._validate_openapi_spec(request.spec_text)
                if not validation_result.is_valid and not request.auto_fix:
                    raise ValidationError(
                        f"Invalid OpenAPI spec: {validation_result.errors}"
                    )

            # Handle JSON patch operations
            if request.json_patches:
                return await self._process_patch_request(request, start_time)

            # Handle streaming vs non-streaming
            if request.streaming != StreamingMode.DISABLED:
                return self._process_streaming_request(request, start_time)
            else:
                return await self._process_standard_request(request, start_time)

        except Exception as e:
            self.logger.error(
                f"AI request processing failed: {str(e)}", extra={"error": str(e)}
            )
            if isinstance(e, (LLMError, ValidationError, OpenAPIError)):
                raise
            raise LLMError(f"Unexpected error in AI processing: {str(e)}")

    async def _process_standard_request(
        self, request: AIRequest, start_time: float
    ) -> AIResponse:
        """
        Process standard (non-streaming) AI request with self-correction.
        """
        messages = await self._build_intelligent_prompt(request)

        # Initial attempt
        try:
            response_text = await self._call_llm_with_retry(
                messages, request.llm_parameters
            )

            # Apply post-processing fixes
            response_text = self._fix_openapi_issues(response_text)

            # Validate and potentially self-correct
            validation_result = await self._validate_and_correct_response(
                response_text, request, messages
            )

            # Build performance metrics
            performance = PerformanceMetrics(
                processing_time_ms=(time.time() - start_time) * 1000,
                token_count=len(response_text.split()),  # Rough estimate
                model_used=request.llm_parameters.model,
                cache_hit=False,  # TODO: Implement caching
                retry_count=0,  # TODO: Track retries
            )

            # Calculate changes and generate summary
            changes_summary, modified_paths = await self._analyze_changes(
                request.spec_text, validation_result["corrected_spec"] or response_text
            )

            return AIResponse(
                updated_spec_text=validation_result["corrected_spec"] or response_text,
                operation_type=request.operation_type,
                validation=validation_result["validation"],
                confidence_score=validation_result["confidence_score"],
                changes_summary=changes_summary,
                modified_paths=modified_paths,
                performance=performance,
                context=request.context,
            )

        except Exception as e:
            self.logger.error(f"Standard request processing failed: {str(e)}")
            raise LLMError(f"Failed to process AI request: {str(e)}")

    async def _process_streaming_request(
        self, request: AIRequest, start_time: float
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Process streaming AI request with real-time updates.
        """
        messages = await self._build_intelligent_prompt(request)
        chunk_id = 0

        try:
            async for chunk_text in self._stream_llm_response(
                messages, request.llm_parameters
            ):
                chunk = StreamingChunk(
                    chunk_id=chunk_id,
                    content=chunk_text,
                    is_final=False,
                    metadata={"timestamp": datetime.utcnow().isoformat()},
                )
                yield chunk
                chunk_id += 1

            # Final validation chunk
            final_chunk = StreamingChunk(
                chunk_id=chunk_id,
                content="",
                is_final=True,
                metadata={
                    "processing_time_ms": (time.time() - start_time) * 1000,
                    "total_chunks": chunk_id,
                },
            )
            yield final_chunk

        except Exception as e:
            error_chunk = StreamingChunk(
                chunk_id=chunk_id,
                content=f"Error: {str(e)}",
                is_final=True,
                metadata={"error": True},
            )
            yield error_chunk

    async def _process_patch_request(
        self, request: AIRequest, start_time: float
    ) -> AIResponse:
        """
        Process JSON patch operations with intelligent conflict resolution.
        """
        try:
            # Parse the original spec
            original_spec = json.loads(request.spec_text)

            # Apply patches with validation
            patched_spec = await self._apply_json_patches(
                original_spec, request.json_patches
            )

            # Validate the patched result
            validation_result = await self._validate_openapi_spec(
                json.dumps(patched_spec, indent=2)
            )

            if not validation_result.is_valid and request.auto_fix:
                # Use AI to fix validation issues
                fix_request = AIRequest(
                    spec_text=json.dumps(patched_spec, indent=2),
                    prompt=f"Fix validation errors: {', '.join(validation_result.errors)}",
                    operation_type=OperationType.VALIDATE,
                    llm_parameters=request.llm_parameters,
                )
                patched_spec = await self._ai_fix_validation_issues(fix_request)

            performance = PerformanceMetrics(
                processing_time_ms=(time.time() - start_time) * 1000,
                token_count=0,  # No LLM tokens used for patch operations
                model_used="json_patch",
                cache_hit=False,
            )

            changes_summary = (
                f"Applied {len(request.json_patches)} JSON patch operations"
            )
            modified_paths = [patch.path for patch in request.json_patches]

            return AIResponse(
                updated_spec_text=json.dumps(patched_spec, indent=2),
                operation_type=OperationType.PATCH,
                validation=validation_result,
                confidence_score=1.0,  # High confidence for direct patch operations
                changes_summary=changes_summary,
                applied_patches=request.json_patches,
                modified_paths=modified_paths,
                performance=performance,
                context=request.context,
            )

        except Exception as e:
            self.logger.error(f"JSON patch operation failed: {str(e)}")
            raise OpenAPIError(f"Failed to apply JSON patches: {str(e)}")

    async def generate_spec_from_prompt(
        self, request: GenerateSpecRequest
    ) -> AIResponse:
        """
        Orchestrates the intelligent multi-agent process to generate a comprehensive OpenAPI spec.
        """
        self.logger.info(
            "Starting intelligent multi-agent spec generation",
            extra={
                "domain": request.domain,
                "complexity": request.complexity_level,
                "use_intelligent_workflow": True,
            },
        )

        try:
            # Use the intelligent workflow instead of the old agentic workflow
            return await self.intelligent_workflow.generate_specification(request)

        except Exception as e:
            self.logger.error(f"Intelligent workflow generation failed: {str(e)}")
            raise LLMError(f"Failed to generate specification: {str(e)}")

    async def _execute_agentic_workflow(
        self, request: GenerateSpecRequest
    ) -> Dict[str, Any]:
        """
        Execute the multi-agent workflow for comprehensive spec generation.
        """
        total_tokens = 0
        suggestions = []

        # Agent 1: Domain Analysis
        self.logger.info("Agent 1: Analyzing domain and requirements")
        domain_analysis = await self._analyze_domain_requirements(request)
        total_tokens += domain_analysis["tokens"]

        # Agent 2: Entity Extraction
        self.logger.info("Agent 2: Extracting entities and relationships")
        entities = await self._extract_entities_with_relationships(
            request, domain_analysis
        )
        total_tokens += entities["tokens"]

        # Agent 3: Schema Generation
        self.logger.info("Agent 3: Generating schemas with advanced features")
        schemas = await self._generate_advanced_schemas(entities["entities"], request)
        total_tokens += schemas["tokens"]

        # Agent 4: Path Generation
        self.logger.info("Agent 4: Generating RESTful paths with patterns")
        paths = await self._generate_intelligent_paths(entities["entities"], request)
        total_tokens += paths["tokens"]

        # Agent 5: Security and Documentation
        self.logger.info("Agent 5: Adding security and documentation")
        security_docs = await self._enhance_with_security_docs(request)
        total_tokens += security_docs["tokens"]

        # Agent 6: Final Assembly and Optimization
        self.logger.info("Agent 6: Assembling and optimizing final spec")
        final_spec = await self._assemble_optimized_spec(
            domain_analysis, entities, schemas, paths, security_docs, request
        )

        return {
            "spec": json.dumps(final_spec, indent=2),
            "total_tokens": total_tokens,
            "entity_count": len(entities["entities"]),
            "confidence": min(0.95, (len(entities["entities"]) * 0.1) + 0.5),
            "suggestions": suggestions + security_docs["suggestions"],
        }

    async def _build_intelligent_prompt(
        self, request: AIRequest
    ) -> List[Dict[str, str]]:
        """
        Build intelligent, context-aware prompts with advanced techniques.
        """
        # Get appropriate system prompt based on operation type
        system_prompt = self._system_prompts.get(
            request.operation_type.value, self._system_prompts["modify"]
        )

        # Enhance with context if available
        if request.context and request.context.previous_operations:
            context_info = self._build_context_summary(request.context)
            system_prompt += f"\n\nContext from previous operations:\n{context_info}"

        # Build user prompt with advanced techniques
        user_prompt = await self._build_enhanced_user_prompt(request)

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    async def _build_enhanced_user_prompt(self, request: AIRequest) -> str:
        """
        Build enhanced user prompt with context and intelligent formatting.
        """
        # Analyze the current spec for context
        spec_analysis = await self._analyze_spec_structure(request.spec_text)

        # Build contextual prompt sections
        prompt_sections = [
            "**Current OpenAPI Specification Analysis:**",
            f"- Version: {spec_analysis['version']}",
            f"- Total Paths: {spec_analysis['path_count']}",
            f"- Components: {spec_analysis['component_count']}",
            f"- Complexity: {spec_analysis['complexity_level']}",
            "",
            "**Current Specification:**",
            "```json",
            request.spec_text,
            "```",
            "",
            "**Your Task:**",
            request.prompt,
            "",
            "**Additional Context:**",
        ]

        # Add operation-specific guidance
        if request.operation_type == OperationType.MODIFY:
            prompt_sections.extend(
                [
                    "- Preserve existing structure unless explicitly asked to change",
                    "- Ensure all references remain valid after modifications",
                    "- Follow OpenAPI 3.0+ best practices",
                ]
            )
        elif request.operation_type == OperationType.ENHANCE:
            prompt_sections.extend(
                [
                    "- Add comprehensive examples and descriptions",
                    "- Include appropriate security schemes",
                    "- Add validation constraints where applicable",
                ]
            )

        # Add target paths if specified
        if request.target_paths:
            prompt_sections.extend(
                [
                    "",
                    "**Focus Areas:**",
                    f"Concentrate changes on these paths: {', '.join(request.target_paths)}",
                ]
            )

        return "\n".join(prompt_sections)

    async def _call_llm_with_retry(
        self,
        messages: List[Dict[str, str]],
        params: LLMParameters,
        max_retries: int = 3,
    ) -> str:
        """
        Call LLM with intelligent retry logic and error handling.
        """
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": params.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": params.temperature,
                        "top_p": params.top_p,
                        "frequency_penalty": params.frequency_penalty,
                        "presence_penalty": params.presence_penalty,
                        "max_tokens": params.max_tokens,
                    },
                    "format": "json",
                }

                response = await self.client.post(self.chat_endpoint, json=payload)

                if response.status_code == 200:
                    response_data = response.json()
                    return self._extract_and_clean_response(response_data)
                else:
                    self.logger.warning(
                        f"LLM request failed with status {response.status_code}: {response.text}"
                    )
                    if attempt == max_retries - 1:
                        raise LLMError(
                            f"LLM service error: {response.status_code} - {response.text}"
                        )

            except httpx.TimeoutException:
                self.logger.warning(f"LLM request timeout on attempt {attempt + 1}")
                if attempt == max_retries - 1:
                    raise LLMTimeoutError("LLM request timed out after all retries")

            except Exception as e:
                self.logger.error(
                    f"LLM request error on attempt {attempt + 1}: {str(e)}"
                )
                if attempt == max_retries - 1:
                    raise LLMError(f"LLM request failed: {str(e)}")

            # Exponential backoff
            await asyncio.sleep(2**attempt)

        raise LLMError("Max retries exceeded")

    def _extract_and_clean_response(self, response_data: Dict[str, Any]) -> str:
        """
        Extract and clean LLM response with advanced parsing.
        """
        try:
            raw_content = response_data["message"]["content"]

            # Advanced cleaning with multiple strategies
            cleaned_content = self._advanced_content_cleaning(raw_content)

            return cleaned_content

        except (KeyError, IndexError, TypeError) as e:
            raise LLMError(f"Failed to parse LLM response: {str(e)}")

    def _advanced_content_cleaning(self, raw_content: str) -> str:
        """
        Advanced content cleaning with multiple parsing strategies.
        """
        content = raw_content.strip()

        # Strategy 1: Remove markdown code blocks
        patterns = [
            (r"```(?:json|yaml|javascript)\n?", ""),
            (r"```\n?", ""),
            (r"^[\s]*//.*$", ""),  # Remove comments
            (r"/\*.*?\*/", ""),  # Remove block comments
        ]

        for pattern, replacement in patterns:
            import re

            content = re.sub(
                pattern, replacement, content, flags=re.MULTILINE | re.DOTALL
            )

        # Strategy 2: Extract JSON/YAML content
        json_start = content.find("{")
        yaml_start = content.find("openapi:")

        if json_start != -1 and (yaml_start == -1 or json_start < yaml_start):
            # Find matching closing brace
            brace_count = 0
            start_idx = json_start
            for i, char in enumerate(content[json_start:], json_start):
                if char == "{":
                    brace_count += 1
                elif char == "}":
                    brace_count -= 1
                    if brace_count == 0:
                        content = content[start_idx : i + 1]
                        break
        elif yaml_start != -1:
            content = content[yaml_start:]

        return content.strip()

    async def _stream_llm_response(
        self, messages: List[Dict[str, str]], params: LLMParameters
    ) -> AsyncGenerator[str, None]:
        """
        Stream LLM response for real-time updates.
        """
        try:
            payload = {
                "model": params.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": params.temperature,
                    "top_p": params.top_p,
                    "max_tokens": params.max_tokens,
                },
            }

            async with self.client.stream(
                "POST", self.chat_endpoint, json=payload
            ) as response:
                if response.status_code != 200:
                    raise LLMError(f"Streaming request failed: {response.status_code}")

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            chunk_data = json.loads(line)
                            if chunk_data.get("message", {}).get("content"):
                                yield chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            self.logger.error(f"Streaming failed: {str(e)}")
            raise LLMError(f"Streaming request failed: {str(e)}")

    async def _apply_json_patches(
        self, original_spec: Dict[str, Any], patches: List[JSONPatchOperation]
    ) -> Dict[str, Any]:
        """
        Apply JSON patches with intelligent conflict resolution.
        """
        try:
            # Convert patches to jsonpatch format
            patch_objects = []
            for patch in patches:
                patch_dict = {"op": patch.op, "path": patch.path}
                if patch.value is not None:
                    patch_dict["value"] = patch.value
                if patch.from_path:
                    patch_dict["from"] = patch.from_path

                patch_objects.append(patch_dict)

            # Apply patches with validation
            patch = jsonpatch.JsonPatch(patch_objects)
            result = patch.apply(original_spec)

            return result

        except Exception as e:
            self.logger.error(f"JSON patch application failed: {str(e)}")
            raise OpenAPIError(f"Failed to apply JSON patches: {str(e)}")

    # System prompt templates for different operation types
    def _get_modification_system_prompt(self) -> str:
        return """
You are an expert OpenAPI architect specializing in precise specification modifications.

**Core Principles:**
1. Preserve existing structure unless explicitly requested to change
2. Maintain all existing references and relationships
3. Follow OpenAPI 3.0+ specification standards strictly
4. Ensure backward compatibility when possible
5. Output ONLY valid JSON without commentary

**Critical JSON Structure Rules:**
- Path operations (get, post, put, delete) must be objects, never strings
- All operation objects must have a "responses" field
- Schema references must point to existing schemas in components/schemas
- When adding $ref, ensure the referenced schema exists
- Operation-level fields (summary, operationId) go INSIDE the operation object, not at path level

**Modification Process:**
1. Analyze the current specification structure
2. Identify the exact components to modify
3. Apply changes while preserving schema integrity
4. If adding $ref, create the referenced schema in components/schemas
5. Ensure the result is a complete, valid OpenAPI specification

**Output Requirements:**
- Complete OpenAPI JSON specification
- No placeholder text or truncation
- Valid JSON syntax with proper object structure
- All required OpenAPI fields present
- All $ref references must point to existing schemas
"""

    def _get_generation_system_prompt(self) -> str:
        return """
You are an expert API designer capable of generating comprehensive OpenAPI specifications.

**Design Principles:**
1. Create RESTful, intuitive API designs
2. Include comprehensive schemas with proper validation
3. Add security schemes appropriate for the domain
4. Provide detailed descriptions and examples
5. Follow industry best practices

**Critical Structure Requirements:**
- Every path must start with "/"
- Every operation (get, post, put, delete) must be a proper object
- Every operation must have a "responses" field
- Operation-level fields (summary, operationId, description) go INSIDE the operation object
- All $ref references must point to schemas defined in components/schemas
- Always create a complete components/schemas section for any referenced schemas

**Generation Process:**
1. Analyze requirements and domain context
2. Design entity relationships and data models
3. Create RESTful path structures with proper operation objects
4. Define comprehensive schemas in components/schemas section
5. Ensure all $ref references are valid and point to existing schemas
6. Add security, examples, and documentation

**Output Requirements:**
- Complete OpenAPI 3.0+ specification
- Valid JSON format with proper object nesting
- All operations must be objects with required fields
- Production-ready structure with all schemas defined
- Comprehensive documentation
"""

    def _get_validation_system_prompt(self) -> str:
        return """
You are an OpenAPI validation specialist focused on ensuring specification correctness.

**Critical Issues to Fix:**
1. Invalid JSON structure (operations must be objects, not strings)
2. Missing required fields (every operation needs "responses")
3. Broken $ref references (must point to existing schemas)
4. Invalid path structures (operations at wrong level)
5. Schema compliance with OpenAPI 3.0+ standards

**Validation Areas:**
1. JSON syntax and object structure validation
2. Reference integrity and circular dependency detection
3. Operation object completeness (responses, parameters)
4. Schema definitions in components/schemas
5. Path and operation method validation

**Correction Process:**
1. Fix critical JSON structure errors first
2. Ensure all $ref references have corresponding schema definitions
3. Move misplaced operation fields to correct locations
4. Add missing required fields (responses, etc.)
5. Preserve original intent while fixing structural issues

**Output Requirements:**
- Valid, corrected OpenAPI specification with proper JSON structure
- All $ref references pointing to existing schemas
- Complete operation objects with required fields
- Detailed list of issues found and fixed
- Confidence score for the validation
"""

    def _get_patch_system_prompt(self) -> str:
        return """
You are a JSON Patch specialist for OpenAPI specifications.

**Patch Operations:**
1. Apply precise modifications using JSON Patch standards
2. Maintain specification integrity during modifications
3. Handle complex nested structure changes
4. Resolve conflicts intelligently
5. Validate results after patch application

**Safety Principles:**
1. Never break existing references
2. Preserve critical specification metadata
3. Maintain OpenAPI standard compliance
4. Apply patches in safe order
5. Rollback on validation failures

**Output Requirements:**
- Successfully patched OpenAPI specification
- Validation of patch application success
- Conflict resolution details if applicable
"""

    # Helper methods for advanced features
    def _find_all_refs(self, obj, refs=None) -> List[str]:
        """Recursively find all $ref references in a specification object."""
        if refs is None:
            refs = []

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    refs.append(value)
                else:
                    self._find_all_refs(value, refs)
        elif isinstance(obj, list):
            for item in obj:
                self._find_all_refs(item, refs)

        return refs

    async def _validate_openapi_spec(self, spec_text: str) -> ValidationResult:
        """
        Validate OpenAPI specification using multiple validators.
        """
        errors = []
        warnings = []
        suggestions = []

        try:
            # Parse JSON
            spec_data = json.loads(spec_text)

            # Basic structure validation
            required_fields = ["openapi", "info", "paths"]
            for field in required_fields:
                if field not in spec_data:
                    errors.append(f"Missing required field: {field}")

            # Version validation
            if "openapi" in spec_data:
                version = spec_data["openapi"]
                if not version.startswith("3."):
                    warnings.append(f"OpenAPI version {version} is not 3.x")

            # Path validation
            if "paths" in spec_data and spec_data["paths"]:
                for path, path_obj in spec_data["paths"].items():
                    if not path.startswith("/"):
                        errors.append(f"Path {path} must start with /")

                    # Validate path operations
                    if isinstance(path_obj, dict):
                        valid_methods = [
                            "get",
                            "post",
                            "put",
                            "delete",
                            "options",
                            "head",
                            "patch",
                            "trace",
                        ]
                        for method, operation in path_obj.items():
                            if method in valid_methods:
                                if not isinstance(operation, dict):
                                    errors.append(
                                        f"Operation {method} in path {path} must be an object"
                                    )
                                else:
                                    # Validate operation structure
                                    if "responses" not in operation:
                                        errors.append(
                                            f"Operation {method} in path {path} missing required 'responses' field"
                                        )
                            elif method not in [
                                "summary",
                                "description",
                                "parameters",
                                "servers",
                            ]:
                                # Invalid field at path level
                                errors.append(
                                    f"Invalid field '{method}' at path level for {path}"
                                )
                    else:
                        errors.append(f"Path {path} must be an object")

            # Schema reference validation
            if "paths" in spec_data:
                refs_found = self._find_all_refs(spec_data)
                components_schemas = spec_data.get("components", {}).get("schemas", {})

                for ref in refs_found:
                    if ref.startswith("#/components/schemas/"):
                        schema_name = ref.replace("#/components/schemas/", "")
                        if schema_name not in components_schemas:
                            errors.append(
                                f"Reference {ref} points to non-existent schema"
                            )

            # Comprehensive validation using prance (if available)
            try:
                from prance import ResolvingParser

                # Use spec_dict parameter correctly
                parser = ResolvingParser(spec_dict=spec_data)
                # If we get here, the spec is valid according to OpenAPI specification
            except ImportError:
                warnings.append(
                    "Advanced validation unavailable (prance not installed)"
                )
            except Exception as e:
                # Don't fail validation for prance-specific issues, just warn
                warnings.append(f"Advanced validation warning: {str(e)}")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
        )

    def _fix_openapi_issues(self, spec_text: str) -> str:
        """Post-process generated spec to fix common OpenAPI 3.0+ issues."""
        try:
            spec_data = json.loads(spec_text)

            # Fix common OpenAPI 3.0 issues
            if "paths" in spec_data:
                for path, path_obj in spec_data["paths"].items():
                    if isinstance(path_obj, dict):
                        for method, operation in path_obj.items():
                            if method in [
                                "get",
                                "post",
                                "put",
                                "delete",
                                "patch",
                                "options",
                                "head",
                            ] and isinstance(operation, dict):
                                # Fix parameters with "in": "body" (invalid in OpenAPI 3.0)
                                if "parameters" in operation:
                                    body_params = []
                                    non_body_params = []

                                    for param in operation["parameters"]:
                                        if (
                                            isinstance(param, dict)
                                            and param.get("in") == "body"
                                        ):
                                            body_params.append(param)
                                        else:
                                            non_body_params.append(param)

                                    # Convert body parameters to requestBody
                                    if body_params and method in [
                                        "post",
                                        "put",
                                        "patch",
                                    ]:
                                        if "requestBody" not in operation:
                                            # Create requestBody from body parameters
                                            properties = {}
                                            required = []

                                            for param in body_params:
                                                prop_name = param.get("name", "unknown")
                                                properties[prop_name] = param.get(
                                                    "schema", {"type": "string"}
                                                )
                                                if param.get("required", False):
                                                    required.append(prop_name)

                                            operation["requestBody"] = {
                                                "required": len(required) > 0,
                                                "content": {
                                                    "application/json": {
                                                        "schema": {
                                                            "type": "object",
                                                            "properties": properties,
                                                            "required": (
                                                                required
                                                                if required
                                                                else None
                                                            ),
                                                        }
                                                    }
                                                },
                                            }
                                            # Remove the required field if empty
                                            if not required:
                                                del operation["requestBody"]["content"][
                                                    "application/json"
                                                ]["schema"]["required"]

                                    # Update parameters to exclude body params
                                    if non_body_params:
                                        operation["parameters"] = non_body_params
                                    elif "parameters" in operation:
                                        del operation["parameters"]

            return json.dumps(spec_data, indent=2)

        except Exception as e:
            self.logger.warning(f"Post-processing failed: {str(e)}")
            return spec_text

    async def _analyze_spec_structure(self, spec_text: str) -> Dict[str, Any]:
        """
        Analyze OpenAPI spec structure for context building.
        """
        try:
            spec_data = json.loads(spec_text)
            return {
                "version": spec_data.get("openapi", "unknown"),
                "path_count": len(spec_data.get("paths", {})),
                "component_count": len(
                    spec_data.get("components", {}).get("schemas", {})
                ),
                "complexity_level": self._assess_complexity(spec_data),
            }
        except:
            return {
                "version": "unknown",
                "path_count": 0,
                "component_count": 0,
                "complexity_level": "unknown",
            }

    def _assess_complexity(self, spec_data: Dict[str, Any]) -> str:
        """
        Assess the complexity level of an OpenAPI specification.
        """
        path_count = len(spec_data.get("paths", {}))
        component_count = len(spec_data.get("components", {}).get("schemas", {}))

        total_complexity = path_count + component_count

        if total_complexity < 10:
            return "simple"
        elif total_complexity < 50:
            return "medium"
        else:
            return "complex"

    async def _analyze_changes(
        self, original_spec: str, updated_spec: str
    ) -> tuple[str, List[str]]:
        """
        Analyze changes between original and updated specifications.
        """
        try:
            original = json.loads(original_spec)
            updated = json.loads(updated_spec)

            # Simple change detection - can be enhanced with jsonpatch
            changes = []
            modified_paths = []

            # Compare paths
            orig_paths = set(original.get("paths", {}).keys())
            new_paths = set(updated.get("paths", {}).keys())

            added_paths = new_paths - orig_paths
            removed_paths = orig_paths - new_paths

            if added_paths:
                changes.append(f"Added {len(added_paths)} new paths")
                modified_paths.extend(list(added_paths))

            if removed_paths:
                changes.append(f"Removed {len(removed_paths)} paths")
                modified_paths.extend(list(removed_paths))

            # TODO: Add more detailed change analysis

            summary = "; ".join(changes) if changes else "Minor modifications applied"
            return summary, modified_paths

        except Exception as e:
            return f"Changes applied (analysis failed: {str(e)})", []

    def _build_context_summary(self, context) -> str:
        """
        Build context summary from previous operations.
        """
        if not context.previous_operations:
            return "No previous context available."

        return f"Previous operations: {', '.join(context.previous_operations[-3:])}"

    # Placeholder methods for agentic workflow - to be implemented
    async def _analyze_domain_requirements(self, request) -> Dict[str, Any]:
        return {"tokens": 100, "analysis": "domain analysis"}

    async def _extract_entities_with_relationships(
        self, request, domain_analysis
    ) -> Dict[str, Any]:
        return {"tokens": 150, "entities": []}

    async def _generate_advanced_schemas(self, entities, request) -> Dict[str, Any]:
        return {"tokens": 200, "schemas": {}}

    async def _generate_intelligent_paths(self, entities, request) -> Dict[str, Any]:
        return {"tokens": 180, "paths": {}}

    async def _enhance_with_security_docs(self, request) -> Dict[str, Any]:
        return {"tokens": 120, "security": {}, "suggestions": []}

    async def _assemble_optimized_spec(self, *args) -> Dict[str, Any]:
        return {
            "openapi": "3.0.0",
            "info": {"title": "Generated API", "version": "1.0.0"},
            "paths": {},
        }

    async def _validate_and_correct_response(
        self, response_text: str, request: AIRequest, messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Validate LLM response and apply self-correction if needed.
        """
        validation_result = await self._validate_openapi_spec(response_text)

        if not validation_result.is_valid and request.auto_fix:
            # Self-correction attempt
            correction_messages = messages + [
                {"role": "assistant", "content": response_text},
                {
                    "role": "user",
                    "content": f"The previous response has validation errors: {', '.join(validation_result.errors)}. Please fix these issues and provide the corrected specification.",
                },
            ]

            try:
                corrected_response = await self._call_llm_with_retry(
                    correction_messages, request.llm_parameters
                )
                corrected_validation = await self._validate_openapi_spec(
                    corrected_response
                )

                return {
                    "validation": corrected_validation,
                    "corrected_spec": (
                        corrected_response if corrected_validation.is_valid else None
                    ),
                    "confidence_score": 0.8 if corrected_validation.is_valid else 0.3,
                }
            except Exception as e:
                self.logger.warning(f"Self-correction failed: {str(e)}")

        return {
            "validation": validation_result,
            "corrected_spec": None,
            "confidence_score": 0.9 if validation_result.is_valid else 0.2,
        }

    async def _ai_fix_validation_issues(self, fix_request: AIRequest) -> Dict[str, Any]:
        """
        Use AI to fix validation issues in patched specifications.
        """
        try:
            response = await self._process_standard_request(fix_request, time.time())
            return json.loads(response.updated_spec_text)
        except Exception as e:
            self.logger.error(f"AI validation fix failed: {str(e)}")
            raise OpenAPIError(f"Failed to fix validation issues: {str(e)}")

    async def __aenter__(self):
        return self

    async def generate(
        self,
        prompt: str,
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Simple method to generate text from the LLM.
        Used by agents for general text generation.

        Args:
            prompt: The prompt to send to the LLM
            model: Model to use (default: settings.default_model)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate

        Returns:
            Dict with 'response' and 'tokens_used'
        """
        try:
            messages = [{"role": "user", "content": prompt}]

            payload = {
                "model": model or settings.default_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "num_ctx": 8192,  # Large context window for agent reasoning
                },
            }

            self.logger.debug(
                f"Sending generation request to Ollama: model={model or settings.default_model}, temp={temperature}"
            )

            response = await self.client.post(self.chat_endpoint, json=payload)

            if response.status_code != 200:
                error_msg = (
                    f"LLM request failed: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            response_data = response.json()
            generated_text = self._extract_and_clean_response(response_data)

            # Extract token usage if available
            eval_count = response_data.get("eval_count", 0)
            prompt_eval_count = response_data.get("prompt_eval_count", 0)
            tokens_used = eval_count + prompt_eval_count

            return {"response": generated_text, "tokens_used": tokens_used}

        except Exception as e:
            self.logger.error(f"Generation failed: {str(e)}")
            raise LLMError(f"Failed to generate response: {str(e)}")

    async def generate_json_response(
        self,
        prompt: str,
        schema_description: str = "JSON response",
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a JSON response from the LLM.
        This is a compatibility method for PatchGenerator and other services.

        Args:
            prompt: The prompt to send to the LLM
            schema_description: Description of expected JSON schema
            max_tokens: Maximum tokens to generate

        Returns:
            JSON string from the LLM
        """
        try:
            messages = [
                {
                    "role": "system",
                    "content": f"You are a helpful assistant that responds only with valid JSON. {schema_description}",
                },
                {"role": "user", "content": prompt},
            ]

            payload = {
                "model": settings.default_model,
                "messages": messages,
                "stream": False,
                "format": "json",  # Force JSON output
                "options": {
                    "temperature": 0.2,  # Lower temperature for more consistent JSON
                    "num_predict": max_tokens,
                    "num_ctx": 4096,  # Increase context window
                },
            }

            self.logger.debug(
                f"Sending JSON generation request to Ollama, max_tokens={max_tokens}"
            )

            response = await self.client.post(self.chat_endpoint, json=payload)

            if response.status_code != 200:
                error_msg = (
                    f"LLM request failed: {response.status_code} - {response.text}"
                )
                self.logger.error(error_msg)
                raise LLMError(error_msg)

            response_data = response.json()
            return self._extract_and_clean_response(response_data)

        except Exception as e:
            self.logger.error(f"JSON response generation failed: {str(e)}")
            raise LLMError(f"Failed to generate JSON response: {str(e)}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._auto_close_client:
            await self.client.aclose()

    async def close(self):
        """Explicitly close the HTTP client."""
        if not self.client.is_closed:
            await self.client.aclose()
