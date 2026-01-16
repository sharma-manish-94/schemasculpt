"""
OpenAPI Specification Validator Interface.

Defines the contract for spec validation implementations.
This abstraction wraps blocking validation libraries for async-safe usage.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.domain.models.value_objects import ValidationResult


class ISpecValidator(ABC):
    """
    Abstract interface for OpenAPI specification validators.

    All validator implementations must implement this interface.
    Implementations should handle blocking operations in a thread pool
    to avoid blocking the event loop.

    Usage:
        # In service layer
        class AIService:
            def __init__(self, validator: ISpecValidator):
                self._validator = validator

            async def process(self, spec_text: str) -> dict:
                # Validate input spec
                result = await self._validator.validate(spec_text)
                if not result.is_valid:
                    raise ValidationError(result.errors)

                # Parse spec for processing
                spec = await self._validator.parse(spec_text)
                return await self._process_spec(spec)
    """

    @abstractmethod
    async def validate(
        self,
        spec_text: str,
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate an OpenAPI specification.

        This method should run validation in a thread pool to avoid blocking.

        Args:
            spec_text: The OpenAPI specification as JSON or YAML string.
            strict: If True, treat warnings as errors.

        Returns:
            ValidationResult with is_valid status, errors, and warnings.
        """
        pass

    @abstractmethod
    async def parse(
        self,
        spec_text: str,
        resolve_refs: bool = True,
    ) -> Dict[str, Any]:
        """
        Parse an OpenAPI specification into a dictionary.

        This method should run parsing in a thread pool to avoid blocking.

        Args:
            spec_text: The OpenAPI specification as JSON or YAML string.
            resolve_refs: If True, resolve $ref references.

        Returns:
            Parsed specification as a dictionary.

        Raises:
            ValidationError: If the spec cannot be parsed.
        """
        pass

    @abstractmethod
    async def get_endpoints(
        self,
        spec_text: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract all endpoints from an OpenAPI specification.

        Args:
            spec_text: The OpenAPI specification as JSON or YAML string.

        Returns:
            List of endpoint dictionaries with path, method, and operation details.
        """
        pass

    @abstractmethod
    async def get_schemas(
        self,
        spec_text: str,
    ) -> Dict[str, Any]:
        """
        Extract all schemas from an OpenAPI specification.

        Args:
            spec_text: The OpenAPI specification as JSON or YAML string.

        Returns:
            Dictionary of schema name to schema definition.
        """
        pass

    @abstractmethod
    async def get_security_schemes(
        self,
        spec_text: str,
    ) -> Dict[str, Any]:
        """
        Extract security schemes from an OpenAPI specification.

        Args:
            spec_text: The OpenAPI specification as JSON or YAML string.

        Returns:
            Dictionary of security scheme name to definition.
        """
        pass

    @abstractmethod
    def detect_format(self, spec_text: str) -> str:
        """
        Detect the format of a specification (JSON or YAML).

        Args:
            spec_text: The specification text.

        Returns:
            "json" or "yaml".
        """
        pass
