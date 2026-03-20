"""
MCP (Model Context Protocol) Integration Module

This module provides integration with MCP servers for repository access.
"""

from .client import MCPClient
from .github_provider import GitHubProvider
from .repository_provider import RepositoryProvider

__all__ = [
    "MCPClient",
    "RepositoryProvider",
    "GitHubProvider",
]
