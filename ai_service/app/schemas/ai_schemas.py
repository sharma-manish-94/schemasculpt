"""
Enhanced Pydantic schemas for SchemaSculpt AI Service.
Provides comprehensive data validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator

from ..core.config import settings


class OperationType(str, Enum):
    """Supported OpenAPI operation types."""

    MODIFY = "modify"
    GENERATE = "generate"
    VALIDATE = "validate"
    OPTIMIZE = "optimize"
    ENHANCE = "enhance"
    PATCH = "patch"
    MERGE = "merge"
    TRANSFORM = "transform"


class ResponseFormat(str, Enum):
    """Supported response formats."""

    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"


class StreamingMode(str, Enum):
    """Streaming response modes."""

    DISABLED = "disabled"
    TOKENS = "tokens"
    CHUNKS = "chunks"
    EVENTS = "events"


class LLMParameters(BaseModel):
    """LLM-specific parameters for fine-tuning responses."""

    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=8192)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    model: str = Field(default_factory=lambda: settings.default_model)


class ContextWindow(BaseModel):
    """Context management for conversation continuity."""

    conversation_id: Optional[UUID] = Field(default_factory=uuid4)
    previous_operations: List[str] = Field(default_factory=list)
    context_size: int = Field(default=10, ge=1, le=50)
    preserve_context: bool = Field(default=True)


class JSONPatchOperation(BaseModel):
    """JSON Patch operation for precise spec modifications."""

    op: str = Field(..., pattern="^(add|remove|replace|move|copy|test)$")
    path: str = Field(..., description="JSON Pointer path")
    value: Optional[Any] = Field(default=None)
    from_path: Optional[str] = Field(default=None, alias="from")


class AIRequest(BaseModel):
    """Enhanced AI request with advanced capabilities."""

    # Core fields - support both camelCase (Spring Boot) and snake_case (Python)
    spec_text: str = Field(
        ..., description="OpenAPI specification text", alias="specText"
    )
    prompt: str = Field(..., min_length=1, description="User prompt for AI")
    operation_type: OperationType = Field(default=OperationType.MODIFY)

    # Advanced features
    streaming: StreamingMode = Field(default=StreamingMode.DISABLED)
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)
    llm_parameters: LLMParameters = Field(default_factory=LLMParameters)
    context: ContextWindow = Field(default_factory=ContextWindow)

    # JSON Patch support
    json_patches: Optional[List[JSONPatchOperation]] = Field(default=None)
    target_paths: Optional[List[str]] = Field(
        default=None, description="Specific paths to modify"
    )

    # Validation options
    validate_output: bool = Field(default=True)
    auto_fix: bool = Field(default=True)
    preserve_formatting: bool = Field(default=True)

    # Metadata
    user_id: Optional[str] = Field(default=None)
    session_id: Optional[UUID] = Field(default=None)
    tags: List[str] = Field(default_factory=list)

    # Pydantic v2 configuration
    model_config = {"populate_by_name": True}  # Allow both spec_text and specText

    @validator("json_patches")
    def validate_patches(cls, v):
        if v:
            for patch in v:
                if patch.op in ["move", "copy"] and not patch.from_path:
                    raise ValueError(f"Operation {patch.op} requires 'from' field")
        return v


class ValidationResult(BaseModel):
    """OpenAPI validation results."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class PerformanceMetrics(BaseModel):
    """Performance metrics for AI operations."""

    processing_time_ms: float
    token_count: int
    model_used: str
    cache_hit: bool = False
    retry_count: int = 0


class AIResponse(BaseModel):
    """Enhanced AI response with comprehensive metadata."""

    # Core response
    updated_spec_text: str = Field(..., description="Modified OpenAPI specification")
    operation_type: OperationType

    # Validation and quality
    validation: ValidationResult
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="AI confidence in the result"
    )

    # Applied changes
    changes_summary: str = Field(description="Human-readable summary of changes")
    applied_patches: Optional[List[JSONPatchOperation]] = Field(default=None)
    modified_paths: List[str] = Field(default_factory=list)

    # Metadata
    request_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    performance: PerformanceMetrics

    # Context preservation
    context: Optional[ContextWindow] = Field(default=None)
    follow_up_suggestions: List[str] = Field(default_factory=list)


class StreamingChunk(BaseModel):
    """Streaming response chunk."""

    chunk_id: int
    content: str
    is_final: bool = False
    metadata: Optional[Dict[str, Any]] = Field(default=None)


class GenerateSpecRequest(BaseModel):
    """Enhanced specification generation request."""

    prompt: str = Field(
        ..., min_length=1, description="Description of the API to generate"
    )

    # Generation parameters
    api_style: str = Field(
        default="REST", description="API style (REST, GraphQL, gRPC)"
    )
    openapi_version: str = Field(default="3.0.0", pattern="^3\.[0-9]+\.[0-9]+$")
    include_examples: bool = Field(default=True)
    include_security: bool = Field(default=True)

    # Domain-specific options
    domain: Optional[str] = Field(
        default=None, description="API domain (e.g., 'ecommerce', 'social')"
    )
    complexity_level: str = Field(default="medium", pattern="^(simple|medium|complex)$")
    target_framework: Optional[str] = Field(default=None)

    # Advanced features
    llm_parameters: LLMParameters = Field(default_factory=LLMParameters)
    streaming: StreamingMode = Field(default=StreamingMode.DISABLED)
    response_format: ResponseFormat = Field(default=ResponseFormat.JSON)

    # Metadata
    user_id: Optional[str] = Field(default=None)
    project_name: Optional[str] = Field(default=None)


class MockStartRequest(BaseModel):
    """Enhanced mock server configuration."""

    spec_text: str = Field(..., description="OpenAPI specification for mocking")

    # Mock server options
    port: Optional[int] = Field(default=None, ge=1024, le=65535)
    host: str = Field(default="localhost")
    base_path: str = Field(default="")

    # Response behavior
    response_delay_ms: int = Field(default=0, ge=0, le=10000)
    error_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    include_cors: bool = Field(default=True)

    # Advanced mocking
    use_ai_responses: bool = Field(
        default=True, description="Generate realistic responses using AI"
    )
    response_variety: int = Field(
        default=3, ge=1, le=10, description="Number of response variations"
    )

    # Metadata
    mock_name: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)


class MockStartResponse(BaseModel):
    """Enhanced mock server response."""

    mock_id: UUID = Field(default_factory=uuid4)
    base_url: str

    # Server details
    host: str
    port: int
    status: str = Field(default="running")

    # Endpoints
    available_endpoints: List[str] = Field(default_factory=list)
    total_endpoints: int

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)


class HealthResponse(BaseModel):
    """Service health status."""

    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime_seconds: float

    # Service dependencies
    dependencies: Dict[str, str] = Field(default_factory=dict)

    # Performance metrics
    total_requests: int = 0
    average_response_time_ms: float = 0.0
    error_rate: float = 0.0


class ErrorResponse(BaseModel):
    """Standardized error response."""

    error: str
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = Field(default=None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[UUID] = Field(default=None)
    correlation_id: Optional[str] = Field(default=None)
