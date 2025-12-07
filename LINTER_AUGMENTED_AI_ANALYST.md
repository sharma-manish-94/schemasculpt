# Linter-Augmented AI Analyst Implementation

## Overview

The **Linter-Augmented AI Analyst** is an advanced feature that combines deterministic linting with AI-powered meta-analysis to detect higher-order patterns, security threats, and design issues in OpenAPI specifications.

## Architecture

### Flow

1. **Frontend** → User clicks "Run AI Analysis" button in ValidationPanel
2. **Java Backend** → Collects linter findings (errors + suggestions)
3. **Java Backend** → Sends spec + linter findings to Python AI service
4. **Python AI Service** → Uses LLM to perform meta-analysis
5. **Python AI Service** → Returns AI insights with patterns detected
6. **Frontend** → Displays insights in AIInsightsPanel

### Key Innovation

Instead of asking the AI to find basic issues (which linters already do), we give the AI:
- The complete OpenAPI specification
- All linter findings (errors and suggestions)

This allows the AI to focus on **higher-level reasoning**:
- Pattern detection across multiple issues
- Security vulnerabilities from combinations of issues
- Design anti-patterns spanning multiple endpoints
- Governance violations

## Components Implemented

### Backend (Java)

#### 1. DTOs
- **`AIMetaAnalysisRequest.java`** - Request containing spec + linter findings
- **`AIMetaAnalysisResponse.java`** - Response with AI insights
  - Contains `AIInsight` records with title, description, severity, category, affected paths, related issues

#### 2. Controller
- **`SpecificationController.java`**
  - New endpoint: `POST /api/v1/sessions/{sessionId}/spec/ai-analysis`
  - Runs validation, collects findings, calls AI service

#### 3. Service
- **`AIService.java`**
  - New method: `performMetaAnalysis(AIMetaAnalysisRequest)`
  - Calls Python AI service at `/ai/meta-analysis`

### AI Service (Python)

#### 1. Schemas
- **`meta_analysis_schemas.py`**
  - `AIMetaAnalysisRequest` - Receives spec + errors + suggestions
  - `AIMetaAnalysisResponse` - Returns insights + summary + confidence
  - `AIInsight` - Individual insight with severity, category, etc.

#### 2. Service
- **`MetaAnalysisService.py`**
  - Builds augmented prompt with linter findings
  - Calls LLM for pattern detection
  - Parses and structures AI response

#### 3. API Endpoint
- **`endpoints.py`**
  - New route: `POST /ai/meta-analysis`
  - Handles meta-analysis requests

### Frontend (React)

#### 1. UI Component
- **`AIInsightsPanel.js`** + **`AIInsightsPanel.css`**
  - Displays AI insights with expandable cards
  - Shows severity icons (🔴 critical, 🟠 high, etc.)
  - Shows category icons (🔐 security, 🎨 design, etc.)
  - Confidence score badge
  - "Run AI Analysis" / "Refresh" button

#### 2. State Management
- **`validationSlice.js`**
  - New state: `aiInsights`, `aiSummary`, `aiConfidenceScore`, `isAIAnalysisLoading`
  - New action: `runAIMetaAnalysis()`

#### 3. API Integration
- **`validationService.js`**
  - New function: `performAIMetaAnalysis(sessionId)`
  - 60-second timeout for AI processing

#### 4. Integration
- **`ValidationPanel.js`**
  - Imports and renders `AIInsightsPanel`
  - Passes AI state and actions as props

## Example Use Cases

### Security Threat Detection
**Linter Findings:**
1. GET /users/{id} - Missing security scheme
2. User schema - Contains `email`, `address`, `ssn` fields

**AI Insight:**
> **Critical Security Threat**: The endpoint GET /users/{id} is publicly accessible but returns a User schema containing multiple forms of PII (email, address, SSN). This creates a high risk of data leak.

### Design Pattern Issues
**Linter Findings:**
1. Multiple endpoints missing operationId
2. Inconsistent path naming (camelCase vs kebab-case)
3. Missing descriptions across several operations

**AI Insight:**
> **Design Inconsistency**: The API lacks standardization in naming conventions and documentation. This suggests incomplete API governance and will make the API difficult to maintain and consume.

### Performance Concerns
**Linter Findings:**
1. GET /products - Missing pagination parameters
2. GET /products - No caching headers
3. Large response schemas with nested objects

**AI Insight:**
> **Performance Risk**: The /products endpoint returns large datasets without pagination or caching, which will cause performance issues at scale. Consider adding limit/offset parameters and Cache-Control headers.

## Testing

To test the implementation:

1. **Start all services:**
   ```bash
   # Redis
   docker run -d --name schemasculpt-redis -p 6379:6379 redis

   # Ollama with mistral model
   ollama pull mistral

   # AI Service
   cd ai_service && uvicorn app.main:app --reload

   # Backend
   cd api && ./mvnw spring-boot:run

   # Frontend
   cd ui && npm start
   ```

2. **Create a session and load a spec with issues**

3. **Click "Run AI Analysis"** in the Validation panel

4. **Observe AI insights** that connect multiple linter findings

## Future Enhancements

1. **Caching** - Cache analysis results for specs that haven't changed
2. **Configurable Rules** - Allow users to configure which patterns to detect
3. **Auto-Fix Suggestions** - AI generates fixes for detected patterns
4. **Historical Tracking** - Track how issues evolve over time
5. **Integration with RAG** - Use security knowledge base for more accurate threat detection

## Files Modified/Created

### Backend
- `api/src/main/java/.../dto/AIMetaAnalysisRequest.java` (NEW)
- `api/src/main/java/.../dto/AIMetaAnalysisResponse.java` (NEW)
- `api/src/main/java/.../controller/SpecificationController.java` (MODIFIED)
- `api/src/main/java/.../service/ai/AIService.java` (MODIFIED)

### AI Service
- `ai_service/app/schemas/meta_analysis_schemas.py` (NEW)
- `ai_service/app/services/meta_analysis_service.py` (NEW)
- `ai_service/app/api/endpoints.py` (MODIFIED)

### Frontend
- `ui/src/components/validation/AIInsightsPanel.js` (NEW)
- `ui/src/components/validation/AIInsightsPanel.css` (NEW)
- `ui/src/store/slices/validationSlice.js` (MODIFIED)
- `ui/src/api/validationService.js` (MODIFIED)
- `ui/src/features/editor/components/ValidationPanel.js` (MODIFIED)

## Summary

This implementation successfully creates a **synergy between deterministic linters and AI reasoning**. The linters do what they're good at (finding factual issues quickly and reliably), and the AI does what it's good at (connecting dots and detecting patterns that require understanding context and relationships).
