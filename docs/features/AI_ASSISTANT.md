# 🤖 AI Assistant Feature

## Overview

The **AI Assistant** is SchemaSculpt's natural language interface for editing OpenAPI specifications. Instead of manually writing YAML/JSON, simply describe what you want in plain English and let AI make the changes. Powered by local LLMs via Ollama, the AI Assistant understands OpenAPI best practices and generates production-ready specifications.

## 🎯 What It Does

The AI Assistant can:

- **Add Endpoints**: "Add a GET endpoint for /health that returns 200 OK"
- **Create Schemas**: "Create a User schema with id, name, email, and createdAt fields"
- **Modify Operations**: "Add pagination parameters to GET /users"
- **Add Security**: "Add OAuth2 authentication to all /admin/* endpoints"
- **Generate Examples**: "Add realistic example data to all schemas"
- **Fix Issues**: "Fix all validation errors" or "Implement linter suggestions"
- **Explain Concepts**: "Explain what OAuth2 scopes are and how to use them"

## 🚀 How to Use

### Via UI (Assistant Tab)

1. Navigate to the **AI Features** panel
2. Click the **ASSISTANT** tab
3. Type your request in natural language
4. Choose processing mode:
   - **Normal Mode**: Single request-response
   - **Streaming Mode**: Real-time updates as AI generates changes
5. Click **"Process"** or **"Stream Process"**
6. Review changes in the Monaco editor
7. Accept, reject, or modify as needed

### Via API

```bash
POST /api/v1/sessions/{sessionId}/spec/ai-process
Content-Type: application/json

{
  "operationType": "MODIFY",
  "prompt": "Add a GET /health endpoint",
  "streaming": "DISABLED"
}
```

