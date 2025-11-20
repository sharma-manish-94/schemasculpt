# SchemaSculpt Developer Onboarding Guide

## 🚀 Welcome to SchemaSculpt Development!

This comprehensive guide will help you contribute effectively to SchemaSculpt - an AI-powered OpenAPI specification editor with real-time validation and mock server capabilities.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Development Environment Setup](#development-environment-setup)
4. [Learning Path by Experience Level](#learning-path-by-experience-level)
5. [Component-Specific Onboarding](#component-specific-onboarding)
6. [Code Flow and Debugging Guide](#code-flow-and-debugging-guide)
7. [Essential Resources](#essential-resources)
8. [Common Development Patterns](#common-development-patterns)
9. [Testing Strategy](#testing-strategy)
10. [Contribution Guidelines](#contribution-guidelines)

---

## Quick Start

### Prerequisites Checklist
- [ ] **Java 17+** (for API component)
- [ ] **Node.js 18+** (for UI component)
- [ ] **Python 3.9+** (for AI component)
- [ ] **Docker** (for Redis and local development)
- [ ] **Git** (version control)
- [ ] **Your favorite IDE** (VS Code, IntelliJ, PyCharm)

### 5-Minute Demo Setup
```bash
# Clone the repository
git clone <repository-url>
cd schemasculpt

# Start Redis (required for session management)
docker run -d --name schemasculpt-redis -p 6379:6379 redis

# Start AI Service (Python)
cd ai_service
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload &

# Start API Gateway (Java)
cd ../api
./mvnw spring-boot:run &

# Start Frontend (React)
cd ../ui
npm install
npm start
```

🎉 **Access the application at**: http://localhost:3000

---

## Architecture Overview

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend (UI) │────│  API Gateway    │────│   AI Service    │
│                 │    │                 │    │                 │
│ React + Monaco  │    │ Spring Boot     │    │ FastAPI + LLM   │
│ Port: 3000      │    │ Port: 8080      │    │ Port: 8000      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │     Redis       │              │
         └──────────────│ (Session Store) │──────────────┘
                        │   Port: 6379    │
                        └─────────────────┘
```

### Data Flow Overview
1. **User Input** → Frontend (Monaco Editor)
2. **Spec Validation** → API Gateway → AI Service
3. **Real-time Updates** → WebSocket connection
4. **Session Management** → Redis storage
5. **AI Processing** → Ollama/LLM integration

---

## Learning Path by Experience Level

### 🌱 Beginner Developer

**Focus**: Understanding basics and getting comfortable with each technology stack

#### Week 1: Foundation Knowledge
**Before touching any code**, study these resources:

1. **Web Development Basics**:
   - [MDN Web Docs - JavaScript](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
   - [React Tutorial](https://reactjs.org/tutorial/tutorial.html)

2. **OpenAPI Specification**:
   - [OpenAPI 3.0 Specification](https://swagger.io/specification/)
   - [OpenAPI Tutorial](https://support.smartbear.com/swaggerhub/docs/tutorials/openapi-3-tutorial.html)

3. **Basic Spring Boot**:
   - [Spring Boot Getting Started](https://spring.io/guides/gs/spring-boot/)

4. **Python FastAPI Basics**:
   - [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

#### Week 2: Code Exploration Order
1. **Start with UI** (most visual feedback):
   ```
   ui/src/
   ├── App.js                    # Start here - main application structure
   ├── components/Editor/        # Monaco editor integration
   ├── api/services.js          # API communication layer
   └── store/slices/            # State management (Zustand)
   ```

2. **Move to API Gateway**:
   ```
   api/src/main/java/.../
   ├── SchemasculptApiApplication.java    # Application entry point
   ├── controller/SpecController.java     # REST endpoints
   ├── service/SessionService.java       # Business logic
   └── config/WebSocketConfig.java       # Real-time features
   ```

3. **Finally AI Service**:
   ```
   ai_service/app/
   ├── main.py                   # FastAPI application
   ├── api/endpoints.py          # AI endpoints
   ├── services/llm_service.py   # Core AI logic
   └── schemas/ai_schemas.py     # Data models
   ```

#### Beginner-Friendly Debugging Strategy
1. **Use browser DevTools** for frontend debugging
2. **Add console.log() statements** to trace React component lifecycle
3. **Use Spring Boot Actuator** endpoints for API health checks
4. **Add Python print() statements** for AI service debugging

### 🎯 Intermediate Developer

**Focus**: Understanding component interactions and implementing features

#### Prerequisites to Review:
1. **Advanced React Patterns**:
   - [React Hooks in Depth](https://reactjs.org/docs/hooks-intro.html)
   - [State Management with Zustand](https://github.com/pmndrs/zustand)

2. **Spring Boot Advanced**:
   - [Spring WebSocket](https://spring.io/guides/gs/messaging-stomp-websocket/)
   - [Spring Data Redis](https://spring.io/projects/spring-data-redis)

3. **AI/ML Concepts**:
   - [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction.html)
   - [Ollama Documentation](https://ollama.ai/docs)

#### Code Flow Understanding Priority:
1. **User Interaction Flow**:
   ```
   Monaco Editor Input → Zustand State Update → API Call → AI Processing → WebSocket Response → UI Update
   ```

2. **Session Management Flow**:
   ```
   User Login → Session Creation → Redis Storage → WebSocket Connection → Real-time Updates
   ```

3. **AI Processing Flow**:
   ```
   Spec Input → Validation → LLM Processing → Response Generation → Format Output
   ```

#### Advanced Debugging Techniques:
- **React DevTools** for component state inspection
- **Spring Boot Logging** configuration for detailed API logs
- **FastAPI Automatic Docs** at http://localhost:8000/docs for AI API testing

### 🚀 Advanced Developer

**Focus**: Architecture decisions, performance optimization, and extending the system

#### Prerequisites:
1. **System Design Concepts**:
   - Microservices architecture patterns
   - Real-time system design
   - Caching strategies

2. **Advanced AI Concepts**:
   - Multi-agent workflows
   - RAG (Retrieval-Augmented Generation)
   - Prompt engineering

#### Code Architecture Analysis:
1. **Study design patterns** used in each component
2. **Understand performance bottlenecks** and optimization strategies
3. **Analyze security implementations** across all layers
4. **Review error handling** and resilience patterns

---

## Component-Specific Onboarding

### 🎨 Frontend (UI) Component

#### Technology Stack
- **React 19** - Component framework
- **Monaco Editor** - Code editor (VS Code editor in browser)
- **Zustand** - State management
- **SockJS/StompJS** - WebSocket communication
- **react-resizable-panels** - UI layout

#### Learning Resources (Read Before Coding)
1. **Monaco Editor Integration**:
   - [Monaco Editor Documentation](https://microsoft.github.io/monaco-editor/)
   - [Monaco Language Services](https://github.com/microsoft/monaco-editor/tree/main/src/basic-languages)

2. **WebSocket in React**:
   - [SockJS Documentation](https://github.com/sockjs/sockjs-client)
   - [STOMP over WebSocket](https://stomp-js.github.io/guide/stompjs/rx-stomp/ng2-stompjs/2018/09/08/using-stompjs-v5.html)

#### Code Reading Order
```
ui/src/
├── 1. App.js                           # Application structure
├── 2. features/editor/
│   ├── Editor.js                       # Main editor component
│   ├── ValidationPanel.js              # Real-time validation display
│   └── MockServerPanel.js              # Mock server interface
├── 3. api/
│   ├── services.js                     # HTTP API calls
│   └── websocket.js                    # WebSocket management
├── 4. store/slices/
│   ├── coreSlice.js                    # Main application state
│   ├── aiSlice.js                      # AI-related state
│   └── validationSlice.js              # Validation state
└── 5. components/                      # Shared UI components
```

#### Key Concepts to Understand
1. **Editor Integration**: How Monaco Editor is configured for OpenAPI
2. **State Flow**: How user actions trigger state updates
3. **Real-time Updates**: WebSocket connection and message handling
4. **Error Boundaries**: How errors are caught and displayed

#### Common UI Debugging Flow
```javascript
// 1. Check component state in React DevTools
// 2. Verify API calls in Network tab
// 3. Monitor WebSocket messages in Console
// 4. Check Zustand state in Redux DevTools (if installed)

// Example debugging code
console.log('Editor content:', editorContent);
console.log('Validation results:', validationResults);
console.log('WebSocket status:', wsConnection.connected);
```

### ⚙️ Backend API Gateway Component

#### Technology Stack
- **Spring Boot 3** - Framework
- **Spring WebSocket** - Real-time communication
- **Spring Data Redis** - Session storage
- **Spring Security** - Authentication/authorization
- **Jackson** - JSON processing

#### Learning Resources (Essential Reading)
1. **Spring Boot Architecture**:
   - [Spring Boot Reference Guide](https://docs.spring.io/spring-boot/docs/current/reference/html/)
   - [Spring WebSocket Guide](https://spring.io/guides/gs/messaging-stomp-websocket/)

2. **Redis Integration**:
   - [Spring Data Redis Reference](https://docs.spring.io/spring-data/redis/docs/current/reference/html/)

#### Code Reading Order
```
api/src/main/java/.../schemasculpt_api/
├── 1. SchemasculptApiApplication.java         # Main application
├── 2. config/
│   ├── WebSocketConfig.java                  # WebSocket configuration
│   ├── RedisConfig.java                      # Redis setup
│   └── CorsConfig.java                       # CORS settings
├── 3. controller/
│   ├── SpecController.java                   # OpenAPI spec endpoints
│   ├── WebSocketController.java              # Real-time endpoints
│   └── HealthController.java                 # Health checks
├── 4. service/
│   ├── SessionService.java                   # Session management
│   ├── ValidationService.java                # Spec validation
│   └── AIIntegrationService.java             # AI service communication
├── 5. dto/                                   # Data transfer objects
└── 6. model/                                 # Entity models
```

#### Key Concepts to Master
1. **Session Management**: How sessions are created and stored in Redis
2. **WebSocket Handling**: Real-time communication patterns
3. **AI Service Integration**: HTTP client configuration and error handling
4. **Validation Pipeline**: How specifications are validated

#### Backend Debugging Strategy
```java
// 1. Enable debug logging in application.yml
logging:
  level:
    com.schemasculpt: DEBUG
    org.springframework.web.socket: DEBUG

// 2. Use breakpoints in key methods
@GetMapping("/api/specs/{id}")
public ResponseEntity<SpecDto> getSpec(@PathVariable String id) {
    log.debug("Fetching spec with id: {}", id);  // Add logging
    // Breakpoint here
    return specService.getSpec(id);
}

// 3. Monitor Redis operations
@Autowired
private RedisTemplate<String, Object> redisTemplate;

// Check session data
Object sessionData = redisTemplate.opsForHash().get("session:" + sessionId, "data");
```

### 🤖 AI Service Component

#### Technology Stack
- **FastAPI** - Web framework
- **Pydantic** - Data validation
- **Ollama** - Local LLM integration
- **OpenAPI Spec Validator** - Specification validation
- **AsyncIO** - Asynchronous processing

#### Learning Resources (Critical Reading)
1. **FastAPI Mastery**:
   - [FastAPI Documentation](https://fastapi.tiangolo.com/)
   - [Async/Await in Python](https://docs.python.org/3/library/asyncio.html)

2. **LLM Integration**:
   - [Ollama Python Library](https://github.com/ollama/ollama-python)
   - [Prompt Engineering Guide](https://www.promptingguide.ai/)

3. **OpenAPI Processing**:
   - [Prance Documentation](https://prance.readthedocs.io/)
   - [OpenAPI Spec Validator](https://github.com/p1c2u/openapi-spec-validator)

#### Code Reading Order
```
ai_service/app/
├── 1. main.py                          # FastAPI application setup
├── 2. api/
│   └── endpoints.py                    # API endpoints (start here)
├── 3. services/
│   ├── llm_service.py                  # Core LLM integration
│   ├── intelligent_workflow.py        # Multi-agent workflows
│   └── agent_manager.py               # Agent orchestration
├── 4. schemas/
│   └── ai_schemas.py                   # Pydantic models
├── 5. core/
│   ├── config.py                       # Configuration
│   ├── logging.py                      # Logging setup
│   └── exceptions.py                   # Custom exceptions
└── 6. requirements.txt                 # Dependencies
```

#### Essential AI Concepts
1. **Prompt Engineering**: How prompts are structured for different operations
2. **Async Processing**: Understanding Python async/await patterns
3. **Multi-Agent Workflows**: How different AI agents collaborate
4. **Error Handling**: LLM failure scenarios and fallbacks

#### AI Service Debugging
```python
# 1. Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# 2. Add debug prints in key functions
async def process_ai_request(self, request: AIRequest):
    logger.debug(f"Processing request: {request.operation_type}")
    logger.debug(f"Spec length: {len(request.spec_text)}")

    # Add breakpoint here for debugging
    result = await self._call_llm_with_retry(messages, params)
    logger.debug(f"LLM response length: {len(result)}")

    return result

# 3. Test individual components
# Use FastAPI's automatic docs at http://localhost:8000/docs
```

---

## Code Flow and Debugging Guide

### 🔍 Complete Request Flow Tracing

#### Scenario: User Edits OpenAPI Spec and Gets AI Suggestions

**Step 1: Frontend (UI)**
```javascript
// File: ui/src/features/editor/Editor.js
const handleEditorChange = (value) => {
  // 1. User types in Monaco Editor
  console.log('Editor content changed:', value);

  // 2. Update Zustand state
  setCoreState({ specContent: value });

  // 3. Trigger validation after debounce
  debouncedValidation(value);
};

// Debug: Check state in React DevTools
```

**Step 2: API Gateway (Java)**
```java
// File: api/src/main/java/.../controller/SpecController.java
@PostMapping("/api/specs/validate")
public ResponseEntity<ValidationResult> validateSpec(@RequestBody SpecDto spec) {
    log.debug("Received spec for validation: {} chars", spec.getContent().length());

    // 4. Validate locally first
    ValidationResult localResult = validationService.validateLocally(spec);

    // 5. Send to AI service if needed
    if (spec.isAiAnalysisRequested()) {
        aiResult = aiIntegrationService.analyze(spec);
    }

    return ResponseEntity.ok(result);
}

// Debug: Set breakpoint here, check logs
```

**Step 3: AI Service (Python)**
```python
# File: ai_service/app/services/llm_service.py
async def process_ai_request(self, request: AIRequest):
    logger.debug(f"AI request received: {request.operation_type}")

    # 6. Multi-agent workflow processing
    if request.operation_type == "analyze":
        result = await self.intelligent_workflow.analyze_specification(request)

    # 7. Return structured response
    return AIResponse(
        updated_spec_text=result.spec,
        validation=result.validation,
        suggestions=result.suggestions
    )

# Debug: Add print statements, use FastAPI docs for testing
```

**Step 4: WebSocket Real-time Updates**
```java
// File: api/src/main/java/.../controller/WebSocketController.java
@MessageMapping("/spec/update")
public void handleSpecUpdate(SpecUpdate update, SimpMessageHeaderAccessor headerAccessor) {
    String sessionId = headerAccessor.getSessionId();

    // 8. Process update and broadcast to connected clients
    messagingTemplate.convertAndSend("/topic/spec/" + sessionId, update);
}

// Debug: Monitor WebSocket messages in browser DevTools
```

### 🐛 Common Debugging Scenarios

#### Problem: "AI Service Not Responding"
**Debug Steps**:
1. Check AI service logs: `docker logs schemasculpt-ai`
2. Verify Ollama is running: `ollama list`
3. Test AI endpoint directly: http://localhost:8000/docs
4. Check API Gateway logs for HTTP client errors

#### Problem: "WebSocket Connection Failed"
**Debug Steps**:
1. Check browser console for WebSocket errors
2. Verify CORS configuration in API Gateway
3. Test WebSocket endpoint with tools like wscat
4. Check Redis connection for session storage

#### Problem: "Editor Not Updating"
**Debug Steps**:
1. Check React component state in DevTools
2. Verify Zustand state updates
3. Check if Monaco Editor event handlers are bound
4. Validate API response format

---

## Essential Resources

### 📚 Documentation Links

#### Frontend Resources
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [Monaco Editor API](https://microsoft.github.io/monaco-editor/api/index.html)
- [Zustand Documentation](https://github.com/pmndrs/zustand)
- [WebSocket Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications)

#### Backend Resources
- [Spring Boot Reference](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Spring WebSocket Guide](https://spring.io/guides/gs/messaging-stomp-websocket/)
- [Redis Commands Reference](https://redis.io/commands/)
- [HTTP Client Best Practices](https://docs.spring.io/spring-framework/docs/current/reference/html/integration.html#rest-client-access)

#### AI/ML Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [OpenAPI Specification](https://swagger.io/specification/)

#### DevOps Resources
- [Docker Documentation](https://docs.docker.com/)
- [Redis Documentation](https://redis.io/documentation)
- [Logging Best Practices](https://12factor.net/logs)

### 🛠️ Development Tools

#### Essential IDE Extensions
**VS Code**:
- ES7+ React/Redux/React-Native snippets
- Spring Boot Extension Pack
- Python extension
- Docker extension
- REST Client

**IntelliJ IDEA**:
- Spring Boot plugin
- OpenAPI Specifications plugin
- Database Tools and SQL

#### Browser Extensions
- React Developer Tools
- Redux DevTools (for Zustand)
- WebSocket Inspector

#### Command Line Tools
```bash
# API testing
curl -X POST http://localhost:8080/api/specs/validate

# WebSocket testing
wscat -c ws://localhost:8080/ws

# Redis inspection
redis-cli -h localhost -p 6379

# Docker monitoring
docker stats
```

---

## Common Development Patterns

### 🔄 State Management Patterns

#### Frontend State (Zustand)
```javascript
// File: ui/src/store/slices/coreSlice.js
const useCoreStore = create((set, get) => ({
  // State
  specContent: '',
  validationResults: null,

  // Actions
  updateSpec: (content) => set({ specContent: content }),

  // Async actions
  validateSpec: async () => {
    const { specContent } = get();
    const results = await api.validateSpec(specContent);
    set({ validationResults: results });
  }
}));

// Usage in components
const { specContent, updateSpec } = useCoreStore();
```

#### Backend Session Management
```java
// File: api/src/main/java/.../service/SessionService.java
@Service
public class SessionService {

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public void storeSession(String sessionId, SessionData data) {
        String key = "session:" + sessionId;
        redisTemplate.opsForHash().putAll(key, data.toMap());
        redisTemplate.expire(key, Duration.ofHours(24));
    }
}
```

### 🚀 API Communication Patterns

#### Frontend API Client
```javascript
// File: ui/src/api/services.js
class ApiService {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8080';
  }

  async validateSpec(specContent) {
    try {
      const response = await fetch(`${this.baseURL}/api/specs/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: specContent })
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }
}
```

#### Backend HTTP Client
```java
// File: api/src/main/java/.../service/AIIntegrationService.java
@Service
public class AIIntegrationService {

    @Autowired
    private WebClient aiServiceClient;

    public Mono<AIResponse> analyzeSpec(SpecDto spec) {
        return aiServiceClient
            .post()
            .uri("/ai/process")
            .bodyValue(spec)
            .retrieve()
            .bodyToMono(AIResponse.class)
            .timeout(Duration.ofSeconds(30))
            .onErrorResume(this::handleAIServiceError);
    }
}
```

### 🤖 AI Processing Patterns

#### Multi-Agent Workflow
```python
# File: ai_service/app/services/intelligent_workflow.py
class IntelligentOpenAPIWorkflow:
    async def generate_specification(self, request: GenerateSpecRequest):
        # Phase 1: Domain Analysis
        domain_model = await self._analyze_domain(request)

        # Phase 2: Path Structure Generation
        path_operations = self._generate_path_structure(domain_model, request)

        # Phase 3: Schema Generation
        schemas = await self._generate_schemas(domain_model, path_operations)

        # Phase 4: Assembly & Validation
        final_spec = self._assemble_specification(
            request, domain_model, path_operations, schemas
        )

        return AIResponse(
            updated_spec_text=json.dumps(final_spec, indent=2),
            operation_type="generate",
            validation=self._validate_specification(final_spec)
        )
```

---

## Testing Strategy

### 🧪 Frontend Testing

#### Component Testing with Jest
```javascript
// File: ui/src/components/__tests__/Editor.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import { Editor } from '../Editor';

describe('Editor Component', () => {
  test('should update content on user input', () => {
    render(<Editor initialContent="" />);

    const editor = screen.getByRole('textbox');
    fireEvent.change(editor, { target: { value: 'openapi: 3.0.0' } });

    expect(editor.value).toBe('openapi: 3.0.0');
  });
});
```

#### Integration Testing
```javascript
// File: ui/src/__tests__/integration/SpecValidation.test.js
import { render, waitFor } from '@testing-library/react';
import { App } from '../App';

test('should validate spec and show results', async () => {
  // Mock API response
  fetch.mockResolvedValueOnce({
    ok: true,
    json: () => Promise.resolve({ isValid: true, errors: [] })
  });

  render(<App />);

  // User interactions...

  await waitFor(() => {
    expect(screen.getByText('Validation passed')).toBeInTheDocument();
  });
});
```

### 🧪 Backend Testing

#### Unit Testing with JUnit 5
```java
// File: api/src/test/java/.../service/SessionServiceTest.java
@ExtendWith(MockitoExtension.class)
class SessionServiceTest {

    @Mock
    private RedisTemplate<String, Object> redisTemplate;

    @InjectMocks
    private SessionService sessionService;

    @Test
    void shouldStoreSessionSuccessfully() {
        // Given
        String sessionId = "test-session";
        SessionData data = new SessionData("user123");

        // When
        sessionService.storeSession(sessionId, data);

        // Then
        verify(redisTemplate.opsForHash()).putAll(eq("session:" + sessionId), any());
    }
}
```

#### Integration Testing with TestContainers
```java
// File: api/src/test/java/.../integration/RedisIntegrationTest.java
@SpringBootTest
@Testcontainers
class RedisIntegrationTest {

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
            .withExposedPorts(6379);

    @Test
    void shouldStoreAndRetrieveSession() {
        // Test with real Redis instance
    }
}
```

### 🧪 AI Service Testing

#### FastAPI Testing
```python
# File: ai_service/tests/test_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/ai/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_spec_generation():
    request_data = {
        "prompt": "Create a simple user API",
        "domain": "users",
        "complexity_level": "simple"
    }

    response = client.post("/ai/generate", json=request_data)
    assert response.status_code == 200

    result = response.json()
    assert "updated_spec_text" in result
    assert result["operation_type"] == "generate"
```

### 🧪 End-to-End Testing

#### Playwright E2E Tests
```javascript
// File: e2e/tests/spec-editing.spec.js
import { test, expect } from '@playwright/test';

test('complete spec editing workflow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Load spec
  await page.getByTestId('editor').fill('openapi: "3.0.0"');

  // Trigger validation
  await page.getByRole('button', { name: 'Validate' }).click();

  // Check results
  await expect(page.getByTestId('validation-results')).toContainText('Valid');

  // Test AI features
  await page.getByRole('button', { name: 'AI Enhance' }).click();
  await expect(page.getByTestId('ai-suggestions')).toBeVisible();
});
```

---

## Contribution Guidelines

### 🔄 Development Workflow

#### 1. Feature Development Process
```bash
# Create feature branch
git checkout -b feature/ai-analysis-improvement

# Make changes and test locally
npm test                    # Frontend tests
./mvnw test                # Backend tests
pytest                     # AI service tests

# Commit with clear messages
git commit -m "feat: improve AI analysis accuracy for security recommendations"

# Push and create PR
git push origin feature/ai-analysis-improvement
```

#### 2. Code Review Checklist
- [ ] **Functionality**: Feature works as expected
- [ ] **Tests**: Adequate test coverage (>80%)
- [ ] **Documentation**: Code is well-documented
- [ ] **Performance**: No performance regressions
- [ ] **Security**: No security vulnerabilities
- [ ] **API Compatibility**: Backward compatibility maintained

#### 3. Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] E2E tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)

## Additional Notes
```

### 🚨 Common Pitfalls and Solutions

#### Frontend Pitfalls
1. **State Updates Not Reflecting**: Use React DevTools to check state flow
2. **WebSocket Connection Issues**: Verify connection status and error handling
3. **Monaco Editor Performance**: Implement proper debouncing for large specs

#### Backend Pitfalls
1. **Session Management**: Ensure proper Redis key expiration
2. **WebSocket Scaling**: Consider sticky sessions for multi-instance deployment
3. **AI Service Timeouts**: Implement proper timeout and retry logic

#### AI Service Pitfalls
1. **LLM Response Consistency**: Implement validation and fallback mechanisms
2. **Memory Usage**: Monitor memory usage with large specification processing
3. **Async Code**: Proper error handling in async workflows

### 📊 Performance Monitoring

#### Key Metrics to Track
```javascript
// Frontend Performance
const performanceMetrics = {
  editorLoadTime: performance.mark('editor-loaded'),
  validationResponseTime: performance.measure('validation-duration'),
  memoryUsage: performance.memory.usedJSHeapSize
};

// Backend Performance (Spring Boot Actuator)
// http://localhost:8080/actuator/metrics
// - http.server.requests
// - redis.connections.active
// - ai.service.response.time

// AI Service Performance
import time
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('ai_requests_total', 'Total AI requests')
REQUEST_DURATION = Histogram('ai_request_duration_seconds', 'AI request duration')
```

---

## 🎯 Next Steps After Onboarding

### Immediate Tasks (First Week)
1. **Set up development environment** and run all components
2. **Complete a small bug fix** to understand the workflow
3. **Add a simple feature** (e.g., new validation rule)
4. **Write tests** for your changes

### Intermediate Goals (First Month)
1. **Implement a new AI analysis feature**
2. **Improve UI/UX** for a specific component
3. **Optimize performance** in one area
4. **Add comprehensive documentation** for a feature

### Advanced Contributions (Ongoing)
1. **Design and implement** multi-agent AI workflows
2. **Contribute to architecture decisions**
3. **Mentor new developers**
4. **Lead feature development** initiatives

### 🤝 Getting Help

#### Communication Channels
- **Development Questions**: Create GitHub issues with detailed descriptions
- **Architecture Discussions**: Use GitHub Discussions
- **Code Reviews**: Comment directly on pull requests

#### Escalation Path
1. **Technical Issues**: Check documentation first, then ask team
2. **Architecture Decisions**: Discuss with senior developers
3. **Priority Conflicts**: Escalate to project maintainers

---

## 📝 Conclusion

Welcome to the SchemaSculpt development team! This guide provides a comprehensive foundation for contributing to our AI-powered OpenAPI platform. Remember:

- **Start small** and gradually take on more complex features
- **Ask questions** when you're stuck - the team is here to help
- **Document your learnings** to help future developers
- **Focus on quality** over speed - good code is maintainable code

Happy coding! 🚀

---

*Last updated: [Current Date]*
*Next review: [Review Date]*