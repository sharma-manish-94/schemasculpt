"""
Custom exceptions for SchemaSculpt AI Service.
Provides structured error handling with appropriate HTTP status codes.
"""

from typing import Optional, Dict, Any


class SchemaSculptException(Exception):
    """Base exception for SchemaSculpt AI Service."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(SchemaSculptException):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="VALIDATION_ERROR",
            details=details
        )


class LLMError(SchemaSculptException):
    """Raised when LLM operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=502,
            error_code="LLM_ERROR",
            details=details
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM requests timeout."""

    def __init__(self, message: str = "LLM request timed out"):
        super().__init__(
            message=message,
            status_code=504,
            error_code="LLM_TIMEOUT"
        )


class OpenAPIError(SchemaSculptException):
    """Raised when OpenAPI spec operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="OPENAPI_ERROR",
            details=details
        )


class RateLimitError(SchemaSculptException):
    """Raised when rate limits are exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED"
        )


class ConfigurationError(SchemaSculptException):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=500,
            error_code="CONFIGURATION_ERROR",
            details=details
        )


class AuthenticationError(SchemaSculptException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(SchemaSculptException):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Authorization failed"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )