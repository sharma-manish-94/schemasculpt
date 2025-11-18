# 🔍 Intelligent Linter Feature

## Overview

The **Intelligent Linter** is SchemaSculpt's rule-based analysis engine that automatically detects issues, inconsistencies, and improvement opportunities in your OpenAPI specifications. With **14+ built-in rules** covering security, best practices, naming conventions, and AI-friendliness, the linter provides actionable suggestions with **one-click auto-fix** capabilities.

## 🎯 What It Does

The linter analyzes your OpenAPI specification in real-time and provides:

- **Instant Feedback**: Suggestions appear as you edit
- **Categorized Issues**: Grouped by severity and category (security, best practices, performance, etc.)
- **Auto-Fix Buttons**: One-click fixes for deterministic issues (⚡)
- **AI-Fix Buttons**: Context-aware AI fixes for complex issues (✨)
- **Detailed Explanations**: Click "?" to understand why an issue matters

## 📋 Linter Rules

### 🔐 Security Rules

#### 1. **Security Requirements Rule**

**What it detects:** Operations that lack security requirements

**Why it matters:** Endpoints without authentication are vulnerable to unauthorized access

**Example issue:**
```
POST /users lacks security requirements. Consider adding authentication.
```

**Quick fix:** Adds appropriate security scheme requirement to the operation

**Category:** `security`
**Severity:** `warning`

---

#### 2. **HTTPS Only Rule**

**What it detects:** API servers using HTTP instead of HTTPS

**Why it matters:** Unencrypted HTTP exposes data to man-in-the-middle attacks

**Example issue:**
```
Server URL 'http://api.example.com' should use HTTPS for security.
```

**Quick fix:** Updates server URLs to use HTTPS protocol

**Category:** `security`
**Severity:** `error`

---

### 💡 Best Practices Rules

#### 3. **Response Success Rule**

**What it detects:** Operations missing successful response definitions (2xx)

**Why it matters:** Every operation should document expected successful responses

**Example issue:**
```
Operation GET /users should have at least one success response (2xx).
```

**Quick fix:** Adds a 200 OK response with appropriate schema

**Category:** `best-practices`
**Severity:** `warning`

---

#### 4. **Operation Tags Rule**

**What it detects:** Operations without tags for logical grouping

**Why it matters:** Tags organize operations in documentation and improve discoverability

**Example issue:**
```
Operation GET /users/{id} should have at least one tag.
```

**Quick fix:** Infers and adds appropriate tag based on path

**Category:** `best-practices`
**Severity:** `info`

---

### 🏷️ Naming Convention Rules

#### 5. **Schema Naming Convention Rule**

**What it detects:** Schema names not following PascalCase convention

**Why it matters:** Consistent naming improves readability and follows OpenAPI best practices

**Example issue:**
```
Schema 'user_profile' should use PascalCase naming (e.g., 'UserProfile').
```

**Quick fix:** Renames schema and updates all references

**Category:** `naming`
**Severity:** `info`

**Recommended format:** `PascalCase` (e.g., `UserProfile`, `OrderItem`)

---

#### 6. **Path Naming Rule**

**What it detects:** Path segments not following kebab-case convention

**Why it matters:** Consistent URL conventions improve API usability

**Example issue:**
```
Path '/user_profile' should use kebab-case (e.g., '/user-profile').
```

**Quick fix:** Renames path to kebab-case format

**Category:** `naming`
**Severity:** `info`

**Recommended format:** `kebab-case` (e.g., `/user-profile`, `/order-items`)

---

### 📝 Documentation Rules

#### 7. **Missing Operation ID Rule**

**What it detects:** Operations without unique `operationId` fields

**Why it matters:** OperationIds are required for code generation tools and API client SDKs

**Example issue:**
```
Operation GET /users is missing an operationId.
```

**Quick fix:** Generates operationId based on method and path (e.g., `getUsers`)

**Category:** `documentation`
**Severity:** `warning`
**Auto-fixable:** ✅

---

#### 8. **Missing Summary Rule**

**What it detects:** Operations without summary descriptions

**Why it matters:** Summaries appear in documentation and improve developer experience

**Example issue:**
```
Operation GET /users is missing a summary.
```

**Quick fix:** AI generates contextual summary based on path and method

**Category:** `documentation`
**Severity:** `info`

---

#### 9. **Missing Description Rule**

**What it detects:** Operations, parameters, or schemas without detailed descriptions

**Why it matters:** Comprehensive descriptions are essential for API documentation

