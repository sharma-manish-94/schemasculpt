"""
OWASP API Security Top 10 compliance validator.
Aggregates findings from other analyzers and maps them to OWASP categories.
"""

from typing import Any, Dict, List

from ...core.logging import get_logger
from ...schemas.security_schemas import (
    AuthenticationAnalysis,
    AuthorizationAnalysis,
    DataExposureAnalysis,
    OWASPCategory,
    OWASPComplianceAnalysis,
    SecurityIssue,
)

logger = get_logger("security.owasp_compliance_validator")


class OWASPComplianceValidator:
    """
    Validates compliance with OWASP API Security Top 10 2023.
    Aggregates findings from specialized analyzers and generates compliance report.
    """

    def __init__(self):
        self.logger = logger

    async def validate(
        self,
        spec: Dict[str, Any],
        auth_analysis: AuthenticationAnalysis,
        authz_analysis: AuthorizationAnalysis,
        data_analysis: DataExposureAnalysis,
    ) -> OWASPComplianceAnalysis:
        """
        Validate OWASP API Security Top 10 compliance.

        Args:
            spec: OpenAPI specification
            auth_analysis: Authentication analysis results
            authz_analysis: Authorization analysis results
            data_analysis: Data exposure analysis results

        Returns:
            OWASPComplianceAnalysis with compliance status
        """
        self.logger.info("Starting OWASP API Security Top 10 compliance validation")

        # Collect all issues from analyzers
        all_issues = []
        all_issues.extend(auth_analysis.issues)
        all_issues.extend(authz_analysis.issues)
        all_issues.extend(data_analysis.issues)

        # Map issues to OWASP categories
        category_issues = self._categorize_issues(all_issues)

        # Additional OWASP checks not covered by other analyzers
        additional_issues = await self._perform_additional_checks(spec)
        all_issues.extend(additional_issues)

        # Update category mapping with additional issues
        for issue in additional_issues:
            if issue.owasp_category:
                category_issues.setdefault(issue.owasp_category, []).append(issue)

        # Determine compliant vs non-compliant categories
        compliant_categories = []
        non_compliant_categories = []

        for category in OWASPCategory:
            issues_in_category = category_issues.get(category, [])
            if not issues_in_category:
                compliant_categories.append(category)
            else:
                non_compliant_categories.append(category)

        # Calculate compliance percentage
        total_categories = len(OWASPCategory)
        compliance_percentage = (len(compliant_categories) / total_categories) * 100

        # Generate recommendations
        recommendations = self._generate_recommendations(
            non_compliant_categories, category_issues
        )

        return OWASPComplianceAnalysis(
            compliant_categories=compliant_categories,
            non_compliant_categories=non_compliant_categories,
            issues=all_issues,
            compliance_percentage=compliance_percentage,
            recommendations=recommendations,
        )

    def _categorize_issues(
        self, issues: List[SecurityIssue]
    ) -> Dict[OWASPCategory, List[SecurityIssue]]:
        """Categorize issues by OWASP category."""
        categorized = {}

        for issue in issues:
            if issue.owasp_category:
                categorized.setdefault(issue.owasp_category, []).append(issue)

        return categorized

    async def _perform_additional_checks(
        self, spec: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """
        Perform additional OWASP checks not covered by other analyzers.
        Focuses on API4, API6, API7, API8, API9, API10.
        """
        issues = []

        # API4: Unrestricted Resource Consumption
        rate_limit_issues = self._check_rate_limiting(spec)
        issues.extend(rate_limit_issues)

        # API7: Server Side Request Forgery
        ssrf_issues = self._check_ssrf_vulnerabilities(spec)
        issues.extend(ssrf_issues)

        # API8: Security Misconfiguration
        config_issues = self._check_security_configuration(spec)
        issues.extend(config_issues)

        # API9: Improper Inventory Management
        inventory_issues = self._check_inventory_management(spec)
        issues.extend(inventory_issues)

        # API10: Unsafe Consumption of APIs
        unsafe_consumption_issues = self._check_unsafe_api_consumption(spec)
        issues.extend(unsafe_consumption_issues)

        return issues

    def _check_rate_limiting(self, spec: Dict[str, Any]) -> List[SecurityIssue]:
        """Check for rate limiting implementation (API4)."""
        issues = []

        # Check if rate limiting is documented
        paths = spec.get("paths", {})
        has_rate_limit_response = False

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    operation = path_item[method]
                    responses = operation.get("responses", {})

                    if "429" in responses:
                        has_rate_limit_response = True
                        break

        if not has_rate_limit_response:
            issues.append(
                SecurityIssue(
                    id="owasp-api4-no-rate-limiting",
                    title="No Rate Limiting Documented",
                    description="API does not document rate limiting (HTTP 429 responses)",
                    severity="medium",
                    owasp_category=OWASPCategory.UNRESTRICTED_RESOURCE,
                    location={"paths": "all"},
                    recommendation="Implement and document rate limiting to prevent resource exhaustion attacks",
                    cwe_id="CWE-770",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/"
                    ],
                )
            )

        return issues

    def _check_ssrf_vulnerabilities(self, spec: Dict[str, Any]) -> List[SecurityIssue]:
        """Check for potential SSRF vulnerabilities (API7)."""
        issues = []

        # Look for endpoints that might accept URLs as parameters
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                parameters = operation.get("parameters", [])
                operation.get("requestBody", {})

                # Check parameters
                for param in parameters:
                    param_name = param.get("name", "").lower()
                    if any(
                        keyword in param_name
                        for keyword in ["url", "uri", "link", "callback"]
                    ):
                        issues.append(
                            SecurityIssue(
                                id=f"owasp-api7-ssrf-param-{path}-{param_name}",
                                title="Potential SSRF Vulnerability",
                                description=f"Parameter '{param_name}' in {method.upper()} {path} accepts URLs - ensure proper validation",
                                severity="high",
                                owasp_category=OWASPCategory.SERVER_SIDE_REQUEST_FORGERY,
                                location={
                                    "path": path,
                                    "method": method,
                                    "parameter": param_name,
                                },
                                recommendation="Validate and sanitize URL parameters, use allowlists, and avoid direct URL fetching",
                                cwe_id="CWE-918",
                                references=[
                                    "https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/"
                                ],
                            )
                        )

        return issues

    def _check_security_configuration(
        self, spec: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Check for security misconfigurations (API8)."""
        issues = []

        # Check for missing security headers documentation
        paths = spec.get("paths", {})
        documents_security_headers = False

        for path_item in paths.values():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    operation = path_item[method]
                    responses = operation.get("responses", {})

                    for response in responses.values():
                        headers = response.get("headers", {})
                        security_headers = [
                            "X-Content-Type-Options",
                            "X-Frame-Options",
                            "Content-Security-Policy",
                            "Strict-Transport-Security",
                        ]

                        if any(h in headers for h in security_headers):
                            documents_security_headers = True
                            break

        if not documents_security_headers:
            issues.append(
                SecurityIssue(
                    id="owasp-api8-no-security-headers",
                    title="Security Headers Not Documented",
                    description="API does not document security headers (X-Content-Type-Options, CSP, etc.)",
                    severity="medium",
                    owasp_category=OWASPCategory.SECURITY_MISCONFIGURATION,
                    location={"responses": "all"},
                    recommendation="Document and implement security headers to prevent common web attacks",
                    cwe_id="CWE-16",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/"
                    ],
                )
            )

        # Check OpenAPI version
        openapi_version = spec.get("openapi", "")
        if not openapi_version.startswith("3."):
            issues.append(
                SecurityIssue(
                    id="owasp-api8-old-openapi-version",
                    title="Outdated OpenAPI Version",
                    description=f"Using OpenAPI version {openapi_version} - consider upgrading to 3.x",
                    severity="low",
                    owasp_category=OWASPCategory.SECURITY_MISCONFIGURATION,
                    location={"openapi": openapi_version},
                    recommendation="Use the latest OpenAPI 3.x specification for better security features",
                    cwe_id="CWE-1104",
                )
            )

        return issues

    def _check_inventory_management(self, spec: Dict[str, Any]) -> List[SecurityIssue]:
        """Check for proper API inventory management (API9)."""
        issues = []

        # Check if spec has proper metadata
        info = spec.get("info", {})

        if not info.get("version"):
            issues.append(
                SecurityIssue(
                    id="owasp-api9-no-version",
                    title="API Version Not Specified",
                    description="API specification does not include version information",
                    severity="medium",
                    owasp_category=OWASPCategory.IMPROPER_INVENTORY,
                    location={"info": info},
                    recommendation="Add version information to track API changes and manage inventory",
                    cwe_id="CWE-1059",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa9-improper-inventory-management/"
                    ],
                )
            )

        if not info.get("description"):
            issues.append(
                SecurityIssue(
                    id="owasp-api9-no-description",
                    title="API Description Missing",
                    description="API specification lacks a description for proper documentation",
                    severity="low",
                    owasp_category=OWASPCategory.IMPROPER_INVENTORY,
                    location={"info": info},
                    recommendation="Add comprehensive API description for better inventory management",
                    cwe_id="CWE-1059",
                )
            )

        return issues

    def _check_unsafe_api_consumption(
        self, spec: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Check for unsafe consumption of external APIs (API10)."""
        issues = []

        # Check if API calls external services (indicated by external URLs in examples or descriptions)
        # This is a simplified check - real implementation would be more sophisticated
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                description = operation.get("description", "").lower()

                # Look for indicators of external API calls
                external_indicators = ["external", "third-party", "webhook", "callback"]

                if any(indicator in description for indicator in external_indicators):
                    issues.append(
                        SecurityIssue(
                            id=f"owasp-api10-external-api-{path}-{method}",
                            title="External API Consumption Detected",
                            description=f"Endpoint {method.upper()} {path} appears to consume external APIs",
                            severity="medium",
                            owasp_category=OWASPCategory.UNSAFE_API_CONSUMPTION,
                            location={"path": path, "method": method},
                            recommendation="Validate external API responses, implement timeouts, and handle errors securely",
                            cwe_id="CWE-20",
                            references=[
                                "https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/"
                            ],
                        )
                    )

        return issues

    def _generate_recommendations(
        self,
        non_compliant: List[OWASPCategory],
        category_issues: Dict[OWASPCategory, List[SecurityIssue]],
    ) -> List[str]:
        """Generate high-level recommendations based on compliance gaps."""
        recommendations = []

        if OWASPCategory.BROKEN_OBJECT_LEVEL_AUTH in non_compliant:
            recommendations.append(
                "Implement object-level authorization checks in your business logic"
            )

        if OWASPCategory.BROKEN_AUTHENTICATION in non_compliant:
            recommendations.append(
                "Upgrade to OAuth2 or OpenID Connect for stronger authentication"
            )

        if OWASPCategory.BROKEN_OBJECT_PROPERTY_AUTH in non_compliant:
            recommendations.append(
                "Implement field-level access control and mark sensitive fields as writeOnly"
            )

        if OWASPCategory.UNRESTRICTED_RESOURCE in non_compliant:
            recommendations.append("Implement rate limiting and resource quotas")

        if OWASPCategory.BROKEN_FUNCTION_AUTH in non_compliant:
            recommendations.append(
                "Apply role-based access control (RBAC) to all administrative functions"
            )

        if OWASPCategory.SECURITY_MISCONFIGURATION in non_compliant:
            recommendations.append(
                "Configure security headers and keep dependencies up to date"
            )

        if len(non_compliant) > 5:
            recommendations.append(
                "Consider a comprehensive security review and penetration testing"
            )

        return recommendations
