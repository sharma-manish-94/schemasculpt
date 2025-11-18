# ✅ Real-time Validator Feature

## Overview

The **Real-time Validator** provides instant OpenAPI specification validation as you type, powered by industry-standard validation libraries. Get immediate feedback on syntax errors, schema violations, and structural issues without leaving the editor.

## 🎯 What It Does

The validator continuously monitors your OpenAPI specification and provides:

- **Instant Validation**: Errors appear within milliseconds of typing
- **Syntax Checking**: JSON and YAML syntax validation
- **Schema Validation**: OpenAPI 3.x schema compliance
- **Reference Resolution**: Validates `$ref` pointers and component references
- **Detailed Error Messages**: Pinpoint exact location and cause of issues
- **WebSocket Updates**: Real-time validation without page refresh

## 🚀 How It Works

### Validation Pipeline

```
User edits spec in Monaco Editor
         ↓
Editor content sent to API Gateway
         ↓
Java swagger-parser validates spec
         ↓
Validation results sent via WebSocket
         ↓
UI displays errors in validation panel
```

### Validation Engines

#### Backend (Java)
- **Library**: `swagger-parser` (OpenAPI Parser)
- **Validates**: OpenAPI 3.x compliance, schema structure, references
- **Location**: `ValidationService.java`

#### Frontend (JavaScript)
- **Library**: `js-yaml` (YAML parsing)
- **Validates**: YAML/JSON syntax
- **Location**: Monaco Editor

## 📋 Validation Types

### 1. **Syntax Validation**

Checks for basic JSON/YAML syntax errors.

**Example errors:**
```
✗ YAML syntax error: unexpected end of file
✗ JSON parsing error: Unexpected token } at line 45
✗ Invalid indentation at line 23
```

**How to fix:**
- Check for missing brackets, braces, or quotes
- Verify YAML indentation (use spaces, not tabs)
- Use Monaco's built-in syntax highlighting

---

### 2. **Schema Validation**

Validates OpenAPI 3.x schema structure and required fields.

**Example errors:**
```
✗ 'openapi' field is required
✗ 'info' object is missing required field 'title'
✗ 'paths' must be an object, got array
✗ Invalid OpenAPI version '2.0', must be 3.x
```

**How to fix:**
- Ensure all required fields are present
- Check OpenAPI 3.x specification for field requirements
- Verify data types match schema expectations

---

### 3. **Reference Validation**

Validates `$ref` pointers and component references.

**Example errors:**
```
✗ Reference '#/components/schemas/User' not found
✗ Circular reference detected: User → Address → User
✗ Invalid reference format: missing '#/'
✗ External reference not resolvable: './users.yaml'
```

**How to fix:**
- Ensure referenced components exist in `components` section
- Fix typos in reference paths
- Avoid circular dependencies
- Verify external file paths are correct

---

### 4. **Structural Validation**

Validates OpenAPI-specific structural requirements.

**Example errors:**
```
✗ Path '/users/{id}' parameter 'id' not defined in parameters
✗ Operation must have at least one response
✗ Response schema references non-existent component
✗ Security requirement 'oauth2' not defined in securitySchemes
```

**How to fix:**
- Define all path parameters
- Add response definitions to operations
- Ensure security schemes are defined before use

---

### 5. **Semantic Validation**

Validates logical consistency and best practices.

**Example errors:**
```
✗ Duplicate operationId 'getUser' found
✗ Response code '418' is not a standard HTTP status
✗ Server URL must start with http:// or https://
✗ Path '/users/{userId}' conflicts with '/users/{id}'
```

**How to fix:**
- Ensure operationIds are unique across all operations
- Use standard HTTP status codes
- Follow URL formatting rules
- Avoid conflicting path parameters

---

## 🎨 Validation Display

### Error Panel

Errors are displayed in the validation panel with:

- **Severity Icon**:
  - 🔴 **Error**: Breaks OpenAPI compliance (must fix)
  - 🟡 **Warning**: Potential issue (should review)
  - 🔵 **Info**: Suggestion or tip

- **Location**: Path to the issue (e.g., `paths./users.get.responses`)

- **Message**: Clear description of the issue

- **Line Number**: Click to jump to the error in the editor

### Monaco Editor Integration

- **Red Squiggly Lines**: Syntax errors highlighted inline
- **Hover Tooltips**: Error details on hover
- **Error Markers**: Red indicators in scrollbar
- **Problems Panel**: List of all issues at bottom

## 🔧 Architecture

### Backend Implementation

**Service:** `ValidationService.java`
**Location:** `api/src/main/java/.../service/ValidationService.java`

**Key method:**
```java
public ValidationResult validate(String specContent) {
  try {
    OpenAPIV3Parser parser = new OpenAPIV3Parser();
    SwaggerParseResult result = parser.readContents(specContent, null, null);

    // Return validation errors and warnings
    return new ValidationResult(
      result.getMessages(),
      result.getOpenAPI()
    );
  } catch (Exception e) {
    return ValidationResult.error(e.getMessage());
  }
}
```

**Technology:**
- `io.swagger.parser.v3.OpenAPIV3Parser`
- `io.swagger.v3.oas.models.OpenAPI`

### Frontend Implementation

**Service:** `validationService.js`
**Location:** `ui/src/api/validationService.js`

