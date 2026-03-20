# SchemaSculpt Architecture Constraints

## Service Boundaries
- **Frontend**: React 19 only, no Angular/Vue components
- **Backend**: Spring Boot 3.x, Java 21+
- **AI Service**: Python 3.12+, FastAPI only (no Flask/Django)
- **Database**: PostgreSQL for persistence, Redis for sessions/cache only

## Communication Patterns
- UI → Backend: REST + WebSocket (STOMP/SockJS)
- Backend → AI Service: HTTP only (no direct WebSocket)
- Never call AI Service directly from Frontend

## Analyzer Architecture (NON-NEGOTIABLE)
All analyzers MUST follow the pattern in `.claude/skills/backend-api/patterns/analyzer-patterns.md`:
- Implement `Analyzer<T>` interface
- Extend `AbstractSchemaAnalyzer<T>` for shared utilities
- Single Responsibility: one analysis per analyzer
- Register in `AnalysisService` facade via constructor injection

## State Management
- Frontend: Zustand slices only (no Redux, no Context for global state)
- Backend: Stateless services, state in Redis sessions
- No in-memory state that doesn't survive restart

## Security Constraints
- No hardcoded credentials (use environment variables)
- All user input validated at controller level
- Authorization checks in service layer
- See `.claude/skills/backend-api/patterns/security-patterns.md`

## Testing Requirements
- Backend: JUnit 5 + Mockito for unit, Testcontainers for integration
- Frontend: Jest + React Testing Library
- Minimum: Unit tests for all public service methods
- Integration tests for all REST endpoints

## Dependencies
- No new dependencies without explicit approval
- Prefer Spring ecosystem libraries
- Document any new dependency in commit message with justification
