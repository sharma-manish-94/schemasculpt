"""
MCP Client - Base client for communicating with MCP servers

This module provides a wrapper around the MCP SDK for managing connections
to various MCP servers (GitHub, GitLab, etc.)
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logging.warning("MCP SDK not installed. Repository features will be disabled.")

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Base exception for MCP client errors"""

    pass


class MCPConnectionError(MCPClientError):
    """Error connecting to MCP server"""

    pass


class MCPOperationError(MCPClientError):
    """Error performing MCP operation"""

    pass


class MCPClient:
    """
    Base MCP Client for managing connections to MCP servers.

    This client handles:
    - Server lifecycle management
    - Connection pooling
    - Error handling and retries
    - Tool invocation
    """

    def __init__(self, server_params: Optional[Dict[str, Any]] = None):
        """
        Initialize MCP client.

        Args:
            server_params: Server configuration parameters
        """
        if not MCP_AVAILABLE:
            raise MCPClientError(
                "MCP SDK is not installed. Install with: pip install mcp"
            )

        self.server_params = server_params or {}
        self.session: Optional[ClientSession] = None
        self._read_stream = None
        self._write_stream = None
        self._connected = False

    async def connect(
        self, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Connect to an MCP server.

        Args:
            command: Command to run the MCP server (e.g., "npx")
            args: Arguments for the command (e.g., ["-y", "@modelcontextprotocol/server-github"])
            env: Environment variables to pass to the server

        Raises:
            MCPConnectionError: If connection fails
        """
        try:
            logger.info(f"Connecting to MCP server: {command} {' '.join(args)}")

            server_params = StdioServerParameters(
                command=command, args=args, env=env or {}
            )

            # Create stdio client context
            self._stdio_context = stdio_client(server_params)
            self._read_stream, self._write_stream = (
                await self._stdio_context.__aenter__()
            )

            # Create session context
            self._session_context = ClientSession(self._read_stream, self._write_stream)
            self.session = await self._session_context.__aenter__()

            # Initialize the session
            await self.session.initialize()

            self._connected = True
            logger.info("Successfully connected to MCP server")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPConnectionError(f"Failed to connect to MCP server: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        try:
            if self._session_context:
                await self._session_context.__aexit__(None, None, None)
            if self._stdio_context:
                await self._stdio_context.__aexit__(None, None, None)

            self.session = None
            self._read_stream = None
            self._write_stream = None
            self._connected = False
            logger.info("Disconnected from MCP server")

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if client is connected to a server."""
        return self._connected and self.session is not None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            MCPOperationError: If tool call fails
        """
        if not self.is_connected():
            raise MCPOperationError("Not connected to MCP server")

        try:
            logger.debug(f"Calling tool: {tool_name} with args: {arguments}")
            result = await self.session.call_tool(tool_name, arguments)
            logger.debug(f"Tool result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            raise MCPOperationError(f"Error calling tool {tool_name}: {e}") from e

    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List available tools on the MCP server.

        Returns:
            List of available tools

        Raises:
            MCPOperationError: If listing fails
        """
        if not self.is_connected():
            raise MCPOperationError("Not connected to MCP server")

        try:
            result = await self.session.list_tools()
            return result.tools if hasattr(result, "tools") else []

        except Exception as e:
            logger.error(f"Error listing tools: {e}")
            raise MCPOperationError(f"Error listing tools: {e}") from e

    async def read_resource(self, uri: str) -> Any:
        """
        Read a resource from the MCP server.

        Args:
            uri: Resource URI

        Returns:
            Resource content

        Raises:
            MCPOperationError: If reading fails
        """
        if not self.is_connected():
            raise MCPOperationError("Not connected to MCP server")

        try:
            logger.debug(f"Reading resource: {uri}")
            result = await self.session.read_resource(uri)
            return result

        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise MCPOperationError(f"Error reading resource {uri}: {e}") from e

    @asynccontextmanager
    async def connection(
        self, command: str, args: List[str], env: Optional[Dict[str, str]] = None
    ):
        """
        Context manager for MCP connection.

        Usage:
            async with client.connection("npx", ["-y", "@modelcontextprotocol/server-github"]):
                result = await client.call_tool("list_repos", {})
        """
        try:
            await self.connect(command, args, env)
            yield self
        finally:
            await self.disconnect()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
