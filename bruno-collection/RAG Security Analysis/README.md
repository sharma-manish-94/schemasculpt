# RAG Security Analysis Test Suite

This collection contains comprehensive tests for the RAG-enhanced security analysis feature of SchemaSculpt AI Service.

## Test Categories

### 1. **Basic Security Analysis** (`Security Analysis - Basic.bru`)
- Tests fundamental security analysis capabilities
- Uses a simple API specification
- Verifies RAG context integration

### 2. **Vulnerable API Analysis** (`Security Analysis - Vulnerable API.bru`)
- Tests analysis of a deliberately vulnerable banking API
- Checks identification of multiple security issues:
  - Data exposure (password, SSN)
  - Missing authentication/authorization
  - Command injection vulnerabilities
- Verifies references to security standards

### 3. **OAuth API Analysis** (`Security Analysis - OAuth API.bru`)
- Tests analysis of OAuth 2.0 protected APIs
- Verifies understanding of OAuth flows and scopes
- Checks recommendations for OAuth best practices
- Tests references to RFC 6749 and OAuth standards

### 4. **Input Validation Analysis** (`Security Analysis - Input Validation.bru`)
- Focuses on input validation security issues
- Tests identification of injection vulnerabilities
- Verifies recommendations for validation patterns
- Checks OWASP guideline references

### 5. **Rate Limiting Analysis** (`Security Analysis - Rate Limiting.bru`)
- Tests analysis for DDoS and rate limiting protection
- Identifies brute force attack vectors
- Suggests protection mechanisms
- Analyzes resource exhaustion vulnerabilities

### 6. **RAG Status Check** (`RAG Status Check.bru`)
- Verifies RAG service availability
- Checks knowledge base statistics
- Monitors vector store status

## Prerequisites

1. **AI Service Running**: Ensure the AI service is running on `http://localhost:8000`
2. **RAG Knowledge Base**: Run `python ingest_data.py` to create the vector store
3. **GPU Acceleration**: Tests will automatically use NVIDIA 3060 if available

## Expected Results

The RAG-enhanced security analysis should provide:

- **Comprehensive Analysis**: Detailed security assessment using OWASP guidelines
- **Context-Aware Recommendations**: Suggestions based on security best practices from knowledge base
- **Standard References**: Citations to OAuth 2.0, JWT, OWASP Top 10, etc.
- **Actionable Insights**: Specific remediation steps for identified vulnerabilities

## Environment Variables

The tests use the following environment variables from `Development.bru`:
- `aiServiceUrl`: http://localhost:8000
- `sampleSessionId`: sample-session-123
- `sampleUserId`: test-user-456

## Running the Tests

1. Open Bruno
2. Load the SchemaSculpt collection
3. Navigate to "RAG Security Analysis" folder
4. Run individual tests or the entire suite
5. Check test results and response analysis

## Knowledge Base Sources

The RAG system uses security knowledge from:
- OWASP API Security Project
- OWASP REST Security Cheat Sheet
- OAuth 2.0 Specification (RFC 6749)
- JWT Specification (RFC 7519)
- OpenID Connect Core Specification
- OWASP Application Security Verification Standard (ASVS)

## Test Validation

Each test includes validation for:
- HTTP 200 response status
- Proper AI response structure
- Security issue identification
- RAG context integration
- Standard compliance references
