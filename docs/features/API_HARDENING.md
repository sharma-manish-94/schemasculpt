# 🛡️ API Hardening Feature

## Overview

The **API Hardening** feature provides one-click security and performance patterns for your OpenAPI specifications. Transform basic API definitions into production-ready specifications by automatically adding industry-standard security, reliability, and performance patterns.

## 🎯 What It Does

API Hardening automatically enhances your API operations with six essential patterns:

| Pattern | Description | Applicable Methods |
|---------|-------------|-------------------|
| **OAuth2 Security** | Adds OAuth2 authentication with scopes | GET, POST, PUT, PATCH, DELETE |
| **Rate Limiting** | Adds rate limit headers and 429 responses | GET, POST, PUT, PATCH, DELETE |
| **HTTP Caching** | Adds caching headers and 304 responses | GET only |
| **Idempotency** | Adds idempotency keys for safe retries | POST, PUT, PATCH |
| **Input Validation** | Adds 400 Bad Request responses | POST, PUT, PATCH |
| **Error Handling** | Adds standard HTTP error responses | GET, POST, PUT, PATCH, DELETE |

## 🚀 How to Use

### Via UI (Hardening Tab)

1. Navigate to the **AI Features** panel
2. Click the **HARDENING** tab
3. Select the **path** and **method** you want to harden
4. Choose your hardening approach:
   - **Individual Patterns**: Click specific pattern buttons (OAuth2, Rate Limiting, etc.)
   - **Complete Hardening**: Click "Complete Hardening" to apply all patterns at once
5. Review the results and warnings in the response panel

### Via API

```bash
# Apply all hardening patterns
POST /api/v1/sessions/{sessionId}/hardening/operations/complete
{
  "path": "/users",
  "method": "GET"
}

# Apply specific pattern (OAuth2)
POST /api/v1/sessions/{sessionId}/hardening/operations/oauth2
{
  "path": "/users",
  "method": "GET"
}

# Apply specific pattern (Rate Limiting)
POST /api/v1/sessions/{sessionId}/hardening/operations/rate-limiting
{
  "path": "/users",
  "method": "GET",
  "options": {
    "rateLimitPolicy": "100/hour"
  }
}
```

## 📋 Hardening Patterns Explained

### 1. OAuth2 Security

**What it adds:**
- OAuth2 security scheme in `components.securitySchemes`
- Authorization code flow configuration
- Read and write scopes
- Security requirement on the operation

**Implementation:**
```yaml
components:
  securitySchemes:
    oauth2:
      type: oauth2
      description: OAuth2 authentication
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth2/authorize
          tokenUrl: https://auth.example.com/oauth2/token
          scopes:
            read: Read access
            write: Write access

paths:
  /users:
    get:
      security:
        - oauth2: [read, write]
```

**Use case:** Protect sensitive endpoints with industry-standard OAuth2 authentication.

---

### 2. Rate Limiting

**What it adds:**
- `X-RateLimit-Limit` header (request limit per hour)
- `X-RateLimit-Remaining` header (remaining requests)
- `X-RateLimit-Reset` header (reset timestamp)
- `429 Too Many Requests` response with retry information

**Implementation:**
```yaml
paths:
  /users:
    get:
      responses:
        '200':
          headers:
            X-RateLimit-Limit:
              schema:
                type: integer
              description: Request limit per hour
            X-RateLimit-Remaining:
              schema:
                type: integer
              description: Remaining requests
            X-RateLimit-Reset:
              schema:
                type: integer
              description: Reset time
        '429':
          description: Too Many Requests - Rate limit exceeded
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Rate limit exceeded
                  retry_after:
                    type: integer
                    example: 3600
```

**Configuration:**
- Default policy: `100/hour`
- Configurable via `rateLimitPolicy` parameter

**Use case:** Prevent API abuse and ensure fair usage across clients.

---

### 3. HTTP Caching

**What it adds:**
- `Cache-Control` header with configurable TTL
- `ETag` header for cache validation
- `If-None-Match` request parameter
- `304 Not Modified` response

**Implementation:**
```yaml
paths:
  /users:
    get:
      parameters:
        - name: If-None-Match
          in: header
          required: false
          description: Conditional request header for cache validation
          schema:
            type: string
      responses:
        '200':
          headers:
            Cache-Control:
              schema:
                type: string
                example: max-age=300
              description: Cache control directives
            ETag:
              schema:
                type: string
              description: Entity tag for cache validation
        '304':
          description: Not Modified - Resource has not been modified
```

**Configuration:**
- Default TTL: `300` seconds (5 minutes)
- Configurable via `cacheTTL` parameter
- **GET requests only**

**Use case:** Reduce server load and improve response times for frequently accessed resources.

---

### 4. Idempotency

**What it adds:**
- `Idempotency-Key` header (required, UUID format)

**Implementation:**
```yaml
paths:
  /users:
    post:
      parameters:
        - name: Idempotency-Key
          in: header
          required: true
          description: Unique key to ensure request idempotency
          schema:
            type: string
            format: uuid
```

**Applicable to:** POST, PUT, PATCH only

**Use case:** Allow safe request retries without duplicate operations (e.g., prevent double payments).

---

### 5. Input Validation

**What it adds:**
- `400 Bad Request` response with detailed validation error schema

**Implementation:**
```yaml
paths:
  /users:
    post:
      responses:
        '400':
          description: Bad Request - Validation failed
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Validation failed
                  details:
                    type: array
                    items:
                      type: object
                      properties:
                        field:
                          type: string
                        message:
                          type: string
```

