"""
Pydantic schemas for Mock Server endpoints.

These schemas provide input validation for mock data generation requests,
ensuring all required fields are present and properly formatted.
"""

from typing import Optional

from pydantic import BaseModel, Field


class MockDataGenerationRequest(BaseModel):
    """Request model for generating realistic mock data for a specific response schema."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="API path to generate mock data for",
    )
    method: str = Field(
        default="GET",
        description="HTTP method (GET, POST, PUT, DELETE, etc.)",
    )
    response_code: str = Field(
        default="200",
        pattern="^[1-5][0-9]{2}$",
        description="HTTP response code to generate data for",
    )
    variation: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Variation number for diversity in generated data",
    )
    use_ai: bool = Field(
        default=True,
        description="Whether to use AI for generating realistic data",
    )


class MockVariationsRequest(BaseModel):
    """Request model for generating multiple variations of mock data."""

    spec_text: str = Field(
        ...,
        min_length=1,
        description="OpenAPI specification text (JSON or YAML)",
    )
    path: str = Field(
        ...,
        min_length=1,
        description="API path to generate mock data for",
    )
    method: str = Field(
        default="GET",
        description="HTTP method (GET, POST, PUT, DELETE, etc.)",
    )
    response_code: str = Field(
        default="200",
        pattern="^[1-5][0-9]{2}$",
        description="HTTP response code to generate data for",
    )
    count: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of variations to generate (max 10 for performance)",
    )
