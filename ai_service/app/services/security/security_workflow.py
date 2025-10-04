"""
Security Analysis Workflow - Orchestrates all security analyzers.
Implements multi-agent security analysis with parallel execution.
"""

import asyncio
import hashlib
import json
from datetime import datetime
from typing import Dict, Any
from ...schemas.security_schemas import (
    SecurityAnalysisReport, SecuritySeverity
)
from ...core.logging import get_logger
from .authentication_analyzer import AuthenticationAnalyzer
from .authorization_analyzer import AuthorizationAnalyzer
from .data_exposure_analyzer import DataExposureAnalyzer
from .owasp_compliance_validator import OWASPComplianceValidator

logger = get_logger("security.workflow")


class SecurityAnalysisWorkflow:
    """
    Multi-agent workflow for comprehensive security analysis.
    Orchestrates authentication, authorization, data exposure, and OWASP compliance checks.
    """

    def __init__(self, llm_service=None):
        self.logger = logger
        self.llm_service = llm_service

        # Initialize all analyzer agents
        self.auth_analyzer = AuthenticationAnalyzer()
        self.authz_analyzer = AuthorizationAnalyzer()
        self.data_analyzer = DataExposureAnalyzer()
        self.owasp_validator = OWASPComplianceValidator()

    async def analyze(
        self,
        spec_text: str,
        validation_suggestions: list = None
    ) -> SecurityAnalysisReport:
        """
        Perform comprehensive security analysis on OpenAPI specification.

        Args:
            spec_text: OpenAPI specification as JSON/YAML string
            validation_suggestions: Optional list of validation suggestions for context

        Returns:
            SecurityAnalysisReport with complete security analysis
        """
        self.logger.info("Starting comprehensive security analysis workflow")

        # Log validation suggestions if provided
        if validation_suggestions:
            security_suggestions = [
                s for s in validation_suggestions
                if self._is_security_related(s)
            ]
            self.logger.info(
                f"Received {len(validation_suggestions)} validation suggestions, "
                f"{len(security_suggestions)} are security-related"
            )

        try:
            # Parse spec
            spec = json.loads(spec_text)
        except json.JSONDecodeError:
            # Try to handle YAML if needed
            self.logger.error("Failed to parse spec as JSON")
            raise ValueError("Invalid OpenAPI specification format")

        # Calculate spec hash for caching
        spec_hash = hashlib.sha256(spec_text.encode()).hexdigest()[:16]

        # Run all analyzers in parallel for better performance
        self.logger.info("Running security analyzers in parallel")

        try:
            auth_analysis, authz_analysis, data_analysis = await asyncio.gather(
                self.auth_analyzer.analyze(spec),
                self.authz_analyzer.analyze(spec),
                self.data_analyzer.analyze(spec),
                return_exceptions=False
            )
        except Exception as e:
            self.logger.error(f"Error running parallel analyzers: {str(e)}")
            raise

        # Run OWASP compliance validator (depends on other analyzers)
        self.logger.info("Running OWASP compliance validation")
        owasp_analysis = await self.owasp_validator.validate(
            spec,
            auth_analysis,
            authz_analysis,
            data_analysis
        )

        # Collect all issues
        all_issues = []
        all_issues.extend(auth_analysis.issues)
        all_issues.extend(authz_analysis.issues)
        all_issues.extend(data_analysis.issues)

        # Calculate overall security score
        overall_score = self._calculate_overall_score(
            auth_analysis.score,
            authz_analysis.score,
            data_analysis.score,
            owasp_analysis.compliance_percentage
        )

        # Determine overall risk level
        risk_level = self._determine_risk_level(overall_score, all_issues)

        # Generate executive summary
        executive_summary = await self._generate_executive_summary(
            spec,
            overall_score,
            risk_level,
            auth_analysis,
            authz_analysis,
            data_analysis,
            owasp_analysis
        )

        # Create comprehensive report
        report = SecurityAnalysisReport(
            overall_score=overall_score,
            risk_level=risk_level,
            authentication=auth_analysis,
            authorization=authz_analysis,
            data_exposure=data_analysis,
            owasp_compliance=owasp_analysis,
            all_issues=all_issues,
            executive_summary=executive_summary,
            generated_at=datetime.utcnow().isoformat(),
            spec_hash=spec_hash
        )

        self.logger.info(f"Security analysis complete. Overall score: {overall_score:.1f}, Risk: {risk_level}")

        return report

    def _calculate_overall_score(
        self,
        auth_score: float,
        authz_score: float,
        data_score: float,
        owasp_compliance: float
    ) -> float:
        """
        Calculate overall security score as weighted average.

        Weights:
        - Authentication: 25%
        - Authorization: 30%
        - Data Protection: 25%
        - OWASP Compliance: 20%
        """
        weights = {
            "auth": 0.25,
            "authz": 0.30,
            "data": 0.25,
            "owasp": 0.20
        }

        overall = (
            auth_score * weights["auth"] +
            authz_score * weights["authz"] +
            data_score * weights["data"] +
            owasp_compliance * weights["owasp"]
        )

        return round(overall, 1)

    def _determine_risk_level(
        self,
        overall_score: float,
        all_issues: list
    ) -> SecuritySeverity:
        """Determine overall risk level based on score and critical issues."""
        # Check for critical issues
        critical_count = sum(
            1 for issue in all_issues
            if issue.severity == SecuritySeverity.CRITICAL
        )

        high_count = sum(
            1 for issue in all_issues
            if issue.severity == SecuritySeverity.HIGH
        )

        # Critical issues override score
        if critical_count > 0:
            return SecuritySeverity.CRITICAL

        if high_count >= 3:
            return SecuritySeverity.HIGH

        # Otherwise use score
        if overall_score >= 80:
            return SecuritySeverity.LOW
        elif overall_score >= 60:
            return SecuritySeverity.MEDIUM
        elif overall_score >= 40:
            return SecuritySeverity.HIGH
        else:
            return SecuritySeverity.CRITICAL

    async def _generate_executive_summary(
        self,
        spec: Dict[str, Any],
        overall_score: float,
        risk_level: SecuritySeverity,
        auth_analysis,
        authz_analysis,
        data_analysis,
        owasp_analysis
    ) -> str:
        """Generate executive summary using LLM if available, otherwise use template."""

        # Count issues by severity
        all_issues = []
        all_issues.extend(auth_analysis.issues)
        all_issues.extend(authz_analysis.issues)
        all_issues.extend(data_analysis.issues)

        critical_count = sum(1 for i in all_issues if i.severity == SecuritySeverity.CRITICAL)
        high_count = sum(1 for i in all_issues if i.severity == SecuritySeverity.HIGH)
        medium_count = sum(1 for i in all_issues if i.severity == SecuritySeverity.MEDIUM)

        # Get API info
        info = spec.get("info", {})
        api_title = info.get("title", "API")

        # Template-based summary
        summary_parts = []

        summary_parts.append(
            f"Security analysis of {api_title} reveals an overall security score of "
            f"{overall_score:.1f}/100 with a {risk_level.value.upper()} risk level."
        )

        if critical_count > 0 or high_count > 0:
            summary_parts.append(
                f"Found {critical_count} critical and {high_count} high-severity security issues "
                f"requiring immediate attention."
            )

        # Authentication summary
        if auth_analysis.has_authentication:
            auth_type = "OAuth2" if any("oauth" in s.lower() for s in auth_analysis.authentication_schemes) else "basic"
            summary_parts.append(
                f"Authentication: {auth_type.title()} authentication is implemented "
                f"(score: {auth_analysis.score:.1f}/100)."
            )
        else:
            summary_parts.append("Authentication: No authentication mechanisms defined - critical security gap.")

        # Authorization summary
        if authz_analysis.rbac_implemented:
            summary_parts.append(
                f"Authorization: RBAC implemented with {authz_analysis.protected_endpoints} protected endpoints "
                f"(score: {authz_analysis.score:.1f}/100)."
            )
        else:
            summary_parts.append(
                f"Authorization: {authz_analysis.unprotected_endpoints} unprotected endpoints detected "
                f"(score: {authz_analysis.score:.1f}/100)."
            )

        # Data protection summary
        pii_count = len(data_analysis.pii_fields_detected)
        if pii_count > 0:
            summary_parts.append(
                f"Data Protection: {pii_count} PII field(s) detected. "
                f"{'HTTPS enforcement missing.' if data_analysis.unencrypted_sensitive_data else 'HTTPS enforced.'}"
            )

        # OWASP compliance
        compliant_count = len(owasp_analysis.compliant_categories)
        total_count = compliant_count + len(owasp_analysis.non_compliant_categories)
        summary_parts.append(
            f"OWASP Compliance: {owasp_analysis.compliance_percentage:.0f}% "
            f"({compliant_count}/{total_count} categories compliant)."
        )

        # Top recommendations
        if critical_count > 0 or high_count > 0:
            summary_parts.append(
                "Immediate actions recommended: "
                "Address all critical security issues, implement proper authentication and authorization, "
                "and ensure HTTPS for all sensitive data transmission."
            )

        return " ".join(summary_parts)

    def _is_security_related(self, suggestion: Dict[str, Any]) -> bool:
        """Check if a validation suggestion is security-related."""
        if not suggestion:
            return False

        security_keywords = [
            'security', 'auth', 'authorization', 'authentication',
            'oauth', 'api-key', 'token', 'credentials', 'password',
            'secret', 'encrypt', 'https', 'ssl', 'tls', 'cors',
            'csrf', 'xss', 'injection', 'vulnerability'
        ]

        search_text = f"{suggestion.get('rule_id', '')} {suggestion.get('message', '')} {suggestion.get('category', '')}".lower()

        return any(keyword in search_text for keyword in security_keywords)
