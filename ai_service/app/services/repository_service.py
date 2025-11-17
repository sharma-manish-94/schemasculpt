"""
Repository Service - High-level repository operations

This service manages repository provider lifecycle and provides business logic
for repository operations.
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta

from app.mcp.repository_provider import (
    RepositoryProvider,
    RepositoryInfo,
    FileInfo,
    FileContent,
    BranchInfo,
)
from app.mcp.github_provider import GitHubProvider
from app.mcp.client import MCPConnectionError, MCPOperationError

logger = logging.getLogger(__name__)


class RepositoryServiceError(Exception):
    """Base exception for repository service errors"""
    pass


class RepositoryService:
    """
    Service for managing repository operations.

    This service handles:
    - Provider lifecycle management
    - Connection pooling (simple session-based)
    - Caching (optional)
    - Business logic for repository operations
    """

    # Provider registry
    PROVIDERS = {
        "github": GitHubProvider,
        # Add more providers here
        # "gitlab": GitLabProvider,
    }

    def __init__(self):
        """Initialize repository service."""
        self._sessions: Dict[str, Dict] = {}  # session_id -> provider info
        self._cache_ttl = 300  # 5 minutes default cache

    async def connect(
        self,
        session_id: str,
        provider_name: str,
        access_token: str
    ) -> Dict:
        """
        Connect to a repository provider.

        Args:
            session_id: Unique session identifier
            provider_name: Provider name (github, gitlab)
            access_token: OAuth access token

        Returns:
            Connection info

        Raises:
            RepositoryServiceError: If connection fails
        """
        try:
            # Validate provider
            if provider_name not in self.PROVIDERS:
                raise RepositoryServiceError(
                    f"Unknown provider: {provider_name}. "
                    f"Available: {', '.join(self.PROVIDERS.keys())}"
                )

            # Disconnect existing session if any
            await self.disconnect(session_id)

            # Create provider instance
            provider_class = self.PROVIDERS[provider_name]
            provider: RepositoryProvider = provider_class(access_token)

            # Connect to provider
            await provider.connect()

            # Store session info
            self._sessions[session_id] = {
                "provider": provider,
                "provider_name": provider_name,
                "connected_at": datetime.now(),
                "access_token": access_token,  # Store for reconnection if needed
            }

            logger.info(f"Session {session_id} connected to {provider_name}")

            return {
                "success": True,
                "provider": provider_name,
                "connected_at": datetime.now().isoformat()
            }

        except MCPConnectionError as e:
            logger.error(f"Failed to connect session {session_id}: {e}")
            raise RepositoryServiceError(f"Connection failed: {e}") from e

    async def disconnect(self, session_id: str) -> None:
        """
        Disconnect a session from its provider.

        Args:
            session_id: Session identifier
        """
        if session_id in self._sessions:
            session_info = self._sessions[session_id]
            provider = session_info.get("provider")

            if provider:
                try:
                    await provider.disconnect()
                except Exception as e:
                    logger.error(f"Error disconnecting session {session_id}: {e}")

            del self._sessions[session_id]
            logger.info(f"Session {session_id} disconnected")

    def _get_provider(self, session_id: str) -> RepositoryProvider:
        """
        Get provider for a session.

        Args:
            session_id: Session identifier

        Returns:
            Repository provider

        Raises:
            RepositoryServiceError: If session not found
        """
        if session_id not in self._sessions:
            raise RepositoryServiceError(
                f"Session {session_id} not connected. Please connect first."
            )

        session_info = self._sessions[session_id]
        provider = session_info.get("provider")

        if not provider or not provider.is_connected():
            raise RepositoryServiceError(
                f"Session {session_id} is not connected. Please reconnect."
            )

        return provider

    async def list_repositories(
        self,
        session_id: str,
        username: Optional[str] = None
    ) -> List[RepositoryInfo]:
        """
        List repositories accessible to the session.

        Args:
            session_id: Session identifier
            username: Optional username to filter

        Returns:
            List of repositories
        """
        try:
            provider = self._get_provider(session_id)
            repos = await provider.list_repositories(username)
            logger.info(f"Listed {len(repos)} repositories for session {session_id}")
            return repos

        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            raise RepositoryServiceError(f"Failed to list repositories: {e}") from e

    async def get_repository(
        self,
        session_id: str,
        owner: str,
        repo: str
    ) -> RepositoryInfo:
        """
        Get information about a specific repository.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information
        """
        try:
            provider = self._get_provider(session_id)
            repo_info = await provider.get_repository(owner, repo)
            return repo_info

        except Exception as e:
            logger.error(f"Error getting repository {owner}/{repo}: {e}")
            raise RepositoryServiceError(f"Failed to get repository: {e}") from e

    async def list_branches(
        self,
        session_id: str,
        owner: str,
        repo: str
    ) -> List[BranchInfo]:
        """
        List branches in a repository.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name

        Returns:
            List of branches
        """
        try:
            provider = self._get_provider(session_id)
            branches = await provider.list_branches(owner, repo)
            logger.info(f"Listed {len(branches)} branches for {owner}/{repo}")
            return branches

        except Exception as e:
            logger.error(f"Error listing branches: {e}")
            raise RepositoryServiceError(f"Failed to list branches: {e}") from e

    async def browse_tree(
        self,
        session_id: str,
        owner: str,
        repo: str,
        path: str = "",
        branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Browse repository tree.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name
            path: Path in repository
            branch: Branch name

        Returns:
            List of files and directories
        """
        try:
            provider = self._get_provider(session_id)
            files = await provider.browse_tree(owner, repo, path, branch)

            # Enhance with OpenAPI detection
            for file in files:
                if file.type == "file":
                    file_lower = file.name.lower()
                    # Check if it's likely an OpenAPI spec
                    is_yaml_json = file_lower.endswith(('.yaml', '.yml', '.json'))
                    has_api_keyword = any(kw in file_lower for kw in ['openapi', 'swagger', 'api', 'spec'])
                    # Add custom attribute (will need to be in FileInfo or handle separately)
                    setattr(file, 'is_openapi_spec', is_yaml_json and has_api_keyword)

            logger.info(f"Browsed tree {owner}/{repo}/{path}: {len(files)} items")
            return files

        except Exception as e:
            logger.error(f"Error browsing tree: {e}")
            raise RepositoryServiceError(f"Failed to browse tree: {e}") from e

    async def read_file(
        self,
        session_id: str,
        owner: str,
        repo: str,
        path: str,
        ref: Optional[str] = None
    ) -> FileContent:
        """
        Read file content from repository.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference

        Returns:
            File content
        """
        try:
            provider = self._get_provider(session_id)
            content = await provider.read_file(owner, repo, path, ref)
            logger.info(f"Read file {owner}/{repo}/{path} ({content.size} bytes)")
            return content

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise RepositoryServiceError(f"Failed to read file: {e}") from e

    async def search_files(
        self,
        session_id: str,
        owner: str,
        repo: str,
        pattern: str,
        branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Search for files matching a pattern.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name
            pattern: File pattern
            branch: Branch name

        Returns:
            List of matching files
        """
        try:
            provider = self._get_provider(session_id)
            files = await provider.search_files(owner, repo, pattern, branch)
            logger.info(f"Found {len(files)} files matching '{pattern}' in {owner}/{repo}")
            return files

        except Exception as e:
            logger.error(f"Error searching files: {e}")
            # Don't raise for search - return empty list
            return []

    async def find_openapi_specs(
        self,
        session_id: str,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Find OpenAPI specification files in a repository.

        Args:
            session_id: Session identifier
            owner: Repository owner
            repo: Repository name
            branch: Branch name

        Returns:
            List of OpenAPI spec files
        """
        try:
            provider = self._get_provider(session_id)
            specs = await provider.find_openapi_specs(owner, repo, branch)
            logger.info(f"Found {len(specs)} OpenAPI specs in {owner}/{repo}")
            return specs

        except Exception as e:
            logger.error(f"Error finding OpenAPI specs: {e}")
            raise RepositoryServiceError(f"Failed to find OpenAPI specs: {e}") from e

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get information about a session.

        Args:
            session_id: Session identifier

        Returns:
            Session information or None if not found
        """
        if session_id not in self._sessions:
            return None

        session_info = self._sessions[session_id]
        return {
            "provider": session_info["provider_name"],
            "connected_at": session_info["connected_at"].isoformat(),
            "connected": session_info["provider"].is_connected(),
        }

    async def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old inactive sessions.

        Args:
            max_age_hours: Maximum session age in hours

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        sessions_to_remove = []

        for session_id, session_info in self._sessions.items():
            connected_at = session_info.get("connected_at")
            if connected_at and connected_at < cutoff_time:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            await self.disconnect(session_id)

        logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions")
        return len(sessions_to_remove)
