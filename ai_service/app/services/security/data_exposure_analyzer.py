"""
Data exposure analyzer agent.
Analyzes PII, sensitive data exposure, and data protection in OpenAPI specs.
"""

import re
from typing import Any, Dict, List

from ...core.logging import get_logger
from ...schemas.security_schemas import (
    DataExposureAnalysis,
    OWASPCategory,
    SecurityIssue,
    SecuritySeverity,
)

logger = get_logger("security.data_exposure_analyzer")


class DataExposureAnalyzer:
    """
    Specialized agent for analyzing data exposure and protection in OpenAPI specs.
    Checks for:
    - PII field detection
    - Sensitive data exposure
    - Encryption requirements
    - OWASP API3 and API6 compliance
    """

    # Common PII field patterns
    PII_PATTERNS = {
        "email": r"email|e-mail|emailaddress",
        "phone": r"phone|telephone|mobile|cell",
        "ssn": r"ssn|social.?security|tax.?id",
        "passport": r"passport",
        "license": r"driver.?license|license.?number",
        "dob": r"birth.?date|dob|date.?of.?birth",
        "name": r"^name$|first.?name|last.?name|full.?name|given.?name|surname",
        "address": r"address|street|city|zipcode|postal|zip.?code",
        "credit_card": r"card.?number|credit.?card|cc.?number|pan",
        "cvv": r"cvv|cvc|card.?verification",
        "bank_account": r"account.?number|bank.?account|routing.?number",
    }

    # Sensitive data patterns
    SENSITIVE_PATTERNS = {
        "password": r"password|passwd|pwd",
        "token": r"token|access.?token|refresh.?token|api.?key",
        "secret": r"secret|private.?key|secret.?key",
        "auth": r"authorization|bearer",
        "session": r"session.?id|session.?token",
    }

    def __init__(self):
        self.logger = logger

    async def analyze(self, spec: Dict[str, Any]) -> DataExposureAnalysis:
        """
        Analyze data exposure and protection in the OpenAPI specification.

        Args:
            spec: Parsed OpenAPI specification dictionary

        Returns:
            DataExposureAnalysis with findings
        """
        self.logger.info("Starting data exposure security analysis")

        issues = []
        recommendations = []
        pii_fields_detected = []
        sensitive_data_fields = []
        unencrypted_sensitive_data = False

        # Get all schemas
        components = spec.get("components", {})
        schemas = components.get("schemas", {})

        # Analyze schemas for PII and sensitive data
        for schema_name, schema_def in schemas.items():
            pii_in_schema, sensitive_in_schema = self._analyze_schema(
                schema_name, schema_def
            )
            pii_fields_detected.extend(pii_in_schema)
            sensitive_data_fields.extend(sensitive_in_schema)

        # Check if sensitive data is in responses
        paths = spec.get("paths", {})
        for path, path_item in paths.items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue

                operation = path_item[method]
                responses = operation.get("responses", {})

                for status_code, response_def in responses.items():
                    if status_code.startswith("2"):  # Success responses
                        pii_in_response = self._check_response_for_pii(
                            response_def, path, method, status_code
                        )
                        if pii_in_response:
                            issues.append(
                                SecurityIssue(
                                    id=f"data-pii-response-{path}-{method}-{status_code}",
                                    title="PII in API Response",
                                    description=f"PII detected in response for {method.upper()} {path} ({status_code})",
                                    severity=SecuritySeverity.HIGH,
                                    owasp_category=OWASPCategory.BROKEN_OBJECT_PROPERTY_AUTH,
                                    location={
                                        "path": path,
                                        "method": method,
                                        "response": status_code,
                                    },
                                    recommendation="Ensure PII is only returned when necessary and implement field-level authorization",
                                    cwe_id="CWE-359",
                                    references=[
                                        "https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/"
                                    ],
                                )
                            )

        # Check for passwords in requests/responses
        password_exposure_issues = self._check_password_exposure(schemas, paths)
        issues.extend(password_exposure_issues)

        # Check for missing HTTPS
        servers = spec.get("servers", [])
        uses_https = (
            all(server.get("url", "").startswith("https://") for server in servers)
            if servers
            else False
        )

        if not uses_https and (pii_fields_detected or sensitive_data_fields):
            unencrypted_sensitive_data = True
            issues.append(
                SecurityIssue(
                    id="data-no-https",
                    title="Sensitive Data Without HTTPS",
                    description="API handles sensitive data but doesn't require HTTPS",
                    severity=SecuritySeverity.CRITICAL,
                    owasp_category=OWASPCategory.SECURITY_MISCONFIGURATION,
                    location={"servers": servers if servers else "not defined"},
                    recommendation="Enforce HTTPS for all API communications, especially when handling PII or sensitive data",
                    cwe_id="CWE-319",
                    references=[
                        "https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/"
                    ],
                )
            )

        # Check for excessive data exposure
        excessive_exposure_issues = self._check_excessive_data_exposure(paths, schemas)
        issues.extend(excessive_exposure_issues)

        # Generate recommendations
        if pii_fields_detected:
            recommendations.append(
                f"Implement field-level access control for {len(pii_fields_detected)} PII field(s)"
            )
            recommendations.append(
                "Consider data minimization - only collect and expose necessary PII"
            )
            recommendations.append(
                "Implement data masking for sensitive fields in logs and responses"
            )

        if sensitive_data_fields:
            recommendations.append(
                "Never expose passwords, tokens, or secrets in API responses"
            )
            recommendations.append(
                "Use proper encryption for sensitive data at rest and in transit"
            )

        if not uses_https:
            recommendations.append("Enforce HTTPS/TLS for all API endpoints")

        recommendations.append("Implement data retention and deletion policies for PII")
        recommendations.append(
            "Add privacy controls (e.g., consent management, data export)"
        )

        # Calculate score
        score = self._calculate_score(
            pii_fields_detected, sensitive_data_fields, uses_https, issues
        )

        return DataExposureAnalysis(
            pii_fields_detected=pii_fields_detected,
            sensitive_data_fields=sensitive_data_fields,
            unencrypted_sensitive_data=unencrypted_sensitive_data,
            issues=issues,
            recommendations=recommendations,
            score=score,
        )

    def _analyze_schema(
        self, schema_name: str, schema_def: Dict[str, Any]
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Analyze a schema for PII and sensitive data fields."""
        pii_fields = []
        sensitive_fields = []

        properties = schema_def.get("properties", {})

        for prop_name, prop_def in properties.items():
            prop_lower = prop_name.lower()

            # Check for PII
            for pii_type, pattern in self.PII_PATTERNS.items():
                if re.search(pattern, prop_lower, re.IGNORECASE):
                    pii_fields.append(
                        {
                            "schema": schema_name,
                            "field": prop_name,
                            "type": pii_type,
                            "description": prop_def.get("description", ""),
                        }
                    )
                    break

            # Check for sensitive data
            for sensitive_type, pattern in self.SENSITIVE_PATTERNS.items():
                if re.search(pattern, prop_lower, re.IGNORECASE):
                    sensitive_fields.append(
                        {
                            "schema": schema_name,
                            "field": prop_name,
                            "type": sensitive_type,
                            "description": prop_def.get("description", ""),
                        }
                    )
                    break

        return pii_fields, sensitive_fields

    def _check_response_for_pii(
        self, response_def: Dict[str, Any], path: str, method: str, status_code: str
    ) -> bool:
        """Check if a response contains PII."""
        content = response_def.get("content", {})

        for media_type, media_def in content.items():
            schema = media_def.get("schema", {})

            # Check if schema references a model with PII
            if "$ref" in schema:
                # Would need to resolve ref and check - simplified here
                return True

            # Check properties directly
            properties = schema.get("properties", {})
            for prop_name in properties.keys():
                prop_lower = prop_name.lower()
                for pattern in self.PII_PATTERNS.values():
                    if re.search(pattern, prop_lower, re.IGNORECASE):
                        return True

        return False

    def _check_password_exposure(
        self, schemas: Dict[str, Any], paths: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Check for password fields in responses."""
        issues = []

        # Check schemas
        for schema_name, schema_def in schemas.items():
            properties = schema_def.get("properties", {})
            for prop_name, prop_def in properties.items():
                if re.search(r"password|passwd|pwd", prop_name, re.IGNORECASE):
                    # Check if it's write-only
                    if not prop_def.get("writeOnly", False):
                        issues.append(
                            SecurityIssue(
                                id=f"data-password-exposure-{schema_name}-{prop_name}",
                                title="Password Field Not Write-Only",
                                description=f"Password field '{prop_name}' in schema '{schema_name}' is not marked as writeOnly",
                                severity=SecuritySeverity.CRITICAL,
                                owasp_category=OWASPCategory.BROKEN_OBJECT_PROPERTY_AUTH,
                                location={"schema": schema_name, "field": prop_name},
                                recommendation="Mark password fields as 'writeOnly: true' to prevent them from being returned in responses",
                                remediation_example='{\n  "password": {\n    "type": "string",\n    "writeOnly": true\n  }\n}',
                                cwe_id="CWE-256",
                                references=[
                                    "https://swagger.io/docs/specification/data-models/data-types/#readonly-writeonly"
                                ],
                            )
                        )

        return issues

    def _check_excessive_data_exposure(
        self, paths: Dict[str, Any], schemas: Dict[str, Any]
    ) -> List[SecurityIssue]:
        """Check for excessive data exposure patterns."""
        issues = []

        # Look for endpoints that return entire objects without filtering
        for path, path_item in paths.items():
            if method := path_item.get("get"):
                responses = method.get("responses", {})
                success_response = responses.get("200") or responses.get("201")

                if success_response:
                    # Check if response has many fields (potential over-exposure)
                    content = success_response.get("content", {})
                    for media_type, media_def in content.items():
                        schema = media_def.get("schema", {})

                        # Count properties if schema is inline
                        properties = schema.get("properties", {})
                        if len(properties) > 15:  # Threshold for "too many fields"
                            issues.append(
                                SecurityIssue(
                                    id=f"data-excessive-exposure-{path}",
                                    title="Potential Excessive Data Exposure",
                                    description=f"GET {path} returns {len(properties)} fields - consider implementing field filtering",
                                    severity=SecuritySeverity.MEDIUM,
                                    owasp_category=OWASPCategory.BROKEN_OBJECT_PROPERTY_AUTH,
                                    location={"path": path, "method": "get"},
                                    recommendation="Implement field filtering (sparse fieldsets) to allow clients to request only needed data",
                                    cwe_id="CWE-213",
                                )
                            )

        return issues

    def _calculate_score(
        self,
        pii_fields: List[Dict[str, Any]],
        sensitive_fields: List[Dict[str, Any]],
        uses_https: bool,
        issues: List[SecurityIssue],
    ) -> float:
        """Calculate data protection score (0-100)."""
        base_score = 70.0

        # Bonus for HTTPS
        if uses_https:
            base_score += 20
        else:
            base_score -= 30

        # Penalty for exposed PII (if not properly protected)
        if pii_fields:
            base_score -= min(20, len(pii_fields) * 2)

        # Penalty for sensitive data issues
        if sensitive_fields:
            base_score -= min(15, len(sensitive_fields) * 3)

        # Deduct for issues
        severity_penalties = {
            SecuritySeverity.CRITICAL: 20,
            SecuritySeverity.HIGH: 10,
            SecuritySeverity.MEDIUM: 5,
            SecuritySeverity.LOW: 2,
            SecuritySeverity.INFO: 1,
        }

        penalty = sum(severity_penalties.get(issue.severity, 0) for issue in issues)

        return max(0.0, min(100.0, base_score - penalty))
