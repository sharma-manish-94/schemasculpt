"""
Enhanced Finding Schema with Pre-Computed Graph Metadata

This schema enriches basic security findings with pre-computed dependency graph
data from the Java backend, eliminating the need for the AI to re-discover relationships.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FindingCategory(str, Enum):
    """Category of security finding"""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_EXPOSURE = "data_exposure"
    INJECTION = "injection"
    MASS_ASSIGNMENT = "mass_assignment"
    RATE_LIMITING = "rate_limiting"
    ENCRYPTION = "encryption"


class DependencyType(str, Enum):
    """Type of dependency relationship"""

    SCHEMA_REFERENCE = "schema_reference"
    ENDPOINT_REFERENCE = "endpoint_reference"
    PARAMETER_REFERENCE = "parameter_reference"


class GraphDependency(BaseModel):
    """
    Pre-computed dependency from Java dependency graph.
    This is THE KEY - we send the graph to AI, not the spec!
    """

    dependency_type: DependencyType
    target: str = Field(
        ..., description="What this depends on (e.g., schema name, endpoint)"
    )
    path: List[str] = Field(
        default_factory=list, description="Dependency path [A -> B -> C]"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnrichedFinding(BaseModel):
    """
    Security finding enriched with pre-computed graph metadata.

    This is the HYBRID MODEL in action:
    - Java backend computes facts (dependencies, reachability)
    - AI receives pre-processed data, not raw spec
    - Result: AI can focus on reasoning, not parsing
    """

    # Basic finding data
    finding_id: str
    category: FindingCategory
    severity: str
    title: str
    description: str

    # Location data
    affected_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    affected_schema: Optional[str] = None
    affected_field: Optional[str] = None

    # PRE-COMPUTED GRAPH DATA (from Java AnalysisService)
    # This is what makes it fast and accurate!
    dependencies: List[GraphDependency] = Field(
        default_factory=list,
        description="Pre-computed dependencies from Java dependency graph",
    )

    dependent_endpoints: List[str] = Field(
        default_factory=list,
        description="Endpoints that depend on this resource (from graph)",
    )

    schema_fields: List[str] = Field(
        default_factory=list,
        description="If schema-related, the actual field names (from graph)",
    )

    is_public: bool = Field(
        default=False,
        description="Whether endpoint is publicly accessible (from Java SecurityLinter)",
    )

    authentication_required: bool = Field(
        default=True,
        description="Whether authentication is required (from Java linter)",
    )

    # Chainability hints (pre-computed by Java)
    chainable_with: List[str] = Field(
        default_factory=list,
        description="Finding IDs that could potentially chain with this one",
    )

    # Raw context (only if needed)
    raw_context: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional context, minimal"
    )


class EnrichedFindingSet(BaseModel):
    """
    Complete set of enriched findings for AI analysis.

    This is what we send to the AI instead of a 5MB spec!
    """

    findings: List[EnrichedFinding]

    # High-level summary stats (pre-computed)
    total_public_endpoints: int = 0
    total_authenticated_endpoints: int = 0
    total_schemas: int = 0

    # Graph metadata
    graph_version: str = Field(description="Hash of the dependency graph (for caching)")

    spec_hash: str = Field(description="Hash of the original spec")

    # Optimization: Pre-identified high-risk patterns
    potential_chains_hint: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Pre-identified potential chains (Java heuristics)",
    )
