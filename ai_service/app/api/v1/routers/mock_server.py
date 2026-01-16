"""
Mock Server Router.

Provides endpoints for managing mock servers and generating realistic mock data
for OpenAPI specifications. This module enables:

- Dynamic mock server creation from OpenAPI specs
- AI-powered response generation with configurable variation
- Request handling with simulated latency and error rates
- Mock data generation for testing purposes

Architecture:
- Mock servers are stored in-memory with configurable lifecycle
- Each mock server is identified by a UUID
- Response generation uses LLM for realistic data when enabled

Thread Safety:
- MOCKED_APIS dictionary should be replaced with a thread-safe cache
  in production (Redis or similar)
"""

import asyncio
import json
import logging
import random
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from prance import ResolvingParser

from app.api.deps import get_mock_data_service
from app.core.logging import set_correlation_id
from app.schemas.ai_schemas import MockStartRequest, MockStartResponse
from app.schemas.mock_server_schemas import (
    MockDataGenerationRequest,
    MockVariationsRequest,
)
from app.services.cache_service import cache_service
from app.services.mock_data_service import MockDataService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Mock Server"])


class AsyncMockStorage:
    """
    Thread-safe mock server storage using asyncio locks.

    This class provides atomic operations for managing mock server state.
    In production, consider replacing with Redis for horizontal scaling
    and persistence across restarts.

    Thread Safety:
        All operations are protected by an asyncio.Lock to ensure
        concurrent coroutines don't corrupt shared state.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, mock_id: str) -> Dict[str, Any] | None:
        """Get mock server data by ID."""
        async with self._lock:
            return self._data.get(mock_id)

    async def exists(self, mock_id: str) -> bool:
        """Check if a mock server exists."""
        async with self._lock:
            return mock_id in self._data

    async def set(self, mock_id: str, data: Dict[str, Any]) -> None:
        """Store mock server data."""
        async with self._lock:
            self._data[mock_id] = data

    async def update(self, mock_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in mock server data. Returns False if not found."""
        async with self._lock:
            if mock_id not in self._data:
                return False
            self._data[mock_id].update(updates)
            return True

    async def delete(self, mock_id: str) -> Dict[str, Any] | None:
        """Delete and return mock server data. Returns None if not found."""
        async with self._lock:
            return self._data.pop(mock_id, None)

    async def increment_request_count(self, mock_id: str) -> int:
        """Atomically increment request count. Returns new count or 0 if not found."""
        async with self._lock:
            if mock_id in self._data:
                current_count = self._data[mock_id].get("request_count", 0)
                self._data[mock_id]["request_count"] = current_count + 1
                return self._data[mock_id]["request_count"]
            return 0


# Singleton instance of async-safe mock storage
mock_storage = AsyncMockStorage()


@router.post("/mock/start", response_model=MockStartResponse)
async def start_mock_server(request: MockStartRequest) -> MockStartResponse:
    """
    Start a mock server with enhanced AI-powered response generation.

    Creates a new mock server instance from the provided OpenAPI specification.
    The mock server can generate AI-powered responses for all defined endpoints.

    Configuration options:
    - response_delay_ms: Add artificial latency to simulate network conditions
    - error_rate: Simulate random failures (0.0 to 1.0)
    - use_ai_responses: Enable/disable AI-powered response generation
    - response_variety: Number of response variations to cycle through

    Args:
        request: MockStartRequest containing the spec and configuration.

    Returns:
        MockStartResponse with mock_id, base_url, and available endpoints.

    Raises:
        HTTPException 400: If the OpenAPI specification is invalid.
    """
    mock_id = str(uuid.uuid4())
    correlation_id = set_correlation_id()

    logger.info(
        f"Creating mock server",
        extra={"correlation_id": correlation_id, "mock_id": mock_id},
    )

    try:
        # Parse and validate the specification
        parser = ResolvingParser(
            spec_string=request.spec_text, backend="openapi-spec-validator"
        )

        created_at = datetime.utcnow()

        # Store mock server configuration using async-safe storage
        await mock_storage.set(
            mock_id,
            {
                "specification": parser.specification,
                "config": request.model_dump(),
                "created_at": created_at,
                "request_count": 0,
                "correlation_id": correlation_id,
            },
        )

        spec_info = parser.specification.get("info", {})
        paths = parser.specification.get("paths", {})

        logger.info(
            "Mock server created successfully",
            extra={
                "correlation_id": correlation_id,
                "mock_id": mock_id,
                "endpoint_count": len(paths),
                "api_title": spec_info.get("title", "Unknown"),
            },
        )

        return MockStartResponse(
            mock_id=mock_id,
            base_url=f"/mock/{mock_id}",
            host=request.host,
            port=request.port or 8000,
            available_endpoints=list(paths.keys()),
            total_endpoints=len(paths),
            created_at=created_at,
        )

    except Exception as e:
        logger.error(
            f"Mock server creation failed: {str(e)}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPEC",
                "message": f"Invalid OpenAPI specification: {str(e)}",
                "correlation_id": correlation_id,
            },
        )


