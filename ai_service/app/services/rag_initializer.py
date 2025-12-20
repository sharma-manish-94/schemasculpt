"""
RAG Knowledge Base Initializer for SchemaSculpt AI

This module handles automatic initialization and population of RAG knowledge bases
on application startup. It consolidates all knowledge ingestion logic in one place.

Two Specialized Knowledge Bases:
1. Attacker Knowledge Base: Offensive security (OWASP, MITRE ATT&CK)
2. Governance Knowledge Base: Risk frameworks (CVSS, DREAD), compliance (GDPR, HIPAA, PCI-DSS)
"""

from pathlib import Path
from typing import Any, Dict

from ..core.config import settings
from ..core.logging import get_logger
from .rag_service import RAGService

logger = get_logger("rag_initializer")


class RAGInitializer:
    """
    Handles initialization and population of RAG knowledge bases.

    Automatically called on application startup to ensure knowledge bases
    are populated with security expertise.
    """

    def __init__(self):
        self.rag_service = RAGService()
        self.knowledge_base_dir = Path(settings.ai_service_data_dir) / "knowledge_base"
        self._initialized = False

    async def initialize_knowledge_bases(
        self, force_reingest: bool = False
    ) -> Dict[str, Any]:
        """
        Initialize both knowledge bases with security knowledge.

        Args:
            force_reingest: If True, re-ingest all documents even if KBs exist

        Returns:
            Dictionary with initialization results
        """
        if self._initialized and not force_reingest:
            logger.info("RAG knowledge bases already initialized")
            return {"status": "already_initialized", "skipped": True}

        logger.info("Starting RAG knowledge base initialization...")

        results = {
            "status": "success",
            "attacker_kb": {},
            "governance_kb": {},
            "total_documents": 0,
        }

        try:
            # Check if knowledge bases need initialization
            stats = await self.rag_service.get_knowledge_base_stats()

            attacker_needs_init = (
                not stats.get("attacker_kb", {}).get("available")
                or stats.get("attacker_kb", {}).get("document_count", 0) == 0
                or force_reingest
            )

            governance_needs_init = (
                not stats.get("governance_kb", {}).get("available")
                or stats.get("governance_kb", {}).get("document_count", 0) == 0
                or force_reingest
            )

            # Initialize Attacker Knowledge Base
            if attacker_needs_init:
                logger.info("Initializing Attacker Knowledge Base...")
                attacker_result = await self._initialize_attacker_kb()
                results["attacker_kb"] = attacker_result
                results["total_documents"] += attacker_result.get("documents_added", 0)
            else:
                logger.info("Attacker KB already populated, skipping...")
                results["attacker_kb"] = {"status": "skipped", "documents_added": 0}

            # Initialize Governance Knowledge Base
            if governance_needs_init:
                logger.info("Initializing Governance Knowledge Base...")
                governance_result = await self._initialize_governance_kb()
                results["governance_kb"] = governance_result
                results["total_documents"] += governance_result.get(
                    "documents_added", 0
                )
            else:
                logger.info("Governance KB already populated, skipping...")
                results["governance_kb"] = {"status": "skipped", "documents_added": 0}

            self._initialized = True
            logger.info(
                f"RAG initialization complete. Total documents: {results['total_documents']}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize RAG knowledge bases: {e}")
            results["status"] = "error"
            results["error"] = str(e)

        return results

    async def _initialize_attacker_kb(self) -> Dict[str, Any]:
        """
        Initialize Attacker Knowledge Base with offensive security knowledge.

        Includes:
        - OWASP API Security Top 10
        - MITRE ATT&CK patterns
        """
        total_docs = 0

        # Ingest OWASP API Security Top 10
        logger.info("Ingesting OWASP API Security Top 10...")
        owasp_result = self._ingest_owasp_api_security()
        total_docs += owasp_result.get("documents_added", 0)

        # Ingest MITRE ATT&CK patterns
        logger.info("Ingesting MITRE ATT&CK patterns...")
        mitre_result = self._ingest_mitre_attack_patterns()
        total_docs += mitre_result.get("documents_added", 0)

        return {
            "status": "success",
            "documents_added": total_docs,
            "sources": ["OWASP API Security Top 10", "MITRE ATT&CK"],
        }

    async def _initialize_governance_kb(self) -> Dict[str, Any]:
        """
        Initialize Governance Knowledge Base with risk frameworks and compliance.

        Includes:
        - CVSS scoring framework
        - DREAD risk assessment
        - GDPR, HIPAA, PCI-DSS compliance requirements
        """
        total_docs = 0

        # Ingest CVSS knowledge
        logger.info("Ingesting CVSS framework...")
        cvss_result = self._ingest_cvss_knowledge()
        total_docs += cvss_result.get("documents_added", 0)

        # Ingest DREAD framework
        logger.info("Ingesting DREAD framework...")
        dread_result = self._ingest_dread_framework()
        total_docs += dread_result.get("documents_added", 0)

        # Ingest compliance frameworks
        logger.info("Ingesting compliance frameworks...")
        compliance_result = self._ingest_compliance_frameworks()
        total_docs += compliance_result.get("documents_added", 0)

        return {
            "status": "success",
            "documents_added": total_docs,
            "sources": ["CVSS v3.1", "DREAD", "GDPR", "HIPAA", "PCI-DSS"],
        }

    def _ingest_owasp_api_security(self) -> Dict[str, Any]:
        """Ingest OWASP API Security Top 10 knowledge."""
        documents = [
            # API1: Broken Object Level Authorization
            """OWASP API1:2023 - Broken Object Level Authorization (BOLA)

Description: APIs tend to expose endpoints that handle object identifiers, creating a wide attack surface of Object Level Access Control issues. Object level authorization checks should be considered in every function that accesses a data source using an ID from the user.

Attack Pattern: Attacker manipulates object IDs in API requests to access resources belonging to other users. Common in RESTful APIs with predictable resource IDs (/api/users/123, /api/orders/456).

Exploitation Technique:
1. Identify API endpoints with object IDs (user IDs, order IDs, document IDs)
2. Test authorization by changing IDs to other users' resources
3. Check if API validates ownership before returning data
4. Exploit by iterating through ID ranges for mass data extraction

Real-World Impact: Unauthorized access to sensitive user data, financial records, private documents. Can lead to complete account takeover or data breach.

Detection: Look for endpoints with path/query parameters containing IDs without proper authorization checks. Test by swapping IDs between different user contexts.

CVSS Score: Typically HIGH (7.0-8.9) to CRITICAL (9.0+) depending on data sensitivity.""",
            # API2: Broken Authentication
            """OWASP API2:2023 - Broken Authentication

Description: Authentication mechanisms are often implemented incorrectly, allowing attackers to compromise authentication tokens or exploit implementation flaws to assume other users' identities temporarily or permanently.

Attack Patterns:
- Credential stuffing using leaked password databases
- Brute force attacks on login endpoints without rate limiting
- JWT token manipulation (weak secret, algorithm confusion, no signature verification)
- Missing token expiration or refresh token abuse
- Insecure password reset flows (predictable tokens, no validation)

Exploitation Techniques:
1. Test for rate limiting on authentication endpoints
2. Analyze JWT tokens for weak secrets or missing validation
3. Test password reset for predictable tokens or timing attacks
4. Check for session fixation vulnerabilities
5. Test multi-factor authentication bypass techniques

Real-World Impact: Complete account takeover, unauthorized access to all user data, privilege escalation to administrator accounts.

Detection: Missing rate limiting, weak JWT implementation, predictable session tokens, no MFA enforcement for sensitive operations.

CVSS Score: CRITICAL (9.0+) when authentication can be fully bypassed.""",
            # API3: Broken Object Property Level Authorization
            """OWASP API3:2023 - Broken Object Property Level Authorization

Description: This combines Excessive Data Exposure and Mass Assignment. APIs may expose more object properties than users should access (read) or allow modification of properties users shouldn't change (write).

Attack Patterns:
- Mass Assignment: Adding unauthorized properties to API requests (isAdmin=true, role=admin)
- Excessive Data Exposure: API returns full objects when only partial data should be exposed
- Property manipulation to gain privileges or access sensitive fields

Exploitation Techniques:
1. Analyze API responses to identify hidden/sensitive properties
2. Test adding extra properties to update requests (mass assignment)
3. Attempt to modify role, permission, or status fields
4. Check if API validates property-level permissions

Real-World Impact: Privilege escalation, unauthorized data disclosure, account takeover through role manipulation.

Detection: API endpoints that accept generic objects without property whitelisting, endpoints returning full database objects without filtering.

CVSS Score: HIGH (7.0-8.9) for privilege escalation scenarios.""",
            # API4: Unrestricted Resource Consumption
            """OWASP API4:2023 - Unrestricted Resource Consumption

Description: Satisfying API requests requires resources such as network bandwidth, CPU, memory, and storage. APIs often don't impose restrictions on the size or number of resources that can be requested, exposing them to Denial of Service (DoS) and performance issues.

Attack Patterns:
- Sending large payloads to exhaust server memory
- Requesting expensive operations repeatedly (complex queries, file generation)
- Uploading large files without size limits
- No pagination limits allowing retrieval of millions of records

Exploitation Techniques:
1. Test file upload size limits (send 1GB+ files)
2. Request large result sets without pagination
3. Trigger expensive database queries or computations
4. Exhaust rate limits to check enforcement

Real-World Impact: Service unavailability, increased infrastructure costs, degraded performance for legitimate users.

Detection: Missing rate limiting, no file size restrictions, no pagination, lack of query complexity limits.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) for critical availability impact.""",
            # API5: Broken Function Level Authorization
            """OWASP API5:2023 - Broken Function Level Authorization

Description: Complex access control policies with different hierarchies, groups, and roles, and unclear separation between administrative and regular functions, tend to lead to authorization flaws. Attackers can gain access to other users' resources and/or administrative functions.

Attack Patterns:
- Regular users accessing admin endpoints by guessing URLs
- Horizontal privilege escalation (user A accessing user B's functions)
- Vertical privilege escalation (user accessing admin functions)
- Missing authorization checks on sensitive operations

Exploitation Techniques:
1. Identify admin/privileged endpoints (common patterns: /admin, /api/admin, DELETE/PUT methods)
2. Test access with regular user credentials
3. Check if API validates user roles before executing functions
4. Test HTTP method manipulation (POST to DELETE)

Real-World Impact: Complete system compromise, data manipulation, unauthorized administrative actions, privilege escalation.

Detection: Missing role/permission checks on sensitive endpoints, endpoints with administrative functions accessible to regular users.

CVSS Score: HIGH (7.0-8.9) to CRITICAL (9.0+) for admin access.""",
            # API6-10 abbreviated for space
            """OWASP API6:2023 - Unrestricted Access to Sensitive Business Flows

Description: APIs vulnerable to this risk expose a business flow without compensating for how the functionality could harm the business if used excessively in an automated manner. Common in ticket purchasing, voting systems, and financial transactions.

Attack Patterns: Automated scalping, mass spam, referral abuse, inventory manipulation, vote manipulation.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) depending on business impact.""",
            """OWASP API7:2023 - Server Side Request Forgery (SSRF)

Description: API fetches remote resource without validating user-supplied URI. Attackers force the application to send crafted requests to unexpected destinations.

Attack Patterns: Internal network scanning, cloud metadata access (AWS 169.254.169.254), firewall bypass, local file reading.

CVSS Score: HIGH (7.0-8.9) to CRITICAL (9.0+) for cloud metadata access.""",
            """OWASP API8:2023 - Security Misconfiguration

Description: APIs contain complex configurations that are often missed or not following security best practices.

Common Issues: Missing security headers, verbose errors exposing stack traces, unnecessary HTTP methods, default credentials, misconfigured CORS, missing TLS.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9).""",
            """OWASP API9:2023 - Improper Inventory Management

Description: APIs expose more endpoints than traditional web applications. Lack of proper inventory leads to deprecated versions and debug endpoints being exposed.

Attack Patterns: Accessing old unpatched API versions, discovering hidden debug endpoints, exploiting deprecated endpoints.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) for exploitable old versions.""",
            """OWASP API10:2023 - Unsafe Consumption of APIs

Description: Developers trust data from third-party APIs more than user input. Weak security in third-party APIs can compromise the consuming API.

Attack Patterns: Injection through third-party responses, data poisoning, malicious redirects, parsing vulnerabilities.

CVSS Score: HIGH (7.0-8.9) when external data flows to sensitive operations.""",
        ]

        metadatas = [
            {
                "source": "OWASP API Security Top 10",
                "category": "API1:2023 BOLA",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API2:2023 Authentication",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API3:2023 Property Authorization",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API4:2023 Resource Consumption",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API5:2023 Function Authorization",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API6:2023 Business Flow",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API7:2023 SSRF",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API8:2023 Misconfiguration",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API9:2023 Inventory Management",
                "type": "vulnerability_pattern",
            },
            {
                "source": "OWASP API Security Top 10",
                "category": "API10:2023 Unsafe Consumption",
                "type": "vulnerability_pattern",
            },
        ]

        return self.rag_service.ingest_documents(
            documents=documents, metadatas=metadatas, knowledge_base="attacker"
        )

    def _ingest_mitre_attack_patterns(self) -> Dict[str, Any]:
        """Ingest MITRE ATT&CK patterns relevant to API security."""
        documents = [
            """MITRE ATT&CK - Initial Access via API Exploitation (T1190)

Technique: Exploit Public-Facing Application

Description: Adversaries exploit weaknesses in Internet-facing APIs to gain initial access. Includes injection vulnerabilities, authentication bypasses, authorization flaws.

API-Specific Tactics: Exploiting unauthenticated endpoints, bypassing weak auth, leveraging default credentials, exploiting SSRF.

Detection: Monitor unusual API traffic patterns, authentication failures, access to sensitive endpoints from new IPs.""",
            """MITRE ATT&CK - Credential Access via API (T1552.001)

Technique: Unsecured Credentials in Files

Description: Adversaries search for API keys, tokens, and credentials in insecure locations such as configuration files, code repositories, or environment variables.

API-Specific Tactics: Extracting hardcoded API keys, discovering exposed .env files, finding tokens in version control, accessing exposed configuration endpoints.""",
            """MITRE ATT&CK - Privilege Escalation in APIs (T1078)

Technique: Valid Accounts with Escalated Privileges

Description: Adversaries obtain credentials with elevated privileges through API exploitation, then use those accounts to expand access.

API-Specific Tactics: Mass assignment for admin privileges, JWT token manipulation, horizontal privilege escalation through BOLA, function-level authorization flaws.""",
            """MITRE ATT&CK - Data Exfiltration via API (T1020)

Technique: Automated Exfiltration

Description: Adversaries use automated methods to collect and exfiltrate sensitive data through APIs at scale.

API-Specific Tactics: Mass data extraction through BOLA, pagination flaws for full datasets, excessive data exposure, export functionality abuse.""",
        ]

        metadatas = [
            {
                "source": "MITRE ATT&CK",
                "category": "Initial Access",
                "technique": "T1190",
                "type": "attack_pattern",
            },
            {
                "source": "MITRE ATT&CK",
                "category": "Credential Access",
                "technique": "T1552.001",
                "type": "attack_pattern",
            },
            {
                "source": "MITRE ATT&CK",
                "category": "Privilege Escalation",
                "technique": "T1078",
                "type": "attack_pattern",
            },
            {
                "source": "MITRE ATT&CK",
                "category": "Exfiltration",
                "technique": "T1020",
                "type": "attack_pattern",
            },
        ]

        return self.rag_service.ingest_documents(
            documents=documents, metadatas=metadatas, knowledge_base="attacker"
        )

    def _ingest_cvss_knowledge(self) -> Dict[str, Any]:
        """Ingest CVSS scoring framework knowledge."""
        documents = [
            """CVSS v3.1 - Common Vulnerability Scoring System

Overview: Standardized method for rating vulnerability severity. Scores range from 0.0 to 10.0.

Severity Ratings:
- CRITICAL: 9.0 - 10.0
- HIGH: 7.0 - 8.9
- MEDIUM: 4.0 - 6.9
- LOW: 0.1 - 3.9

Base Metrics:
1. Exploitability: Attack Vector (Network/Adjacent/Local/Physical), Attack Complexity (Low/High), Privileges Required (None/Low/High), User Interaction (None/Required)
2. Impact: Confidentiality Impact (High/Low/None), Integrity Impact (High/Low/None), Availability Impact (High/Low/None)
3. Scope: Unchanged/Changed

API Security Examples:
- Broken Authentication: CVSS 9.0+ (AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)
- BOLA/IDOR: CVSS 7.0-8.5 depending on data sensitivity
- SSRF with cloud metadata: CVSS 9.0+
- Missing rate limiting: CVSS 5.0-7.0 depending on impact"""
        ]

        metadatas = [
            {"source": "CVSS v3.1", "category": "Risk Scoring", "type": "framework"},
        ]

        return self.rag_service.ingest_documents(
            documents=documents, metadatas=metadatas, knowledge_base="governance"
        )

    def _ingest_dread_framework(self) -> Dict[str, Any]:
        """Ingest DREAD risk assessment framework."""
        documents = [
            """DREAD Risk Assessment Framework

Overview: Microsoft risk assessment model. Mnemonic for risk rating based on five categories (1-10 scale each).

Categories:
1. Damage Potential: Impact severity (10=total compromise, 1=minimal)
2. Reproducibility: Ease of reproduction (10=always works, 1=very difficult)
3. Exploitability: Ease of exploitation (10=no auth needed, 1=insider access required)
4. Affected Users: Impact scope (10=all users, 1=individual users)
5. Discoverability: Ease of discovery (10=publicly known, 1=theoretical)

Final Score: Average of all five categories

API Example - BOLA:
- Damage: 8 (sensitive data access)
- Reproducibility: 10 (works every time)
- Exploitability: 9 (just change ID in URL)
- Affected Users: 9 (all users)
- Discoverability: 8 (well-known)
DREAD Score: 8.8/10 (HIGH RISK)"""
        ]

        metadatas = [
            {
                "source": "DREAD Framework",
                "category": "Risk Assessment",
                "type": "framework",
            },
        ]

        return self.rag_service.ingest_documents(
            documents=documents, metadatas=metadatas, knowledge_base="governance"
        )

    def _ingest_compliance_frameworks(self) -> Dict[str, Any]:
        """Ingest compliance and regulatory framework knowledge."""
        documents = [
            """GDPR - API Security Requirements

General Data Protection Regulation (EU)

Key Requirements:
1. Data Protection by Design (Article 25): Privacy/security controls by default, minimize data collection, implement access controls and encryption
2. Right to Access (Article 15): User data export functionality, secure authentication, audit logs
3. Right to Erasure (Article 17): Complete data deletion, cascade deletion, verify backup removal
4. Data Breach Notification (Article 33): Detect and log incidents, 72-hour notification, implement monitoring
5. Data Portability (Article 20): Export in machine-readable format (JSON, XML)

API Violations: BOLA exposing personal data, missing encryption, excessive data exposure, inadequate authentication

Penalties: Up to €20 million or 4% of global annual revenue""",
            """PCI-DSS - Payment API Security Requirements

Payment Card Industry Data Security Standard

Key Requirements:
1. Firewall configuration: API gateway security, network segmentation
2. Default passwords: No default credentials, secure API key generation/rotation
3. Protect cardholder data: Encrypt at rest and in transit, never store CVV, use tokenization
4. Encrypt transmission: TLS 1.2+ for all payment APIs, strong cipher suites, certificate validation
6. Secure systems: Secure development practices, regular security testing, prompt patching
8. Identify and authenticate: MFA for payment APIs, strong key management, no shared credentials
10. Track and monitor: Log all payment data access, secure audit storage, regular review

API Violations: Exposing card data in responses, missing encryption, weak authentication, insufficient logging""",
            """HIPAA - Healthcare API Security Requirements

Health Insurance Portability and Accountability Act (US)

Security Requirements:
1. Access Control (164.312(a)(1)): Unique user identification, emergency access procedures, automatic logoff, encryption/decryption of ePHI
2. Audit Controls (164.312(b)): Log all health information access, track who/what/when, detect unauthorized access
3. Integrity (164.312(c)(1)): Ensure ePHI not altered in transit, endpoint authentication, detect tampering
4. Transmission Security (164.312(e)(1)): Encrypt ePHI over networks, TLS for all healthcare APIs, integrity controls

Required Controls: Role-based access control, patient consent management, audit logging with tamper protection, encryption at rest and in transit, OAuth 2.0 authentication

Common Violations: BOLA exposing patient records, missing encryption, inadequate logging, lack of consent verification, excessive PHI exposure

Penalties: Up to $1.5 million per violation category per year""",
        ]

        metadatas = [
            {
                "source": "GDPR",
                "category": "Compliance",
                "type": "regulatory_framework",
            },
            {
                "source": "PCI-DSS",
                "category": "Compliance",
                "type": "regulatory_framework",
            },
            {
                "source": "HIPAA",
                "category": "Compliance",
                "type": "regulatory_framework",
            },
        ]

        return self.rag_service.ingest_documents(
            documents=documents, metadatas=metadatas, knowledge_base="governance"
        )


# Global instance for application startup
_rag_initializer_instance = None


async def initialize_rag_on_startup(force_reingest: bool = False) -> Dict[str, Any]:
    """
    Initialize RAG knowledge bases on application startup.

    This function is called from the FastAPI lifespan manager in app/main.py

    Args:
        force_reingest: If True, re-ingest all documents even if KBs exist

    Returns:
        Dictionary with initialization results
    """
    global _rag_initializer_instance

    if _rag_initializer_instance is None:
        _rag_initializer_instance = RAGInitializer()

    return await _rag_initializer_instance.initialize_knowledge_bases(force_reingest)


def get_rag_initializer() -> RAGInitializer:
    """Get the global RAG initializer instance."""
    global _rag_initializer_instance

    if _rag_initializer_instance is None:
        _rag_initializer_instance = RAGInitializer()

    return _rag_initializer_instance
