"""
Repository API Endpoints

FastAPI endpoints for repository operations via MCP.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status

from app.schemas.repository import (
    RepositoryConnectionRequest,
    RepositoryConnectionResponse,
    RepositoryListRequest,
    RepositoryListResponse,
    RepositoryInfoResponse,
    BranchListResponse,
    BranchInfoResponse,
    BrowseTreeRequest,
    BrowseTreeResponse,
    FileInfoResponse,
    ReadFileRequest,
    ReadFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
    FindOpenAPISpecsRequest,
    FindOpenAPISpecsResponse,
    RepositoryHealthResponse,
)
from app.services.repository_service import RepositoryService, RepositoryServiceError
from app.mcp.client import MCP_AVAILABLE

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/repository", tags=["repository"])

# Service instance (singleton pattern - could be injected via dependency)
repository_service = RepositoryService()


def get_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Extract session ID from header."""
    if not x_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Session-ID header is required"
        )
    return x_session_id


@router.get("/health", response_model=RepositoryHealthResponse)
async def health_check(x_session_id: Optional[str] = Header(None)):
    """
    Health check for repository service.

    Returns MCP availability and connection status.
    """
    session_info = None
    if x_session_id:
        session_info = repository_service.get_session_info(x_session_id)

    return RepositoryHealthResponse(
        status="healthy" if MCP_AVAILABLE else "degraded",
        mcp_available=MCP_AVAILABLE,
        connected=session_info is not None if session_info else False,
        provider=session_info.get("provider") if session_info else None
    )


@router.post("/connect", response_model=RepositoryConnectionResponse)
async def connect_repository(
    request: RepositoryConnectionRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Connect to a repository provider (GitHub, GitLab, etc.).

    Requires:
    - X-Session-ID header: Unique session identifier
    - provider: Repository provider name
    - access_token: OAuth access token

    Returns connection status and provider info.
    """
    if not MCP_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MCP SDK is not available. Repository features are disabled."
        )

    try:
        result = await repository_service.connect(
            session_id=session_id,
            provider_name=request.provider,
            access_token=request.access_token
        )

        return RepositoryConnectionResponse(
            success=True,
            message=f"Successfully connected to {request.provider}",
            provider=request.provider
        )

    except RepositoryServiceError as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error during connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during connection"
        )


@router.post("/disconnect")
async def disconnect_repository(session_id: str = Header(..., alias="X-Session-ID")):
    """
    Disconnect from repository provider.

    Requires X-Session-ID header.
    """
    try:
        await repository_service.disconnect(session_id)
        return {"success": True, "message": "Disconnected successfully"}

    except Exception as e:
        logger.error(f"Error during disconnect: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during disconnect"
        )


@router.post("/list", response_model=RepositoryListResponse)
async def list_repositories(
    request: RepositoryListRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    List repositories accessible to the authenticated user.

    Requires X-Session-ID header.
    Optional: username to filter repositories.
    """
    try:
        repos = await repository_service.list_repositories(
            session_id=session_id,
            username=request.username
        )

        return RepositoryListResponse(
            repositories=[
                RepositoryInfoResponse(
                    owner=repo.owner,
                    name=repo.name,
                    full_name=repo.full_name,
                    description=repo.description,
                    url=repo.url,
                    default_branch=repo.default_branch,
                    private=repo.private,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at
                )
                for repo in repos
            ],
            count=len(repos)
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing repositories"
        )


@router.get("/{owner}/{repo}/branches", response_model=BranchListResponse)
async def list_branches(
    owner: str,
    repo: str,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    List branches in a repository.

    Requires X-Session-ID header.
    """
    try:
        branches = await repository_service.list_branches(
            session_id=session_id,
            owner=owner,
            repo=repo
        )

        return BranchListResponse(
            branches=[
                BranchInfoResponse(
                    name=branch.name,
                    commit_sha=branch.commit_sha,
                    protected=branch.protected
                )
                for branch in branches
            ],
            count=len(branches)
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing branches: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing branches"
        )


@router.post("/browse", response_model=BrowseTreeResponse)
async def browse_tree(
    request: BrowseTreeRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Browse repository tree at a specific path.

    Requires X-Session-ID header.
    Returns files and directories at the specified path.
    """
    try:
        files = await repository_service.browse_tree(
            session_id=session_id,
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            branch=request.branch
        )

        return BrowseTreeResponse(
            files=[
                FileInfoResponse(
                    path=file.path,
                    name=file.name,
                    type=file.type,
                    size=file.size,
                    sha=file.sha,
                    url=file.url,
                    is_openapi_spec=getattr(file, 'is_openapi_spec', False)
                )
                for file in files
            ],
            path=request.path,
            branch=request.branch
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error browsing tree: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error browsing repository tree"
        )


@router.post("/file", response_model=ReadFileResponse)
async def read_file(
    request: ReadFileRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Read file content from repository.

    Requires X-Session-ID header.
    Returns file content and metadata.
    """
    try:
        content = await repository_service.read_file(
            session_id=session_id,
            owner=request.owner,
            repo=request.repo,
            path=request.path,
            ref=request.ref
        )

        return ReadFileResponse(
            path=content.path,
            content=content.content,
            encoding=content.encoding,
            size=content.size,
            sha=content.sha,
            url=content.url
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading file"
        )


@router.post("/search", response_model=SearchFilesResponse)
async def search_files(
    request: SearchFilesRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Search for files matching a pattern.

    Requires X-Session-ID header.
    Returns list of matching files.
    """
    try:
        files = await repository_service.search_files(
            session_id=session_id,
            owner=request.owner,
            repo=request.repo,
            pattern=request.pattern,
            branch=request.branch
        )

        return SearchFilesResponse(
            files=[
                FileInfoResponse(
                    path=file.path,
                    name=file.name,
                    type=file.type,
                    size=file.size,
                    sha=file.sha,
                    url=file.url
                )
                for file in files
            ],
            count=len(files),
            pattern=request.pattern
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching files"
        )


@router.post("/find-specs", response_model=FindOpenAPISpecsResponse)
async def find_openapi_specs(
    request: FindOpenAPISpecsRequest,
    session_id: str = Header(..., alias="X-Session-ID")
):
    """
    Find OpenAPI specification files in a repository.

    Requires X-Session-ID header.
    Returns list of OpenAPI spec files.
    """
    try:
        specs = await repository_service.find_openapi_specs(
            session_id=session_id,
            owner=request.owner,
            repo=request.repo,
            branch=request.branch
        )

        return FindOpenAPISpecsResponse(
            specs=[
                FileInfoResponse(
                    path=spec.path,
                    name=spec.name,
                    type=spec.type,
                    size=spec.size,
                    sha=spec.sha,
                    url=spec.url,
                    is_openapi_spec=True
                )
                for spec in specs
            ],
            count=len(specs)
        )

    except RepositoryServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error finding OpenAPI specs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error finding OpenAPI specifications"
        )
