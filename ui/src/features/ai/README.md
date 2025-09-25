# AI Features Integration

This directory contains the complete AI integration for SchemaSculpt. The integration connects the React frontend with the Spring Boot backend AI services.

## Components

### AIPanel (`components/AIPanel.js`)
Main AI features panel with tabs for:
- **Assistant**: Basic AI assistance with streaming support
- **Generator**: Generate complete OpenAPI specifications
- **Agents**: Manage and monitor AI agents
- **Workflows**: Execute predefined and custom workflows
- **Prompts**: Build and optimize prompts
- **Health**: Monitor AI service health

### AIHealthStatus (`components/AIHealthStatus.js`)
Real-time monitoring of AI service health with:
- Service status indicators
- Performance metrics
- Auto-refresh capability
- Service details breakdown

### AIAgentManager (`components/AIAgentManager.js`)
Management interface for AI agents with:
- Agent status monitoring
- Performance metrics
- Agent restart capabilities
- Capability descriptions

### AISpecGenerator (`components/AISpecGenerator.js`)
Complete specification generation with:
- Domain selection (e-commerce, finance, healthcare, etc.)
- Complexity levels (simple, moderate, complex)
- Authentication options
- Feature specification
- Generated spec management

### AIPromptBuilder (`components/AIPromptBuilder.js`)
Advanced prompt management with:
- Intelligent prompt generation
- Template system
- Prompt optimization
- Usage statistics

### AIWorkflowRunner (`components/AIWorkflowRunner.js`)
Workflow execution system with:
- Predefined workflows
- Custom workflow builder
- Step-by-step execution
- Result tracking

## Integration Points

### Backend Endpoints
The AI components integrate with these Spring Boot endpoints:
- `/api/v1/ai/process` - Process specifications
- `/api/v1/ai/generate` - Generate specifications
- `/api/v1/ai/agents/*` - Agent management
- `/api/v1/ai/prompt/*` - Prompt services
- `/api/v1/ai/workflow/*` - Workflow execution
- `/api/v1/ai/health` - Health monitoring

### State Management
AI state is managed through the enhanced `aiSlice.js`:
- Processing states
- Agent status
- Health monitoring
- Response handling
- Error management

### UI Integration
AI features are integrated into the main layout:
- New "AI Features" tab in the right panel
- Enhanced AI assistant bar with advanced options
- Seamless integration with existing validation and explorer panels

## Usage

### Basic AI Assistance
1. Use the AI assistant bar at the bottom of the editor
2. Enter natural language requests
3. Click Submit to process with legacy endpoint
4. Click the gear icon (⚙️) for advanced features

### Advanced Features
1. Click the "AI Features" tab in the right panel
2. Select from available tabs (Assistant, Generator, etc.)
3. Use domain-specific features for your needs

### Specification Generation
1. Go to AI Features > Generator
2. Select domain and complexity
3. Describe your API requirements
4. Click "Generate Specification"
5. Use the generated spec directly in the editor

### Agent Monitoring
1. Go to AI Features > Agents
2. View real-time agent status
3. Restart agents if needed
4. Monitor performance metrics

## Development

### Adding New AI Features
1. Create component in `components/`
2. Add to `AIPanel.js` tabs
3. Implement corresponding backend service
4. Add state management to `aiSlice.js`

### Styling
All AI components use `ai-features.css` for consistent styling.

### Error Handling
Components use the standard error handling pattern with:
- Success/error states
- Loading indicators
- User-friendly error messages

## Backend Requirements

Ensure the following services are running:
1. **Spring Boot API** on port 8080
2. **AI Service (Python)** on port 8000
3. **Ollama** with required models
4. **Redis** for session management

## Future Enhancements

- Real-time collaboration features
- AI-powered specification analysis
- Advanced workflow templates
- Integration with external AI services
- Performance optimization