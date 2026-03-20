"""
Global Exception Handler Middleware.

Catches all unhandled exceptions and converts them to standardized JSON responses.
This replaces the dependency-based exception handling pattern that required
adding `Depends(handle_exceptions)` to every endpoint.

Benefits:
- Consistent error response format across all endpoints
- No need to remember to add exception handling to each endpoint
- Centralized error logging and monitoring
"""

import logging
import traceback
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import SchemaSculptException

logger = logging.getLogger(__name__)


class GlobalExceptionHandler(BaseHTTPMiddleware):
    """
    Middleware that catches all exceptions and returns standardized error responses.

    This middleware should be added early in the middleware stack so it can catch
    exceptions from other middleware and route handlers.

    Error Response Format:
        {
            "error": "ERROR_CODE",
            "message": "Human readable error message",
            "details": {...},  # Optional additional context
            "correlation_id": "uuid"  # For tracing
        }

    Usage:
        app.add_middleware(GlobalExceptionHandler)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process the request and catch any exceptions."""
        correlation_id = getattr(request.state, "correlation_id", "unknown")

        try:
            response = await call_next(request)
            return response

        except SchemaSculptException as application_error:
            # Handle known application errors
            return self._create_error_response_for_application_error(
                application_error, correlation_id
            )

        except Exception as unexpected_error:
            # Handle unexpected errors
            return self._create_error_response_for_unexpected_error(
                unexpected_error, correlation_id, request
            )

    def _create_error_response_for_application_error(
        self,
        error: SchemaSculptException,
        correlation_id: str,
    ) -> JSONResponse:
        """
        Create a JSON response for a known application error.

        Application errors have well-defined error codes and messages.
        """
        logger.warning(
            f"Application error occurred: {error.error_code}",
            extra={
                "error_code": error.error_code,
                "message": error.message,
                "correlation_id": correlation_id,
            },
        )

        return JSONResponse(
            status_code=error.status_code,
            content={
                "error": error.error_code,
                "message": error.message,
                "details": error.details,
                "correlation_id": correlation_id,
            },
        )

    def _create_error_response_for_unexpected_error(
        self,
        error: Exception,
        correlation_id: str,
        request: Request,
    ) -> JSONResponse:
        """
        Create a JSON response for an unexpected error.

        Unexpected errors are logged with full stack trace but
        return generic messages to avoid exposing internal details.
        """
        error_id = correlation_id  # Use correlation ID for tracking

        logger.error(
            f"Unexpected error occurred: {str(error)}",
            extra={
                "error_id": error_id,
                "error_type": type(error).__name__,
                "path": str(request.url.path),
                "method": request.method,
                "correlation_id": correlation_id,
                "traceback": traceback.format_exc(),
            },
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "error_id": error_id,
                "correlation_id": correlation_id,
            },
        )
