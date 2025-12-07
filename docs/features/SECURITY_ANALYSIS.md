# 🔐 Security Analysis Feature

## Overview

The **Security Analysis** feature provides AI-powered security auditing of your OpenAPI specifications using a multi-agent approach. Unlike simple linting, this deep analysis examines authentication, authorization, data exposure, and cryptographic practices to identify real security vulnerabilities.

## 🎯 What It Does

Security Analysis runs three specialized AI agents in parallel:

| Agent | Focus Area | What It Finds |
|-------|------------|---------------|
| **Authentication Agent** | Identity verification | Missing auth schemes, weak credentials, insecure flows |
| **Authorization Agent** | Access control | Missing permissions, privilege escalation, RBAC issues |
| **Data Exposure Agent** | Sensitive data leaks | PII in responses, over-permissive schemas, data minimization violations |

## 🚀 How to Use

### Via UI (Security Tab)

1. Navigate to the **AI Features** panel
2. Click the **SECURITY** tab
3. Click **"Run Security Analysis"** button
4. Wait for AI agents to complete analysis (typically 10-30 seconds)
5. Review findings organized by severity and category

### Via API

```bash
POST http://localhost:8000/ai/security/analyze
Content-Type: application/json

{
  "spec_text": "...", // OpenAPI spec as string
  "force_refresh": false, // Bypass cache
  "validation_suggestions": [] // Optional linter findings for context
}
```

**Response:**
```json
{
  "cached": false,
  "report": {
    "authentication": { /* findings */ },
    "authorization": { /* findings */ },
    "dataExposure": { /* findings */ },
    "overall": {
      "securityScore": 65,
      "criticalIssues": 2,
      "highIssues": 5,
      "recommendations": [/* ... */]
    }
  },
  "correlation_id": "uuid"
}
```

## 📋 Analysis Categories

### 1. **Authentication Analysis**

**What it examines:**
- Security scheme definitions (`securitySchemes`)
- Authentication flows (OAuth2, OpenID Connect, API keys)
- Credential storage and transmission
- Token validation and expiration

**Example findings:**

#### ❌ Critical: Missing Authentication
```yaml
Issue: Sensitive endpoint '/users/{id}' has no security requirements
Severity: CRITICAL
Impact: Anyone can access user data without authentication
Recommendation: Add OAuth2 or API key authentication
```

#### ⚠️ High: Weak Authentication Scheme
```yaml
Issue: Using basic authentication over HTTP
Severity: HIGH
Impact: Credentials transmitted in cleartext
Recommendation: Require HTTPS and use OAuth2 or JWT
```

#### ⚠️ Medium: Missing Token Expiration
```yaml
Issue: JWT tokens have no expiration documented
Severity: MEDIUM
Impact: Compromised tokens remain valid indefinitely
Recommendation: Document token TTL and refresh flow
```

---

### 2. **Authorization Analysis**

**What it examines:**
- Role-based access control (RBAC) implementation
- OAuth2 scopes and permissions
- Operation-level security requirements
- Privilege escalation vulnerabilities

**Example findings:**

#### ❌ Critical: Missing Authorization Check
```yaml
Issue: DELETE /users/{id} allows any authenticated user to delete any account
Severity: CRITICAL
Impact: Privilege escalation - users can delete admin accounts
Recommendation: Implement role-based access control (admin-only scope)
```

#### ⚠️ High: Overly Permissive Scopes
```yaml
Issue: 'write' scope grants access to all mutation operations including admin functions
Severity: HIGH
Impact: Insufficient granularity for least-privilege access
Recommendation: Define fine-grained scopes (user:write, admin:write, etc.)
```

#### ⚠️ Medium: Inconsistent Security Requirements
```yaml
Issue: Similar operations have different security requirements
  - GET /users requires OAuth2 [read]
  - GET /users/{id} requires OAuth2 [read, write]
Severity: MEDIUM
Impact: Confusing security model, potential for misconfiguration
Recommendation: Standardize security requirements for similar operations
```

---

### 3. **Data Exposure Analysis**

**What it examines:**
- PII (Personally Identifiable Information) in responses
- Sensitive data fields (passwords, SSNs, credit cards)
- Data minimization compliance
- GDPR/privacy considerations

**Example findings:**

#### ❌ Critical: Sensitive Data Exposure
```yaml
Issue: GET /users returns password hashes in response
Severity: CRITICAL
Impact: Password hashes exposed to clients, vulnerable to offline cracking
Recommendation: Remove password fields from all responses
```

