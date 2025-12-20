"""
Test Case Generator Service.
Generates comprehensive test cases for OpenAPI endpoints including happy paths and sad paths.
"""

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger
from ..schemas.ai_schemas import AIRequest, OperationType

logger = get_logger("test_case_generator")


class TestCaseType(str, Enum):
    """Types of test cases."""

    HAPPY_PATH = "happy_path"
    SAD_PATH_VALIDATION = "sad_path_validation"
    SAD_PATH_AUTH = "sad_path_auth"
    SAD_PATH_PERMISSION = "sad_path_permission"
    SAD_PATH_NOT_FOUND = "sad_path_not_found"
    SAD_PATH_CONFLICT = "sad_path_conflict"
    EDGE_CASE = "edge_case"
    BOUNDARY = "boundary"


class TestCase:
    """Represents a single test case."""

    def __init__(
        self,
        name: str,
        description: str,
        test_type: TestCaseType,
        method: str,
        path: str,
        request_body: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        expected_status: int = 200,
        expected_response: Optional[Dict[str, Any]] = None,
        assertions: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.test_type = test_type
        self.method = method
        self.path = path
        self.request_body = request_body
        self.query_params = query_params or {}
        self.headers = headers or {}
        self.expected_status = expected_status
        self.expected_response = expected_response
        self.assertions = assertions or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert test case to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.test_type.value,
            "method": self.method,
            "path": self.path,
            "request_body": self.request_body,
            "query_params": self.query_params,
            "headers": self.headers,
            "expected_status": self.expected_status,
            "expected_response": self.expected_response,
            "assertions": self.assertions,
        }


