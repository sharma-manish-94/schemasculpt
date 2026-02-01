"""
Repository Provider - Abstract interface for repository operations

This module defines the interface that all repository providers (GitHub, GitLab, etc.)
must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class RepositoryInfo:
    """Information about a repository."""

    owner: str
    name: str
    full_name: str
    description: Optional[str]
    url: str
    default_branch: str
    private: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class FileInfo:
    """Information about a file in a repository."""

    path: str
    name: str
    type: str  # "file" or "dir"
    size: Optional[int]
    sha: Optional[str]
    url: Optional[str]


@dataclass
class FileContent:
    """Content of a file from a repository."""

    path: str
    content: str
    encoding: str
    size: int
    sha: str
    url: Optional[str]


@dataclass
class BranchInfo:
    """Information about a branch."""

    name: str
    commit_sha: str
    protected: bool


class RepositoryProvider(ABC):
    """
    Abstract base class for repository providers.

    All repository providers (GitHub, GitLab, etc.) must implement this interface.
    """

    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize the repository provider.

        Args:
            access_token: OAuth access token for authentication
        """
        self.access_token = access_token
        self._client = None

    @abstractmethod
    async def connect(self) -> None:
        """
        Connect to the repository provider.

        Raises:
            MCPConnectionError: If connection fails
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the repository provider."""

    @abstractmethod
    async def list_repositories(
        self, username: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """
        List repositories accessible to the authenticated user.

        Args:
            username: Optional username to filter repositories (default: authenticated user)

        Returns:
            List of repository information

        Raises:
            MCPOperationError: If listing fails
        """

    @abstractmethod
    async def get_repository(self, owner: str, repo: str) -> RepositoryInfo:
        """
        Get information about a specific repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information

        Raises:
            MCPOperationError: If repository not found or access denied
        """

    @abstractmethod
    async def list_branches(self, owner: str, repo: str) -> List[BranchInfo]:
        """
        List branches in a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            List of branch information

        Raises:
            MCPOperationError: If listing fails
        """

    @abstractmethod
    async def browse_tree(
        self, owner: str, repo: str, path: str = "", branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Browse repository tree at a specific path.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Path in the repository (empty for root)
            branch: Branch name (default: default branch)

        Returns:
            List of files and directories

        Raises:
            MCPOperationError: If browsing fails
        """

    @abstractmethod
    async def read_file(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> FileContent:
        """
        Read file content from repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content

        Raises:
            MCPOperationError: If file not found or read fails
        """

    @abstractmethod
    async def search_files(
        self, owner: str, repo: str, pattern: str, branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Search for files matching a pattern.

        Args:
            owner: Repository owner
            repo: Repository name
            pattern: File name pattern (e.g., "*.yaml", "*.json")
            branch: Branch name (default: default branch)

        Returns:
            List of matching files

        Raises:
            MCPOperationError: If search fails
        """

    async def find_openapi_specs(
        self, owner: str, repo: str, branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Find OpenAPI specification files in a repository.

        This is a convenience method that searches for common OpenAPI file patterns.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (default: default branch)

        Returns:
            List of OpenAPI spec files
        """
        # Common OpenAPI file patterns
        patterns = ["*.yaml", "*.yml", "*.json"]
        common_names = ["openapi", "swagger", "api", "spec"]

        all_files: List[FileInfo] = []

        # Search for files matching patterns
        for pattern in patterns:
            try:
                files = await self.search_files(owner, repo, pattern, branch)
                all_files.extend(files)
            except Exception:
                continue

        # Filter for likely OpenAPI specs
        openapi_files = []
        for file in all_files:
            file_lower = file.name.lower()
            # Check if filename contains common OpenAPI keywords
            if any(name in file_lower for name in common_names):
                openapi_files.append(file)
            # Or if it's in common directories
            elif any(
                dir in file.path.lower()
                for dir in ["api", "spec", "docs", "openapi", "swagger"]
            ):
                openapi_files.append(file)

        return openapi_files

    def is_connected(self) -> bool:
        """Check if provider is connected."""
        return self._client is not None and self._client.is_connected()