#### ⚠️ High: PII Without Authentication
```yaml
Issue: Public endpoint '/users/{id}' returns email, phone, address
Severity: HIGH
Impact: PII accessible without authentication
Recommendation: Add authentication requirement or create public/private schemas
```

#### ⚠️ Medium: Over-Disclosure
```yaml
Issue: Response includes internal IDs, timestamps, system metadata
Severity: MEDIUM
Impact: Information leakage may aid attackers
Recommendation: Create separate internal/external schemas
```

#### ℹ️ Info: Missing Data Classification
```yaml
Issue: Schemas lack data classification labels
Severity: INFO
Impact: Difficult to audit compliance with privacy regulations
Recommendation: Add x-data-classification extensions (public, internal, confidential, restricted)
```

---

## 🏗️ Architecture

### Multi-Agent System

```
User triggers analysis
         ↓
┌────────────────────────────┐
│   Orchestrator Service     │
│  (FastAPI - Python)        │
└────────────────────────────┘
         ↓
    ┌────┴────┬─────────────┐
    ↓         ↓             ↓
┌─────────┐ ┌──────────┐ ┌────────────┐
│  Auth   │ │  Authz   │ │   Data     │
│  Agent  │ │  Agent   │ │  Exposure  │
│         │ │          │ │   Agent    │
└─────────┘ └──────────┘ └────────────┘
    ↓         ↓             ↓
    └────┬────┴─────────────┘
         ↓
   Aggregate Results
         ↓
   Generate Report
```

### Agent Execution

**Mode:** Parallel execution
- All three agents run simultaneously
- Results aggregated when all complete
- Total time: ~10-30 seconds (depending on spec size)

**Caching:**
- Analysis results cached by spec content hash
- Cache duration: 1 hour
- Force refresh with `force_refresh: true`

### Backend Implementation

**Service:** `SecurityAnalysisService` (Python FastAPI)
**Location:** `ai_service/app/services/security_analysis_service.py`

**Endpoint:** `POST /ai/security/analyze`

**Dependencies:**
- Ollama (LLM inference)
- OpenAPI parser (prance/openapi-spec-validator)
- Redis (caching)

### Frontend Implementation

**Component:** `SecurityAnalysisTab` in `AIPanel.js`
**Location:** `ui/src/features/ai/components/AIPanel.js`

**API Client:** `securityService.js`
**Location:** `ui/src/api/securityService.js`

Functions:
- `runSecurityAnalysis()` - Full security audit
- `analyzeAuthentication()` - Auth-only analysis
- `analyzeAuthorization()` - Authz-only analysis
- `analyzeDataExposure()` - Data exposure analysis

## 📊 Security Score Calculation

The overall security score (0-100) is calculated based on:

```
Security Score = 100 - (Critical × 20) - (High × 10) - (Medium × 5) - (Low × 2)
```

**Score Interpretation:**

| Score | Rating | Meaning |
|-------|--------|---------|
| 90-100 | 🟢 Excellent | Production-ready, minimal issues |
| 70-89 | 🟡 Good | Some improvements needed |
| 50-69 | 🟠 Fair | Significant vulnerabilities present |
| 0-49 | 🔴 Poor | Critical security issues, not production-ready |

## 🎯 Common Vulnerabilities Detected

### Authentication Vulnerabilities

- ❌ No authentication on sensitive endpoints
- ❌ Basic auth over HTTP (credentials in cleartext)
- ❌ API keys in query parameters (logged in URLs)
- ❌ Missing token refresh flows
- ❌ Hardcoded credentials in examples
- ❌ Weak password policies documented

### Authorization Vulnerabilities

