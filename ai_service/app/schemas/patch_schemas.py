"""
JSON Patch (RFC 6902) schemas for precise spec modifications.
"""

from typing import List, Optional, Any, Literal
from pydantic import BaseModel, Field, validator


class JsonPatchOperation(BaseModel):
    """Single JSON Patch operation following RFC 6902."""

    op: Literal["add", "remove", "replace", "move", "copy", "test"] = Field(
        ...,
        description="The operation to perform"
    )
    path: str = Field(
        ...,
        description="JSON Pointer path to the target location"
    )
    value: Optional[Any] = Field(
        None,
        description="Value for add/replace/test operations"
    )
    from_path: Optional[str] = Field(
        None,
        alias="from",
        description="Source path for move/copy operations"
    )

    @validator('path')
    def validate_path(cls, v):
        """Ensure path starts with /"""
        if not v.startswith('/'):
            raise ValueError('JSON Pointer path must start with /')
        return v

    @validator('value')
    def validate_value_required(cls, v, values):
        """Ensure value is present for operations that require it"""
        if values.get('op') in ['add', 'replace', 'test'] and v is None:
            raise ValueError(f"Value is required for {values.get('op')} operation")
        return v

    @validator('from_path')
    def validate_from_required(cls, v, values):
        """Ensure from is present for operations that require it"""
        if values.get('op') in ['move', 'copy'] and v is None:
            raise ValueError(f"'from' is required for {values.get('op')} operation")
        return v

    class Config:
        allow_population_by_field_name = True


class PatchGenerationRequest(BaseModel):
    """Request to generate JSON Patch for a fix."""

    spec_text: str = Field(..., description="OpenAPI specification")
    rule_id: str = Field(..., description="Rule identifier for the fix")
    context: dict = Field(default_factory=dict, description="Additional context for the fix")
    suggestion_message: Optional[str] = Field(None, description="The suggestion message")


class PatchGenerationResponse(BaseModel):
    """Response containing JSON Patch operations."""

    patches: List[JsonPatchOperation] = Field(
        ...,
        description="List of JSON Patch operations to apply"
    )
    explanation: str = Field(
        ...,
        description="Human-readable explanation of the changes"
    )
    rule_id: str = Field(..., description="Rule that was addressed")
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence level of the patch (0-1)"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Any warnings about the patch"
    )


class PatchApplicationRequest(BaseModel):
    """Request to apply JSON Patch to spec."""

    spec_text: str = Field(..., description="OpenAPI specification to modify")
    patches: List[JsonPatchOperation] = Field(..., description="Patch operations to apply")
    validate_after: bool = Field(
        default=True,
        description="Validate spec after applying patch"
    )


class PatchApplicationResponse(BaseModel):
    """Response after applying JSON Patch."""

    success: bool = Field(..., description="Whether patch was applied successfully")
    updated_spec: Optional[dict] = Field(None, description="Updated specification")
    errors: List[str] = Field(default_factory=list, description="Any errors during application")
    validation_errors: List[str] = Field(
        default_factory=list,
        description="Validation errors if validate_after=True"
    )
