# SchemaSculpt API Bruno Collection

This Bruno collection provides comprehensive testing coverage for all SchemaSculpt Spring Boot API endpoints, including the new AI service integration features.

## Setup

1. **Install Bruno**: Download and install Bruno from [https://www.usebruno.com/](https://www.usebruno.com/)

2. **Import Collection**: Open Bruno and import this collection by selecting the `bruno-collection` folder

3. **Configure Environment**:
   - Select the "Development" environment
   - Update the variables in `environments/Development.bru` if your services are running on different ports:
     - `baseUrl`: Spring Boot API URL (default: http://localhost:8080)
     - `aiServiceUrl`: AI Service URL (default: http://localhost:8000)
     - Update sample IDs as needed for testing

## Prerequisites

Before running the collection, ensure all services are running:

1. **Redis**: Required for session management
   ```bash
   docker run -d --name schemasculpt-redis -p 6379:6379 redis
   ```

2. **AI Service**: Python FastAPI service
   ```bash
   cd ai_service
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

3. **Spring Boot API**: Java backend service
   ```bash
   cd api
   mvn spring-boot:run
   ```

4. **Ollama**: Required for AI functionality
   ```bash
   ollama pull mistral
   ```

## Collection Structure

### 1. AI Processing (`/AI Processing/`)
Core AI functionality endpoints:
- **Process Specification**: Enhanced AI processing with streaming support
- **Generate Specification**: Complete OpenAPI spec generation using agentic workflows
- **Execute Workflow**: Run predefined AI workflows
- **Execute Custom Workflow**: Run ad-hoc custom workflows
- **Get Available Workflows**: List all available workflow templates
- **AI Health Check**: Comprehensive health check for AI services

### 2. AI Context (`/AI Context/`)
Context and session management:
- **Create Session**: Create new AI conversation sessions
- **Get Session Summary**: Retrieve session history and context
- **Get Context Statistics**: Overall context management statistics

### 3. AI Prompt (`/AI Prompt/`)
Intelligent prompt engineering:
- **Generate Intelligent Prompt**: Create context-aware prompts
- **Get Prompt Statistics**: Prompt engine performance metrics
- **Use Prompt Template**: Apply predefined prompt templates
- **Get Available Templates**: List available prompt templates
- **Optimize Prompt**: Improve prompt clarity and effectiveness

### 4. AI Agents (`/AI Agents/`)
AI agent management and monitoring:
- **Get Agents Status**: Overall agent health and status
- **Get Specific Agent Status**: Individual agent monitoring
- **Get Agents Performance**: Performance metrics and analytics
- **Get Agents Capabilities**: Available agent capabilities and features

### 5. Enhanced Mock Server (`/Enhanced Mock Server/`)
AI-powered mock server functionality:
- **Start Mock Server**: Create AI-enhanced mock servers
- **Get Mock Server Info**: Retrieve mock server details
- **Update Mock Server**: Modify existing mock servers
- **Get Mock Service Health**: Mock service health status

### 6. Session-Based AI (`/Session-Based AI/`)
Session-integrated AI operations:
- **Process Advanced AI**: Session-aware AI processing
- **Generate Specification for Session**: Session-scoped spec generation
- **Execute Session Workflow**: Run workflows within session context
- **Analyze Specification**: In-depth specification analysis
- **Optimize Specification**: Session-based optimization

### 7. Legacy Endpoints (`/Legacy Endpoints/`)
Backward-compatible existing functionality:
- **Validate Specification**: OpenAPI specification validation
- **Apply Quick Fix**: Automated specification fixes
- **Transform Specification**: Basic AI transformations

## Testing Strategy

### Unit Tests
Each request includes comprehensive tests that verify:
- HTTP status codes
- Response structure and required properties
- Data types and constraints
- Business logic validation

### Integration Tests
The collection tests the full integration between:
- Spring Boot API ↔ AI Service communication
- Session management with Redis
- AI service ↔ Ollama integration

### Error Handling
Tests cover various error scenarios:
- AI service unavailable
- Invalid request payloads
- Session not found
- Authentication failures

## Usage Examples

### Basic Workflow
1. **Health Check**: Start with `AI Processing/AI Health Check` to verify all services
2. **Create Session**: Use `AI Context/Create Session` to establish a working context
3. **Process Specification**: Use any of the AI processing endpoints with your OpenAPI spec

### Advanced Workflow
1. **Generate New Spec**: Use `AI Processing/Generate Specification` for complete spec creation
2. **Analyze Results**: Use `Session-Based AI/Analyze Specification` for insights
3. **Optimize**: Apply `Session-Based AI/Optimize Specification` for improvements
4. **Mock Testing**: Create mock servers with `Enhanced Mock Server/Start Mock Server`

### Prompt Engineering
1. **Check Templates**: Use `AI Prompt/Get Available Templates`
2. **Use Template**: Apply with `AI Prompt/Use Prompt Template`
3. **Optimize**: Improve with `AI Prompt/Optimize Prompt`

## Environment Variables

The collection uses these environment variables:
- `baseUrl`: Spring Boot API base URL
- `aiServiceUrl`: AI Service base URL (for reference)
- `sampleSessionId`: Test session ID
- `sampleUserId`: Test user ID
- `sampleMockId`: Test mock server ID

## Troubleshooting

### Common Issues

1. **Connection Refused**: Verify all services are running on correct ports
2. **AI Service Timeout**: Check if Ollama is running and model is downloaded
3. **Session Not Found**: Use a valid session ID from `Create Session` response
4. **Redis Connection**: Ensure Redis is running and accessible

### Service Health Checks
Use these endpoints to diagnose issues:
- `/api/v1/ai/health` - Overall AI system health
- `/api/v1/mock/health` - Mock service health
- `/api/v1/ai/agents/status` - Individual agent status

## Notes

- Some endpoints may take longer to respond due to AI processing
- Streaming endpoints require special handling in Bruno
- Mock server endpoints may return fallback responses if AI service is unavailable
- Session-based endpoints require valid session IDs from the session service

This collection provides comprehensive coverage of all SchemaSculpt API functionality and can be used for development, testing, and integration validation.
