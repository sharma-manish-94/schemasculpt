# ⚔️ Attack Path Simulation Feature

## Overview

The **Attack Path Simulation** (also called "Advanced Security Audit") is SchemaSculpt's most advanced security feature. It uses AI to think like a real attacker, discovering **multi-step attack chains** that combine individual vulnerabilities into high-impact exploits. This goes far beyond simple vulnerability scanning - it finds sophisticated attack patterns that would require expert penetration testing to discover.

## 🎯 What It Does

Unlike basic security scanners that find isolated issues, Attack Path Simulation discovers:

- **Attack Chains**: Multi-step sequences that chain vulnerabilities together
- **Attack Goals**: What an attacker can ultimately achieve (data theft, privilege escalation, etc.)
- **Attack Complexity**: How difficult the attack is to execute
- **Business Impact**: Real-world consequences of successful attacks
- **Remediation Roadmap**: Prioritized actions to break attack chains

### Example Attack Chain

```
Step 1: Enumerate users via public GET /users endpoint (no auth required)
   ↓ Gains: List of valid user IDs
Step 2: Access individual profiles via GET /users/{id} (no ownership check)
   ↓ Gains: Email addresses, phone numbers, roles
Step 3: Identify admin accounts from role field
   ↓ Gains: List of admin user IDs
Step 4: Delete admin accounts via DELETE /users/{id} (missing RBAC)
   ↓ Impact: Privilege escalation, account takeover, system compromise
```

**Result:** Critical risk, 4-step attack chain leading to complete system compromise

## 🚀 How to Use

### Via UI

1. Navigate to the **Security** tab in the main interface
2. Click **"Run Advanced Security Audit"** button
3. Wait for AI analysis (typically 30-90 seconds)
4. Review the generated report with:
   - Executive summary
   - Critical attack chains
   - High-priority attack chains
   - Remediation roadmap

### Via API

```bash
POST /api/v1/sessions/{sessionId}/analysis/attack-path-simulation?analysisDepth=standard&maxChainLength=5
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `analysisDepth` | string | `standard` | Analysis thoroughness: `quick`, `standard`, `comprehensive`, `exhaustive` |
| `maxChainLength` | integer | `5` | Maximum steps in attack chains (1-10) |

**Response:**
```json
{
  "executive_summary": "API has CRITICAL vulnerabilities...",
  "risk_level": "CRITICAL",
  "overall_security_score": 35,
  "critical_chains": [...],
  "high_priority_chains": [...],
  "all_chains": [...],
  "total_chains_found": 12,
  "total_vulnerabilities": 25,
  "vulnerabilities_in_chains": 18,
  "isolated_vulnerabilities": 7,
  "immediate_actions": [...],
  "short_term_actions": [...],
  "long_term_actions": [...]
}
```

## 📋 Report Components

### 1. Executive Summary

High-level overview written for non-technical stakeholders:

```
Your API has CRITICAL security vulnerabilities that could lead to complete
system compromise. We discovered 3 critical attack chains that allow:
- Unauthorized access to all user data (12,000+ accounts)
- Privilege escalation from regular user to admin
- Mass data deletion without authentication

