"""
RepoMind HTTP Proxy Router.

Bridges the Java API layer (which speaks HTTP REST) to RepoMind's MCP stdio
protocol. Java's RepoMindServiceImpl calls:

    POST /ai/repomind/call_tool
    Body: {"tool_name": "get_context", "arguments": {...}}

This proxy forwards the call to RepoMind via MCP stdio and returns the result.

Architecture:
    Java RepoMindServiceImpl
        → POST http://localhost:8000/ai/repomind/call_tool
        → RepoMindProxyRouter (this file)
        → RepoMindClient (MCP stdio)
        → RepoMind MCP server

This approach keeps the Java layer thin (no MCP SDK needed) while the Python
AI service handles the MCP protocol complexity.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/repomind", tags=["RepoMind Proxy"])


class ToolCallRequest(BaseModel):
    """
    Matches Java's McpToolCallRequest record:
        private record McpToolCallRequest(String tool_name, Map<String, Object> arguments) {}
    """

    tool_name: str
    arguments: Dict[str, Any] = {}


@router.post("/call_tool")
async def proxy_repomind_tool_call(request: ToolCallRequest) -> Dict[str, Any]:
    """
    HTTP proxy for RepoMind MCP tool calls.

    Accepts the same payload format as Java's McpToolCallRequest and forwards
    to RepoMind via MCP stdio. Supports all 40 RepoMind tools including:

    Code intelligence:  get_context, semantic_grep, lookup_symbol
    Call graph:         find_callers, find_callees
    Security:           scan_vulnerabilities, map_attack_surface, analyze_auth_flows
    SchemaSculpt tools: correlate_spec_to_code, validate_attack_chain,
                        verify_auth_contract_deep, trace_schema_field_to_sink
    Production:         get_metrics, find_tests, analyze_ownership

    Returns:
        {"result": <tool output>, "tool": "<tool_name>"}

    Raises:
        502 Bad Gateway if RepoMind is unavailable or the tool call fails.
    """
    from app.services.repomind_client import RepoMindClient

    logger.debug(
        "RepoMind proxy: %s args=%s", request.tool_name, list(request.arguments.keys())
    )

    try:
        client = RepoMindClient()
        result = await client.call_tool(request.tool_name, request.arguments)
        return {"result": result, "tool": request.tool_name}

    except Exception as exc:
        logger.error("RepoMind proxy failed for tool '%s': %s", request.tool_name, exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": "REPOMIND_TOOL_FAILED",
                "tool": request.tool_name,
                "message": str(exc),
                "hint": (
                    "Ensure RepoMind is installed and REPOMIND_COMMAND / REPOMIND_ARGS "
                    "environment variables are configured correctly."
                ),
            },
        )


@router.get("/health")
async def repomind_health() -> Dict[str, Any]:
    """
    Check RepoMind availability by listing its tools.

    Returns status and tool count if RepoMind is reachable.
    """
    import os

    from app.mcp.client import MCPClient, MCPConnectionError

    command = os.environ.get("REPOMIND_COMMAND", "repomind")
    args = os.environ.get("REPOMIND_ARGS", "serve").split()

    client = MCPClient()
    try:
        await client.connect(command, args)
        tools = await client.list_tools()
        return {
            "status": "available",
            "command": command,
            "tool_count": len(tools),
            "tools_sample": [t.name for t in tools[:5]] if tools else [],
        }
    except MCPConnectionError as exc:
        return {
            "status": "unavailable",
            "command": command,
            "error": str(exc),
        }
    finally:
        await client.disconnect()
