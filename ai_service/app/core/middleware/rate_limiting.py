"""
Rate Limiting Middleware.

Implements token bucket rate limiting to prevent API abuse.
Each client IP address has a separate bucket of request tokens.

Configuration (from settings):
- rate_limit_enabled: Whether rate limiting is active
- rate_limit_calls: Maximum requests per period
- rate_limit_period: Time period in seconds
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitEnforcer(BaseHTTPMiddleware):
    """
    Middleware that enforces rate limits using the token bucket algorithm.

    Each client IP gets a bucket that holds up to `max_requests` tokens.
    Each request consumes one token. Tokens are replenished over `time_window_seconds`.

    When a client exceeds the rate limit, they receive HTTP 429 (Too Many Requests).

    Usage:
        app.add_middleware(
            RateLimitEnforcer,
            max_requests_per_window=100,
            time_window_seconds=3600
        )
    """

    def __init__(
        self,
        app,
        max_requests_per_window: int = None,
        time_window_seconds: int = None,
    ):
        """
        Initialize the rate limit enforcer.

        Args:
            app: The ASGI application.
            max_requests_per_window: Maximum requests allowed per time window.
                                     Defaults to settings.rate_limit_calls.
            time_window_seconds: Time window in seconds.
                                 Defaults to settings.rate_limit_period.
        """
        super().__init__(app)
        self.max_requests_per_window = (
            max_requests_per_window or settings.rate_limit_calls
        )
        self.time_window_seconds = time_window_seconds or settings.rate_limit_period
        self.is_enabled = settings.rate_limit_enabled

        # Stores request timestamps per client IP
        # Format: {"192.168.1.1": [timestamp1, timestamp2, ...]}
        self._request_history_by_client: Dict[str, List[float]] = defaultdict(list)

        logger.info(
            f"Rate limiter initialized: {self.max_requests_per_window} requests "
            f"per {self.time_window_seconds} seconds"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process the request, enforcing rate limits."""
        # Skip rate limiting if disabled
        if not self.is_enabled:
            return await call_next(request)

        # Skip rate limiting for health checks
        if self._is_health_check_request(request):
            return await call_next(request)

        client_identifier = self._get_client_identifier(request)

        if self._client_has_exceeded_rate_limit(client_identifier):
            return self._create_rate_limit_exceeded_response(client_identifier)

        self._record_request_from_client(client_identifier)

        return await call_next(request)

    def _is_health_check_request(self, request: Request) -> bool:
        """Check if this is a health check or metrics request that should bypass rate limiting."""
        paths_exempt_from_rate_limiting = [
            "/",
            "/ai/health",
            "/health",
            "/metrics",
            "/docs",
            "/openapi.json",
            "/redoc",
        ]
        return request.url.path in paths_exempt_from_rate_limiting

    def _get_client_identifier(self, request: Request) -> str:
        """
        Get a unique identifier for the client making the request.

        Uses X-Forwarded-For header if behind a proxy, otherwise client IP.
        """
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs; use the first one
            return forwarded_for.split(",")[0].strip()

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _client_has_exceeded_rate_limit(self, client_identifier: str) -> bool:
        """
        Check if the client has exceeded their rate limit.

        Removes expired request timestamps before checking.
        """
        current_time = time.time()
        window_start_time = current_time - self.time_window_seconds

        # Remove expired timestamps (older than the time window)
        client_request_times = self._request_history_by_client[client_identifier]
        recent_request_times = [
            timestamp
            for timestamp in client_request_times
            if timestamp > window_start_time
        ]
        self._request_history_by_client[client_identifier] = recent_request_times

        # Check if client has exceeded the limit
        request_count_in_window = len(recent_request_times)
        return request_count_in_window >= self.max_requests_per_window

    def _record_request_from_client(self, client_identifier: str) -> None:
        """Record a new request from the client."""
        current_time = time.time()
        self._request_history_by_client[client_identifier].append(current_time)

    def _create_rate_limit_exceeded_response(
        self, client_identifier: str
    ) -> JSONResponse:
        """Create the HTTP 429 response when rate limit is exceeded."""
        logger.warning(
            f"Rate limit exceeded for client: {client_identifier}",
            extra={"client_id": client_identifier},
        )

        seconds_until_reset = self._calculate_seconds_until_reset(client_identifier)

        return JSONResponse(
            status_code=429,
            content={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests. Please try again in {seconds_until_reset} seconds.",
                "retry_after_seconds": seconds_until_reset,
            },
            headers={
                "Retry-After": str(seconds_until_reset),
                "X-RateLimit-Limit": str(self.max_requests_per_window),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + seconds_until_reset),
            },
        )

    def _calculate_seconds_until_reset(self, client_identifier: str) -> int:
        """Calculate how many seconds until the client's rate limit resets."""
        client_request_times = self._request_history_by_client[client_identifier]
        if not client_request_times:
            return 0

        oldest_request_time = min(client_request_times)
        reset_time = oldest_request_time + self.time_window_seconds
        seconds_until_reset = int(reset_time - time.time())

        return max(0, seconds_until_reset)