Immediate action required before production deployment.
```

### 2. Risk Level

Overall risk classification:

| Risk Level | Security Score | Meaning |
|------------|----------------|---------|
| 🔴 **CRITICAL** | 0-39 | Immediate remediation required, do not deploy |
| 🟠 **HIGH** | 40-59 | Significant risks, deployment not recommended |
| 🟡 **MEDIUM** | 60-79 | Moderate risks, improvements needed |
| 🟢 **LOW** | 80-100 | Minor issues, acceptable for production |

### 3. Attack Chains

Each attack chain includes:

#### Chain Metadata
- **Name**: Descriptive attack chain name
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW
- **Complexity**: LOW, MEDIUM, HIGH, VERY_HIGH
- **Likelihood**: Probability of exploitation (0-100%)
- **Impact Score**: Business impact rating (0-10)

#### Attack Details
- **Attack Goal**: Ultimate objective (e.g., "Steal all customer PII")
- **Business Impact**: Real-world consequences (e.g., "GDPR violation, $20M fine")
- **Attacker Profile**: Required skill level (e.g., "Script kiddie with basic HTTP knowledge")

#### Attack Steps
Each step in the chain contains:
- **Step Number**: Sequential order
- **Step Type**: `RECONNAISSANCE`, `INITIAL_ACCESS`, `PRIVILEGE_ESCALATION`, `DATA_EXFILTRATION`, `IMPACT`
- **HTTP Method & Endpoint**: API call to make
- **Description**: What the attacker does
- **Technical Detail**: How to exploit the vulnerability
- **Information Gained**: Data obtained from this step
- **Example Request**: Actual exploit code

### 4. Remediation Roadmap

Actionable fixes organized by timeline:

#### Immediate Actions (Do Today)
```
1. Add authentication to public /users endpoint
2. Disable DELETE /users/{id} endpoint until RBAC implemented
3. Remove PII fields from /users response schema
```

#### Short-Term Actions (This Sprint)
```
1. Implement role-based access control (admin, user roles)
2. Add ownership checks for all /users/{id} operations
3. Implement rate limiting on enumeration endpoints
```

#### Long-Term Actions (Next Quarter)
```
1. Migrate to OAuth2 with fine-grained scopes
2. Implement comprehensive audit logging
3. Add automated security testing to CI/CD pipeline
```

## 🔍 Attack Chain Analysis

### Step Types

#### 1. **RECONNAISSANCE**
- **Purpose**: Information gathering
- **Examples**:
  - Enumerate users via `/users` endpoint
  - Discover API endpoints via `/openapi.json`
  - Test for missing authentication

#### 2. **INITIAL_ACCESS**
- **Purpose**: Gain unauthorized access
- **Examples**:
  - Bypass authentication with SQL injection
  - Access resources without credentials
  - Exploit missing authorization checks

#### 3. **PRIVILEGE_ESCALATION**
- **Purpose**: Elevate permissions
- **Examples**:
  - Modify user role via PUT request
  - Access admin endpoints with user credentials
  - Exploit IDOR to access other accounts

#### 4. **DATA_EXFILTRATION**
- **Purpose**: Steal sensitive data
- **Examples**:
  - Download all user records via pagination
  - Access PII without authentication
  - Export database via backup endpoint

#### 5. **IMPACT**
- **Purpose**: Cause damage or disruption
- **Examples**:
  - Delete user accounts
  - Modify critical data
  - Disable system functionality

### Complexity Levels

| Complexity | Description | Attacker Skill |
|------------|-------------|----------------|
| **LOW** | Simple, well-documented exploits | Script kiddie |
| **MEDIUM** | Requires understanding of HTTP/APIs | Intermediate hacker |
| **HIGH** | Needs creativity and chaining | Advanced penetration tester |
| **VERY_HIGH** | Novel attack, deep expertise | APT/nation-state actor |

## 🏗️ Architecture

### AI-Powered Analysis Engine

```
User triggers simulation
         ↓
Load OpenAPI spec from session
         ↓
┌──────────────────────────────┐
│   Vulnerability Discovery    │
│  - Missing auth              │
│  - Broken access control     │
│  - Information disclosure    │
└──────────────────────────────┘
         ↓
┌──────────────────────────────┐
│   Attack Chain Generation    │
│  - AI identifies sequences   │
│  - Calculates exploitability │
│  - Assesses business impact  │
└──────────────────────────────┘
         ↓
┌──────────────────────────────┐
│   Report Generation          │
│  - Executive summary         │
│  - Remediation roadmap       │
│  - Detailed attack steps     │
└──────────────────────────────┘
         ↓
