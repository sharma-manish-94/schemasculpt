"""
Repository Schemas - Pydantic models for repository operations

These schemas define the request/response models for repository endpoints.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RepositoryConnectionRequest(BaseModel):
    """Request to connect to a repository provider."""
    model_config = ConfigDict(populate_by_name=True)  # Accept both access_token and accessToken

    provider: str = Field(..., description="Repository provider (github, gitlab)")
    access_token: str = Field(..., description="OAuth access token", alias="accessToken")


class RepositoryConnectionResponse(BaseModel):
    """Response after connecting to a repository provider."""
    success: bool
    message: str
    provider: str


class RepositoryInfoResponse(BaseModel):
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


class RepositoryListRequest(BaseModel):
    """Request to list repositories."""
    username: Optional[str] = Field(None, description="Optional username to filter repositories")


class RepositoryListResponse(BaseModel):
    """Response with list of repositories."""
    repositories: List[RepositoryInfoResponse]
    count: int


class BranchInfoResponse(BaseModel):
    """Information about a branch."""
    name: str
    commit_sha: str
    protected: bool


class BranchListResponse(BaseModel):
    """Response with list of branches."""
    branches: List[BranchInfoResponse]
    count: int


class FileInfoResponse(BaseModel):
    """Information about a file or directory."""
    path: str
    name: str
    type: str = Field(..., description="Type: file or dir")
    size: Optional[int] = None
    sha: Optional[str] = None
    url: Optional[str] = None
    is_openapi_spec: bool = Field(default=False, description="Whether this file is likely an OpenAPI spec")


class BrowseTreeRequest(BaseModel):
    """Request to browse repository tree."""
    owner: str
    repo: str
    path: str = Field(default="", description="Path in repository (empty for root)")
    branch: Optional[str] = Field(None, description="Branch name (default: default branch)")


class BrowseTreeResponse(BaseModel):
    """Response with repository tree contents."""
    files: List[FileInfoResponse]
    path: str
    branch: Optional[str]


class ReadFileRequest(BaseModel):
    """Request to read a file from repository."""
    owner: str
    repo: str
    path: str
    ref: Optional[str] = Field(None, description="Git reference (branch, tag, commit)")


class ReadFileResponse(BaseModel):
    """Response with file content."""
    path: str
    content: str
    encoding: str
    size: int
    sha: str
    url: Optional[str] = None


class SearchFilesRequest(BaseModel):
    """Request to search for files."""
    owner: str
    repo: str
    pattern: str = Field(..., description="File pattern (e.g., *.yaml, *.json)")
    branch: Optional[str] = Field(None, description="Branch name")


class SearchFilesResponse(BaseModel):
    """Response with search results."""
    files: List[FileInfoResponse]
    count: int
    pattern: str


class FindOpenAPISpecsRequest(BaseModel):
    """Request to find OpenAPI specs in a repository."""
    owner: str
    repo: str
    branch: Optional[str] = Field(None, description="Branch name")


class FindOpenAPISpecsResponse(BaseModel):
    """Response with OpenAPI spec files."""
    specs: List[FileInfoResponse]
    count: int


class RepositoryHealthResponse(BaseModel):
    """Health check response for repository service."""
    status: str
    mcp_available: bool
    connected: bool
    provider: Optional[str] = None