**Use case:** Document validation error responses with field-level error details.

---

### 6. Error Handling

**What it adds:**
- `401 Unauthorized` response
- `403 Forbidden` response
- `500 Internal Server Error` response with detailed schema

**Implementation:**
```yaml
paths:
  /users:
    get:
      responses:
        '401':
          description: Unauthorized - Authentication required
        '403':
          description: Forbidden - Access denied
        '500':
          description: Internal Server Error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    example: Internal server error
                  timestamp:
                    type: string
                    format: date-time
                  request_id:
                    type: string
                    format: uuid
```

**Use case:** Provide complete error documentation with traceability.

---

## 🔧 Architecture

### Backend Implementation

**Service:** `HardeningService.java`
**Location:** `api/src/main/java/.../service/HardeningService.java`

The service provides methods for each pattern:
- `applyOAuth2Security()` - Lines 120-168
- `applyRateLimiting()` - Lines 170-233
- `applyCaching()` - Lines 235-297
- `applyIdempotency()` - Lines 299-325
- `applyValidation()` - Lines 327-362
- `applyErrorHandling()` - Lines 364-406

**Controller:** `HardeningController.java`
**Location:** `api/src/main/java/.../controller/HardeningController.java`

REST endpoints:
- `POST /api/v1/sessions/{sessionId}/hardening/operations`
- `POST /api/v1/sessions/{sessionId}/hardening/operations/oauth2`
- `POST /api/v1/sessions/{sessionId}/hardening/operations/rate-limiting`
- `POST /api/v1/sessions/{sessionId}/hardening/operations/caching`
- `POST /api/v1/sessions/{sessionId}/hardening/operations/complete`
- `GET /api/v1/sessions/{sessionId}/hardening/patterns`

### Frontend Implementation

**Component:** `AIHardeningTab` in `AIPanel.js`
**Location:** `ui/src/features/ai/components/AIPanel.js:202-351`

**API Client:** `validationService.js`
**Location:** `ui/src/api/validationService.js`

Functions:
- `addOAuth2Security()`
- `addRateLimiting()`
- `addCaching()`
- `hardenOperationComplete()`

## 📊 Response Format

Successful hardening operations return:

```json
{
  "path": "/users",
  "method": "GET",
  "appliedPatterns": ["OAuth2", "Rate Limiting", "Caching"],
  "changes": {
    "oauth2_scheme_added": true,
    "oauth2_requirement_added": true,
    "rate_limiting_added": true,
    "rate_limit_policy": "100/hour",
    "caching_added": true,
    "cache_ttl": "300"
  },
  "warnings": [],
  "success": true
}
```

### Warnings

The system provides warnings when:
- Security scheme already exists
- Pattern was already applied to the operation
- Pattern is not applicable to the HTTP method

Example warning:
```json
{
  "warnings": ["OAuth2 security scheme already exists"]
}
```

## 💡 Best Practices

1. **Start with Complete Hardening** - Apply all patterns first, then customize
2. **Review Warnings** - Check warnings for conflicts with existing configurations
3. **Test Your Changes** - Use the API Lab to verify hardened endpoints work as expected
4. **Customize Policies** - Adjust rate limits and cache TTL based on your use case
5. **Apply Progressively** - Harden critical endpoints first (authentication, payments)

## 🎯 Use Cases

### E-commerce API
- **OAuth2**: Protect user account endpoints
- **Rate Limiting**: Prevent checkout abuse
- **Idempotency**: Ensure payment operations aren't duplicated
- **Caching**: Cache product catalogs

### Public API
- **Rate Limiting**: Prevent abuse from free-tier users
- **Caching**: Reduce load on documentation endpoints
- **Error Handling**: Provide clear error messages for developers

### Microservices
- **OAuth2**: Secure inter-service communication
- **Idempotency**: Safe retries in distributed systems
- **Error Handling**: Standardize error responses across services

## 🔍 Troubleshooting

### Pattern Not Applied

**Issue:** Hardening operation completes but pattern not visible in spec

**Solution:**
1. Check warnings in response - pattern may already exist
2. Verify correct path and method selected
3. Check if pattern is applicable to the HTTP method

### Validation Errors After Hardening

**Issue:** OpenAPI spec shows validation errors after hardening

**Solution:**
1. Review the generated schemas for conflicts
2. Check if existing responses conflict with new ones
3. Verify security schemes are properly formatted

### Caching Not Working

**Issue:** Caching pattern not applied to endpoint

**Solution:**
- Caching is **only applied to GET requests**
- Verify the method is GET, not POST/PUT/DELETE

## 📚 Related Features

- **[Security Analysis](./SECURITY_ANALYSIS.md)** - Analyze security vulnerabilities before hardening
- **[Attack Simulation](./ATTACK_SIMULATION.md)** - Discover attack vectors to determine what needs hardening
- **[Linter](./LINTER.md)** - Get suggestions for missing security patterns
- **[Validator](./VALIDATOR.md)** - Verify hardened spec is valid OpenAPI

## 🔗 Additional Resources

- [OpenAPI Security Best Practices](https://swagger.io/docs/specification/authentication/)
- [HTTP Caching - MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)
- [Idempotency Keys - Stripe Guide](https://stripe.com/docs/api/idempotent_requests)

---

[← Back to README](../../README.md) | [Next: Linter →](./LINTER.md)