Return comprehensive report
```

### Analysis Depth Options

#### Quick (5-15 seconds)
- Basic vulnerability scan
- 1-2 step attack chains only
- Top 3 critical issues
- **Use case:** Rapid security check during development

#### Standard (30-60 seconds) ⭐ Recommended
- Comprehensive vulnerability discovery
- Up to 5-step attack chains
- Full attack chain analysis
- **Use case:** Pre-deployment security audit

#### Comprehensive (1-3 minutes)
- Deep analysis with AI reasoning
- Up to 7-step attack chains
- Multiple attack vectors per vulnerability
- **Use case:** Production API security assessment

#### Exhaustive (3-10 minutes)
- Maximum thoroughness
- Up to 10-step attack chains
- Explores all possible combinations
- **Use case:** Critical systems, financial/healthcare APIs

### Backend Implementation

**Controller:** `AttackPathController.java`
**Location:** `api/src/main/java/.../controller/AttackPathController.java`

**Endpoint:** `POST /api/v1/sessions/{sessionId}/analysis/attack-path-simulation`

**AI Service:** `AttackPathService` (Python FastAPI)
**Location:** `ai_service/app/services/attack_path_service.py`

**LLM Integration:**
- Uses specialized prompts for adversarial thinking
- Chains reasoning across multiple LLM calls
- Validates attack chains for feasibility

### Frontend Implementation

**Component:** `AdvancedSecurityAudit.js`
**Location:** `ui/src/components/security/AdvancedSecurityAudit.js`

**Report Component:** `AttackPathReport.js`
**Location:** `ui/src/components/security/AttackPathReport.js`

**API Client:** `attackPathService.js`
**Location:** `ui/src/api/attackPathService.js`

## 📊 Example Attack Chains

### Critical: Account Takeover Chain

```yaml
Name: "Admin Account Takeover via Privilege Escalation"
Severity: CRITICAL
Complexity: MEDIUM
Likelihood: 85%
Impact: 10/10

Attack Goal: Gain admin access to entire system
Business Impact: Complete system compromise, data breach, regulatory fines

Steps:
  1. RECONNAISSANCE - GET /users
     Description: List all users without authentication
     Information Gained: Valid user IDs, roles

  2. INITIAL_ACCESS - GET /users/{normalUserId}
     Description: Access own profile
     Information Gained: User object structure, update endpoint

  3. PRIVILEGE_ESCALATION - PUT /users/{normalUserId}
     Payload: {"role": "admin"}
     Description: Modify own role to admin
     Information Gained: Admin privileges

  4. IMPACT - DELETE /users/{adminUserId}
     Description: Delete legitimate admin accounts
     Information Gained: Full system control
```

### High: Data Exfiltration Chain

```yaml
Name: "Mass PII Exfiltration via Enumeration"
Severity: HIGH
Complexity: LOW
Likelihood: 95%
Impact: 8/10

Attack Goal: Steal all customer personal data
Business Impact: GDPR violation, identity theft risk, reputation damage

Steps:
  1. RECONNAISSANCE - GET /users?limit=1000&offset=0
     Description: Discover pagination parameters
     Information Gained: Total record count

  2. DATA_EXFILTRATION - GET /users?limit=1000&offset=0
     Description: Retrieve first 1000 user records with PII
     Information Gained: Names, emails, phone numbers, addresses

  3. DATA_EXFILTRATION - GET /users?limit=1000&offset=1000
     Description: Paginate through all records
     Information Gained: Complete customer database
