"""
Pydantic schemas for Test Generation endpoints.

These schemas provide input validation for test case generation requests,
ensuring all required fields are present and properly formatted.
"""

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TestType(str, Enum):
    """Types of test cases that can be generated."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    EDGE_CASE = "edge_case"


class TestPriority(str, Enum):
    """Priority levels for test cases."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Mapping from test type to priority
TEST_TYPE_TO_PRIORITY: dict[TestType, TestPriority] = {
    TestType.POSITIVE: TestPriority.HIGH,
    TestType.NEGATIVE: TestPriority.MEDIUM,
    TestType.EDGE_CASE: TestPriority.LOW,
}


class TestCaseGenerationRequest(BaseModel):
    """Request model for AI-powered test case generation for a single operation."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="API path to generate tests for (e.g., '/users/{id}')",
    )
    method: str = Field(
        default="GET",
        description="HTTP method (GET, POST, PUT, DELETE, etc.)",
    )
    operation_summary: str = Field(
        default="",
        description="Description of the operation being tested",
    )
    test_types: List[str] = Field(
        default=["positive", "negative", "edge_cases"],
        description="Types of tests to generate",
    )


class TestSuiteOptions(BaseModel):
    """Options for test suite generation."""

    include_ai_tests: bool = Field(
        default=True,
        description="Whether to include AI-generated advanced tests",
    )
    max_endpoints: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of endpoints to process",
    )
    test_types: List[str] = Field(
        default=["positive", "negative", "edge_case"],
        description="Types of tests to generate",
    )
    coverage_level: str = Field(
        default="standard",
        pattern="^(minimal|standard|comprehensive)$",
        description="Test coverage level",
    )


class TestSuiteGenerationRequest(BaseModel):
    """Request model for generating a complete test suite for an entire API."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    options: Optional[TestSuiteOptions] = Field(
        default=None,
        description="Generation options",
    )


class SingleEndpointTestRequest(BaseModel):
    """Request model for generating tests for a single endpoint with caching support."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="API path to generate tests for",
    )
    method: str = Field(
        default="GET",
        description="HTTP method",
    )
    include_ai_tests: bool = Field(
        default=True,
        description="Whether to include AI-generated tests",
    )


class BulkTestGenerationRequest(BaseModel):
    """Request model for generating tests for all endpoints in a specification."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    include_ai_tests: bool = Field(
        default=False,
        description="Whether to include AI-generated tests (default false for performance)",
    )
    max_endpoints: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of endpoints to process",
    )
