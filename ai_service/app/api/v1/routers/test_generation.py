"""
Test Generation Router.

Provides endpoints for AI-powered test case generation for OpenAPI specifications.
Generates comprehensive test suites including:
- Positive tests (happy path)
- Negative tests (error handling)
- Edge case tests
- Security tests

Uses LLM to create realistic, framework-agnostic test cases that can be
exported to Jest, Postman, Newman, or Python requests.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

import yaml
from fastapi import APIRouter, Depends, HTTPException
from prance import ResolvingParser

from app.api.deps import get_llm_service, get_test_case_generator
from app.api.v1.endpoints import sanitize_openapi_spec
from app.core.config import settings
from app.core.logging import set_correlation_id
from app.schemas.ai_schemas import (
    AIRequest,
    LLMParameters,
    OperationType,
    StreamingMode,
)
from app.schemas.test_generation_schemas import (
    TEST_TYPE_TO_PRIORITY,
    BulkTestGenerationRequest,
    SingleEndpointTestRequest,
    TestCaseGenerationRequest,
    TestPriority,
    TestSuiteGenerationRequest,
    TestType,
)
from app.services.cache_service import cache_service
from app.services.llm_service import LLMService
from app.services.test_case_generator import TestCaseGeneratorService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Test Generation"])


def _map_test_type_to_priority(test_type: str) -> str:
    """Map a test type string to its corresponding priority level."""
    try:
        test_type_enum = TestType(test_type)
        return TEST_TYPE_TO_PRIORITY.get(test_type_enum, TestPriority.MEDIUM).value
    except ValueError:
        return TestPriority.MEDIUM.value


@router.post("/ai/test-cases/generate")
async def generate_test_cases_for_single_operation(
    request: TestCaseGenerationRequest,
    llm_service: LLMService = Depends(get_llm_service),
) -> Dict[str, Any]:
    """
    Generate comprehensive test cases for a single API operation using AI.

    Creates both positive and negative test scenarios with realistic data.
    Uses LLM to generate diverse test cases based on the operation's
    purpose and constraints.

    Args:
        request: Validated request containing spec_text, path, method, and test options.

    Returns:
        Dictionary with test cases, summary, and metadata.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Generating test cases for API operation",
        extra={
            "correlation_id": correlation_id,
            "operation": request.operation_summary or "unknown",
        },
    )

    try:
        spec_text = request.spec_text
        operation_path = request.path
        operation_method = request.method
        operation_summary = request.operation_summary
        test_types = request.test_types

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
                temperature=0.4, max_tokens=3000  # Moderate creativity for test variety
            ),
            validate_output=False,
            tags=["test_generation", "quality_assurance"],
        )

        # Get test cases from LLM
        result = await llm_service.process_ai_request(ai_request)

        # Try to parse the JSON response
        try:
            test_cases_data = json.loads(result.updated_spec_text)
            if (
                not isinstance(test_cases_data, dict)
                or "test_cases" not in test_cases_data
            ):
                raise ValueError("Invalid test cases format")

            # Enhance test cases with additional metadata
            enhanced_test_cases = []
            for i, test_case in enumerate(test_cases_data["test_cases"]):
                enhanced_test_case = {
                    **test_case,
                    "id": f"test_{i+1}",
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                    "priority": _map_test_type_to_priority(
                        test_case.get("type", "positive")
                    ),
                    "estimated_execution_time": "< 1s",
                }
                enhanced_test_cases.append(enhanced_test_case)

            response = {
                "test_cases": enhanced_test_cases,
                "summary": {
                    "total_tests": len(enhanced_test_cases),
                    "positive_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "positive"
                        ]
                    ),
                    "negative_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "negative"
                        ]
                    ),
                    "edge_case_tests": len(
                        [
                            tc
                            for tc in enhanced_test_cases
                            if tc.get("type") == "edge_case"
                        ]
                    ),
                    "operation": f"{operation_method.upper()} {operation_path}",
                    "generated_at": datetime.utcnow().isoformat(),
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered",
                    "llm_model": settings.default_model,
                    "test_framework_compatible": [
                        "jest",
                        "postman",
                        "newman",
                        "python-requests",
                    ],
                },
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
                    "body": {},
                },
                "expected_response": {"status_code": 200, "body": {}},
                "assertions": ["Response status should be successful"],
                "operation": f"{operation_method.upper()} {operation_path}",
                "generated_at": datetime.utcnow().isoformat(),
                "priority": "medium",
                "notes": "Fallback test case - original AI response was not parseable",
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
                    "fallback_mode": True,
                },
                "metadata": {
                    "correlation_id": correlation_id,
                    "generation_method": "ai_powered_fallback",
                    "original_response": result.updated_spec_text[:500],
                },
            }

        logger.info(
            f"Generated {len(response['test_cases'])} test cases for "
            f"{operation_method.upper()} {operation_path}"
        )
        return response

    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_GENERATION_FAILED",
                "message": f"Failed to generate test cases: {str(e)}",
                "operation": f"{request.method} {request.path}",
            },
        )


