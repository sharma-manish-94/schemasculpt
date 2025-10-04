"""
Authorization security analyzer agent.
Analyzes authorization controls and RBAC implementation in OpenAPI specs.
"""

import json
from typing import Dict, Any, List, Set
from ...schemas.security_schemas import (
    AuthorizationAnalysis, SecurityIssue, SecuritySeverity, OWASPCategory
)
from ...core.logging import get_logger

logger = get_logger("security.authorization_analyzer")


class AuthorizationAnalyzer:
    """
    Specialized agent for analyzing authorization security in OpenAPI specs.
    Checks for:
    - Function-level authorization
    - RBAC implementation
    - Object-level authorization
    - OWASP API1 and API5 compliance
    """

    # HTTP methods that typically require authorization
    SENSITIVE_METHODS = {"post", "put", "patch", "delete"}

    # Paths that are typically sensitive
    SENSITIVE_PATH_PATTERNS = [
        "/admin", "/user", "/account", "/profile", "/payment",
        "/order", "/transaction", "/settings", "/config"
    ]

    def __init__(self):
        self.logger = logger

    async def analyze(self, spec: Dict[str, Any]) -> AuthorizationAnalysis:
        """
        Analyze authorization security in the OpenAPI specification.

        Args:
            spec: Parsed OpenAPI specification dictionary

        Returns:
            AuthorizationAnalysis with findings
        """
        self.logger.info("Starting authorization security analysis")

        issues = []
        recommendations = []

        # Get security schemes
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        global_security = spec.get("security", [])

        # Analyze OAuth2 scopes for RBAC
        rbac_implemented = False
        oauth_scopes = self._extract_oauth_scopes(security_schemes)

        if oauth_scopes:
            rbac_implemented = True
            # Check if scopes are actually used
            if not self._scopes_are_used(spec, oauth_scopes):
                issues.append(SecurityIssue(
                    id="authz-unused-scopes",
                    title="OAuth2 Scopes Defined But Not Used",
                    description="OAuth2 scopes are defined but not applied to any endpoints",
                    severity=SecuritySeverity.MEDIUM,
                    owasp_category=OWASPCategory.BROKEN_FUNCTION_AUTH,
                    location={"components": {"securitySchemes": {}}},
                    recommendation="Apply OAuth2 scopes to endpoints based on required permissions",
                    remediation_example=json.dumps({
                        "paths": {
                            "/admin/users": {
                                "get": {
                                    "security": [{"oauth2": ["admin:read"]}]
                                }
                            }
                        }
                    }, indent=2),
                    cwe_id="CWE-285"
                ))

        # Analyze paths
        paths = spec.get("paths", {})
        protected_endpoints = 0
        unprotected_endpoints = 0
        sensitive_unprotected = []

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                operation_security = operation.get("security", global_security)

                is_protected = bool(operation_security) and operation_security != [{}]
                is_sensitive = self._is_sensitive_endpoint(path, method)

                if is_protected:
                    protected_endpoints += 1
                else:
                    unprotected_endpoints += 1
                    if is_sensitive:
                        sensitive_unprotected.append(f"{method.upper()} {path}")

        # Check for broken object level authorization (BOLA)
        bola_issues = self._check_object_level_authorization(paths, security_schemes)
        issues.extend(bola_issues)

        # Check for broken function level authorization (BFLA)
        bfla_issues = self._check_function_level_authorization(paths, global_security)
        issues.extend(bfla_issues)

        # Issue for sensitive unprotected endpoints
        if sensitive_unprotected:
            issues.append(SecurityIssue(
                id="authz-sensitive-unprotected",
                title="Sensitive Endpoints Without Authorization",
                description=f"Found {len(sensitive_unprotected)} sensitive endpoint(s) without authorization controls",
                severity=SecuritySeverity.CRITICAL,
                owasp_category=OWASPCategory.BROKEN_FUNCTION_AUTH,
                location={"paths": sensitive_unprotected[:5]},
                recommendation="Apply appropriate authorization controls to all sensitive endpoints",
                cwe_id="CWE-862",
                references=[
                    "https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/"
                ]
            ))

        # Check for admin endpoints
        admin_issues = self._check_admin_endpoints(paths, global_security)
        issues.extend(admin_issues)

        # Generate recommendations
        if not rbac_implemented:
            recommendations.append("Implement Role-Based Access Control (RBAC) using OAuth2 scopes")

        recommendations.append("Ensure all sensitive operations require proper authorization")
        recommendations.append("Implement resource-level authorization checks")
        recommendations.append("Use principle of least privilege for API access")

        if sensitive_unprotected:
            recommendations.append(f"Add authorization to {len(sensitive_unprotected)} unprotected sensitive endpoints")

        # Calculate score
        score = self._calculate_score(
            protected_endpoints,
            unprotected_endpoints,
            sensitive_unprotected,
            rbac_implemented,
            issues
        )

        has_authorization = protected_endpoints > 0 or rbac_implemented

        return AuthorizationAnalysis(
            has_authorization=has_authorization,
            protected_endpoints=protected_endpoints,
            unprotected_endpoints=unprotected_endpoints,
            rbac_implemented=rbac_implemented,
            issues=issues,
            recommendations=recommendations,
            score=score
        )

    def _extract_oauth_scopes(self, security_schemes: Dict[str, Any]) -> Set[str]:
        """Extract all OAuth2 scopes from security schemes."""
        scopes = set()
        for scheme_name, scheme_def in security_schemes.items():
            if scheme_def.get("type") == "oauth2":
                flows = scheme_def.get("flows", {})
                for flow_def in flows.values():
                    if "scopes" in flow_def:
                        scopes.update(flow_def["scopes"].keys())
        return scopes

    def _scopes_are_used(self, spec: Dict[str, Any], defined_scopes: Set[str]) -> bool:
        """Check if defined scopes are actually used in endpoints."""
        paths = spec.get("paths", {})
        for path_item in paths.values():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method in path_item:
                    operation = path_item[method]
                    security = operation.get("security", [])
                    for sec_req in security:
                        for scopes in sec_req.values():
                            if any(scope in defined_scopes for scope in scopes):
                                return True
        return False

    def _is_sensitive_endpoint(self, path: str, method: str) -> bool:
        """Determine if an endpoint is sensitive based on path and method."""
        # Check method
        if method.lower() in self.SENSITIVE_METHODS:
            return True

        # Check path patterns
        path_lower = path.lower()
        return any(pattern in path_lower for pattern in self.SENSITIVE_PATH_PATTERNS)

    def _check_object_level_authorization(
        self,
        paths: Dict[str, Any],
        security_schemes: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Check for Broken Object Level Authorization (BOLA) vulnerabilities."""
        issues = []

        # Look for path parameters that might be user/object IDs
        for path, path_item in paths.items():
            if "{" in path:  # Has path parameters
                # Check for common ID parameters
                if any(param in path.lower() for param in ["id}", "userid}", "accountid}", "objectid}"]):
                    for method in ["get", "put", "patch", "delete"]:
                        if method in path_item:
                            operation = path_item[method]

                            # Check if there's a description mentioning authorization
                            description = operation.get("description", "").lower()
                            summary = operation.get("summary", "").lower()

                            mentions_authz = any(
                                keyword in description or keyword in summary
                                for keyword in ["owner", "authorize", "permission", "access control"]
                            )

                            if not mentions_authz:
                                issues.append(SecurityIssue(
                                    id=f"authz-bola-{path}-{method}",
                                    title="Potential Broken Object Level Authorization",
                                    description=f"Endpoint {method.upper()} {path} accesses objects by ID but doesn't document authorization checks",
                                    severity=SecuritySeverity.HIGH,
                                    owasp_category=OWASPCategory.BROKEN_OBJECT_LEVEL_AUTH,
                                    location={"path": path, "method": method},
                                    recommendation="Implement and document object-level authorization checks to ensure users can only access their own resources",
                                    cwe_id="CWE-639",
                                    references=[
                                        "https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/"
                                    ]
                                ))

        return issues

    def _check_function_level_authorization(
        self,
        paths: Dict[str, Any],
        global_security: List[Dict[str, Any]]
    ) -> List[SecurityIssue]:
        """Check for Broken Function Level Authorization (BFLA) vulnerabilities."""
        issues = []

        # Check administrative functions
        for path, path_item in paths.items():
            if "/admin" in path.lower() or "/manage" in path.lower():
                for method in ["get", "post", "put", "patch", "delete"]:
                    if method in path_item:
                        operation = path_item[method]
                        operation_security = operation.get("security", global_security)

                        # Admin endpoints should have specific security requirements
                        has_specific_security = operation_security and operation_security != global_security

                        if not has_specific_security:
                            issues.append(SecurityIssue(
                                id=f"authz-bfla-admin-{path}-{method}",
                                title="Admin Function Without Specific Authorization",
                                description=f"Administrative endpoint {method.upper()} {path} lacks function-level authorization",
                                severity=SecuritySeverity.CRITICAL,
                                owasp_category=OWASPCategory.BROKEN_FUNCTION_AUTH,
                                location={"path": path, "method": method},
                                recommendation="Apply role-based authorization (e.g., admin scope) to administrative functions",
                                remediation_example=json.dumps({
                                    "security": [{"oauth2": ["admin"]}]
                                }, indent=2),
                                cwe_id="CWE-285",
                                references=[
                                    "https://owasp.org/API-Security/editions/2023/en/0xa5-broken-function-level-authorization/"
                                ]
                            ))

        return issues

    def _check_admin_endpoints(
        self,
        paths: Dict[str, Any],
        global_security: List[Dict[str, Any]]
    ) -> List[SecurityIssue]:
        """Check admin endpoint security."""
        issues = []
        admin_paths = [p for p in paths.keys() if "/admin" in p.lower()]

        if admin_paths and not global_security:
            issues.append(SecurityIssue(
                id="authz-admin-no-global-security",
                title="Admin Endpoints Without Global Security",
                description=f"Found {len(admin_paths)} admin endpoint(s) but no global security defined",
                severity=SecuritySeverity.CRITICAL,
                owasp_category=OWASPCategory.BROKEN_FUNCTION_AUTH,
                location={"paths": admin_paths[:3]},
                recommendation="Define global security requirements or ensure each admin endpoint has security requirements",
                cwe_id="CWE-306"
            ))

        return issues

    def _calculate_score(
        self,
        protected: int,
        unprotected: int,
        sensitive_unprotected: List[str],
        rbac: bool,
        issues: List[SecurityIssue]
    ) -> float:
        """Calculate authorization security score (0-100)."""
        if protected + unprotected == 0:
            return 50.0  # No endpoints

        # Base score from protection ratio
        total = protected + unprotected
        protection_ratio = protected / total
        base_score = protection_ratio * 60

        # Bonus for RBAC
        if rbac:
            base_score += 20

        # Penalty for sensitive unprotected
        if sensitive_unprotected:
            base_score -= min(30, len(sensitive_unprotected) * 10)

        # Deduct for issues
        severity_penalties = {
            SecuritySeverity.CRITICAL: 25,
            SecuritySeverity.HIGH: 12,
            SecuritySeverity.MEDIUM: 6,
            SecuritySeverity.LOW: 2,
            SecuritySeverity.INFO: 1
        }

        penalty = sum(severity_penalties.get(issue.severity, 0) for issue in issues)

        return max(0.0, min(100.0, base_score - penalty))
