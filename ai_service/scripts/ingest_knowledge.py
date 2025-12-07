#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script for SchemaSculpt AI

This script ingests security knowledge into the dual knowledge bases:
1. Attacker KB - Offensive security expertise
2. Governance KB - Risk frameworks and compliance

Usage:
    python ingest_knowledge.py --kb attacker --source owasp
    python ingest_knowledge.py --kb governance --source cvss
    python ingest_knowledge.py --all  # Ingest everything
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.rag_service import RAGService
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeIngester:
    """Handles ingestion of security knowledge into RAG system."""

    def __init__(self):
        self.rag_service = RAGService()
        self.knowledge_base_dir = Path(settings.ai_service_data_dir) / "knowledge_base"
        self.raw_docs_dir = self.knowledge_base_dir / "raw_documents"

    def ingest_owasp_api_security(self) -> Dict[str, Any]:
        """
        Ingest OWASP API Security Top 10 knowledge.

        Creates documents covering:
        - API1: Broken Object Level Authorization
        - API2: Broken Authentication
        - API3: Broken Object Property Level Authorization
        - API4: Unrestricted Resource Consumption
        - API5: Broken Function Level Authorization
        - API6: Unrestricted Access to Sensitive Business Flows
        - API7: Server Side Request Forgery
        - API8: Security Misconfiguration
        - API9: Improper Inventory Management
        - API10: Unsafe Consumption of APIs
        """
        logger.info("Ingesting OWASP API Security Top 10 knowledge...")

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

            # API6: Unrestricted Access to Sensitive Business Flows
            """OWASP API6:2023 - Unrestricted Access to Sensitive Business Flows

Description: APIs vulnerable to this risk expose a business flow (e.g., buying tickets, posting comments) without compensating for how the functionality could harm the business if used excessively in an automated manner.

Attack Patterns:
- Automated ticket/product scalping using bots
- Mass comment/review spam
- Referral bonus abuse through automation
- Inventory manipulation through rapid purchases
- Vote/rating manipulation

Exploitation Techniques:
1. Identify critical business flows (purchase, registration, voting)
2. Automate the flow using scripts/bots
3. Test for CAPTCHA, rate limiting, or bot detection
4. Exploit lack of controls for financial gain or disruption

Real-World Impact: Revenue loss, legitimate users unable to access services, reputation damage, market manipulation.

Detection: Critical business operations without rate limiting, CAPTCHA, or device fingerprinting.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) depending on business impact.""",

            # API7: Server Side Request Forgery
            """OWASP API7:2023 - Server Side Request Forgery (SSRF)

Description: Server-Side Request Forgery occurs when an API fetches a remote resource without validating the user-supplied URI. Attackers can force the application to send crafted requests to unexpected destinations, even when protected by a firewall or VPN.

Attack Patterns:
- Internal network scanning through API
- Accessing cloud metadata endpoints (AWS: 169.254.169.254)
- Bypassing firewall/IP restrictions
- Reading local files through file:// protocol

Exploitation Techniques:
1. Identify endpoints accepting URLs (webhooks, import functions, proxies)
2. Test with internal IP ranges (192.168.x.x, 10.x.x.x, 127.0.0.1)
3. Attempt cloud metadata access (AWS, Azure, GCP metadata endpoints)
4. Try protocol smuggling (file://, gopher://, dict://)

Real-World Impact: Internal network compromise, cloud credential theft, sensitive data exposure, RCE through protocol exploitation.

Detection: API endpoints accepting URLs without proper validation and sanitization.

CVSS Score: HIGH (7.0-8.9) to CRITICAL (9.0+) for cloud metadata access.""",

            # API8: Security Misconfiguration
            """OWASP API8:2023 - Security Misconfiguration

Description: APIs and supporting systems typically contain complex configurations, meant to make the APIs more customizable. Software and DevOps engineers can miss these configurations, or don't follow security best practices when it comes to configuration, opening the door for different types of attacks.

Common Misconfigurations:
- Missing security headers (CORS, CSP, HSTS)
- Verbose error messages exposing stack traces
- Unnecessary HTTP methods enabled (TRACE, OPTIONS abuse)
- Default credentials on services
- Misconfigured CORS allowing any origin
- TLS misconfiguration or missing

Exploitation Techniques:
1. Check HTTP response headers for security controls
2. Trigger errors to reveal stack traces/internal paths
3. Test CORS configuration with different origins
4. Enumerate HTTP methods (OPTIONS request)
5. Check for default credentials on admin panels

Real-World Impact: Information disclosure, XSS through CORS misconfiguration, credential exposure, unauthorized access.

Detection: Missing security headers, detailed error messages in production, overly permissive CORS policies.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) depending on exposed information.""",

            # API9: Improper Inventory Management
            """OWASP API9:2023 - Improper Inventory Management

Description: APIs tend to expose more endpoints than traditional web applications, making proper documentation important. A proper inventory of API versions and exposed endpoints is important to mitigate issues such as deprecated API versions and exposed debug endpoints.

Attack Patterns:
- Accessing old, unpatched API versions (v1 vs v2)
- Discovering hidden/debug endpoints
- Exploiting deprecated endpoints with known vulnerabilities
- Accessing staging/dev environments in production

Exploitation Techniques:
1. Enumerate API versions (/api/v1, /api/v2, /api/old)
2. Test for debug/internal endpoints (/debug, /internal, /_health)
3. Access documentation endpoints (swagger, openapi, graphql playground)
4. Check for environment confusion (dev/staging accessible)

Real-World Impact: Exploitation of known vulnerabilities in old versions, sensitive debug information exposure, backdoor access through dev endpoints.

Detection: Multiple API versions in production, accessible debug endpoints, outdated API documentation.

CVSS Score: MEDIUM (4.0-6.9) to HIGH (7.0-8.9) for exploitable old versions.""",

            # API10: Unsafe Consumption of APIs
            """OWASP API10:2023 - Unsafe Consumption of APIs

Description: Developers tend to trust data received from third-party APIs more than user input. This is especially true for APIs offered by well-known companies. Weak security standards in third-party APIs can be exploited to compromise the consuming API.

Attack Patterns:
- Injection attacks through third-party API responses
- Data poisoning in consumed external APIs
- Malicious redirects through trusted APIs
- XML/JSON parsing vulnerabilities from external sources

Exploitation Techniques:
1. Identify third-party API integrations
2. Test if external API responses are validated/sanitized
3. Attempt injection through compromised external API
4. Exploit trust relationships between services

Real-World Impact: SQL injection, XSS, XXE through trusted sources, supply chain attacks, data integrity compromise.

Detection: Missing input validation on external API responses, blind trust in third-party data.

CVSS Score: HIGH (7.0-8.9) when external data flows to sensitive operations."""
        ]

        metadatas = [
            {"source": "OWASP API Security Top 10", "category": "API1:2023 BOLA", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API2:2023 Authentication", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API3:2023 Property Authorization", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API4:2023 Resource Consumption", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API5:2023 Function Authorization", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API6:2023 Business Flow", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API7:2023 SSRF", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API8:2023 Misconfiguration", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API9:2023 Inventory Management", "type": "vulnerability_pattern"},
            {"source": "OWASP API Security Top 10", "category": "API10:2023 Unsafe Consumption", "type": "vulnerability_pattern"},
        ]

        result = self.rag_service.ingest_documents(
            documents=documents,
            metadatas=metadatas,
            knowledge_base="attacker"
        )

        logger.info(f"OWASP API Security ingestion result: {result}")
        return result

    def ingest_mitre_attack_patterns(self) -> Dict[str, Any]:
        """
        Ingest MITRE ATT&CK patterns relevant to API security.

        Focuses on tactics applicable to API exploitation.
        """
        logger.info("Ingesting MITRE ATT&CK patterns...")

        documents = [
            """MITRE ATT&CK - Initial Access via API Exploitation (T1190)

Technique: Exploit Public-Facing Application

Description: Adversaries may exploit weaknesses in Internet-facing APIs to gain initial access to systems. This includes exploiting injection vulnerabilities, authentication bypasses, or authorization flaws in APIs.

API-Specific Tactics:
- Exploiting unauthenticated API endpoints
- Bypassing weak authentication mechanisms
- Leveraging default credentials on API gateways
- Exploiting SSRF in API proxy endpoints

Detection: Monitor for unusual API traffic patterns, authentication failures, access to sensitive endpoints from new IPs, exploitation attempts in API logs.""",

            """MITRE ATT&CK - Credential Access via API (T1552.001)

Technique: Unsecured Credentials in Files

Description: Adversaries may search for API keys, tokens, and credentials stored in insecure locations such as configuration files, code repositories, or environment variables.

API-Specific Tactics:
- Extracting hardcoded API keys from client-side code
- Discovering credentials in exposed .env files
- Finding tokens in version control history (GitHub secrets)
- Accessing credentials through exposed configuration endpoints

Detection: Monitor for access to configuration endpoints, unusual repository cloning activity, credential validation attempts from new locations.""",

            """MITRE ATT&CK - Privilege Escalation in APIs (T1078)

Technique: Valid Accounts with Escalated Privileges

Description: Adversaries may obtain credentials of accounts with elevated privileges through API exploitation, then use those accounts to expand access.

API-Specific Tactics:
- Exploiting mass assignment to add admin privileges
- JWT token manipulation to escalate roles
- Horizontal privilege escalation through BOLA
- Exploiting function-level authorization flaws

Detection: Monitor for role/permission changes through API, unusual administrative API calls, privilege modifications outside normal workflows.""",

            """MITRE ATT&CK - Data Exfiltration via API (T1020)

Technique: Automated Exfiltration

Description: Adversaries may use automated methods to collect and exfiltrate sensitive data through APIs, often using legitimate API functionality at scale.

API-Specific Tactics:
- Mass data extraction through BOLA exploitation
- Using pagination flaws to extract full datasets
- Exploiting excessive data exposure in responses
- Leveraging export functionality for bulk data theft

Detection: Monitor for unusual volume of API requests, large response sizes, access to many different resources in short time, export functionality abuse."""
        ]

        metadatas = [
            {"source": "MITRE ATT&CK", "category": "Initial Access", "technique": "T1190", "type": "attack_pattern"},
            {"source": "MITRE ATT&CK", "category": "Credential Access", "technique": "T1552.001", "type": "attack_pattern"},
            {"source": "MITRE ATT&CK", "category": "Privilege Escalation", "technique": "T1078", "type": "attack_pattern"},
            {"source": "MITRE ATT&CK", "category": "Exfiltration", "technique": "T1020", "type": "attack_pattern"},
        ]

        result = self.rag_service.ingest_documents(
            documents=documents,
            metadatas=metadatas,
            knowledge_base="attacker"
        )

        logger.info(f"MITRE ATT&CK ingestion result: {result}")
        return result

    def ingest_cvss_knowledge(self) -> Dict[str, Any]:
        """
        Ingest CVSS (Common Vulnerability Scoring System) framework knowledge.
        """
        logger.info("Ingesting CVSS risk scoring framework...")

        documents = [
            """CVSS v3.1 - Common Vulnerability Scoring System

Overview: CVSS provides a standardized method for rating the severity of security vulnerabilities. Scores range from 0.0 to 10.0, with higher scores indicating more severe vulnerabilities.

Severity Ratings:
- CRITICAL: 9.0 - 10.0
- HIGH: 7.0 - 8.9
- MEDIUM: 4.0 - 6.9
- LOW: 0.1 - 3.9

Base Metric Groups:

1. Exploitability Metrics:
   - Attack Vector (AV): Network (N), Adjacent (A), Local (L), Physical (P)
   - Attack Complexity (AC): Low (L), High (H)
   - Privileges Required (PR): None (N), Low (L), High (H)
   - User Interaction (UI): None (N), Required (R)

2. Impact Metrics:
   - Confidentiality Impact (C): High (H), Low (L), None (N)
   - Integrity Impact (I): High (H), Low (L), None (N)
   - Availability Impact (A): High (H), Low (L), None (N)

3. Scope (S): Unchanged (U), Changed (C)

API Security Scoring Guidelines:
- Broken Authentication: CVSS 9.0+ (AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)
- BOLA/IDOR: CVSS 7.0-8.5 depending on data sensitivity
- SSRF with cloud metadata access: CVSS 9.0+
- Missing rate limiting: CVSS 5.0-7.0 depending on business impact""",

            """CVSS v3.1 - API Vulnerability Scoring Examples

Example 1: Broken Object Level Authorization (BOLA)
- Attack Vector: Network (exploitable remotely)
- Attack Complexity: Low (no special conditions)
- Privileges Required: Low (requires authenticated user)
- User Interaction: None
- Confidentiality: High (access to all user data)
- Integrity: Low (can read but not modify)
- Availability: None
- Scope: Unchanged
CVSS Score: 7.7 (HIGH)

Example 2: Unauthenticated Admin Access
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None (no authentication)
- User Interaction: None
- Confidentiality: High
- Integrity: High (can modify system)
- Availability: High (can disrupt service)
- Scope: Changed (affects resources beyond vulnerable component)
CVSS Score: 10.0 (CRITICAL)

Example 3: Missing Rate Limiting on Login
- Attack Vector: Network
- Attack Complexity: Low
- Privileges Required: None
- User Interaction: None
- Confidentiality: Low (credential bruteforce possible but time-consuming)
- Integrity: None
- Availability: Low (potential for resource exhaustion)
- Scope: Unchanged
CVSS Score: 5.3 (MEDIUM)"""
        ]

        metadatas = [
            {"source": "CVSS v3.1", "category": "Risk Scoring", "type": "framework"},
            {"source": "CVSS v3.1", "category": "API Examples", "type": "framework"},
        ]

        result = self.rag_service.ingest_documents(
            documents=documents,
            metadatas=metadatas,
            knowledge_base="governance"
        )

        logger.info(f"CVSS ingestion result: {result}")
        return result

    def ingest_dread_framework(self) -> Dict[str, Any]:
        """
        Ingest DREAD risk assessment framework.
        """
        logger.info("Ingesting DREAD risk framework...")

        documents = [
            """DREAD Risk Assessment Framework

Overview: DREAD is a risk assessment model originally developed by Microsoft. It provides a mnemonic for risk rating based on five categories. Each category is scored 1-10, and the final risk score is the average.

DREAD Categories:

1. Damage Potential (D): How severe is the impact if exploited?
   - 10: Complete system compromise, total data breach
   - 7-9: Significant data exposure, privilege escalation
   - 4-6: Limited data exposure, single account compromise
   - 1-3: Minimal impact, information disclosure only

2. Reproducibility (R): How easy is it to reproduce the attack?
   - 10: Works every time, no special conditions
   - 7-9: Works most of the time with minimal effort
   - 4-6: Requires specific timing or conditions
   - 1-3: Very difficult to reproduce, requires extensive knowledge

3. Exploitability (E): How easy is it to launch the attack?
   - 10: No authentication needed, single HTTP request
   - 7-9: Requires low-level authentication or simple tools
   - 4-6: Requires custom tools or advanced privileges
   - 1-3: Requires insider access or sophisticated techniques

4. Affected Users (A): How many users are impacted?
   - 10: All users, entire system
   - 7-9: Large subset of users
   - 4-6: Some users, specific user groups
   - 1-3: Individual users or administrators only

5. Discoverability (D): How easy is it to find the vulnerability?
   - 10: Publicly known, documented in OWASP
   - 7-9: Easy to discover with basic testing
   - 4-6: Requires deeper analysis or tools
   - 1-3: Very difficult to find, theoretical

API Security DREAD Scoring Example:

BOLA Vulnerability:
- Damage: 8 (access to sensitive user data)
- Reproducibility: 10 (works every time)
- Exploitability: 9 (just change ID in URL)
- Affected Users: 9 (affects all users)
- Discoverability: 8 (well-known pattern)
DREAD Score: 8.8 / 10 (HIGH RISK)"""
        ]

        metadatas = [
            {"source": "DREAD Framework", "category": "Risk Assessment", "type": "framework"},
        ]

        result = self.rag_service.ingest_documents(
            documents=documents,
            metadatas=metadatas,
            knowledge_base="governance"
        )

        logger.info(f"DREAD ingestion result: {result}")
        return result

    def ingest_compliance_frameworks(self) -> Dict[str, Any]:
        """
        Ingest compliance and regulatory framework knowledge.
        """
        logger.info("Ingesting compliance frameworks...")

        documents = [
            """GDPR - API Security Requirements

General Data Protection Regulation (EU)

Key API Security Requirements:

1. Data Protection by Design (Article 25):
   - APIs must implement privacy and security controls by default
   - Minimize data collection (only necessary fields)
   - Implement access controls and encryption

2. Right to Access (Article 15):
   - APIs must provide user data export functionality
   - Secure authentication required for data access
   - Audit logs for all data access requests

3. Right to Erasure (Article 17):
   - APIs must support complete data deletion
   - Cascade deletion across all systems
   - Verify data removal from backups

4. Data Breach Notification (Article 33):
   - Detect and log API security incidents
   - 72-hour notification requirement for breaches
   - Implement API monitoring and alerting

5. Data Portability (Article 20):
   - APIs must export data in machine-readable format
   - Structured, commonly used format (JSON, XML)

API Violations Leading to GDPR Fines:
- BOLA allowing unauthorized access to personal data
- Missing encryption on sensitive data transmission
- Excessive data exposure in API responses
- Lack of consent management in API design
- Inadequate API authentication mechanisms

Penalties: Up to €20 million or 4% of global annual revenue (whichever is higher)""",

            """PCI-DSS - Payment API Security Requirements

Payment Card Industry Data Security Standard

Requirements for APIs Handling Payment Data:

Requirement 1: Install and maintain firewall configuration
- API gateway security controls
- Network segmentation for payment APIs

Requirement 2: Default passwords and security parameters
- No default credentials in API configurations
- Secure API key generation and rotation

Requirement 3: Protect stored cardholder data
- Encrypt payment data at rest and in transit
- Never store CVV codes via API
- Tokenization for sensitive data

Requirement 4: Encrypt transmission of cardholder data
- TLS 1.2+ for all payment APIs
- Strong cipher suites only
- Certificate validation

Requirement 6: Develop and maintain secure systems
- Secure API development practices
- Regular security testing of payment APIs
- Patch vulnerabilities promptly

Requirement 8: Identify and authenticate access
- Multi-factor authentication for payment APIs
- Strong API key management
- No shared authentication credentials

Requirement 10: Track and monitor all access
- Log all API access to payment data
- Secure audit log storage
- Regular log review

API Violations:
- Exposing credit card data in API responses
- Missing encryption on payment endpoints
- Weak authentication on payment APIs
- Insufficient API logging""",

            """HIPAA - Healthcare API Security Requirements

Health Insurance Portability and Accountability Act (US)

Key Security Requirements for Healthcare APIs:

1. Access Control (164.312(a)(1)):
   - Unique user identification for API access
   - Emergency access procedures
   - Automatic logoff from API sessions
   - Encryption and decryption of ePHI

2. Audit Controls (164.312(b)):
   - Log all API access to health information
   - Track who accessed what data and when
   - Detect unauthorized API access attempts

3. Integrity (164.312(c)(1)):
   - Ensure ePHI transmitted via API is not altered
   - Authentication of API endpoints
   - Detect tampering of health data

4. Transmission Security (164.312(e)(1)):
   - Encrypt ePHI transmitted over networks
   - TLS for all healthcare APIs
   - Integrity controls during transmission

API Security Controls Required:
- Role-based access control (doctor, nurse, admin)
- Patient consent management via API
- Audit logging with tamper protection
- Encryption of PHI at rest and in transit
- Secure API authentication (OAuth 2.0 recommended)

Common HIPAA Violations in APIs:
- BOLA exposing patient records
- Missing encryption on health data endpoints
- Inadequate API access logging
- Lack of patient consent verification
- Excessive data exposure of PHI

Penalties: Up to $1.5 million per violation category per year"""
        ]

        metadatas = [
            {"source": "GDPR", "category": "Compliance", "type": "regulatory_framework"},
            {"source": "PCI-DSS", "category": "Compliance", "type": "regulatory_framework"},
            {"source": "HIPAA", "category": "Compliance", "type": "regulatory_framework"},
        ]

        result = self.rag_service.ingest_documents(
            documents=documents,
            metadatas=metadatas,
            knowledge_base="governance"
        )

        logger.info(f"Compliance frameworks ingestion result: {result}")
        return result

    def ingest_all(self) -> Dict[str, Any]:
        """Ingest all knowledge sources."""
        logger.info("Starting full knowledge base ingestion...")

        results = {
            "owasp": self.ingest_owasp_api_security(),
            "mitre": self.ingest_mitre_attack_patterns(),
            "cvss": self.ingest_cvss_knowledge(),
            "dread": self.ingest_dread_framework(),
            "compliance": self.ingest_compliance_frameworks()
        }

        # Summary
        total_docs = sum(r.get("documents_added", 0) for r in results.values())
        logger.info(f"✅ Ingestion complete! Total documents ingested: {total_docs}")

        return results


