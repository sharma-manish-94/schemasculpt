"""
Authentication security analyzer agent.
Analyzes authentication schemes and security requirements in OpenAPI specs.
"""

import json
from typing import Any, Dict, List

from ...core.logging import get_logger
from ...schemas.security_schemas import (
    AuthenticationAnalysis,
    OWASPCategory,
    SecurityIssue,
    SecuritySeverity,
)

logger = get_logger("security.authentication_analyzer")


class AuthenticationAnalyzer:
    """
    Specialized agent for analyzing authentication security in OpenAPI specs.
    Checks for:
    - Presence of security schemes
    - Proper authentication implementation
    - Security requirements on endpoints
    - OWASP API2:2023 compliance
    """

    def __init__(self):
        self.logger = logger

    async def analyze(self, spec: Dict[str, Any]) -> AuthenticationAnalysis:
        """
        Analyze authentication security in the OpenAPI specification.

        Args:
            spec: Parsed OpenAPI specification dictionary

        Returns:
            AuthenticationAnalysis with findings
        """
        self.logger.info("Starting authentication security analysis")

        issues = []
        recommendations = []
        authentication_schemes = []
        has_authentication = False

        # Check for security schemes definition
        components = spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})

        if security_schemes:
            has_authentication = True
            authentication_schemes = list(security_schemes.keys())

            # Analyze each security scheme
            for scheme_name, scheme_def in security_schemes.items():
                scheme_type = scheme_def.get("type", "").lower()

                # Check for weak authentication schemes
                if scheme_type == "apikey":
                    issues.append(
                        SecurityIssue(
                            id=f"auth-weak-apikey-{scheme_name}",
                            title="Weak Authentication: API Key",
                            description=f"API key authentication ({scheme_name}) is less secure than OAuth2 or OpenID Connect",
                            severity=SecuritySeverity.MEDIUM,
                            owasp_category=OWASPCategory.BROKEN_AUTHENTICATION,
                            location={
                                "components": {
                                    "securitySchemes": {scheme_name: scheme_def}
                                }
                            },
                            recommendation="Consider using OAuth2 or OpenID Connect for better security",
                            cwe_id="CWE-287",
                            references=[
                                "https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html#authentication"
                            ],
                        )
                    )

                # Check HTTP basic auth
                if scheme_type == "http" and scheme_def.get("scheme") == "basic":
                    issues.append(
                        SecurityIssue(
                            id=f"auth-basic-{scheme_name}",
                            title="Insecure Authentication: HTTP Basic Auth",
                            description=f"HTTP Basic authentication ({scheme_name}) should only be used over HTTPS",
                            severity=SecuritySeverity.HIGH,
                            owasp_category=OWASPCategory.BROKEN_AUTHENTICATION,
                            location={
                                "components": {
                                    "securitySchemes": {scheme_name: scheme_def}
                                }
                            },
                            recommendation="Use OAuth2/OpenID Connect, or ensure HTTPS is enforced",
                            remediation_example=json.dumps(
                                {
                                    "components": {
                                        "securitySchemes": {
                                            "oauth2": {
                                                "type": "oauth2",
                                                "flows": {
                                                    "authorizationCode": {
                                                        "authorizationUrl": "https://example.com/oauth/authorize",
                                                        "tokenUrl": "https://example.com/oauth/token",
                                                        "scopes": {},
                                                    }
                                                },
                                            }
                                        }
                                    }
                                },
                                indent=2,
                            ),
                            cwe_id="CWE-319",
                            references=[
                                "https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/"
                            ],
                        )
                    )

                # Check OAuth2 configuration
                if scheme_type == "oauth2":
                    flows = scheme_def.get("flows", {})
                    if not flows:
                        issues.append(
                            SecurityIssue(
                                id=f"auth-oauth2-noflows-{scheme_name}",
                                title="OAuth2 Configuration Issue",
                                description=f"OAuth2 scheme ({scheme_name}) has no flows defined",
                                severity=SecuritySeverity.HIGH,
                                owasp_category=OWASPCategory.BROKEN_AUTHENTICATION,
                                location={
                                    "components": {
                                        "securitySchemes": {scheme_name: scheme_def}
                                    }
                                },
                                recommendation="Define at least one OAuth2 flow (authorizationCode, implicit, password, or clientCredentials)",
                                cwe_id="CWE-1390",
                            )
                        )

                    # Check for scopes definition
                    for flow_name, flow_def in flows.items():
                        if "scopes" not in flow_def:
                            issues.append(
                                SecurityIssue(
                                    id=f"auth-oauth2-noscopes-{scheme_name}-{flow_name}",
                                    title="OAuth2 Missing Scopes",
                                    description=f"OAuth2 flow '{flow_name}' in scheme '{scheme_name}' has no scopes defined",
                                    severity=SecuritySeverity.MEDIUM,
                                    owasp_category=OWASPCategory.BROKEN_FUNCTION_AUTH,
                                    location={
                                        "components": {
                                            "securitySchemes": {
                                                scheme_name: {
                                                    "flows": {flow_name: flow_def}
                                                }
                                            }
                                        }
                                    },
                                    recommendation="Define granular scopes for better access control",
                                    cwe_id="CWE-285",
                                )
                            )
        else:
            # No security schemes defined at all
            issues.append(
                SecurityIssue(
                    id="auth-no-schemes",
                    title="No Authentication Defined",
                    description="OpenAPI spec has no security schemes defined in components",
                    severity=SecuritySeverity.CRITICAL,
                    owasp_category=OWASPCategory.BROKEN_AUTHENTICATION,
                    location={"components": {}},
                    recommendation="Define at least one security scheme (OAuth2, OpenID Connect, or API Key with proper protection)",
                    remediation_example=json.dumps(
                        {
                            "components": {
                                "securitySchemes": {
                                    "bearerAuth": {
                                        "type": "http",
                                        "scheme": "bearer",
                                        "bearerFormat": "JWT",
                                    }
                                }
                            }
                        },
                        indent=2,
                    ),
                    cwe_id="CWE-306",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/"
                    ],
                )
            )

        # Check global security requirements
        global_security = spec.get("security", [])

        # Check path-level security
        paths = spec.get("paths", {})
        unprotected_paths = []

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete", "head", "options"]:
                if method in path_item:
                    operation = path_item[method]
                    operation_security = operation.get("security", global_security)

                    # Check if endpoint has no security
                    if not operation_security or operation_security == [{}]:
                        unprotected_paths.append(f"{method.upper()} {path}")

        if unprotected_paths and has_authentication:
            issues.append(
                SecurityIssue(
                    id="auth-unprotected-endpoints",
                    title="Unprotected Endpoints Detected",
                    description=f"Found {len(unprotected_paths)} endpoint(s) without authentication requirements",
                    severity=SecuritySeverity.HIGH,
                    owasp_category=OWASPCategory.BROKEN_AUTHENTICATION,
                    location={"paths": unprotected_paths[:5]},  # Show first 5
                    recommendation="Apply security requirements to all sensitive endpoints",
                    cwe_id="CWE-306",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa2-broken-authentication/"
                    ],
                )
            )

        # Generate recommendations
        if not has_authentication:
            recommendations.append(
                "Implement OAuth2 or OpenID Connect for authentication"
            )
            recommendations.append(
                "Use HTTPS for all authentication-related communications"
            )
        else:
            if any(s.get("type") == "apiKey" for s in security_schemes.values()):
                recommendations.append(
                    "Consider migrating from API keys to OAuth2 for better security"
                )
            if unprotected_paths:
                recommendations.append(
                    f"Protect {len(unprotected_paths)} unprotected endpoints"
                )

        recommendations.append("Implement rate limiting to prevent brute force attacks")
        recommendations.append(
            "Use strong password policies if password-based auth is used"
        )
        recommendations.append(
            "Implement multi-factor authentication (MFA) for sensitive operations"
        )

        # Calculate security score
        score = self._calculate_score(
            has_authentication, issues, authentication_schemes
        )

        return AuthenticationAnalysis(
            has_authentication=has_authentication,
            authentication_schemes=authentication_schemes,
            issues=issues,
            recommendations=recommendations,
            score=score,
        )

    def _calculate_score(
        self, has_auth: bool, issues: List[SecurityIssue], schemes: List[str]
    ) -> float:
        """Calculate authentication security score (0-100)."""
        if not has_auth:
            return 0.0

        base_score = 60.0  # Has some authentication

        # Bonus for OAuth2/OIDC
        if any("oauth" in s.lower() or "openid" in s.lower() for s in schemes):
            base_score += 20.0

        # Deduct for issues
        severity_penalties = {
            SecuritySeverity.CRITICAL: 30,
            SecuritySeverity.HIGH: 15,
            SecuritySeverity.MEDIUM: 8,
            SecuritySeverity.LOW: 3,
            SecuritySeverity.INFO: 1,
        }

        penalty = sum(severity_penalties.get(issue.severity, 0) for issue in issues)

        return max(0.0, min(100.0, base_score - penalty))
