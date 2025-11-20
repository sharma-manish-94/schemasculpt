# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SchemaSculpt is a multi-service application for editing OpenAPI specifications with AI assistance. The architecture consists of three main components:

- **Frontend (UI)**: React application with Monaco Editor, WebSocket communication, and real-time validation
- **Backend API Gateway**: Java Spring Boot application handling REST APIs, WebSocket connections, and session management
- **AI Service**: Python FastAPI service providing LLM-powered features via Ollama

## Architecture

### Service Communication
- **UI → API Gateway**: REST calls via axios, WebSocket via SockJS/StompJS for real-time features
- **API Gateway → AI Service**: HTTP requests for AI operations (editing, mock data generation)
- **API Gateway → Redis**: Session storage and caching
- **AI Service → Ollama**: Local LLM integration for AI features

### Key Technologies
- **Frontend**: React 19, Monaco Editor, Zustand state management, react-resizable-panels
- **Backend**: Spring Boot 3, Spring WebSockets, Spring Data Redis, Spring Security
- **AI Service**: FastAPI, Ollama integration, OpenAPI spec validation (prance, openapi-spec-validator)
- **Infrastructure**: Redis for sessions, Docker for Redis deployment

## Development Commands

### Prerequisites Setup
```bash
# Start Redis (required before backend)
docker run -d --name schemasculpt-redis -p 6379:6379 redis

# Ensure Ollama is running with mistral model
ollama pull mistral
```

### AI Service (Python)
```bash
cd ai_service
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Runs on http://localhost:8000

### Backend API (Java)
```bash
cd api
./mvnw spring-boot:run
```
Runs on http://localhost:8080

### Frontend (React)
```bash
cd ui
npm install
npm start
```
Runs on http://localhost:3000

### Testing
- **UI**: `npm test` (Jest/React Testing Library)
- **Backend**: `./mvnw test` (JUnit 5, Testcontainers)
- **AI Service**: No specific test framework configured

### Building
- **UI**: `npm run build` (production build)
- **Backend**: `./mvnw package` (JAR file)
- **AI Service**: No specific build process (Python)

## Code Structure

### Frontend (ui/src/)
- `features/editor/`: Main OpenAPI editor components with Monaco integration
- `api/`: Service layer for backend communication (REST and WebSocket)
- `store/slices/`: Zustand state management (coreSlice, aiSlice, validationSlice)
- `components/`: Shared UI components

### Backend (api/src/main/java/.../schemasculpt_api/)
- `controller/`: REST controllers and WebSocket endpoints
- `service/`: Business logic layer, including SessionService for session management
- `dto/`: Data transfer objects for API communication
- `config/`: Spring configuration classes

### AI Service (ai_service/app/)
- `api/endpoints.py`: FastAPI route definitions
- `services/llm_service.py`: Ollama integration and LLM operations
- `main.py`: FastAPI application entry point

## Development Notes

### Session Management
- Sessions stored in Redis with automatic expiration
- WebSocket connections tied to session IDs
- Session state includes current OpenAPI spec and validation results

### AI Integration
- Local Ollama instance required for AI features
- AI service validates OpenAPI specs before LLM processing
- Mock server functionality generates realistic data using LLM

### Real-time Features
- WebSocket connection for live validation updates
- SockJS fallback for WebSocket compatibility
- STOMP protocol for structured messaging

### OpenAPI Handling
- Supports both JSON and YAML formats
- Real-time validation using swagger-parser (Java) and prance (Python)
- Built-in linter with auto-fix capabilities