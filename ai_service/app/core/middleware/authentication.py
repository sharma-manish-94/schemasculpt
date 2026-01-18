"""
Authentication Middleware.

Validates requests using either JWT tokens or API keys.
Supports multiple authentication methods for flexibility:
- Bearer JWT tokens (for user authentication)
- X-API-Key header (for service-to-service authentication)

Configuration (from settings):
- api_key: Expected API key value (if using API key auth)
- jwt_secret: Secret for JWT token validation
"""

import logging
from typing import Callable, List, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestAuthenticator(BaseHTTPMiddleware):
    """
    Middleware that authenticates incoming requests.

    Supports two authentication methods:
    1. API Key: Via X-API-Key header
    2. JWT Token: Via Authorization: Bearer <token> header

    Paths can be excluded from authentication (e.g., health checks, docs).

    Usage:
        app.add_middleware(
            RequestAuthenticator,
            paths_that_skip_authentication=["/", "/health", "/docs"]
        )
    """

    DEFAULT_PATHS_WITHOUT_AUTHENTICATION = [
        "/",
        "/ai/health",
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
    ]

    def __init__(
        self,
        app,
        paths_that_skip_authentication: Optional[List[str]] = None,
        require_authentication: bool = True,
    ):
        """
        Initialize the request authenticator.

        Args:
            app: The ASGI application.
            paths_that_skip_authentication: List of paths that don't require auth.
            require_authentication: If False, authentication is optional
                                   (request proceeds even if auth fails).
        """
        super().__init__(app)
        self.paths_without_authentication = (
            paths_that_skip_authentication or self.DEFAULT_PATHS_WITHOUT_AUTHENTICATION
        )
        self.require_authentication = require_authentication
        self.api_key = settings.api_key

        logger.info(
            f"Request authenticator initialized. "
            f"Authentication {'required' if require_authentication else 'optional'}."
        )

    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """Process the request, validating authentication."""

        # Allow OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Skip authentication for excluded paths
        if self._path_does_not_require_authentication(request):
            return await call_next(request)

        # Try to authenticate the request
        authentication_result = await self._authenticate_request(request)

        if authentication_result.is_authenticated:
            # Store authenticated user info in request state
            request.state.user = authentication_result.user_info
            request.state.auth_method = authentication_result.authentication_method
            return await call_next(request)

        # Authentication failed
        if self.require_authentication and self.api_key:
            return self._create_authentication_failed_response(
                authentication_result.failure_reason
            )

        # Authentication is optional or no API key configured
        return await call_next(request)

    def _path_does_not_require_authentication(self, request: Request) -> bool:
        """Check if the request path is excluded from authentication."""
        path = self._normalize_request_path(request)
        return path in self.paths_without_authentication or path == ""

    def _normalize_request_path(self, request: Request):
        return request.url.path.rstrip("/")

    async def _authenticate_request(self, request: Request) -> "AuthenticationResult":
        """
        Attempt to authenticate the request using available methods.

        Tries API key first, then JWT token.
        """
        # Try API key authentication
        api_key_result = self._validate_api_key(request)
        if api_key_result.is_authenticated:
            return api_key_result

        # Try JWT token authentication
        jwt_result = await self._validate_jwt_token(request)
        if jwt_result.is_authenticated:
            return jwt_result

        # No valid authentication found
        return AuthenticationResult(
            is_authenticated=False,
            failure_reason="No valid authentication credentials provided",
        )

    def _validate_api_key(self, request: Request) -> "AuthenticationResult":
        """Validate the X-API-Key header."""
        provided_api_key = request.headers.get("X-API-Key")

        if not provided_api_key:
            return AuthenticationResult(
                is_authenticated=False,
                failure_reason="API key not provided",
            )

        if not self.api_key:
            # No API key configured on server
            return AuthenticationResult(
                is_authenticated=False,
                failure_reason="API key authentication not configured",
            )

        if provided_api_key == self.api_key:
            logger.debug("Request authenticated via API key")
            return AuthenticationResult(
                is_authenticated=True,
                authentication_method="api_key",
                user_info={"auth_type": "api_key"},
            )

        return AuthenticationResult(
            is_authenticated=False,
            failure_reason="Invalid API key",
        )

    async def _validate_jwt_token(self, request: Request) -> "AuthenticationResult":
        """Validate the JWT Bearer token."""
        authorization_header = request.headers.get("Authorization")

        if not authorization_header:
            return AuthenticationResult(
                is_authenticated=False,
                failure_reason="Authorization header not provided",
            )

        if not authorization_header.startswith("Bearer "):
            return AuthenticationResult(
                is_authenticated=False,
                failure_reason="Invalid authorization header format",
            )

        token = authorization_header[7:]  # Remove "Bearer " prefix

        try:
            payload = self._decode_jwt_token(token)
            logger.debug(
                f"Request authenticated via JWT for user: {payload.get('sub')}"
            )
            return AuthenticationResult(
                is_authenticated=True,
                authentication_method="jwt",
                user_info=payload,
            )
        except JWTValidationError as error:
            return AuthenticationResult(
                is_authenticated=False,
                failure_reason=f"JWT validation failed: {error.reason}",
            )

    def _decode_jwt_token(self, token: str) -> dict:
        """
        Decode and validate a JWT token.

        Raises:
            JWTValidationError: If token is invalid.
        """
        try:
            from jose import JWTError, jwt

            jwt_secret = getattr(settings, "jwt_secret", None)
            if not jwt_secret:
                raise JWTValidationError("JWT secret not configured")

            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience=settings.jwt_audience,
                issuer=settings.jwt_issuer,
            )

            if "sub" not in payload:
                raise JWTValidationError("Missing subject claim.")

            return payload

        except JWTError as error:
            logger.error(f"JWT validation error: {error}")
            raise JWTValidationError("Invalid or expired token")
        except ImportError:
            raise JWTValidationError("JWT library not installed")

    def _create_authentication_failed_response(self, reason: str) -> JSONResponse:
        """Create the HTTP 401 response when authentication fails."""
        logger.warning(f"Authentication failed: {reason}")

        return JSONResponse(
            status_code=401,
            content={
                "error": "AUTHENTICATION_REQUIRED",
                "message": "Valid authentication credentials are required to access this resource.",
                "hint": "Provide either X-API-Key header or Authorization: Bearer <token>",
            },
            headers={
                "WWW-Authenticate": 'Bearer realm="schemasculpt"',
            },
        )


class AuthenticationResult:
    """Result of an authentication attempt."""

    def __init__(
        self,
        is_authenticated: bool,
        authentication_method: Optional[str] = None,
        user_info: Optional[dict] = None,
        failure_reason: Optional[str] = None,
    ):
        self.is_authenticated = is_authenticated
        self.authentication_method = authentication_method
        self.user_info = user_info or {}
        self.failure_reason = failure_reason


class JWTValidationError(Exception):
    """Raised when JWT token validation fails."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)
