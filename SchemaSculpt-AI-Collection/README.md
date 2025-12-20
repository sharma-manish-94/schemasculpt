# SchemaSculpt AI Service - Bruno Collection

A comprehensive Bruno collection for testing the SchemaSculpt AI Service with realistic scenarios covering all endpoints.

## 🚀 Quick Start

### Prerequisites
1. **Start Redis**:
   ```bash
   docker run -d --name schemasculpt-redis -p 6379:6379 redis
   ```

2. **Start Ollama with Mistral**:
   ```bash
   ollama pull mistral
   ```

3. **Start AI Service**:
   ```bash
   cd ai_service
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

### Import Collection
1. Open Bruno
2. Click "Open Collection"
3. Select the `SchemaSculpt-AI-Collection` folder
4. The collection will load with the Local environment configured

## 🧪 Test Requests

### Core Functionality
1. **Health Check** - Verify service status and dependencies
2. **Basic AI Modification** - Simple OpenAPI spec modifications
3. **Generate Simple API** - AI-powered API generation from descriptions
4. **Advanced JSON Patches** - Precise spec editing with JSON patches

### Context & Session Management
5. **Create Session** - Initialize conversation sessions for context continuity (query parameter approach)
5b. **Create Session (JSON Body)** - Alternative approach using JSON body
6. **Get Available Workflows** - Discover predefined AI workflows

### Mock Server Testing
7. **Start Mock Server** - Create AI-powered mock servers with realistic responses
8. **Test Mock Endpoint** - Validate AI-generated mock responses

### Error Handling & Edge Cases
9. **Error Handling Test** - Test error handling with invalid input
10. **Legacy Process Endpoint** - Backward compatibility testing

## 🔧 Environment Variables

The collection includes a `Local` environment with these variables:

- `baseUrl`: http://localhost:8000 (AI Service base URL)
- `sessionId`: {{$guid}} (Auto-generated session ID)
- `userId`: test-user (Test user identifier)
- `mockId`: (Set dynamically by mock server tests)
- `correlationId`: {{$guid}} (Request correlation tracking)

## 📊 Expected Response Times

| Test Category | Expected Time |
|---------------|---------------|
| Health Check | < 1 second |
| Basic Processing | 5-15 seconds |
| API Generation | 10-30 seconds |
| Mock Operations | < 2 seconds |
| Error Handling | < 5 seconds |

## 🎯 Test Execution Tips

### Sequential Testing
1. Always run **Health Check** first to verify service status
2. Run **Create Session** before any context-dependent tests
3. Execute **Start Mock Server** before mock endpoint tests

### Variable Persistence
- Session IDs are automatically stored and reused across requests
- Mock IDs are captured and used in subsequent mock tests
- Correlation IDs help track requests in service logs

## 🚨 Troubleshooting

### Common Issues

**"Connection refused" errors**:
- Ensure AI service is running on port 8000
- Check that Redis is running on port 6379
- Verify Ollama is running and has the Mistral model

**Slow responses**:
- AI operations are computationally intensive
- Ensure sufficient system resources (8GB+ RAM recommended)
- Check Ollama model is loaded and not swapped to disk

**Test failures**:
- Run Health Check to verify all dependencies are healthy
- Check service logs for detailed error information
- Ensure proper request sequencing (create session before using)

### Service Logs
Monitor AI service logs to debug issues:
```bash
# In ai_service directory
uvicorn app.main:app --reload --log-level debug
```

## 🔮 Advanced Features Tested

- ✅ **AI-Powered Processing**: Natural language to OpenAPI conversion
- ✅ **Context Management**: Session-based conversation continuity
- ✅ **JSON Patch Operations**: Precise specification modifications
- ✅ **Mock Server Generation**: AI-generated realistic test data
- ✅ **Workflow Management**: Multi-step AI enhancement processes
- ✅ **Error Handling**: Robust error recovery and reporting
- ✅ **Legacy Compatibility**: Backward compatibility with older endpoints

## 📈 Performance Monitoring

Each request includes:
- Response time measurement
- Correlation ID for tracking
- Performance metrics in responses
- Validation results and confidence scores

This enables comprehensive monitoring of AI service performance and quality.

---

**Ready to explore SchemaSculpt's AI capabilities! 🚀**