**Example issue:**
```
Operation GET /users is missing a description.
```

**Quick fix:** AI generates detailed description based on context

**Category:** `documentation`
**Severity:** `info`

---

#### 10. **Example Rule**

**What it detects:** Schemas and responses missing example values

**Why it matters:** Examples help developers understand expected data formats

**Example issue:**
```
Schema 'User' is missing example values.
```

**Quick fix:** AI generates realistic example data based on schema

**Category:** `documentation`
**Severity:** `info`

---

### ⚡ Performance Rules

#### 11. **Unused Component Rule**

**What it detects:** Schemas defined in `components` but never referenced

**Why it matters:** Unused components bloat specification files and confuse developers

**Example issue:**
```
Component schema 'OldUser' is defined but never used.
```

**Quick fix:** Removes the unused schema from components

**Category:** `performance`
**Severity:** `warning`
**Auto-fixable:** ✅

---

### 🤖 AI-Friendliness Rules

These rules help optimize your API for consumption by AI agents and comply with MCP (Model Context Protocol) best practices.

#### 12. **Pagination Support Rule**

**What it detects:** Collection endpoints (GET) without pagination parameters

**Why it matters:** Prevents AI agents from fetching massive datasets, causing timeouts

**Example issue:**
```
Collection endpoint GET /users should support pagination (limit, offset).
```

**Quick fix:** Adds `limit` and `offset` query parameters

**Category:** `ai-friendliness`
**Severity:** `info`

**Suggested parameters:**
- `limit`: Maximum items to return (default: 100)
- `offset`: Number of items to skip (default: 0)
- Alternative: `cursor` for cursor-based pagination

---

#### 13. **Batch Endpoint Suggestion Rule**

**What it detects:** Individual resource endpoints without batch alternatives

**Why it matters:** AI agents can reduce 100 API calls to 1 with batch endpoints

**Example issue:**
```
Consider adding a batch endpoint like POST /users/batch-get to complement GET /users/{id}.
```

**Quick fix:** AI generates batch endpoint specification

**Category:** `ai-friendliness`
**Severity:** `info`

**Example batch endpoint:**
```yaml
/users/batch-get:
  post:
    requestBody:
      content:
        application/json:
          schema:
            type: object
            properties:
              ids:
                type: array
                items:
                  type: string
```

---

#### 14. **AI-Friendly Response Format Rule**

**What it detects:** Error responses not following RFC 7807 (Problem Details)

**Why it matters:** Standardized error formats enable AI agents to parse errors consistently

**Example issue:**
```
Error responses should follow RFC 7807 format for machine readability.
```

**Quick fix:** Converts error response schemas to RFC 7807 format

**Category:** `ai-friendliness`
**Severity:** `info`

**RFC 7807 format:**
```yaml
components:
  schemas:
    ProblemDetails:
      type: object
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string
          format: uri
```

---

## 🚀 How to Use

### Automatic Linting

The linter runs automatically when:
1. You load an OpenAPI specification
2. You make changes in the Monaco editor
3. You trigger validation manually

No configuration needed - it just works!

### Viewing Suggestions

1. **Validation Panel**: All suggestions appear in the right panel
2. **Categorized View**: Suggestions are grouped by category:
   - 🔐 Security
   - 💡 Best Practices
   - 🏷️ Naming
   - 📝 Documentation
   - ⚡ Performance
   - 🤖 AI-Friendliness

3. **Severity Levels**:
   - 🔴 **Error**: Must be fixed (breaks OpenAPI spec)
   - 🟡 **Warning**: Should be fixed (security/critical issues)
   - 🔵 **Info**: Nice to have (improvements)

### Applying Fixes

#### Quick Fix (⚡)
- Click the **⚡ Auto-Fix** button
- Instant, deterministic fix
- No AI needed
- Examples: Remove unused schema, add operationId

#### AI Fix (✨)
- Click the **✨ AI-Fix** button
- Context-aware, intelligent fix
- Uses local Ollama LLM
- Examples: Generate descriptions, add examples

### Batch Fixes

Apply multiple fixes at once:
1. Select multiple suggestions (checkbox)
2. Click "Apply Selected Fixes"
3. Review changes in the editor

## 🔧 Architecture

### Backend Implementation

**Main Service:** `SpecificationLinter.java`
**Location:** `api/src/main/java/.../service/linter/SpecificationLinter.java`