```

## 💡 Best Practices

### 1. **Run Before Deployment**
- Always run attack simulation before production release
- Include in security review checklist
- Require security score > 70 for deployment

### 2. **Prioritize Remediation**
- Fix CRITICAL chains immediately
- Address HIGH chains before deployment
- Plan MEDIUM/LOW for next sprint

### 3. **Break the Chain**
- You don't need to fix every vulnerability
- Breaking one step breaks the entire chain
- Focus on easiest high-impact fixes

### 4. **Validate Fixes**
- Rerun simulation after implementing fixes
- Verify chains are actually broken
- Check that new vulnerabilities weren't introduced

### 5. **Continuous Monitoring**
- Run after major API changes
- Include in CI/CD security gates
- Track security score trend over time

## 🎯 Common Attack Patterns

### Pattern 1: Enumeration → Unauthorized Access

**Vulnerabilities:**
- Public collection endpoints
- Missing authentication
- No rate limiting

**Attack Chain:**
1. List all resources via collection endpoint
2. Access individual resources without auth
3. Extract sensitive data

**Fix:** Add authentication to all endpoints, implement rate limiting

---

### Pattern 2: IDOR → Privilege Escalation

**Vulnerabilities:**
- Missing ownership checks
- User-controlled IDs in paths
- Writable role fields

**Attack Chain:**
1. Access own resource via /users/{id}
2. Modify ID parameter to access other users
3. Update role field to gain privileges

**Fix:** Implement ownership validation, make role fields read-only

---

### Pattern 3: Information Disclosure → Account Takeover

**Vulnerabilities:**
- Verbose error messages
- Exposed system internals
- Predictable identifiers

**Attack Chain:**
1. Trigger errors to learn system details
2. Identify valid usernames/emails
3. Brute force passwords or reset flows
4. Take over accounts

**Fix:** Generic error messages, implement rate limiting, use UUIDs

---

## 🔍 Troubleshooting

### Analysis Times Out

**Issue:** Simulation doesn't complete after 5 minutes

**Solution:**
1. Reduce `analysisDepth` to `quick` or `standard`
2. Reduce `maxChainLength` to 3
3. Check Ollama is responsive
4. Try smaller API spec to isolate issue

---

### No Attack Chains Found

**Issue:** Report shows 0 attack chains despite known vulnerabilities

**Solution:**
1. Verify spec is valid OpenAPI 3.x
2. Check that operations have responses defined
3. Ensure security schemes are documented (even if missing)
4. Try increasing `maxChainLength`

---

### Irrelevant Attack Chains

**Issue:** AI generates unrealistic attack scenarios

**Solution:**
1. Ensure spec accurately reflects implementation
2. Document actual authentication/authorization logic
3. Report issue with spec example for improvement

---

## 📚 Related Features

- **[Security Analysis](./SECURITY_ANALYSIS.md)** - Find individual vulnerabilities before chaining
- **[API Hardening](./API_HARDENING.md)** - Implement security patterns to break chains
- **[Linter](./LINTER.md)** - Catch security issues during development
- **[Validator](./VALIDATOR.md)** - Ensure fixes don't break spec

## 🔗 Additional Resources

### Security Frameworks
- [MITRE ATT&CK for Enterprise](https://attack.mitre.org/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)

### Penetration Testing
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [PortSwigger Web Security Academy](https://portswigger.net/web-security)
- [HackTheBox](https://www.hackthebox.com/)

### Attack Chain Examples
- [Cyber Kill Chain](https://www.lockheedmartin.com/en-us/capabilities/cyber/cyber-kill-chain.html)
- [Unified Kill Chain](https://www.unifiedkillchain.com/)

---

## 🎓 Understanding the AI Agent

### How It Thinks Like an Attacker

The AI agent is prompted to:

1. **Adopt Adversarial Mindset**: Think like a malicious hacker
2. **Identify Weak Points**: Find missing security controls
3. **Chain Vulnerabilities**: Combine issues for maximum impact
4. **Assess Feasibility**: Only report realistic attacks
5. **Calculate Impact**: Understand business consequences

### Limitations

- **Spec-Based Only**: Cannot test actual implementation
- **No Runtime Analysis**: Doesn't interact with live API
- **AI Hallucination Risk**: May generate unlikely scenarios
- **Static Analysis**: Cannot detect logic flaws or race conditions

**Recommendation:** Use attack simulation as a starting point, follow up with manual penetration testing for critical systems.

---

[← Back to README](../../README.md) | [← Previous: Security Analysis](./SECURITY_ANALYSIS.md) | [Next: AI Assistant →](./AI_ASSISTANT.md)