- ❌ Missing role-based access control
- ❌ Horizontal privilege escalation (user A can access user B's data)
- ❌ Vertical privilege escalation (user can perform admin actions)
- ❌ Inconsistent security requirements
- ❌ Missing resource ownership checks
- ❌ Overly permissive OAuth scopes

### Data Exposure Vulnerabilities

- ❌ PII returned without authentication
- ❌ Password hashes in responses
- ❌ Credit card data not masked
- ❌ Internal IDs and system metadata exposed
- ❌ Stack traces in error responses
- ❌ Overly detailed error messages revealing system internals

### Cryptographic Vulnerabilities

- ❌ Weak TLS versions (TLS 1.0, 1.1)
- ❌ Insecure OAuth flows (implicit grant)
- ❌ Missing PKCE for mobile OAuth
- ❌ Weak JWT algorithms (HS256 with weak secrets)
- ❌ Missing signature validation requirements

## 💡 Best Practices

### 1. **Run Early and Often**
- Run security analysis before deployment
- Rerun after major changes to security model
- Integrate into CI/CD pipeline

### 2. **Prioritize Findings**
- Fix CRITICAL issues immediately
- Address HIGH severity within sprint
- Plan MEDIUM issues for next release
- Track INFO items as technical debt

### 3. **Use With Other Features**
- Run after linter fixes to ensure no new issues
- Use API Hardening to implement recommended patterns
- Verify fixes with Attack Simulation

### 4. **Document Security Decisions**
- Add comments explaining security choices
- Use OpenAPI extensions for security metadata:
  ```yaml
  x-security-classification: confidential
  x-requires-permission: admin:delete
  x-data-retention: 30-days
  ```

### 5. **Combine With Manual Review**
- AI finds common issues, but not everything
- Perform manual security review for critical APIs
- Consider professional penetration testing

## 🔍 Troubleshooting

### Analysis Takes Too Long

**Issue:** Security analysis doesn't complete after 60 seconds

**Solution:**
1. Check Ollama is running and responsive (`ollama list`)
2. Verify AI service is not overloaded (check logs)
3. Try smaller spec to isolate issue
4. Increase timeout in configuration

---

### Inaccurate Findings

**Issue:** False positives or missed vulnerabilities

**Solution:**
1. Ensure spec is valid OpenAPI 3.x
2. Check that security schemes are properly defined
3. Review context provided to AI (linter suggestions help)
4. Report issue with spec example for improvement

---

### Cached Results Not Updating

**Issue:** Analysis shows old results after spec changes

**Solution:**
1. Use `force_refresh: true` parameter
2. Clear analysis cache via API
3. Check spec content hash is changing

---

## 📚 Related Features

- **[Attack Simulation](./ATTACK_SIMULATION.md)** - Discover multi-step attack chains
- **[API Hardening](./API_HARDENING.md)** - Apply security patterns from recommendations
- **[Linter](./LINTER.md)** - Catch security issues during development
- **[Validator](./VALIDATOR.md)** - Ensure security schemes are valid

## 🔗 Additional Resources

### Standards & Guidelines

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OpenAPI Security Scheme Specification](https://spec.openapis.org/oas/v3.1.0#security-scheme-object)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [GDPR Data Protection](https://gdpr.eu/)

### Security Patterns

- [OAuth2 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)
- [PKCE for Mobile Apps](https://oauth.net/2/pkce/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [API Key Security](https://cloud.google.com/endpoints/docs/openapi/when-why-api-key)

### Tools & Testing

- [OWASP ZAP](https://www.zaproxy.org/) - Security testing tool
- [Burp Suite](https://portswigger.net/burp) - Web security testing
- [jwt.io](https://jwt.io/) - JWT decoder and debugger

---

## 🎓 Example Analysis Report

```json
{
  "report": {
    "authentication": {
      "findings": [
        {
          "severity": "CRITICAL",
          "category": "missing-authentication",
          "message": "POST /users has no security requirements",
          "affected_paths": ["/users"],
          "recommendation": "Add OAuth2 security requirement with 'user:create' scope"
        }
      ]
    },
    "authorization": {
      "findings": [
        {
          "severity": "HIGH",
          "category": "privilege-escalation",
          "message": "DELETE /users/{id} allows any user to delete any account",
          "affected_paths": ["/users/{id}"],
          "recommendation": "Restrict to admin role or add ownership check"
        }
      ]
    },
    "dataExposure": {
      "findings": [
        {
          "severity": "HIGH",
          "category": "pii-exposure",
          "message": "User schema includes SSN field",
          "affected_schemas": ["User"],
          "recommendation": "Remove SSN from response or require elevated permissions"
        }
      ]
    },
    "overall": {
      "securityScore": 45,
      "rating": "POOR",
      "criticalIssues": 1,
      "highIssues": 2,
      "mediumIssues": 5,
      "lowIssues": 3,
      "recommendations": [
        "Implement authentication on all endpoints",
        "Add role-based access control",
        "Remove PII from public responses",
        "Enable HTTPS-only communication"
      ]
    }
  }
}
```

---

[← Back to README](../../README.md) | [← Previous: Validator](./VALIDATOR.md) | [Next: Attack Simulation →](./ATTACK_SIMULATION.md)
