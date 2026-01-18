"""
Request Tracing Middleware.

Adds correlation IDs to requests for distributed tracing.
The correlation ID follows the request through all service calls,
making it easy to trace issues across multiple services.

Features:
- Generates unique correlation ID if not provided
- Reads correlation ID from X-Correlation-ID or X-Request-ID headers
- Adds correlation ID to response headers
- Stores correlation ID in request state for logging
"""

import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestTracer(BaseHTTPMiddleware):
    """
    Middleware that adds correlation IDs and timing information to requests.

    Each request gets a unique correlation ID that:
    - Can be used to trace the request through logs
    - Is returned in the response headers
    - Can be passed to downstream services

    Also tracks request duration for performance monitoring.

    Usage:
        app.add_middleware(RequestTracer)

    Headers:
        Request (optional):
            - X-Correlation-ID: Existing correlation ID to use
            - X-Request-ID: Alternative header for correlation ID

        Response:
            - X-Correlation-ID: The correlation ID used for this request
            - X-Request-Duration-Ms: Time taken to process the request
    """

    CORRELATION_ID_HEADERS = ["X-Correlation-ID", "X-Request-ID"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request, adding tracing information."""
        # Get or generate correlation ID
        correlation_id = self._get_or_generate_correlation_id(request)

        # Store in request state for use by other middleware and handlers
        request.state.correlation_id = correlation_id

        # Record start time for duration tracking
        request_started_at = time.time()

        # Log request start
        self._log_request_started(request, correlation_id)

        try:
            response = await call_next(request)

            # Calculate request duration
            request_duration_ms = self._calculate_duration_in_milliseconds(
                request_started_at
            )

            # Add tracing headers to response
            self._add_tracing_headers_to_response(
                response, correlation_id, request_duration_ms
            )

            # Log request completion
            self._log_request_completed(
                request, correlation_id, response.status_code, request_duration_ms
            )

            return response

        except Exception as error:
            # Calculate duration even for failed requests
            request_duration_ms = self._calculate_duration_in_milliseconds(
                request_started_at
            )

            # Log the error
            self._log_request_failed(
                request, correlation_id, error, request_duration_ms
            )

            raise

    def _get_or_generate_correlation_id(self, request: Request) -> str:
        """
        Get existing correlation ID from headers or generate a new one.

        Checks multiple header names for compatibility with different systems.
        """
        for header_name in self.CORRELATION_ID_HEADERS:
            existing_correlation_id = request.headers.get(header_name)
            if existing_correlation_id:
                return existing_correlation_id

        # Generate a new correlation ID
        return self._generate_correlation_id()

    def _generate_correlation_id(self) -> str:
        """Generate a unique correlation ID."""
        return str(uuid.uuid4())

    def _calculate_duration_in_milliseconds(self, start_time: float) -> int:
        """Calculate elapsed time in milliseconds since start_time."""
        elapsed_seconds = time.time() - start_time
        return int(elapsed_seconds * 1000)

    def _add_tracing_headers_to_response(
        self,
        response: Response,
        correlation_id: str,
        duration_ms: int,
    ) -> None:
        """Add tracing headers to the response."""
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-Duration-Ms"] = str(duration_ms)

    def _log_request_started(self, request: Request, correlation_id: str) -> None:
        """Log when a request starts processing."""
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": str(request.url.path),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

    def _log_request_completed(
        self,
        request: Request,
        correlation_id: str,
        status_code: int,
        duration_ms: int,
    ) -> None:
        """Log when a request completes successfully."""
        log_level = logging.INFO if status_code < 400 else logging.WARNING

        logger.log(
            log_level,
            f"Request completed: {request.method} {request.url.path} "
            f"- Status: {status_code} - Duration: {duration_ms}ms",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": str(request.url.path),
                "status_code": status_code,
                "duration_ms": duration_ms,
            },
        )

    def _log_request_failed(
        self,
        request: Request,
        correlation_id: str,
        error: Exception,
        duration_ms: int,
    ) -> None:
        """Log when a request fails with an exception."""
        logger.error(
            f"Request failed: {request.method} {request.url.path} "
            f"- Error: {type(error).__name__}: {str(error)} - Duration: {duration_ms}ms",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": str(request.url.path),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "duration_ms": duration_ms,
            },
        )