def main():
    parser = argparse.ArgumentParser(
        description="Ingest security knowledge into SchemaSculpt AI knowledge bases"
    )
    parser.add_argument(
        "--kb",
        choices=["attacker", "governance"],
        help="Target knowledge base (attacker or governance)"
    )
    parser.add_argument(
        "--source",
        choices=["owasp", "mitre", "cvss", "dread", "compliance"],
        help="Knowledge source to ingest"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Ingest all knowledge sources"
    )

    args = parser.parse_args()

    ingester = KnowledgeIngester()

    if args.all:
        results = ingester.ingest_all()
        print("\n=== Ingestion Summary ===")
        for source, result in results.items():
            status = "✅" if result.get("success") else "❌"
            docs = result.get("documents_added", 0)
            print(f"{status} {source.upper()}: {docs} documents")
    elif args.source:
        if args.source == "owasp":
            result = ingester.ingest_owasp_api_security()
        elif args.source == "mitre":
            result = ingester.ingest_mitre_attack_patterns()
        elif args.source == "cvss":
            result = ingester.ingest_cvss_knowledge()
        elif args.source == "dread":
            result = ingester.ingest_dread_framework()
        elif args.source == "compliance":
            result = ingester.ingest_compliance_frameworks()

        print(f"\n{'✅' if result.get('success') else '❌'} {result}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