**How it works:**
```java
public List<ValidationSuggestion> lint(OpenAPI openAPI) {
  // Run all registered linter rules
  return rules.stream()
    .flatMap(linterRule -> linterRule.lint(openAPI).stream())
    .toList();
}
```

**Rule Interface:** `LinterRule.java`

Each rule implements:
```java
public interface LinterRule {
  List<ValidationSuggestion> lint(OpenAPI openApi);
}
```

### Frontend Integration

**Component:** Validation panel in main editor view
**State:** Managed by Zustand `validationSlice`

**Real-time Updates:**
- WebSocket connection receives validation updates
- Suggestions automatically refresh on spec changes
- UI updates without page reload

## 📊 Suggestion Format

Each suggestion includes:

```json
{
  "message": "Operation GET /users is missing an operationId",
  "fixId": "add-operation-id",
  "severity": "warning",
  "category": "documentation",
  "context": {
    "path": "/users",
    "method": "GET"
  },
  "autoFixable": true
}
```

### Properties

| Property | Description | Values |
|----------|-------------|--------|
| `message` | Human-readable issue description | String |
| `fixId` | Unique identifier for the fix type | String (kebab-case) |
| `severity` | Issue importance level | `error`, `warning`, `info` |
| `category` | Issue classification | `security`, `best-practices`, `naming`, `documentation`, `performance`, `ai-friendliness` |
| `context` | Additional data for applying fix | Object (varies by rule) |
| `autoFixable` | Can be fixed automatically | Boolean |

## 💡 Best Practices

1. **Fix High-Severity First**: Address errors and warnings before info suggestions
2. **Review AI Fixes**: Always review AI-generated fixes before committing
3. **Batch Similar Fixes**: Apply the same fix type across multiple operations
4. **Use Explanations**: Click "?" to understand why a rule matters
5. **Customize When Needed**: Not all suggestions apply to every API

## 🎯 Common Workflows

### New API Development

1. Create basic OpenAPI structure
2. Run linter to find missing elements
3. Apply auto-fixes for operationIds, tags
4. Use AI fixes for descriptions and examples
5. Review security and pagination suggestions

### Legacy API Modernization

1. Load existing OpenAPI 2.0/3.0 spec
2. Fix naming convention issues
3. Add missing security requirements
4. Implement pagination for collections
5. Add batch endpoints for AI-friendliness

### Pre-Production Checklist

1. ✅ No error-level issues
2. ✅ All endpoints have security requirements
3. ✅ HTTPS-only server URLs
4. ✅ Complete documentation (summaries, descriptions)
5. ✅ Examples for all schemas
6. ✅ Pagination on collection endpoints

## 🔍 Troubleshooting

### Linter Not Running

**Issue:** Suggestions panel is empty

**Solution:**
1. Check that spec is valid OpenAPI 3.x
2. Verify WebSocket connection is active
3. Try manual validation (refresh button)

### Fix Not Applied

**Issue:** Clicked fix button but spec unchanged

**Solution:**
1. Check browser console for errors
2. Verify session is active (check Redis connection)
3. Review fix response for error messages

### Too Many Suggestions

**Issue:** Overwhelmed by 100+ suggestions

**Solution:**
1. Filter by severity (show errors/warnings only)
2. Filter by category (start with security)
3. Apply batch fixes for similar issues

## 📚 Related Features

- **[API Hardening](./API_HARDENING.md)** - Apply security patterns suggested by linter
- **[AI Assistant](./AI_ASSISTANT.md)** - Use natural language to implement linter suggestions
- **[Validator](./VALIDATOR.md)** - Verify fixes don't break OpenAPI compliance
- **[Security Analysis](./SECURITY_ANALYSIS.md)** - Deep security audit beyond linter rules

## 🔗 Additional Resources

- [OpenAPI Specification 3.1](https://spec.openapis.org/oas/latest.html)
- [OpenAPI Best Practices](https://swagger.io/resources/articles/best-practices-in-api-design/)
- [RFC 7807 - Problem Details](https://www.rfc-editor.org/rfc/rfc7807)
- [MCP Protocol](https://github.com/anthropics/model-context-protocol)

## 🎓 Custom Rules (Future)

**Coming soon:** Create custom linter rules for your organization

```yaml
custom-rules:
  - name: internal-auth-required
    description: All /internal/* paths must use API key auth
    severity: error
    pattern:
      path: /internal/**
      require: security.apiKey
```

---

[← Back to README](../../README.md) | [← Previous: API Hardening](./API_HARDENING.md) | [Next: Validator →](./VALIDATOR.md)
