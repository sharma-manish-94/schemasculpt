"""
Domain interfaces (Ports) for SchemaSculpt AI Service.

These interfaces define contracts that infrastructure adapters must implement.
Following the Dependency Inversion Principle, high-level modules (services)
depend on these abstractions, not on concrete implementations.
"""

from app.domain.interfaces.cache_repository import ICacheRepository
from app.domain.interfaces.llm_provider import ILLMProvider
from app.domain.interfaces.rag_repository import IRAGRepository
from app.domain.interfaces.spec_validator import ISpecValidator

__all__ = [
    "ILLMProvider",
    "ICacheRepository",
    "IRAGRepository",
    "ISpecValidator",
]
