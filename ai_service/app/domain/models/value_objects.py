"""
Domain Value Objects.

Immutable data classes representing domain concepts.
These have no behavior, only data - following Value Object pattern from DDD.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class LLMUsage:
    """Token usage statistics from an LLM response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @property
    def is_available(self) -> bool:
        """Check if usage stats are available."""
        return self.total_tokens > 0


@dataclass(frozen=True)
class LLMResponse:
    """
    Standard response from an LLM provider.

    This is a value object - immutable and comparable by value.
    """

    content: str
    model: str
    provider: str
    usage: Optional[LLMUsage] = None
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def has_content(self) -> bool:
        """Check if response has content."""
        return bool(self.content and self.content.strip())

    @property
    def token_count(self) -> int:
        """Get total token count if available."""
        return self.usage.total_tokens if self.usage else 0


@dataclass(frozen=True)
class LLMStreamChunk:
    """
    A chunk of a streaming LLM response.

    Used for streaming responses where content arrives incrementally.
    """

    content: str
    model: str
    provider: str
    is_final: bool = False
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_content(self) -> bool:
        """Check if chunk has content."""
        return bool(self.content)


@dataclass(frozen=True)
class ValidationError:
    """A single validation error."""

    message: str
    path: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    severity: str = "error"  # "error", "warning", "info"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "column": self.column,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ValidationResult:
    """
    Result of validating an OpenAPI specification.

    This is a value object containing validation status and any errors/warnings.
    """

    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    spec_version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        """Get number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Get number of warnings."""
        return len(self.warnings)

    @property
    def has_issues(self) -> bool:
        """Check if there are any errors or warnings."""
        return len(self.errors) > 0 or len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "spec_version": self.spec_version,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class CacheEntry:
    """
    A cached value with metadata.

    Used internally by cache implementations.
    """

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    hit_count: int = 0

    @property
    def is_expired(self) -> bool:
        """Check if the entry has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass(frozen=True)
class SecurityFinding:
    """
    A security finding from analysis.

    Represents a potential security issue found in an OpenAPI spec.
    """

    id: str
    title: str
    description: str
    severity: str  # "critical", "high", "medium", "low", "info"
    category: str  # "authentication", "authorization", "data_exposure", etc.
    path: Optional[str] = None
    method: Optional[str] = None
    recommendation: Optional[str] = None
    cwe_id: Optional[str] = None
    owasp_category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "path": self.path,
            "method": self.method,
            "recommendation": self.recommendation,
            "cwe_id": self.cwe_id,
            "owasp_category": self.owasp_category,
            "metadata": self.metadata,
        }
