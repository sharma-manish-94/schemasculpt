"""
RepoMind MCP Client for SchemaSculpt AI Service.

Provides async access to RepoMind's 40 code intelligence tools via MCP stdio
protocol. RepoMind is a Python MCP server that indexes source code and exposes
tools for semantic search, security analysis, and spec-to-code correlation.

This client is used by:
- AttackPathOrchestrator: validate AI-generated attack chains against real code
- HTTP proxy endpoint: bridge Java API calls (REST) to RepoMind (MCP stdio)

Architecture:
    Java API  →  HTTP  →  /ai/repomind/call_tool  →  RepoMindClient  →  MCP stdio  →  RepoMind

Environment variables:
    REPOMIND_COMMAND: Command to start RepoMind server (default: "repomind")
    REPOMIND_ARGS:    Space-separated args (default: "serve")
    REPOMIND_ENABLED: Set to "true" to enable code validation (default: "false")
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _is_enabled() -> bool:
    """Check if RepoMind integration is enabled via environment."""
    return os.environ.get("REPOMIND_ENABLED", "false").lower() == "true"


def _parse_mcp_result(result: Any) -> Any:
    """
    Parse the result from an MCP tool call into a plain Python value.

    MCP results are CallToolResult objects with a .content list of
    TextContent/ImageContent items. We extract the text and parse as JSON.
    """
    if result is None:
        return None

    # Handle MCP SDK CallToolResult
    if hasattr(result, "content") and result.content:
        for item in result.content:
            if hasattr(item, "text") and item.text:
                try:
                    return json.loads(item.text)
                except (json.JSONDecodeError, ValueError):
                    return {"result": item.text}

    # Already a plain value (e.g. in tests)
    if isinstance(result, (dict, list, str, int, float, bool)):
        return result

    return {"result": str(result)}


class RepoMindUnavailableError(Exception):
    """Raised when RepoMind is not available or not enabled."""


class RepoMindClient:
    """
    Async client for RepoMind's MCP stdio server.

    Each call_tool() invocation opens a short-lived MCP connection, calls the
    tool, and disconnects. This is safe for low-frequency calls (attack path
    validation, code context lookups). For high-frequency batch usage, reuse
    a persistent session via the async context manager.

    Usage (single call):
        client = RepoMindClient()
        result = await client.call_tool("validate_attack_chain", {...})

    Usage (batch — one connection):
        async with RepoMindClient() as client:
            r1 = await client.call_tool("correlate_spec_to_code", {...})
            r2 = await client.call_tool("validate_attack_chain", {...})
    """

    def __init__(
        self,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
    ):
        from app.core.config import settings

        self.command = command or settings.repomind_command
        raw_args = args
        if raw_args is None:
            raw_args = settings.repomind_args.split()
        self.args: List[str] = raw_args if isinstance(raw_args, list) else [raw_args]
        self._client = None
        self._session_active = False

    # ------------------------------------------------------------------
    # Context manager (persistent session for batch calls)
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "RepoMindClient":
        from app.mcp.client import MCPClient

        self._client = MCPClient()
        await self._client.connect(self.command, self.args)
        self._session_active = True
        logger.debug("RepoMindClient: persistent session opened")
        return self

    async def __aexit__(self, *_) -> None:
        if self._client:
            await self._client.disconnect()
        self._session_active = False
        logger.debug("RepoMindClient: persistent session closed")

    # ------------------------------------------------------------------
    # Core call_tool (per-call or session-based)
    # ------------------------------------------------------------------

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a RepoMind MCP tool.

        Opens a connection per call unless already inside an async context
        manager session (more efficient for batch operations).
        """
        if self._session_active and self._client:
            raw = await self._client.call_tool(tool_name, arguments)
            return _parse_mcp_result(raw)

        # Per-call connection (stateless usage)
        from app.mcp.client import MCPClient

        client = MCPClient()
        try:
            await client.connect(self.command, self.args)
            raw = await client.call_tool(tool_name, arguments)
            return _parse_mcp_result(raw)
        except Exception as exc:
            logger.error(f"RepoMind tool '{tool_name}' failed: {exc}")
            raise
        finally:
            await client.disconnect()

    # ------------------------------------------------------------------
    # SchemaSculpt integration tools
    # ------------------------------------------------------------------

    async def validate_attack_chain(
        self,
        attack_chain: List[Dict[str, Any]],
        repo_name: Optional[str] = None,
        chain_id: Optional[str] = None,
        chain_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate whether an AI-generated attack chain is exploitable in actual code.

        Per-step verdicts: CODE_CONFIRMED | CODE_DISPUTED | PARTIAL | UNVERIFIABLE
        Overall verdict: FULLY_EXPLOITABLE | PARTIALLY_EXPLOITABLE | MITIGATED | INSUFFICIENT_DATA
        """
        args: Dict[str, Any] = {"attack_chain": attack_chain}
        if repo_name:
            args["repo_name"] = repo_name
        if chain_id:
            args["chain_id"] = chain_id
        if chain_description:
            args["chain_description"] = chain_description
        return await self.call_tool("validate_attack_chain", args)

    async def correlate_spec_to_code(
        self,
        openapi_path: str,
        http_method: str,
        repo_name: Optional[str] = None,
        include_all_candidates: bool = False,
    ) -> Dict[str, Any]:
        """Find the code handler that implements a given OpenAPI endpoint."""
        args: Dict[str, Any] = {
            "openapi_path": openapi_path,
            "http_method": http_method,
            "include_all_candidates": include_all_candidates,
        }
        if repo_name:
            args["repo_name"] = repo_name
        return await self.call_tool("correlate_spec_to_code", args)

    async def verify_auth_contract_deep(
        self,
        openapi_path: str,
        http_method: str,
        declared_security: List[Any],
        repo_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verify that auth constraints in code match what the spec declares."""
        args: Dict[str, Any] = {
            "openapi_path": openapi_path,
            "http_method": http_method,
            "declared_security": declared_security,
        }
        if repo_name:
            args["repo_name"] = repo_name
        return await self.call_tool("verify_auth_contract_deep", args)

    async def trace_schema_field_to_sink(
        self,
        field_name: str,
        openapi_path: str,
        http_method: str,
        repo_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trace a request field through the codebase to its final sinks."""
        args: Dict[str, Any] = {
            "field_name": field_name,
            "openapi_path": openapi_path,
            "http_method": http_method,
        }
        if repo_name:
            args["repo_name"] = repo_name
        return await self.call_tool("trace_schema_field_to_sink", args)

    # ------------------------------------------------------------------
    # General RepoMind tools (used by Java proxy / ImplementationController)
    # ------------------------------------------------------------------

    async def get_context(
        self,
        symbol_name: str,
        repo_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get code context (implementation) for a named symbol."""
        args: Dict[str, Any] = {"symbol_name": symbol_name}
        if repo_filter:
            args["repo_filter"] = repo_filter
        return await self.call_tool("get_context", args)

    async def get_metrics(
        self,
        symbol_name: str,
        repo_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get complexity and quality metrics for a symbol."""
        args: Dict[str, Any] = {"symbol_name": symbol_name}
        if repo_filter:
            args["repo_filter"] = repo_filter
        return await self.call_tool("get_metrics", args)

    async def find_tests(
        self,
        symbol_name: str,
        repo_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find test functions that cover a given symbol."""
        args: Dict[str, Any] = {"symbol_name": symbol_name}
        if repo_filter:
            args["repo_filter"] = repo_filter
        return await self.call_tool("find_tests", args)

    async def index_repo(
        self,
        repo_path: str,
        repo_name: str,
    ) -> Dict[str, Any]:
        """Trigger repository indexing in RepoMind."""
        return await self.call_tool(
            "index_repo", {"repo_path": repo_path, "repo_name": repo_name}
        )

    async def analyze_ownership(
        self,
        file_paths: List[str],
        repo_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze code ownership via git blame patterns."""
        args: Dict[str, Any] = {"file_paths": file_paths}
        if repo_filter:
            args["repo_filter"] = repo_filter
        return await self.call_tool("analyze_ownership", args)

    async def semantic_grep(
        self,
        query: str,
        repo_filter: Optional[str] = None,
        n_results: int = 10,
    ) -> Dict[str, Any]:
        """Semantic search over indexed code chunks."""
        args: Dict[str, Any] = {"query": query, "n_results": n_results}
        if repo_filter:
            args["repo_filter"] = repo_filter
        return await self.call_tool("semantic_grep", args)
