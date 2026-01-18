"""
Pydantic schemas for OpenAPI Specification Analysis endpoints.

These schemas provide input validation for AI-powered analysis interpretation
requests, ensuring all required analysis data is present and properly formatted.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Risk level classification for analysis results."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class TaintVulnerability(BaseModel):
    """A single taint analysis vulnerability."""

    endpoint: str = Field(..., description="The affected API endpoint")
    severity: str = Field(..., description="Vulnerability severity (CRITICAL, WARNING)")
    source: Optional[str] = Field(default=None, description="Data source location")
    sink: Optional[str] = Field(default=None, description="Data sink location")
    tainted_path: Optional[str] = Field(
        default=None, description="Data flow path from source to sink"
    )


class TaintAnalysisRequest(BaseModel):
    """Request model for AI-powered taint analysis interpretation."""

    vulnerabilities: List[TaintVulnerability] = Field(
        default_factory=list,
        description="List of taint vulnerabilities from backend analyzer",
    )
    spec_text: Optional[str] = Field(
        default=None,
        description="OpenAPI specification for additional context",
    )


class AuthorizationMatrixRequest(BaseModel):
    """Request model for AI-powered authorization matrix interpretation."""

    scopes: List[str] = Field(
        default_factory=list,
        description="All OAuth2 scopes/roles defined in the API",
    )
    matrix: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Maps 'METHOD /path' to required scopes",
    )
    spec_text: Optional[str] = Field(
        default=None,
        description="OpenAPI specification for additional context",
    )


class SchemaCluster(BaseModel):
    """A cluster of similar schemas detected by the similarity analyzer."""

    schemas: List[str] = Field(..., description="Names of similar schemas")
    similarity_score: float = Field(
        ..., ge=0.0, le=1.0, description="How similar the schemas are"
    )
    shared_fields: Optional[List[str]] = Field(
        default=None, description="Fields common to all schemas in cluster"
    )


class SchemaSimilarityRequest(BaseModel):
    """Request model for AI-powered schema similarity interpretation."""

    clusters: List[SchemaCluster] = Field(
        default_factory=list,
        description="Schema clusters from similarity analyzer",
    )
    spec_text: Optional[str] = Field(
        default=None,
        description="OpenAPI specification for additional context",
    )


class ZombieApiRequest(BaseModel):
    """Request model for AI-powered zombie API detection interpretation."""

    shadowedEndpoints: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Endpoints unreachable due to routing conflicts",
    )
    orphanedOperations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Operations with no params/body/response defined",
    )
    spec_text: Optional[str] = Field(
        default=None,
        description="OpenAPI specification for additional context",
    )


class ComprehensiveAnalysisRequest(BaseModel):
    """Request model for comprehensive architectural analysis combining all analyzers."""

    taint_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from taint analyzer",
    )
    authz_matrix: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from authorization matrix analyzer",
    )
    schema_similarity: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from schema similarity analyzer",
    )
    zombie_apis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Results from zombie API detector",
    )
    spec_text: Optional[str] = Field(
        default=None,
        description="OpenAPI specification for additional context",
    )