@router.post("/ai/test-suite/generate")
async def generate_test_suite_for_entire_spec(
    request: TestSuiteGenerationRequest,
    test_case_generator: TestCaseGeneratorService = Depends(get_test_case_generator),
) -> Dict[str, Any]:
    """
    Generate a complete test suite for an entire API specification.

    Analyzes all operations in the spec and generates comprehensive
    test cases for each one.

    Args:
        request: Validated request containing spec_text and generation options.

    Returns:
        Complete test suite with tests for all operations.
    """
    correlation_id = set_correlation_id()

    logger.info(
        "Generating complete test suite",
        extra={
            "correlation_id": correlation_id,
            "spec_size": len(request.spec_text),
        },
    )

    try:
        spec_text = request.spec_text
        test_options = request.options.model_dump() if request.options else {}

        if not spec_text:
            raise ValueError("OpenAPI specification is required")

        # Parse the specification to extract operations
        try:
            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_SPEC",
                    "message": f"Failed to parse OpenAPI specification: {str(e)}",
                },
            )

        # Generate tests for all endpoints
        all_tests = {}
        total_test_count = 0
        endpoint_count = 0
        include_ai_tests = test_options.get("include_ai_tests", True)
        max_endpoints = test_options.get("max_endpoints", 50)

        for path, path_item in spec.get("paths", {}).items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    endpoint_count += 1

                    if endpoint_count > max_endpoints:
                        logger.warning(f"Reached max_endpoints limit ({max_endpoints})")
                        break

                    try:
                        result = await test_case_generator.generate_test_cases(
                            spec=spec,
                            path=path,
                            method=method,
                            include_ai_tests=include_ai_tests,
                        )

                        endpoint_key = f"{method.upper()} {path}"
                        all_tests[endpoint_key] = result
                        total_test_count += result.get("total_tests", 0)

                    except Exception as e:
                        logger.error(
                            f"Failed to generate tests for {method.upper()} {path}: {e}"
                        )
                        all_tests[f"{method.upper()} {path}"] = {
                            "error": str(e),
                            "endpoint": f"{method.upper()} {path}",
                        }

            if endpoint_count > max_endpoints:
                break

        logger.info(
            f"Generated {total_test_count} tests across {endpoint_count} endpoints",
            extra={"correlation_id": correlation_id},
        )

        return {
            "test_suite": all_tests,
            "summary": {
                "total_endpoints": endpoint_count,
                "total_tests": total_test_count,
                "include_ai_tests": include_ai_tests,
                "api_title": spec.get("info", {}).get("title", "Unknown API"),
                "api_version": spec.get("info", {}).get("version", "1.0.0"),
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test suite generation failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_SUITE_GENERATION_FAILED",
                "message": f"Failed to generate test suite: {str(e)}",
            },
        )