class TestCaseGeneratorService:
    """
    Service for generating comprehensive test cases from OpenAPI specifications.
    Creates both happy path and sad path test scenarios.
    """

    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.logger = logger

    async def generate_test_cases(
        self,
        spec: Dict[str, Any],
        path: str,
        method: str,
        include_ai_tests: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive test cases for a specific endpoint.

        Args:
            spec: Full OpenAPI specification
            path: The API path to generate tests for
            method: HTTP method (GET, POST, etc.)
            include_ai_tests: Whether to include AI-generated advanced tests

        Returns:
            Dictionary containing happy path, sad path, and edge case tests
        """
        self.logger.info(f"Generating test cases for {method.upper()} {path}")

        operation = spec["paths"][path][method.lower()]

        # Generate deterministic test cases
        happy_path_tests = await self._generate_happy_path_tests(
            spec, path, method, operation
        )
        sad_path_tests = await self._generate_sad_path_tests(
            spec, path, method, operation
        )
        edge_case_tests = await self._generate_edge_case_tests(
            spec, path, method, operation
        )

        result = {
            "endpoint": f"{method.upper()} {path}",
            "operation_id": operation.get("operationId", ""),
            "summary": operation.get("summary", ""),
            "happy_path_tests": [t.to_dict() for t in happy_path_tests],
            "sad_path_tests": [t.to_dict() for t in sad_path_tests],
            "edge_case_tests": [t.to_dict() for t in edge_case_tests],
            "total_tests": len(happy_path_tests)
            + len(sad_path_tests)
            + len(edge_case_tests),
        }

        # Optionally add AI-generated advanced tests
        if include_ai_tests:
            try:
                ai_tests = await self._generate_ai_test_cases(
                    spec, path, method, operation
                )
                result["ai_generated_tests"] = [t.to_dict() for t in ai_tests]
                result["total_tests"] += len(ai_tests)
            except Exception as e:
                self.logger.warning(f"AI test generation failed: {e}")
                result["ai_generated_tests"] = []

        return result

    async def _generate_happy_path_tests(
        self, spec: Dict[str, Any], path: str, method: str, operation: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate happy path test cases."""
        tests = []

        # Get successful response schema
        responses = operation.get("responses", {})
        success_response = (
            responses.get("200") or responses.get("201") or responses.get("204")
        )

        if not success_response:
            self.logger.warning(f"No success response defined for {method} {path}")
            return tests

        expected_status = (
            200 if "200" in responses else (201 if "201" in responses else 204)
        )

        # Generate request body if needed
        request_body = None
        if method.upper() in ["POST", "PUT", "PATCH"]:
            request_body_schema = (
                operation.get("requestBody", {})
                .get("content", {})
                .get("application/json", {})
                .get("schema")
            )
            if request_body_schema:
                request_body = self._generate_valid_request_body(
                    request_body_schema, spec
                )

        # Get query parameters
        query_params = {}
        parameters = operation.get("parameters", [])
        for param in parameters:
            if param.get("in") == "query" and param.get("required", False):
                query_params[param["name"]] = self._generate_param_value(param)

        # Create happy path test
        test = TestCase(
            name=f"Happy Path - {operation.get('summary', 'Valid Request')}",
            description=f"Successful {method.upper()} request with valid data",
            test_type=TestCaseType.HAPPY_PATH,
            method=method.upper(),
            path=path,
            request_body=request_body,
            query_params=query_params,
            expected_status=expected_status,
            assertions=[
                f"Response status should be {expected_status}",
                "Response should match the schema",
                "All required fields should be present",
            ],
        )

        tests.append(test)

        # If it's a GET with optional parameters, create test without them
        if method.upper() == "GET" and query_params:
            test_minimal = TestCase(
                name="Happy Path - Minimal Parameters",
                description="Successful GET request with only required parameters",
                test_type=TestCaseType.HAPPY_PATH,
                method=method.upper(),
                path=path,
                expected_status=expected_status,
                assertions=[
                    f"Response status should be {expected_status}",
                    "Response should handle missing optional parameters gracefully",
                ],
            )
            tests.append(test_minimal)

        return tests

    async def _generate_sad_path_tests(
        self, spec: Dict[str, Any], path: str, method: str, operation: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate sad path test cases."""
        tests = []

        # 1. Validation errors (400)
        if method.upper() in ["POST", "PUT", "PATCH"]:
            tests.extend(self._generate_validation_tests(path, method, operation, spec))

        # 2. Authentication errors (401)
        if self._requires_authentication(operation, spec):
            tests.append(
                TestCase(
                    name="Sad Path - Missing Authentication",
                    description="Request without authentication credentials",
                    test_type=TestCaseType.SAD_PATH_AUTH,
                    method=method.upper(),
                    path=path,
                    expected_status=401,
                    assertions=[
                        "Response status should be 401",
                        "Response should contain authentication error message",
                    ],
                )
            )

            tests.append(
                TestCase(
                    name="Sad Path - Invalid Authentication",
                    description="Request with invalid/expired authentication token",
                    test_type=TestCaseType.SAD_PATH_AUTH,
                    method=method.upper(),
                    path=path,
                    headers={"Authorization": "Bearer invalid_token_12345"},
                    expected_status=401,
                    assertions=[
                        "Response status should be 401",
                        "Response should indicate invalid credentials",
                    ],
                )
            )

        # 3. Authorization/Permission errors (403)
        if self._has_authorization(operation, spec):
            tests.append(
                TestCase(
                    name="Sad Path - Insufficient Permissions",
                    description="Request with valid auth but insufficient permissions",
                    test_type=TestCaseType.SAD_PATH_PERMISSION,
                    method=method.upper(),
                    path=path,
                    expected_status=403,
                    assertions=[
                        "Response status should be 403",
                        "Response should indicate insufficient permissions",
                    ],
                )
            )

        # 4. Not Found errors (404)
        if "{" in path:  # Path has parameters
            tests.append(
                TestCase(
                    name="Sad Path - Resource Not Found",
                    description="Request for non-existent resource ID",
                    test_type=TestCaseType.SAD_PATH_NOT_FOUND,
                    method=method.upper(),
                    path=path.replace("{id}", "99999999").replace(
                        "{uuid}", "00000000-0000-0000-0000-000000000000"
                    ),
                    expected_status=404,
                    assertions=[
                        "Response status should be 404",
                        "Response should indicate resource not found",
                    ],
                )
            )

        # 5. Conflict errors (409) - for POST/PUT
        if method.upper() in ["POST", "PUT"]:
            tests.append(
                TestCase(
                    name="Sad Path - Resource Conflict",
                    description="Attempt to create duplicate resource",
                    test_type=TestCaseType.SAD_PATH_CONFLICT,
                    method=method.upper(),
                    path=path,
                    expected_status=409,
                    assertions=[
                        "Response status should be 409",
                        "Response should indicate conflict/duplicate",
                    ],
                )
            )

        return tests

    def _generate_validation_tests(
        self, path: str, method: str, operation: Dict[str, Any], spec: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate validation error test cases."""
        tests = []

        request_body_schema = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema")
        )

        if not request_body_schema:
            return tests

        # Test 1: Missing required fields
        required_fields = request_body_schema.get("required", [])
        if required_fields:
            incomplete_body = self._generate_valid_request_body(
                request_body_schema, spec
            )
            # Remove first required field
            if incomplete_body and required_fields[0] in incomplete_body:
                del incomplete_body[required_fields[0]]

            tests.append(
                TestCase(
                    name="Sad Path - Missing Required Field",
                    description=f"Request missing required field: {required_fields[0] if required_fields else 'field'}",
                    test_type=TestCaseType.SAD_PATH_VALIDATION,
                    method=method.upper(),
                    path=path,
                    request_body=incomplete_body,
                    expected_status=400,
                    assertions=[
                        "Response status should be 400",
                        "Response should indicate validation error",
                        f"Error should mention missing required field",
                    ],
                )
            )

        # Test 2: Invalid data types
        invalid_body = self._generate_invalid_type_body(request_body_schema, spec)
        if invalid_body:
            tests.append(
                TestCase(
                    name="Sad Path - Invalid Data Type",
                    description="Request with field having wrong data type",
                    test_type=TestCaseType.SAD_PATH_VALIDATION,
                    method=method.upper(),
                    path=path,
                    request_body=invalid_body,
                    expected_status=400,
                    assertions=[
                        "Response status should be 400",
                        "Response should indicate type validation error",
                    ],
                )
            )

        # Test 3: Invalid format (email, date, etc.)
        format_invalid_body = self._generate_invalid_format_body(
            request_body_schema, spec
        )
        if format_invalid_body:
            tests.append(
                TestCase(
                    name="Sad Path - Invalid Format",
                    description="Request with field having invalid format (email, date, etc.)",
                    test_type=TestCaseType.SAD_PATH_VALIDATION,
                    method=method.upper(),
                    path=path,
                    request_body=format_invalid_body,
                    expected_status=400,
                    assertions=[
                        "Response status should be 400",
                        "Response should indicate format validation error",
                    ],
                )
            )

        # Test 4: Empty body
        tests.append(
            TestCase(
                name="Sad Path - Empty Request Body",
                description="Request with empty/null body",
                test_type=TestCaseType.SAD_PATH_VALIDATION,
                method=method.upper(),
                path=path,
                request_body={},
                expected_status=400,
                assertions=[
                    "Response status should be 400",
                    "Response should indicate missing request body",
                ],
            )
        )

        return tests

    async def _generate_edge_case_tests(
        self, spec: Dict[str, Any], path: str, method: str, operation: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate edge case test scenarios."""
        tests = []

        request_body_schema = (
            operation.get("requestBody", {})
            .get("content", {})
            .get("application/json", {})
            .get("schema")
        )

        if request_body_schema:
            # Test with boundary values
            boundary_body = self._generate_boundary_value_body(
                request_body_schema, spec
            )
            if boundary_body:
                tests.append(
                    TestCase(
                        name="Edge Case - Boundary Values",
                        description="Request with minimum/maximum allowed values",
                        test_type=TestCaseType.BOUNDARY,
                        method=method.upper(),
                        path=path,
                        request_body=boundary_body,
                        expected_status=200,
                        assertions=[
                            "Response should handle boundary values correctly",
                            "No overflow or underflow errors",
                        ],
                    )
                )

            # Test with very long strings
            long_string_body = self._generate_long_string_body(
                request_body_schema, spec
            )
            if long_string_body:
                tests.append(
                    TestCase(
                        name="Edge Case - Maximum Length Strings",
                        description="Request with maximum length string fields",
                        test_type=TestCaseType.EDGE_CASE,
                        method=method.upper(),
                        path=path,
                        request_body=long_string_body,
                        expected_status=200,
                        assertions=[
                            "Response should handle long strings correctly",
                            "No truncation or buffer overflow",
                        ],
                    )
                )

        # Test with special characters in path parameters
        if "{" in path:
            special_char_path = path.replace("{id}", "test%20id").replace(
                "{uuid}", "special-char-123"
            )
            tests.append(
                TestCase(
                    name="Edge Case - Special Characters in Path",
                    description="Request with special characters in path parameters",
                    test_type=TestCaseType.EDGE_CASE,
                    method=method.upper(),
                    path=special_char_path,
                    expected_status=404,  # Might be 404 or 400 depending on implementation
                    assertions=[
                        "Response should handle special characters safely",
                        "No injection vulnerabilities",
                    ],
                )
            )

        return tests

    async def _generate_ai_test_cases(
        self, spec: Dict[str, Any], path: str, method: str, operation: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate advanced test cases using AI."""
        self.logger.info("Generating AI-powered test cases")

        prompt = f"""Generate advanced test case scenarios for this API endpoint.

**Endpoint**: {method.upper()} {path}
**Summary**: {operation.get('summary', 'N/A')}
**Description**: {operation.get('description', 'N/A')}

**Operation Details**:
```json
{json.dumps(operation, indent=2)}
```

Generate 3-5 creative test scenarios that test:
1. Race conditions or concurrent access
2. State transition edge cases
3. Business logic validation
4. Data consistency scenarios
5. Performance/load edge cases

For each test case, provide:
- name: Short descriptive name
- description: What this test validates
- scenario: Detailed test scenario
- expected_behavior: What should happen

Return as a JSON array of test scenarios.
"""

        try:
            ai_request = AIRequest(
                spec_text=json.dumps(spec, indent=2),
                prompt=prompt,
                operation_type=OperationType.GENERATE,
            )

            result = await self.llm_service.process_ai_request(ai_request)

            # Parse AI response
            response_text = result.updated_spec_text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()

            scenarios = json.loads(response_text)

            # Convert to TestCase objects
            tests = []
            for i, scenario in enumerate(scenarios):
                test = TestCase(
                    name=f"AI Test - {scenario.get('name', f'Scenario {i+1}')}",
                    description=scenario.get("description", ""),
                    test_type=TestCaseType.EDGE_CASE,
                    method=method.upper(),
                    path=path,
                    expected_status=200,
                    assertions=[
                        scenario.get("expected_behavior", "Test should pass"),
                        "AI-generated advanced scenario",
                    ],
                )
                tests.append(test)

            self.logger.info(f"Generated {len(tests)} AI test cases")
            return tests

        except Exception as e:
            self.logger.error(f"AI test generation failed: {e}")
            return []

    def _generate_valid_request_body(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a valid request body from schema."""
        if schema.get("type") != "object":
            return None

        body = {}
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            if prop_name in required:
                body[prop_name] = self._generate_valid_value(prop_schema)

        return body if body else None

    def _generate_valid_value(self, schema: Dict[str, Any]) -> Any:
        """Generate a valid value for a schema property."""
        prop_type = schema.get("type", "string")

        if prop_type == "string":
            format_type = schema.get("format")
            if format_type == "email":
                return "test@example.com"
            elif format_type == "date-time":
                return "2024-01-15T10:30:00Z"
            elif format_type == "date":
                return "2024-01-15"
            elif format_type == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            return schema.get("example", "test-value")

        elif prop_type == "integer":
            return schema.get("example", 42)

        elif prop_type == "number":
            return schema.get("example", 42.5)

        elif prop_type == "boolean":
            return schema.get("example", True)

        elif prop_type == "array":
            return schema.get("example", [])

        elif prop_type == "object":
            return schema.get("example", {})

        return None

    def _generate_invalid_type_body(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate request body with invalid type."""
        body = self._generate_valid_request_body(schema, spec)
        if not body:
            return None

        properties = schema.get("properties", {})

        # Find first string field and make it a number (type mismatch)
        for prop_name, prop_schema in properties.items():
            if prop_schema.get("type") == "string" and prop_name in body:
                body[prop_name] = 12345  # Number instead of string
                break

        return body

    def _generate_invalid_format_body(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate request body with invalid format."""
        body = self._generate_valid_request_body(schema, spec)
        if not body:
            return None

        properties = schema.get("properties", {})

        # Find field with format constraint and violate it
        for prop_name, prop_schema in properties.items():
            if prop_name in body:
                format_type = prop_schema.get("format")
                if format_type == "email":
                    body[prop_name] = "not-an-email"
                    return body
                elif format_type == "date-time":
                    body[prop_name] = "invalid-date"
                    return body
                elif format_type == "uuid":
                    body[prop_name] = "not-a-uuid"
                    return body

        return None

    def _generate_boundary_value_body(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate request body with boundary values."""
        body = self._generate_valid_request_body(schema, spec)
        if not body:
            return None

        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            if prop_name in body:
                prop_type = prop_schema.get("type")
                if prop_type == "integer":
                    body[prop_name] = prop_schema.get("minimum", 0)
                elif prop_type == "number":
                    body[prop_name] = prop_schema.get("minimum", 0.0)
                elif prop_type == "string":
                    min_length = prop_schema.get("minLength", 0)
                    body[prop_name] = "x" * min_length if min_length > 0 else "x"

        return body

    def _generate_long_string_body(
        self, schema: Dict[str, Any], spec: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate request body with maximum length strings."""
        body = self._generate_valid_request_body(schema, spec)
        if not body:
            return None

        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            if prop_name in body and prop_schema.get("type") == "string":
                max_length = prop_schema.get("maxLength", 1000)
                body[prop_name] = "x" * min(
                    max_length, 1000
                )  # Cap at 1000 for reasonableness

        return body

    def _generate_param_value(self, param: Dict[str, Any]) -> str:
        """Generate a valid value for a parameter."""
        schema = param.get("schema", {})
        param_type = schema.get("type", "string")

        if param_type == "string":
            return schema.get("example", "test-value")
        elif param_type == "integer":
            return str(schema.get("example", 1))
        elif param_type == "boolean":
            return "true"

        return "test"

    def _requires_authentication(
        self, operation: Dict[str, Any], spec: Dict[str, Any]
    ) -> bool:
        """Check if operation requires authentication."""
        # Check operation-level security
        if "security" in operation:
            return len(operation["security"]) > 0

        # Check global security
        if "security" in spec:
            return len(spec["security"]) > 0

        return False

    def _has_authorization(
        self, operation: Dict[str, Any], spec: Dict[str, Any]
    ) -> bool:
        """Check if operation has authorization requirements."""
        # Look for OAuth2 scopes or other authorization indicators
        security = operation.get("security", spec.get("security", []))

        for sec_req in security:
            for scheme_name, scopes in sec_req.items():
                if scopes:  # Has scopes means authorization
                    return True

        return False