@router.put("/mock/{mock_id}")
async def update_mock_server(mock_id: str, request: MockStartRequest) -> Dict[str, Any]:
    """
    Update the specification for an existing mock server.

    Replaces the entire specification while preserving request statistics.

    Args:
        mock_id: UUID of the mock server to update.
        request: New specification and configuration.

    Returns:
        Confirmation message with update timestamp.

    Raises:
        HTTPException 404: If mock server not found.
        HTTPException 400: If new specification is invalid.
    """
    correlation_id = set_correlation_id()

    mock_data = await mock_storage.get(mock_id)
    if not mock_data:
        logger.warning(
            "Mock server not found",
            extra={"correlation_id": correlation_id, "mock_id": mock_id},
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    try:
        parser = ResolvingParser(
            spec_string=request.spec_text, backend="openapi-spec-validator"
        )

        # Preserve request count from previous configuration
        previous_request_count = mock_data.get("request_count", 0)
        updated_at = datetime.utcnow()

        await mock_storage.update(
            mock_id,
            {
                "specification": parser.specification,
                "config": request.model_dump(),
                "updated_at": updated_at,
            },
        )

        logger.info(
            "Mock server updated successfully",
            extra={
                "correlation_id": correlation_id,
                "mock_id": mock_id,
                "previous_request_count": previous_request_count,
            },
        )

        return {
            "message": f"Mock server {mock_id} updated successfully",
            "updated_at": updated_at,
            "correlation_id": correlation_id,
        }

    except Exception as e:
        logger.error(
            f"Mock server update failed: {str(e)}",
            extra={"correlation_id": correlation_id, "mock_id": mock_id},
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_SPEC",
                "message": f"Invalid OpenAPI specification: {str(e)}",
            },
        )


