"""
Domain layer for SchemaSculpt AI Service.

This layer contains:
- interfaces/: Abstract interfaces following Dependency Inversion Principle
- models/: Domain models and value objects

Following Clean Architecture / Hexagonal Architecture principles,
this layer has no dependencies on infrastructure or framework code.
"""

from app.domain.interfaces import (
    ICacheRepository,
    ILLMProvider,
    IRAGRepository,
    ISpecValidator,
)
from app.domain.models import LLMResponse, LLMStreamChunk, ValidationResult

__all__ = [
    "ILLMProvider",
    "ICacheRepository",
    "IRAGRepository",
    "ISpecValidator",
    "LLMResponse",
    "LLMStreamChunk",
    "ValidationResult",
]