**Operation Types:**
- `MODIFY`: Modify existing specification
- `CREATE`: Generate new specification from scratch
- `EXPLAIN`: Get explanation (doesn't modify spec)

**Streaming Options:**
- `DISABLED`: Wait for complete response
- `REALTIME`: Stream updates via WebSocket

## 📋 Common Use Cases

### 1. Adding Endpoints

**Prompt:**
```
Add a POST /users endpoint that accepts name and email in the request body
and returns the created user with id, name, email, and createdAt fields.
```

**Result:**
```yaml
paths:
  /users:
    post:
      operationId: createUser
      summary: Create a new user
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [name, email]
              properties:
                name:
                  type: string
                email:
                  type: string
                  format: email
      responses:
        '201':
          description: User created successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                    format: uuid
                  name:
                    type: string
                  email:
                    type: string
                  createdAt:
                    type: string
                    format: date-time
```

---

### 2. Creating Schemas

**Prompt:**
```
Create an Order schema with orderId (UUID), customerId (UUID),
items (array of OrderItem), totalAmount (number), and status (enum).
OrderItem should have productId, quantity, and price.
```

**Result:**
```yaml
components:
  schemas:
    Order:
      type: object
      required: [orderId, customerId, items, totalAmount, status]
      properties:
        orderId:
          type: string
          format: uuid
        customerId:
          type: string
          format: uuid
        items:
          type: array
          items:
            $ref: '#/components/schemas/OrderItem'
        totalAmount:
          type: number
          format: double
        status:
          type: string
          enum: [pending, processing, shipped, delivered, cancelled]
    OrderItem:
      type: object
      required: [productId, quantity, price]
      properties:
        productId:
          type: string
          format: uuid
        quantity:
          type: integer
          minimum: 1
        price:
          type: number
          format: double
```

---

### 3. Adding Security

**Prompt:**
```
Add OAuth2 authentication to all endpoints under /admin/* with an 'admin' scope.
Public endpoints like /health and /docs should not require authentication.
```

**Result:**
```yaml
components:
  securitySchemes:
    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/oauth2/authorize
          tokenUrl: https://auth.example.com/oauth2/token
          scopes:
            admin: Administrative access

paths:
  /admin/users:
    get:
      security:
        - oauth2: [admin]
  /admin/settings:
    put:
      security:
        - oauth2: [admin]
  /health:
    get:
      security: []  # Public endpoint
```

---

### 4. Implementing Pagination

**Prompt:**
```
Add pagination to GET /users with limit and offset parameters,
and include total count in the response.
```

**Result:**
```yaml
paths:
  /users:
    get:
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
          description: Maximum number of users to return
        - name: offset
          in: query
          schema:
            type: integer
            minimum: 0
            default: 0
          description: Number of users to skip
      responses:
        '200':
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    type: object
                    properties:
                      total:
                        type: integer
                      limit:
                        type: integer
                      offset:
                        type: integer
```

---

### 5. Adding Examples

**Prompt:**
```
Add realistic example data to the User schema and all responses that use it.
```

**Result:**
```yaml
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          example: "123e4567-e89b-12d3-a456-426614174000"
        name:
          type: string
          example: "Jane Doe"
        email:
          type: string
          example: "jane.doe@example.com"
        createdAt:
          type: string
          format: date-time
          example: "2025-01-17T10:30:00Z"
```

---

### 6. Fixing Validation Errors

**Prompt:**
```
Fix all validation errors in my spec.
```

**AI analyzes errors and makes corrections:**
- Adds missing required fields (`info.title`, `info.version`)
- Fixes broken references
- Corrects schema types
- Adds missing response definitions

---

### 7. Implementing Best Practices

**Prompt:**
```
Make my API follow RESTful best practices and OpenAPI conventions.
```

**AI applies patterns:**
- Ensures proper HTTP methods (GET, POST, PUT, DELETE)
- Adds appropriate status codes (200, 201, 204, 400, 404, 500)
- Implements HATEOAS links where appropriate
- Adds operationIds, summaries, descriptions
- Ensures consistent naming conventions

---

## 🧠 AI Capabilities

### What the AI Understands

✅ **OpenAPI 3.x Syntax**
- Valid schema structures
- Reference formats (`$ref`)
- All OpenAPI keywords

✅ **REST Conventions**
- HTTP methods and semantics
- Status code meanings
- Resource naming patterns

✅ **Security Best Practices**
- OAuth2, API keys, JWT
- HTTPS requirements
- Authentication vs authorization

✅ **Data Modeling**
- Schema composition
- Type constraints and validation
- Relationships and references

✅ **API Design Patterns**
- Pagination strategies
- Error response formats (RFC 7807)
- Versioning approaches
- HATEOAS principles

### What the AI Cannot Do

❌ **Understand Your Business Logic**
- AI generates generic patterns, you must customize
- Review all AI-generated code before deployment

❌ **Access External Systems**
- Cannot fetch data from databases or APIs
- Cannot validate against live implementations

❌ **Guarantee Correctness**
- AI may generate syntactically valid but semantically incorrect specs
- Always validate and test generated specifications

❌ **Read Your Mind**
- Be specific in prompts for best results
- Vague requests get generic responses

## ⚙️ Processing Modes

### Normal Mode

**How it works:**
1. User submits prompt
2. AI analyzes current specification
3. AI generates changes
4. Complete result returned at once
5. Editor updated with new spec

**Best for:**
- Small changes
- Quick edits
- Batch operations

**Pros:**
- Simple, predictable
- Easy to review changes
- Transactional (all or nothing)

**Cons:**
- No progress feedback
- Can feel slow for large changes

---

### Streaming Mode

**How it works:**
1. User submits prompt
2. AI streams changes via WebSocket
3. Editor updates in real-time as AI generates
4. User sees progressive changes

**Best for:**
- Large specifications
- Complex modifications
- Interactive experience

**Pros:**
- Instant feedback
- See AI "thinking"
- Can cancel mid-stream

**Cons:**
- Partial updates if cancelled
- Harder to review changes
- Requires stable WebSocket connection

## 🏗️ Architecture

### Request Flow

```
User enters prompt in UI
         ↓
Frontend → API Gateway
         ↓
API Gateway → AI Service (Python FastAPI)
         ↓
AI Service → Ollama (LLM)
         ↓
Ollama generates response
         ↓
AI Service applies changes to spec
         ↓
Updated spec → API Gateway → Frontend
         ↓
Monaco Editor updates
```

### Backend Implementation

**Controller:** `SpecificationController.java`
**Location:** `api/src/main/java/.../controller/SpecificationController.java`

**Endpoint:** `POST /api/v1/sessions/{sessionId}/spec/ai-process`

**AI Service:** `LLMService` (Python FastAPI)
**Location:** `ai_service/app/services/llm_service.py`

**LLM Integration:**
- Uses Ollama API for inference
- Default model: `mistral` (configurable)
- Context window: 8K tokens
- Temperature: 0.7 (balanced creativity/accuracy)

### Frontend Implementation

**Component:** `AIAssistantTab` in `AIPanel.js`
**Location:** `ui/src/features/ai/components/AIPanel.js:94-200`

**State Management:** Zustand `aiSlice`
**Location:** `ui/src/store/slices/aiSlice.js`

**WebSocket:** For streaming mode
- Protocol: STOMP over SockJS
- Endpoint: `/ws/sessions/{sessionId}/ai-stream`

## 💡 Prompt Engineering Tips

### Be Specific

❌ **Vague:** "Add a user endpoint"
✅ **Specific:** "Add a POST /users endpoint that accepts name and email, returns 201 with created user including id"

### Provide Context

❌ **No Context:** "Add pagination"
✅ **With Context:** "Add cursor-based pagination to GET /posts endpoint with cursor, limit, and hasMore fields"

### Use Examples

❌ **Abstract:** "Add error handling"
✅ **With Example:** "Add error responses following RFC 7807 format with type, title, status, and detail fields"

### Break Down Complex Requests

❌ **Too Complex:** "Build a complete e-commerce API with products, orders, cart, checkout, and payments"
✅ **Step by Step:**
1. "Create Product schema with id, name, price, stock"
2. "Add GET /products endpoint with pagination"
3. "Add POST /products for creating products"
4. (Continue incrementally)

### Reference Standards

✅ **Good Prompts:**
- "Add authentication following OAuth2 best practices"
- "Implement error responses using RFC 7807"
- "Add HATEOAS links to navigation endpoints"
- "Follow REST conventions for CRUD operations"

## 🎯 Suggested Prompts

### Getting Started
```
- "Create a basic API spec for a blog with posts and comments"
- "Generate a user management API with CRUD operations"
- "Build a simple e-commerce product catalog API"
```

### Adding Features
```
- "Add search functionality to GET /products with query parameter"
- "Implement soft delete for users (add deletedAt field and filter)"
- "Add webhook endpoints for order status changes"
```

### Improving Quality
```
- "Add missing descriptions to all operations and schemas"
- "Generate realistic examples for all request and response bodies"
- "Add input validation constraints (min, max, pattern) to all fields"
```

### Security
```
- "Add JWT authentication with bearer token"
- "Implement API key authentication for external integrations"
- "Add rate limiting documentation to all endpoints"
```

### Documentation
```
- "Add detailed descriptions explaining what each endpoint does"
- "Generate examples showing common use cases"
- "Add tags to organize endpoints by feature"
```

## 🔍 Troubleshooting

### AI Response Is Inaccurate

**Issue:** AI generates wrong schema or endpoint

**Solution:**
1. Be more specific in your prompt
2. Provide examples of desired output
3. Reference OpenAPI spec sections
4. Break complex requests into smaller prompts

---

### Changes Not Applied

**Issue:** Prompt processed but spec unchanged

**Solution:**
1. Check AI response for errors
2. Verify spec is valid before AI processing
3. Review session logs for errors
4. Ensure Ollama service is running

---

### Streaming Stops Mid-Way

**Issue:** Streaming mode disconnects during processing

**Solution:**
1. Check WebSocket connection status
2. Verify network stability
3. Try normal (non-streaming) mode
4. Reduce prompt complexity

---

### AI Is Too Slow

**Issue:** Takes 30+ seconds to respond

**Solution:**
1. Check Ollama performance (`ollama list`)
2. Reduce spec size (split into modules)
3. Use more powerful LLM model
4. Ensure adequate system resources (RAM, CPU)

---

## 📚 Related Features

- **[Linter](./LINTER.md)** - AI can implement linter suggestions
- **[Validator](./VALIDATOR.md)** - AI can fix validation errors
- **[API Hardening](./API_HARDENING.md)** - AI can apply hardening patterns
- **[Security Analysis](./SECURITY_ANALYSIS.md)** - AI can fix security issues

## 🔗 Additional Resources

### OpenAPI Learning
- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [OpenAPI Tutorial](https://swagger.io/docs/specification/about/)
- [OpenAPI Examples](https://github.com/OAI/OpenAPI-Specification/tree/main/examples)

### API Design
- [RESTful API Design Best Practices](https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/)
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines)
- [Google API Design Guide](https://cloud.google.com/apis/design)

### LLM & Prompt Engineering
- [Ollama Documentation](https://ollama.com/docs)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)

## 🎓 Advanced Usage

### Custom LLM Models

**Change default model:**
```bash
# In ai_service/.env
OLLAMA_MODEL=llama3
```

**Available models:**
- `mistral` - Default, balanced performance
- `llama3` - Better reasoning, slower
- `codellama` - Optimized for code generation
- `phi` - Faster, less accurate

### Batch Processing

**Process multiple prompts:**
```javascript
const prompts = [
  "Add operationIds to all endpoints",
  "Add examples to all schemas",
  "Add 400 and 500 responses to all operations"
];

for (const prompt of prompts) {
  await processSpecification({ prompt, streaming: 'DISABLED' });
}
```

### Template-Based Generation

**Use templates for consistency:**
```
Use this template for all CRUD endpoints:

GET /{resource} - List all, with pagination (limit, offset)
GET /{resource}/{id} - Get by ID, 404 if not found
POST /{resource} - Create, return 201 with location header
PUT /{resource}/{id} - Full update, return 200
PATCH /{resource}/{id} - Partial update, return 200
DELETE /{resource}/{id} - Delete, return 204

Apply this template to create endpoints for: products, orders, customers
```

---

[← Back to README](../../README.md) | [← Previous: Attack Simulation](./ATTACK_SIMULATION.md)