@router.get("/mock/{mock_id}")
async def get_mock_server_info(mock_id: str) -> Dict[str, Any]:
    """
    Get information about a mock server.

    Returns configuration, statistics, and available endpoints.

    Args:
        mock_id: UUID of the mock server.

    Returns:
        Mock server information including endpoints and statistics.

    Raises:
        HTTPException 404: If mock server not found.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    mock_data = MOCKED_APIS[mock_id]
    spec_info = mock_data["specification"].get("info", {})
    paths = mock_data["specification"].get("paths", {})

    return {
        "mock_id": mock_id,
        "title": spec_info.get("title", "Untitled API"),
        "version": spec_info.get("version", "1.0.0"),
        "description": spec_info.get("description", "No description"),
        "total_endpoints": len(paths),
        "available_endpoints": list(paths.keys()),
        "created_at": mock_data.get("created_at"),
        "updated_at": mock_data.get("updated_at"),
        "request_count": mock_data.get("request_count", 0),
        "config": mock_data.get("config", {}),
        "message": "Mock server is running",
        "docs": "Append a valid path from your specification to this URL to get mock responses",
    }


@router.delete("/mock/{mock_id}")
async def delete_mock_server(mock_id: str) -> Dict[str, Any]:
    """
    Delete a mock server and free its resources.

    Args:
        mock_id: UUID of the mock server to delete.

    Returns:
        Confirmation message.

    Raises:
        HTTPException 404: If mock server not found.
    """
    correlation_id = set_correlation_id()

    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    mock_data = MOCKED_APIS.pop(mock_id)

    logger.info(
        f"Mock server deleted",
        extra={
            "correlation_id": correlation_id,
            "mock_id": mock_id,
            "total_requests_served": mock_data.get("request_count", 0),
        },
    )

    return {
        "message": f"Mock server {mock_id} deleted successfully",
        "total_requests_served": mock_data.get("request_count", 0),
        "correlation_id": correlation_id,
    }


@router.api_route(
    "/mock/{mock_id}/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def handle_mock_request(
    mock_id: str,
    full_path: str,
    request: Request,
    mock_data_service: MockDataService = Depends(get_mock_data_service),
) -> JSONResponse:
    """
    Enhanced mock request handler with AI-powered response generation.

    Handles any HTTP request to the mock server and returns appropriate
    mock responses based on the OpenAPI specification.

    Features:
    - Path parameter extraction and validation
    - Configurable response delay simulation
    - Random error injection for resilience testing
    - AI-powered response generation with variations

    Args:
        mock_id: UUID of the mock server.
        full_path: Request path (everything after /mock/{mock_id}/).
        request: FastAPI Request object.
        mock_data_service: Injected mock data service for response generation.

    Returns:
        JSONResponse with mock data or error response.

    Raises:
        HTTPException 404: If mock server or endpoint not found.
        HTTPException 500: For simulated errors when error_rate is configured.
    """
    if mock_id not in MOCKED_APIS:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "MOCK_NOT_FOUND",
                "message": f"Mock server {mock_id} not found",
            },
        )

    mock_data = MOCKED_APIS[mock_id]
    spec = mock_data["specification"]
    config = mock_data.get("config", {})
    http_method = request.method.lower()

    # Increment request counter
    MOCKED_APIS[mock_id]["request_count"] = mock_data.get("request_count", 0) + 1

    # Add artificial delay if configured
    response_delay_ms = config.get("response_delay_ms", 0)
    if response_delay_ms > 0:
        await asyncio.sleep(response_delay_ms / 1000)

    # Simulate error rate if configured
    error_rate = config.get("error_rate", 0.0)
    if random.random() < error_rate:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "SIMULATED_ERROR",
                "message": "Simulated error for testing purposes",
                "mock_id": mock_id,
            },
        )

    # Look up the path in the specification
    path_to_lookup = f"/{full_path}"
    path_spec = spec.get("paths", {}).get(path_to_lookup)

    # If exact path not found, try to match parameterized paths
    if not path_spec:
        path_spec, matched_path = _match_parameterized_path(
            path_to_lookup, spec.get("paths", {})
        )
        if matched_path:
            path_to_lookup = matched_path

    if not path_spec or http_method not in path_spec:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "ENDPOINT_NOT_FOUND",
                "message": f"Endpoint {http_method.upper()} {path_to_lookup} not found in specification",
                "available_paths": list(spec.get("paths", {}).keys()),
            },
        )

    operation_spec = path_spec[http_method]

    # Try to get response schema
    try:
        response_schema = operation_spec["responses"]["200"]["content"][
            "application/json"
        ]["schema"]
    except KeyError:
        # No schema defined, return simple OK response
        return JSONResponse(
            content={"message": "OK", "mock_id": mock_id},
            status_code=200,
        )

    # Generate AI-powered response if enabled
    use_ai_responses = config.get("use_ai_responses", True)
    if use_ai_responses:
        try:
            mock_response = await mock_data_service.generate_mock_response(
                operation_spec=operation_spec,
                response_schema=response_schema,
                spec_context=spec,
                variation=random.randint(1, config.get("response_variety", 3)),
                use_ai=True,
            )
            return JSONResponse(content=mock_response)

        except Exception as e:
            logger.warning(
                f"AI response generation failed: {str(e)}, falling back to simple response"
            )
            return JSONResponse(
                content={"message": "OK", "mock_id": mock_id, "fallback": True}
            )

    return JSONResponse(content={"message": "OK", "mock_id": mock_id})


@router.post("/mock/generate-data")
async def generate_mock_data(
    request: MockDataGenerationRequest,
    mock_data_service: MockDataService = Depends(get_mock_data_service),
) -> Dict[str, Any]:
    """
    Generate realistic mock data for a specific response schema.

    Creates mock data based on the response schema of an API endpoint.
    Useful for generating test fixtures and sample responses.

    Args:
        request: Validated request containing spec_text, path, method, and generation options.

    Returns:
        Generated mock data with metadata.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info("Generating mock data", extra={"correlation_id": correlation_id})

    try:
        spec_text = request.spec_text
        path = request.path
        method = request.method.lower()
        response_code = request.response_code
        variation = request.variation
        use_ai = request.use_ai

        # Parse specification
        parser = ResolvingParser(
            spec_string=spec_text, backend="openapi-spec-validator"
        )
        spec = parser.specification

        # Get operation and response schema
        path_item = spec.get("paths", {}).get(path)
        if not path_item:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PATH_NOT_FOUND",
                    "message": f"Path '{path}' not found in specification",
                },
            )

        operation = path_item.get(method)
        if not operation:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "METHOD_NOT_FOUND",
                    "message": f"Method '{method.upper()}' not found for path '{path}'",
                },
            )

        response_spec = operation.get("responses", {}).get(response_code)
        if not response_spec:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "RESPONSE_NOT_FOUND",
                    "message": f"Response {response_code} not found for {method.upper()} {path}",
                },
            )

        # Extract schema
        response_schema = (
            response_spec.get("content", {}).get("application/json", {}).get("schema")
        )

        if not response_schema:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NO_SCHEMA",
                    "message": "No JSON schema found for response",
                },
            )

        # Generate mock data
        mock_data = await mock_data_service.generate_mock_response(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            variation=variation,
            use_ai=use_ai,
        )

        logger.info(
            "Mock data generated successfully", extra={"correlation_id": correlation_id}
        )

        return {
            "mock_data": mock_data,
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "variation": variation,
            "used_ai": use_ai,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock data generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MOCK_DATA_GENERATION_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


@router.post("/mock/generate-variations")
async def generate_mock_variations(
    request: MockVariationsRequest,
    mock_data_service: MockDataService = Depends(get_mock_data_service),
) -> Dict[str, Any]:
    """
    Generate multiple variations of mock data for testing diversity.

    Creates multiple unique mock responses for the same endpoint,
    useful for testing different scenarios and edge cases.

    Args:
        request: Validated request containing spec_text, path, method, and variation count.

    Returns:
        List of mock data variations with metadata.
    """
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)

    logger.info(
        "Generating mock data variations", extra={"correlation_id": correlation_id}
    )

    try:
        spec_text = request.spec_text
        path = request.path
        method = request.method.lower()
        response_code = request.response_code
        count = request.count  # Already validated by Pydantic (max 10)

        # Check cache first
        cached_mock_data = cache_service.get_mock_data(
            spec_text, path, method, response_code, count
        )
        if cached_mock_data:
            logger.info(f"Returning cached mock data for {method} {path}")
            return {
                "variations": cached_mock_data,
                "count": len(cached_mock_data),
                "endpoint": f"{method.upper()} {path}",
                "response_code": response_code,
                "cached": True,
                "correlation_id": correlation_id,
                "generated_at": datetime.utcnow().isoformat(),
            }

        # Parse specification (with caching)
        spec = cache_service.get_parsed_spec(spec_text)
        if not spec:
            parser = ResolvingParser(
                spec_string=spec_text, backend="openapi-spec-validator"
            )
            spec = parser.specification
            cache_service.cache_parsed_spec(spec_text, spec)

        # Get operation and response schema
        operation = spec["paths"][path][method]
        response_spec = operation.get("responses", {}).get(response_code)
        response_schema = (
            response_spec.get("content", {}).get("application/json", {}).get("schema")
        )

        if not response_schema:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NO_SCHEMA",
                    "message": "No JSON schema found for response",
                },
            )

        # Generate variations
        variations = await mock_data_service.generate_test_variations(
            operation_spec=operation,
            response_schema=response_schema,
            spec_context=spec,
            count=count,
        )

        # Cache the results
        cache_service.cache_mock_data(
            spec_text, path, method, response_code, count, variations
        )

        logger.info(
            f"Generated {len(variations)} mock data variations",
            extra={"correlation_id": correlation_id},
        )

        return {
            "variations": variations,
            "count": len(variations),
            "endpoint": f"{method.upper()} {path}",
            "response_code": response_code,
            "cached": False,
            "correlation_id": correlation_id,
            "generated_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mock variations generation failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "MOCK_VARIATIONS_FAILED",
                "message": str(e),
                "correlation_id": correlation_id,
            },
        )


def _match_parameterized_path(
    request_path: str, paths: Dict[str, Any]
) -> tuple[Dict[str, Any] | None, str | None]:
    """
    Match a request path against parameterized paths in the specification.

    For example, matches /users/123 against /users/{id}.

    Args:
        request_path: The actual request path (e.g., /users/123)
        paths: Dictionary of path specifications from OpenAPI spec

    Returns:
        Tuple of (path_spec, matched_path) if found, (None, None) otherwise
    """
    request_segments = request_path.strip("/").split("/")

    for spec_path, path_spec in paths.items():
        spec_segments = spec_path.strip("/").split("/")

        if len(request_segments) != len(spec_segments):
            continue

        match = True
        for req_seg, spec_seg in zip(request_segments, spec_segments):
            # Check if spec segment is a parameter (e.g., {id})
            if spec_seg.startswith("{") and spec_seg.endswith("}"):
                continue  # Parameter matches any value
            if req_seg != spec_seg:
                match = False
                break

        if match:
            return path_spec, spec_path

    return None, None