**WebSocket Integration:**
```javascript
// Subscribe to validation updates
stompClient.subscribe(`/topic/sessions/${sessionId}/validation`,
  (message) => {
    const validation = JSON.parse(message.body);
    updateValidationPanel(validation);
  }
);
```

**State Management:**
- Zustand store: `validationSlice`
- Real-time updates via WebSocket
- Debounced validation (500ms delay)

## 🚀 Usage Examples

### Valid OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      operationId: getUsers
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
components:
  schemas:
    UserList:
      type: array
      items:
        $ref: '#/components/schemas/User'
    User:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
```

✅ **Result**: No validation errors

---

### Invalid Specification (Missing Required Fields)

```yaml
openapi: 3.0.0
paths:
  /users:
    get:
      responses:
        '200':
          description: Success
```

❌ **Errors:**
```
✗ 'info' field is required
✗ 'info.title' is required
✗ 'info.version' is required
```

---

### Invalid Specification (Broken Reference)

```yaml
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users:
    get:
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserNotDefined'
```

❌ **Error:**
```
✗ Reference '#/components/schemas/UserNotDefined' not found
```

---

## ⚙️ Configuration

### Validation Settings

**Debounce Delay**: 500ms (configurable)
- Prevents validation on every keystroke
- Reduces server load
- Balances responsiveness and performance

**WebSocket Reconnection**: Automatic
- Reconnects on connection loss
- Retry interval: 5 seconds
- Max retries: 10

**Validation Cache**: Session-based
- Caches last validation result
- Invalidated on spec change
- Stored in Redis (backend)

## 💡 Best Practices

1. **Fix Errors First**: Address validation errors before linter warnings
2. **Use Format Conversion**: Switch between JSON/YAML to catch format-specific issues
3. **Check References Early**: Validate references before building complex specs
4. **Monitor WebSocket**: Ensure real-time validation is active (check connection status)
5. **Save Frequently**: Valid specs are automatically saved to session

## 🎯 Common Workflows

### New Specification

1. Create basic structure with required fields
2. Wait for validation feedback
3. Fix any errors before adding operations
4. Build spec incrementally, validating as you go

### Debugging Invalid Spec

1. Check validation panel for errors
2. Click error to jump to line in editor
3. Review error message and context
4. Fix issue and verify validation passes
5. Repeat for remaining errors

### Importing External Spec

1. Load spec into editor
2. Review all validation errors
3. Fix critical errors (schema, references)
4. Address warnings and linter suggestions
5. Verify spec is fully valid

## 🔍 Troubleshooting

### Validation Not Running

**Issue:** Changes in editor don't trigger validation

**Solution:**
1. Check WebSocket connection status (look for indicator in UI)
2. Verify session is active (check session ID in URL)
3. Refresh the page to reconnect
4. Check browser console for WebSocket errors

---

### False Positive Errors

**Issue:** Valid spec shows validation errors

**Solution:**
1. Verify OpenAPI version is 3.x (not 2.0/Swagger)
2. Check for unsupported extensions or custom fields
3. Ensure all references use correct format (`#/components/...`)
4. Try converting between JSON and YAML formats

---

### Slow Validation

**Issue:** Validation takes several seconds

**Solution:**
1. Large specs (>1000 lines) may validate slower
2. Reduce debounce delay if needed
3. Check network latency to backend
4. Consider breaking spec into smaller modules

---

### WebSocket Disconnections

**Issue:** Validation stops updating in real-time

**Solution:**
1. Check Redis connection (backend dependency)
2. Verify WebSocket port is accessible (default: 8080)
3. Check for firewall or proxy blocking WebSocket
4. Review backend logs for connection errors

---

## 📊 Validation Response Format

```json
{
  "valid": false,
  "errors": [
    {
      "message": "Reference '#/components/schemas/User' not found",
      "location": "paths./users.get.responses.200.content.application/json.schema",
      "line": 15,
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "message": "Response is missing description",
      "location": "paths./users.get.responses.200",
      "line": 12,
      "severity": "warning"
    }
  ],
  "timestamp": "2025-01-17T10:30:00Z"
}
```

## 📚 Related Features

- **[Linter](./LINTER.md)** - Go beyond validation with intelligent suggestions
- **[AI Assistant](./AI_ASSISTANT.md)** - Fix validation errors with natural language
- **[API Hardening](./API_HARDENING.md)** - Ensure valid spec is also production-ready
- **[Security Analysis](./SECURITY_ANALYSIS.md)** - Validate security configuration

## 🔗 Additional Resources

- [OpenAPI 3.0 Specification](https://spec.openapis.org/oas/v3.0.0)
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [swagger-parser Documentation](https://github.com/swagger-api/swagger-parser)
- [JSON Schema Validation](https://json-schema.org/understanding-json-schema/)

## 🎓 Advanced Topics

### Custom Validation Rules

**Coming soon:** Define organization-specific validation rules

```yaml
custom-validation:
  - rule: require-x-correlation-id
    description: All operations must document X-Correlation-Id header
    paths: /**
    require:
      parameters:
        - name: X-Correlation-Id
          in: header
```

### External Reference Validation

**Coming soon:** Validate specifications split across multiple files

```yaml
# main.yaml
components:
  schemas:
    User:
      $ref: './schemas/user.yaml#/User'
```

---

[← Back to README](../../README.md) | [← Previous: Linter](./LINTER.md) | [Next: Security Analysis →](./SECURITY_ANALYSIS.md)