@router.post("/tests/generate")
async def generate_test_cases_with_caching(
    request: SingleEndpointTestRequest,
    test_case_generator: TestCaseGeneratorService = Depends(get_test_case_generator),
) -> Dict[str, Any]:
    """
    Generate comprehensive test cases for an OpenAPI endpoint with caching.

    Creates happy path, sad path, edge cases, and AI-generated advanced tests.
    Results are cached for improved performance on repeated requests.

    Args:
        request: Validated request containing spec_text, path, method, and AI test flag.

    Returns:
        Generated test cases with metadata.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info("Generating test cases", extra={"correlation_id": correlation_id})

    try:
        spec_text = request.spec_text
        path = request.path
        method = request.method.upper()
        include_ai_tests = request.include_ai_tests

        # Check cache first
        cached_tests = cache_service.get_test_cases(
            spec_text, path, method, include_ai_tests
        )
        if cached_tests:
            logger.info(f"Returning cached test cases for {method} {path}")
            return {
                **cached_tests,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            try:
                # First, parse the spec text to dict and sanitize it
                try:
                    spec_dict = json.loads(spec_text)
                except json.JSONDecodeError:
                    spec_dict = yaml.safe_load(spec_text)

                # Sanitize the spec to replace None schemas with {}
                sanitized_spec = sanitize_openapi_spec(spec_dict)

                # Convert back to JSON string for ResolvingParser
                sanitized_spec_text = json.dumps(sanitized_spec)

                # Now parse with ResolvingParser
                parser = ResolvingParser(
                    spec_string=sanitized_spec_text, backend="openapi-spec-validator"
                )
                spec = parser.specification
                cache_service.cache_parsed_spec(spec_text, spec)
            except Exception as e:
                logger.error(f"Invalid OpenAPI specification: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "INVALID_SPEC",
                        "message": f"Failed to parse OpenAPI specification: {str(e)}",
                    },
                )

        # Validate path exists
        if path not in spec.get("paths", {}):
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PATH_NOT_FOUND",
                    "message": f"Path '{path}' not found in specification",
                    "available_paths": list(spec.get("paths", {}).keys()),
                },
            )

        # Validate method exists
        method_lower = method.lower()
        if method_lower not in spec["paths"][path]:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "METHOD_NOT_FOUND",
                    "message": f"Method '{method}' not found for path '{path}'",
                    "available_methods": list(spec["paths"][path].keys()),
                },
            )

        # Generate test cases
        result = await test_case_generator.generate_test_cases(
            spec=spec, path=path, method=method_lower, include_ai_tests=include_ai_tests
        )

        # Cache the results
        cache_service.cache_test_cases(
            spec_text, path, method_lower, include_ai_tests, result
        )

        logger.info(
            f"Generated {result['total_tests']} test cases for {method} {path}",
            extra={"correlation_id": correlation_id},
        )

        return {
            **result,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test case generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "TEST_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


@router.post("/tests/generate/all")
async def generate_bulk_test_cases(
    request: BulkTestGenerationRequest,
    test_case_generator: TestCaseGeneratorService = Depends(get_test_case_generator),
) -> Dict[str, Any]:
    """
    Generate test cases for all endpoints in an OpenAPI specification.

    Args:
        request: Validated request containing spec_text, AI test flag, and max endpoints.

    Returns:
        Test cases for all endpoints with summary.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        "Generating test cases for all endpoints",
        extra={"correlation_id": correlation_id},
    )

    try:
        spec_text = request.spec_text
        include_ai_tests = request.include_ai_tests
        max_endpoints = request.max_endpoints

        # Parse specification
        try:
            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "INVALID_SPEC",
                    "message": f"Failed to parse OpenAPI specification: {str(e)}",
                },
            )

        # Generate tests for all endpoints
        all_tests = {}
        total_test_count = 0
        endpoint_count = 0

        for path, path_item in spec.get("paths", {}).items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    endpoint_count += 1

                    if endpoint_count > max_endpoints:
                        logger.warning(f"Reached max_endpoints limit ({max_endpoints})")
                        break

                    try:
                        result = await test_case_generator.generate_test_cases(
                            spec=spec,
                            path=path,
                            method=method,
                            include_ai_tests=include_ai_tests,
                        )

                        endpoint_key = f"{method.upper()} {path}"
                        all_tests[endpoint_key] = result
                        total_test_count += result["total_tests"]

                    except Exception as e:
                        logger.error(
                            f"Failed to generate tests for {method.upper()} {path}: {e}"
                        )
                        all_tests[f"{method.upper()} {path}"] = {
                            "error": str(e),
                            "endpoint": f"{method.upper()} {path}",
                        }

            if endpoint_count > max_endpoints:
                break

        logger.info(
            f"Generated {total_test_count} tests across {endpoint_count} endpoints",
            extra={"correlation_id": correlation_id},
        )

        return {
            "endpoints": all_tests,
            "summary": {
                "total_endpoints": endpoint_count,
                "total_tests": total_test_count,
                "include_ai_tests": include_ai_tests,
            },
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk test generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "BULK_TEST_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )
