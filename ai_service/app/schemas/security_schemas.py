"""
Security analysis schemas for multi-agent security workflow.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SecuritySeverity(str, Enum):
    """Security issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class OWASPCategory(str, Enum):
    """OWASP API Security Top 10 categories."""

    BROKEN_OBJECT_LEVEL_AUTH = "API1:2023 Broken Object Level Authorization"
    BROKEN_AUTHENTICATION = "API2:2023 Broken Authentication"
    BROKEN_OBJECT_PROPERTY_AUTH = "API3:2023 Broken Object Property Level Authorization"
    UNRESTRICTED_RESOURCE = "API4:2023 Unrestricted Resource Consumption"
    BROKEN_FUNCTION_AUTH = "API5:2023 Broken Function Level Authorization"
    UNRESTRICTED_SENSITIVE_DATA = (
        "API6:2023 Unrestricted Access to Sensitive Business Flows"
    )
    SERVER_SIDE_REQUEST_FORGERY = "API7:2023 Server Side Request Forgery"
    SECURITY_MISCONFIGURATION = "API8:2023 Security Misconfiguration"
    IMPROPER_INVENTORY = "API9:2023 Improper Inventory Management"
    UNSAFE_API_CONSUMPTION = "API10:2023 Unsafe Consumption of APIs"


class SecurityIssue(BaseModel):
    """Individual security issue found during analysis."""

    id: str = Field(..., description="Unique issue identifier")
    title: str = Field(..., description="Issue title")
    description: str = Field(..., description="Detailed description")
    severity: SecuritySeverity = Field(..., description="Issue severity")
    owasp_category: Optional[OWASPCategory] = Field(None, description="OWASP category")
    location: Dict[str, Any] = Field(
        default_factory=dict, description="Issue location in spec"
    )
    recommendation: str = Field(..., description="How to fix the issue")
    remediation_example: Optional[str] = Field(None, description="Code example for fix")
    cwe_id: Optional[str] = Field(None, description="CWE identifier")
    references: List[str] = Field(
        default_factory=list, description="External references"
    )


class AuthenticationAnalysis(BaseModel):
    """Results from authentication analysis."""

    has_authentication: bool = Field(..., description="Has any auth scheme defined")
    authentication_schemes: List[str] = Field(
        default_factory=list, description="Detected auth schemes"
    )
    issues: List[SecurityIssue] = Field(
        default_factory=list, description="Authentication issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="General recommendations"
    )
    score: float = Field(..., ge=0, le=100, description="Authentication security score")


class AuthorizationAnalysis(BaseModel):
    """Results from authorization analysis."""

    has_authorization: bool = Field(..., description="Has authorization controls")
    protected_endpoints: int = Field(0, description="Number of protected endpoints")
    unprotected_endpoints: int = Field(0, description="Number of unprotected endpoints")
    rbac_implemented: bool = Field(False, description="RBAC pattern detected")
    issues: List[SecurityIssue] = Field(
        default_factory=list, description="Authorization issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="General recommendations"
    )
    score: float = Field(..., ge=0, le=100, description="Authorization security score")


class DataExposureAnalysis(BaseModel):
    """Results from data exposure analysis."""

    pii_fields_detected: List[Dict[str, Any]] = Field(
        default_factory=list, description="PII fields found"
    )
    sensitive_data_fields: List[Dict[str, Any]] = Field(
        default_factory=list, description="Sensitive fields"
    )
    unencrypted_sensitive_data: bool = Field(
        False, description="Sensitive data without encryption"
    )
    issues: List[SecurityIssue] = Field(
        default_factory=list, description="Data exposure issues"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="General recommendations"
    )
    score: float = Field(..., ge=0, le=100, description="Data protection score")


class OWASPComplianceAnalysis(BaseModel):
    """Results from OWASP compliance validation."""

    compliant_categories: List[OWASPCategory] = Field(
        default_factory=list, description="Compliant categories"
    )
    non_compliant_categories: List[OWASPCategory] = Field(
        default_factory=list, description="Non-compliant"
    )
    issues: List[SecurityIssue] = Field(
        default_factory=list, description="OWASP compliance issues"
    )
    compliance_percentage: float = Field(
        ..., ge=0, le=100, description="Overall compliance %"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="General recommendations"
    )


class SecurityAnalysisReport(BaseModel):
    """Complete security analysis report."""

    overall_score: float = Field(
        ..., ge=0, le=100, description="Overall security score"
    )
    risk_level: SecuritySeverity = Field(..., description="Overall risk level")
    authentication: AuthenticationAnalysis = Field(
        ..., description="Authentication analysis"
    )
    authorization: AuthorizationAnalysis = Field(
        ..., description="Authorization analysis"
    )
    data_exposure: DataExposureAnalysis = Field(
        ..., description="Data exposure analysis"
    )
    owasp_compliance: OWASPComplianceAnalysis = Field(
        ..., description="OWASP compliance"
    )
    all_issues: List[SecurityIssue] = Field(
        default_factory=list, description="All issues combined"
    )
    executive_summary: str = Field(..., description="Executive summary of findings")
    generated_at: str = Field(..., description="Timestamp of analysis")
    spec_hash: Optional[str] = Field(None, description="Hash of analyzed spec")


class ValidationSuggestion(BaseModel):
    """Validation suggestion from spec linter."""

    rule_id: Optional[str] = Field(None, description="Rule identifier")
    message: str = Field(..., description="Suggestion message")
    severity: str = Field("info", description="Severity level")
    path: Optional[str] = Field(None, description="Path in spec")
    category: Optional[str] = Field(None, description="Suggestion category")


class SecurityAnalysisRequest(BaseModel):
    """Request for security analysis."""

    spec_text: str = Field(..., description="OpenAPI specification to analyze")
    validation_suggestions: Optional[List[ValidationSuggestion]] = Field(
        None,
        description="Optional validation suggestions to provide additional context",
    )
    force_refresh: bool = Field(False, description="Force fresh analysis, bypass cache")
    include_remediation: bool = Field(True, description="Include remediation examples")
    severity_threshold: SecuritySeverity = Field(
        SecuritySeverity.LOW, description="Minimum severity to report"
    )
    owasp_only: bool = Field(False, description="Only check OWASP Top 10")
