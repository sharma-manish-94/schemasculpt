"""
GitHub Provider - MCP-based GitHub repository access

This module provides GitHub repository operations using the MCP GitHub server.
"""

import logging
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime

from .client import MCPClient, MCPConnectionError, MCPOperationError
from .repository_provider import (
    RepositoryProvider,
    RepositoryInfo,
    FileInfo,
    FileContent,
    BranchInfo,
)

logger = logging.getLogger(__name__)


class GitHubProvider(RepositoryProvider):
    """
    GitHub repository provider using MCP.

    This provider uses the @modelcontextprotocol/server-github MCP server
    to interact with GitHub repositories.
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize GitHub provider.

        Args:
            access_token: GitHub personal access token
        """
        super().__init__(access_token)
        self._client = MCPClient()

    async def connect(self) -> None:
        """Connect to GitHub MCP server."""
        try:
            env = {}
            if self.access_token:
                env["GITHUB_PERSONAL_ACCESS_TOKEN"] = self.access_token

            await self._client.connect(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env=env
            )

            logger.info("Connected to GitHub MCP server")

        except Exception as e:
            logger.error(f"Failed to connect to GitHub: {e}")
            raise MCPConnectionError(f"Failed to connect to GitHub: {e}") from e

    async def disconnect(self) -> None:
        """Disconnect from GitHub MCP server."""
        if self._client:
            await self._client.disconnect()

    async def list_repositories(self, username: Optional[str] = None) -> List[RepositoryInfo]:
        """
        List GitHub repositories.

        Args:
            username: GitHub username (default: authenticated user)

        Returns:
            List of repositories
        """
        try:
            # Note: The actual tool name may vary based on MCP server implementation
            # This is a placeholder - we'll need to check actual GitHub MCP server tools
            result = await self._client.call_tool(
                "list_repositories",
                {"username": username} if username else {}
            )

            repos = []
            # Parse result based on actual MCP server response format
            repo_data = result.content[0].text if hasattr(result, 'content') else result

            # This parsing will need adjustment based on actual response format
            if isinstance(repo_data, list):
                for repo in repo_data:
                    repos.append(self._parse_repository_info(repo))

            return repos

        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            raise MCPOperationError(f"Error listing repositories: {e}") from e

    async def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """
        Get information about a specific repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information
        """
        try:
            result = await self._client.call_tool(
                "get_repository",
                {
                    "owner": owner,
                    "repo": repo
                }
            )

            repo_data = result.content[0].text if hasattr(result, 'content') else result
            return self._parse_repository_info(repo_data)

        except Exception as e:
            logger.error(f"Error getting repository {owner}/{repo}: {e}")
            raise MCPOperationError(f"Error getting repository: {e}") from e

    async def list_branches(self, owner: str, repo: str) -> List[BranchInfo]:
        """
        List branches in a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of branches
        """
        try:
            result = await self._client.call_tool(
                "list_branches",
                {
                    "owner": owner,
                    "repo": repo
                }
            )

            branches = []
            branch_data = result.content[0].text if hasattr(result, 'content') else result

            if isinstance(branch_data, list):
                for branch in branch_data:
                    branches.append(self._parse_branch_info(branch))

            return branches

        except Exception as e:
            logger.error(f"Error listing branches for {owner}/{repo}: {e}")
            raise MCPOperationError(f"Error listing branches: {e}") from e

    async def browse_tree(
        self,
        owner: str,
        repo: str,
        path: str = "",
        branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Browse repository tree.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path in repository
            branch: Branch name

        Returns:
            List of files and directories
        """
        try:
            args = {
                "owner": owner,
                "repo": repo,
                "path": path
            }
            if branch:
                args["ref"] = branch

            result = await self._client.call_tool("get_file_contents", args)

            files = []
            file_data = result.content[0].text if hasattr(result, 'content') else result

            if isinstance(file_data, list):
                for item in file_data:
                    files.append(self._parse_file_info(item))

            return files

        except Exception as e:
            logger.error(f"Error browsing tree {owner}/{repo}/{path}: {e}")
            raise MCPOperationError(f"Error browsing tree: {e}") from e

    async def read_file(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> FileContent:
        """
        Read file content from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference

        Returns:
            File content
        """
        try:
            args = {
                "owner": owner,
                "repo": repo,
                "path": path
            }
            if ref:
                args["ref"] = ref

            result = await self._client.call_tool("get_file_contents", args)

            # Parse result
            content_data = result.content[0].text if hasattr(result, 'content') else result
            return self._parse_file_content(content_data, path)

        except Exception as e:
            logger.error(f"Error reading file {owner}/{repo}/{path}: {e}")
            raise MCPOperationError(f"Error reading file: {e}") from e

    async def search_files(
        self,
        owner: str,
        repo: str,
        pattern: str,
        branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Search for files matching a pattern.

        Args:
            owner: Repository owner
            repo: Repository name
            pattern: File pattern
            branch: Branch name

        Returns:
            List of matching files
        """
        try:
            args = {
                "owner": owner,
                "repo": repo,
                "pattern": pattern
            }
            if branch:
                args["ref"] = branch

            result = await self._client.call_tool("search_files", args)

            files = []
            file_data = result.content[0].text if hasattr(result, 'content') else result

            if isinstance(file_data, list):
                for item in file_data:
                    files.append(self._parse_file_info(item))

            return files

        except Exception as e:
            logger.error(f"Error searching files in {owner}/{repo}: {e}")
            # Return empty list instead of raising error for search failures
            return []

    # Helper methods for parsing MCP responses

    def _parse_repository_info(self, data: Any) -> RepositoryInfo:
        """Parse repository info from MCP response."""
        if isinstance(data, dict):
            return RepositoryInfo(
                owner=data.get("owner", {}).get("login", "") if isinstance(data.get("owner"), dict) else data.get("owner", ""),
                name=data.get("name", ""),
                full_name=data.get("full_name", ""),
                description=data.get("description"),
                url=data.get("html_url", ""),
                default_branch=data.get("default_branch", "main"),
                private=data.get("private", False),
                created_at=self._parse_datetime(data.get("created_at")),
                updated_at=self._parse_datetime(data.get("updated_at")),
            )
        else:
            # Handle string response - create minimal info
            return RepositoryInfo(
                owner="",
                name=str(data),
                full_name=str(data),
                description=None,
                url="",
                default_branch="main",
                private=False
            )

    def _parse_file_info(self, data: Any) -> FileInfo:
        """Parse file info from MCP response."""
        if isinstance(data, dict):
            return FileInfo(
                path=data.get("path", ""),
                name=data.get("name", ""),
                type=data.get("type", "file"),
                size=data.get("size"),
                sha=data.get("sha"),
                url=data.get("url"),
            )
        else:
            return FileInfo(
                path=str(data),
                name=str(data).split("/")[-1],
                type="file",
                size=None,
                sha=None,
                url=None
            )

    def _parse_file_content(self, data: Any, path: str) -> FileContent:
        """Parse file content from MCP response."""
        if isinstance(data, dict):
            content = data.get("content", "")
            encoding = data.get("encoding", "utf-8")

            # Decode base64 if needed
            if encoding == "base64":
                try:
                    content = base64.b64decode(content).decode("utf-8")
                    encoding = "utf-8"
                except Exception:
                    pass

            return FileContent(
                path=path,
                content=content,
                encoding=encoding,
                size=data.get("size", len(content)),
                sha=data.get("sha", ""),
                url=data.get("url")
            )
        else:
            # Assume string response is the content
            content = str(data)
            return FileContent(
                path=path,
                content=content,
                encoding="utf-8",
                size=len(content),
                sha="",
                url=None
            )

    def _parse_branch_info(self, data: Any) -> BranchInfo:
        """Parse branch info from MCP response."""
        if isinstance(data, dict):
            return BranchInfo(
                name=data.get("name", ""),
                commit_sha=data.get("commit", {}).get("sha", "") if isinstance(data.get("commit"), dict) else "",
                protected=data.get("protected", False)
            )
        else:
            return BranchInfo(
                name=str(data),
                commit_sha="",
                protected=False
            )

    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string."""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            return None
