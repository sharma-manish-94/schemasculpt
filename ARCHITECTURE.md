# SchemaSculpt Architecture & Function Call Hierarchy

This document provides a comprehensive overview of the SchemaSculpt system architecture, including detailed function call hierarchies for all three services.

## Table of Contents

- [System Architecture Overview](#system-architecture-overview)
- [Service Communication Flow](#service-communication-flow)
- [Frontend (React) Call Hierarchy](#1-frontend-react-call-hierarchy)
- [API Gateway (Spring Boot) Call Hierarchy](#2-api-gateway-spring-boot-call-hierarchy)
- [AI Service (Python FastAPI) Call Hierarchy](#3-ai-service-python-fastapi-call-hierarchy)
- [Cross-Service Communication](#cross-service-communication-summary)
- [Design Patterns](#key-design-patterns)
- [File References](#key-file-references)

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER BROWSER                                        │
│                                                                                  │
│  React Frontend (localhost:3000)                                                │
│  ├── Zustand Store (6 slices: core, validation, ai, request, repository, code)  │
│  ├── REST API calls (axios) ──────────────────┐                                  │
│  └── WebSocket (STOMP/SockJS) ────────────────┼──────────────────────────┐       │
└───────────────────────────────────────────────┼──────────────────────────┼───────┘
                                                │                          │
                                                ▼                          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     SPRING BOOT API GATEWAY (localhost:8080)                     │
│  Controllers (13)                                                                │
│  ├── SessionController ─────────────────┐                                        │
│  ├── SpecificationController ───────────┼─► Services                             │
│  ├── AnalysisController ────────────────┤   ├── SessionService (Redis)           │
│  ├── ImplementationController ──────────┤   ├── ValidationService (linter)       │
│  ├── RepositoryController ──────────────┤   ├── AnalysisService (7 analyzers)    │
│  └── ...                                 │   ├── AIService (WebClient) ──────┐    │
│                                          │   └── RepoMindService (WebClient) ─┼──┐ │
└──────────────────────────────────────────┴───────────────────────────────────┼──┘ │
                                                                              │  │
                                                                              ▼  │
┌─────────────────────────────────────────────────────────────────────────────────┐ │
│                      FASTAPI AI SERVICE (localhost:8000)                         │ │
│  Routers                                                                         │ │
│  ├── /ai/security/confirm-finding ─────► RemediationAgent + RepoMind Client ◄──┤ │
│  ├── /ai/findings/{id}/suggest-fix ────► RemediationAgent                   │ │
│  └── ...                                                                         │ │
│                                                                                  │
│  External Integrations                                                           │
│  ├── Ollama (localhost:11434) ◄────── LLM inference                              │ │
│  ├── ChromaDB (local) ◄──────────────── Vector store (RAG)                       │ │
│  └── RepoMind (localhost:8001) ◄─────── Code context, metrics, tests ─────────┤ │
└──────────────────────────────────────────────────────────────────────────────────┘ │
                                                                                   │
                                                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     REPOMIND - CODE ANALYSIS (localhost:8001)                    │
│  Tools:                                                                          │
│  ├── index_repo                                                                  │
│  ├── get_context                                                                 │
│  ├── find_tests                                                                  │
│  └── analyze_ownership                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Service Communication Flow

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 19, Zustand, Monaco Editor | OpenAPI editor UI |
| **API Gateway** | Spring Boot 3, WebFlux | REST/WebSocket gateway |
| **AI Service** | FastAPI, LangChain | LLM-powered analysis |
| **Code Analysis** | Python (RepoMind) | Source code intelligence |
| **LLM** | Ollama (Mistral) | Local LLM inference |
| **Vector Store** | ChromaDB | RAG knowledge base |
| **Cache** | Redis | Session storage |

---

## 1. Frontend (React) Call Hierarchy

### Component Tree

```
App
├── AuthContext.Provider (wraps entire app)
│   ├── ProjectDashboard (when no project selected)
│   │   └── projectAPI.getProjects/createProject/deleteProject
│   │
│   └── SpecEditor (when project selected)
│       └── ThreePanelLayout
│           ├── NavigationPanel
│           │   └── useSpecStore: endpoints, selectedNavItem, setSelectedNavItem
│           │
│           ├── DetailPanel
│           │   ├── EnhancedEditorPanel (no selection)
│           │   │   ├── EditorToolbar
│           │   │   ├── Monaco Editor
│           │   │   └── AiAssistantBar
│           │   │
│           │   └── OperationSpecViewer (when nav item selected)
│           │
│           └── RightPanel (tabs)
│               ├── ValidationPanel (tab: validation)
│               ├── EnhancedSwaggerUI (tab: api_explorer)
│               ├── AIPanel (tab: ai_features)
│               │   ├── AIAssistantTab
│               │   ├── SecurityAnalysisTab
│               │   ├── AdvancedAnalysisTab
│               │   ├── AIHardeningTab
│               │   └── AISpecGenerator
│               └── RepositoryPanel (tab: repository)
```

### User Interaction Flows

#### Editor Flow
```
User types in Monaco Editor
│
└── MonacoEditor.onChange
    └── coreSlice.setSpecText(newText)
        └── useEffect (debounced 500ms)
            ├── requestSlice.parseEndpoints()
            ├── validationSlice.validateCurrentSpec()
            │   ├── PUT /api/v1/sessions/{id}/spec
            │   └── POST /api/v1/sessions/{id}/spec/validate
            └── websocketService.sendMessage() → STOMP /app/spec/edit
```

#### AI Assistant Flow
```
User submits AI prompt
│
└── AiAssistantBar.onSubmit
    └── aiSlice.submitAIRequest()
        ├── POST /api/v1/sessions/{id}/spec/transform → API Gateway
        └── coreSlice.setSpecText(updatedSpec) → triggers validation
```

#### Quick Fix Flow
```
User clicks fix button
│
└── ValidationPanel.clickFix
    └── validationSlice.applyQuickFix()
        ├── PUT /api/v1/sessions/{id}/spec
        ├── POST /api/v1/sessions/{id}/spec/fix
        └── coreSlice.setSpecText(fixedSpec)
```

#### Security Analysis Flow
```
User clicks analyze (direct to AI service)
│
└── SecurityAnalysisTab.clickAnalyze
    └── securityService.runSecurityAnalysis()
        └── POST http://localhost:8000/ai/security/analyze
```

#### Advanced Analysis Flow
```
User clicks comprehensive analysis
│
└── AdvancedAnalysisTab.clickComprehensive
    └── analysisService.runComprehensiveAnalysis()
        ├── GET /api/v1/sessions/{id}/analysis/taint-analysis
        ├── GET /api/v1/sessions/{id}/analysis/authz-matrix
        ├── GET /api/v1/sessions/{id}/analysis/schema-similarity
        ├── GET /api/v1/sessions/{id}/analysis/zombie-apis
        └── POST /api/v1/sessions/{id}/analysis/blast-radius
```

#### Repository Flow
```
User connects repository
│
└── RepositoryPanel.connect
    └── repositorySlice.connectToRepository()
        ├── POST /api/v1/sessions/{id}/repository/connect
        └── repositorySlice.browseRepositoryTree()
            └── GET /api/v1/sessions/{id}/repository/tree
```

### Store → API Service → Endpoint Mapping

| Store Action | API Service Function | HTTP Endpoint |
|--------------|---------------------|---------------|
| `coreSlice.createSession` | direct axios | `POST /api/v1/sessions` |
| `coreSlice.connectWebSocket` | `websocketService.connect` | WebSocket `/ws` |
| `coreSlice.updateOperationDetails` | `validationService.updateOperation` | `PATCH /api/v1/sessions/{id}/spec/operations` |
| `validationSlice.validateCurrentSpec` | `validationService.validateSpec` | `POST /api/v1/sessions/{id}/spec/validate` |
| `validationSlice.applyQuickFix` | `validationService.applyQuickFix` | `POST /api/v1/sessions/{id}/spec/fix` |
| `validationSlice.runAIMetaAnalysis` | `validationService.performAIMetaAnalysis` | `POST /api/v1/sessions/{id}/spec/ai-analysis` |
| `validationSlice.runDescriptionAnalysis` | `validationService.analyzeDescriptions` | `POST /api/v1/sessions/{id}/spec/analyze-descriptions` |
| `aiSlice.submitAIRequest` | `aiService.executeAiAction` | `POST /api/v1/sessions/{id}/spec/transform` |
| `aiSlice.processSpecification` | `aiService.processSpecification` | `POST /ai/process` |
| `aiSlice.generateSpecification` | `aiService.generateSpecification` | `POST /ai/generate` |
| `aiSlice.fetchAgentsStatus` | `aiService.getAgentsStatus` | `GET /ai/agents/status` |
| `aiSlice.executeWorkflow` | `aiService.executeWorkflow` | `POST /ai/workflow/{name}` |
| `requestSlice.startMockServer` | `validationService.startMockServer` | `POST /sessions/mock` |
| `requestSlice.sendRequest` | `validationService.executeProxyRequest` | `POST /proxy/request` |
| `repositorySlice.connectToRepository` | `repositoryService.connectRepository` | `POST /api/v1/sessions/{id}/repository/connect` |
| `repositorySlice.browseRepositoryTree` | `repositoryService.browseTree` | `GET /api/v1/sessions/{id}/repository/tree` |
| N/A (direct) | `securityService.runSecurityAnalysis` | `POST http://localhost:8000/ai/security/analyze` |
| N/A (direct) | `analysisService.runTaintAnalysis` | `GET /api/v1/sessions/{id}/analysis/taint-analysis` |
| N/A (direct) | `analysisService.runBlastRadiusAnalysis` | `POST /api/v1/sessions/{id}/analysis/blast-radius` |
| N/A (direct) | `projectAPI.getProjects` | `GET /api/v1/projects` |
| N/A (direct) | `projectAPI.saveSpecification` | `POST /api/v1/projects/{id}/specifications` |

---

## 2. API Gateway (Spring Boot) Call Hierarchy

### Controller Layer

```
HTTP Request
│
├── SessionController (@RequestMapping("/api/v1/sessions"))
│   ├── POST /
│   │   └── SessionService.createSession() → Redis
│   ├── POST /mock
│   │   └── WebClient.post("/mock/start") → AI Service
│   ├── GET /{sessionId}/spec
│   │   └── SessionService.getSpecForSession() → Redis
│   ├── PUT /{sessionId}/spec
│   │   └── SessionService.updateSessionSpec() → Redis
│   └── DELETE /{sessionId}
│       └── SessionService.closeSession() → Redis
│
├── SpecificationController (@RequestMapping("/api/v1/sessions/{sessionId}/spec"))
│   ├── POST /validate
│   │   ├── SessionService.getSpecForSession()
│   │   └── ValidationService.analyze()
│   │       ├── OpenAPIV3Parser.readContents()
│   │       └── SpecificationLinter.lint() → List<LinterRule>
│   │
│   ├── POST /ai-analysis
│   │   ├── SessionService.getSpecForSession()
│   │   ├── ValidationService.analyze()
│   │   └── AIService.performMetaAnalysis()
│   │       └── WebClient.post("/ai/meta-analysis") → AI Service
│   │
│   ├── POST /analyze-descriptions
│   │   ├── SessionService.getSpecForSession()
│   │   ├── AIService.extractDescriptionsForAnalysis()
│   │   └── AIService.analyzeDescriptionQuality()
│   │       └── WebClient.post("/ai/analyze-descriptions") → AI Service
│   │
│   ├── POST /fix
│   │   └── QuickFixService.applyFix()
│   │       ├── SessionService.getSpecForSession()
│   │       ├── [AUTO_FIXABLE] Direct OpenAPI manipulation
│   │       └── [AI_FIXABLE] WebClient.post("/ai/patch/generate") → AI Service
│   │
│   └── POST /transform
│       └── AIService.processSpecification()
│           ├── SessionService.getSpecForSession()
│           ├── WebClient.post("/ai/fix/smart") → AI Service
│           ├── SpecParsingService.parse()
│           └── SessionService.updateSessionSpec()
│
├── SpecUpdateController (@RequestMapping("/api/v1/sessions/{sessionId}/spec"))
│   ├── PATCH /operations
│   │   └── SpecUpdateService.updateOperation()
│   └── GET /operations
│       ├── SessionService.getSpecForSession()
│       └── TreeShakingService.extractOperationWithDependencies()
│
├── AnalysisController (@RequestMapping("/api/v1/sessions/{sessionId}/analysis"))
│   ├── GET /dependencies
│   │   └── AnalysisService.buildReverseDependencyGraph()
│   │       └── ReverseDependencyGraphAnalyzer.analyze()
│   │
│   ├── GET /nesting-depth
│   │   └── AnalysisService.calculateNestingDepthForOperation()
│   │       └── NestingDepthAnalyzer.analyzeOperation()
│   │
│   ├── POST /attack-path-simulation
│   │   ├── SessionService.getSpecTextForSession()
│   │   └── WebClient.post("/ai/security/attack-path-simulation") → AI Service
│   │
│   ├── POST /attack-path-findings
│   │   ├── SessionService.getSpecForSession()
│   │   ├── SecurityFindingsExtractor.extractFindings() ← Java extracts FACTS
│   │   └── WebClient.post("/ai/security/attack-path-findings") → AI Service
│   │
│   ├── GET /authz-matrix
│   │   └── AnalysisService.generateAuthzMatrix()
│   │       └── AuthorizationMatrixAnalyzer.analyze()
│   │
│   ├── GET /taint-analysis
│   │   └── AnalysisService.performTaintAnalysis()
│   │       └── TaintAnalyzer.analyze()
│   │
│   ├── GET /schema-similarity
│   │   └── AnalysisService.analyzeSchemaSimilarity()
│   │       └── SchemaSimilarityAnalyzer.analyze()
│   │
│   ├── GET /zombie-apis
│   │   └── AnalysisService.detectZombieApis()
│   │       └── ZombieApiAnalyzer.analyze()
│   │
│   ├── POST /blast-radius
│   │   └── AnalysisService.performBlastRadiusAnalysis()
│   │       └── BlastRadiusAnalyzer.analyze()
│   │           └── ReverseDependencyGraphAnalyzer.analyze()
│   │
│   └── POST /diff
│       └── SchemaDiffService.compareSpecs()
│
├── HardeningController (@RequestMapping("/api/v1/sessions/{sessionId}/hardening"))
│   ├── POST /operations/oauth2
│   │   └── HardeningService.hardenOperation()
│   ├── POST /operations
│   │   └── HardeningService.hardenOperation()
│   │       ├── SessionService.getSpecForSession()
│   │       ├── applyOAuth2Security()
│   │       ├── applyRateLimiting()
│   │       ├── applyCaching()
│   │       ├── applyIdempotency()
│   │       ├── applyValidation()
│   │       ├── applyErrorHandling()
│   │       └── SessionService.updateSessionSpec()
│   ├── POST /operations/rate-limiting
│   ├── POST /operations/caching
│   ├── POST /operations/complete
│   └── GET /patterns
│
├── ExplanationController (@RequestMapping("/api/v1/explanations"))
│   ├── POST /explain
│   │   ├── SessionService.getSpecForSession()
│   │   └── AIService.explainValidationIssue()
│   │       └── WebClient.post("/ai/explain") → AI Service
│   └── GET /health
│
├── ProxyController (@RequestMapping("/api/v1/proxy"))
│   └── POST /request
│       └── ProxyService.forwardRequest()
│           ├── validateUrl() - Security: only localhost allowed
│           └── WebClient.method().uri().exchange()
│
├── RepositoryController (@RequestMapping("/api/v1/repository"))
│   ├── POST /connect
│   │   └── RepositoryService.connect()
│   │       └── WebClient.post("/api/repository/connect") → AI Service
│   ├── POST /disconnect
│   │   └── RepositoryService.disconnect()
│   ├── POST /browse
│   │   └── RepositoryService.browseTree()
│   ├── POST /file
│   │   └── RepositoryService.readFile()
│   └── GET /status
│       └── RepositoryService.getRepositoryContext()
│
├── AuthController (@RequestMapping("/api/v1/auth"))
│   ├── GET /me → UserRepository.findById()
│   ├── POST /token → JwtTokenProvider.generateToken()
│   ├── POST /logout
│   └── GET /health
│
├── ProjectController (@RequestMapping("/api/v1/projects"))
│   ├── POST / → ProjectService.createProject()
│   ├── GET / → ProjectService.getUserProjects()
│   ├── GET /{projectId} → ProjectService.getProject()
│   ├── PUT /{projectId} → ProjectService.updateProject()
│   └── DELETE /{projectId} → ProjectService.deleteProject()
│
├── SpecificationManagementController (@RequestMapping("/api/v1/projects/{projectId}/specifications"))
│   ├── POST / → SpecificationService.saveSpecification()
│   ├── GET /current → SpecificationService.getCurrentSpecification()
│   ├── GET / → SpecificationService.getSpecificationVersions()
│   ├── GET /versions/{version} → SpecificationService.getSpecificationByVersion()
│   └── POST /versions/{version}/revert → SpecificationService.revertToVersion()
│
└── WebSocketController (STOMP @MessageMapping)
    └── @MessageMapping("/spec/edit")
        └── SessionService.updateSessionSpec()
```

### Analyzer Architecture (SOLID-Compliant)

```
Analyzer<T> (Strategy Pattern Interface)
│
└── AbstractSchemaAnalyzer<T> (Template Method Pattern)
    │
    ├── analyze(OpenAPI) - final template method
    │   ├── validateOpenApi(openApi)
    │   └── performAnalysis(openApi) - abstract, implemented by subclasses
    │
    ├── getAllSchemas(openApi) - utility
    └── extractSchemaName(refPath) - utility

Concrete Analyzers (all @Component):
│
├── ReverseDependencyGraphAnalyzer
│   └── performAnalysis() → Map<String, Set<String>>
│       └── SchemaTraversalUtil.findRefsInSchema()
│
├── BlastRadiusAnalyzer
│   └── analyze(openApi, targetSchema) → BlastRadiusResponse
│       └── BFS traversal for impact analysis
│
├── NestingDepthAnalyzer
│   └── performAnalysis() → Map<String, Integer>
│       └── Calculates max nesting depth per operation
│
├── TaintAnalyzer
│   └── performAnalysis() → TaintAnalysisResponse
│       └── Tracks sensitive data flow (sources → barriers → sinks)
│
├── AuthorizationMatrixAnalyzer
│   └── performAnalysis() → AuthzMatrixResponse
│       └── Extracts scopes per operation
│
├── SchemaSimilarityAnalyzer
│   └── performAnalysis() → SchemaSimilarityResponse
│       └── Jaccard similarity clustering O(n²)
│
└── ZombieApiAnalyzer
    └── performAnalysis() → ZombieApiResponse
        └── Detects shadowed paths and orphaned operations

AnalysisService (Facade Pattern)
├── Injects all 7 analyzers via constructor
└── Provides unified methods:
    ├── buildReverseDependencyGraph()
    ├── performBlastRadiusAnalysis()
    ├── calculateNestingDepthForOperation()
    ├── generateAuthzMatrix()
    ├── performTaintAnalysis()
    ├── analyzeSchemaSimilarity()
    └── detectZombieApis()
```

---

## 3. AI Service (Python FastAPI) Call Hierarchy

### Endpoint Flows

#### POST /ai/process (Core AI Processing)
```
ai_processing.py::process_specification()
│
├── deps.get_llm_service() → LLMService (singleton)
├── deps.get_context_manager() → ContextManager (singleton)
│
├── ContextManager.create_session()
├── ContextManager.get_context_for_request()
│
└── LLMService.process_ai_request()
    │
    ├── [If validate_output=True]
    │   └── LLMService._validate_openapi_spec()
    │
    ├── [If json_patches provided]
    │   └── LLMService._process_patch_request()
    │       ├── json.loads(spec_text)
    │       ├── LLMService._apply_json_patches()
    │       │   └── jsonpatch.JsonPatch().apply()
    │       └── LLMService._validate_openapi_spec()
    │
    ├── [If streaming enabled]
    │   └── LLMService._process_streaming_request()
    │       ├── LLMService._build_intelligent_prompt()
    │       └── LLMService._stream_llm_response()
    │           └── httpx.AsyncClient.stream("POST", Ollama /api/chat)
    │
    └── [Standard request]
        └── LLMService._process_standard_request()
            ├── LLMService._build_intelligent_prompt()
            │   ├── _get_modification_system_prompt()
            │   ├── _build_context_summary()
            │   └── _build_enhanced_user_prompt()
            │
            ├── LLMService._call_llm_with_retry(max_retries=3)
            │   ├── httpx.AsyncClient.post(Ollama /api/chat)
            │   └── LLMService._extract_and_clean_response()
            │
            ├── LLMService._fix_openapi_issues()
            ├── LLMService._validate_and_correct_response()
            └── LLMService._analyze_changes()
```

#### POST /ai/generate (Agentic Generation)
```
ai_processing.py::generate_specification_agentic()
│
├── deps.get_agent_manager() → AgentManager
│
└── AgentManager.execute_complete_spec_generation()
    │
    └── CoordinatorAgent.execute(workflow_task)
        │
        ├── _pre_execution_hook()
        └── _execute_sequential_workflow()
            │
            ├── [Step 1] DomainAnalyzerAgent.execute()
            │   ├── LLMAgent._call_llm() → Ollama
            │   └── LLMAgent._parse_llm_json_response()
            │
            ├── [Step 2] DomainAnalyzerAgent.execute(extract_entities)
            │   └── Returns {entities with relationships}
            │
            ├── [Step 3] SchemaGeneratorAgent.execute()
            │   └── Returns {schemas: {...}}
            │
            └── [Step 4] PathGeneratorAgent.execute()
                └── Returns {paths: {...}, security_schemes: {...}}
        │
        ├── AgentManager._assemble_final_specification()
        ├── LLMService._validate_openapi_spec()
        ├── AgentManager._calculate_confidence_score()
        └── AgentManager._generate_follow_up_suggestions()
```

#### POST /ai/security/analyze (Comprehensive Security)
```
security_analysis.py::run_comprehensive_security_analysis()
│
├── deps.get_security_workflow() → SecurityAnalysisWorkflow
├── deps.get_cache_repository() → ICacheRepository
│
├── _generate_cache_key_for_spec()
├── [Check cache] _get_cached_security_report()
│
└── SecurityAnalysisWorkflow.analyze()
    │
    ├── AuthenticationAnalyzer.analyze()
    │   ├── Analyze security schemes (OAuth2, API Key, Bearer, Basic)
    │   └── Detect unprotected endpoints
    │
    ├── AuthorizationAnalyzer.analyze()
    │   ├── RBAC analysis
    │   ├── BOLA detection
    │   └── BFLA detection
    │
    ├── DataExposureAnalyzer.analyze()
    │   ├── PII field detection
    │   └── Sensitive data exposure
    │
    └── OWASPComplianceValidator.validate()
        └── OWASP API Security Top 10 check
```

#### POST /ai/security/attack-path-simulation
```
security_analysis.py::run_attack_path_simulation()
│
├── deps.get_llm_service() → LLMService
├── deps.get_cache_repository() → ICacheRepository
│
└── AttackPathOrchestrator.run_attack_path_analysis()
    │
    ├── [Agent 1] VulnerabilityScannerAgent.scan()
    │   └── Returns List[Vulnerability]
    │
    ├── [Agent 2] ThreatModelingAgent.analyze()
    │   ├── LLMAgent._call_llm() with RAG context
    │   └── Chain vulnerabilities into attack paths
    │
    └── [Agent 3] SecurityReporterAgent.generate_report()
        ├── LLMAgent._call_llm()
        ├── Generate executive summary
        └── Prioritize remediation actions
```

#### POST /ai/explain (RAG-Enhanced)
```
explanation.py::explain_validation_issue()
│
├── deps.get_llm_service() → LLMService
├── deps.get_rag_service() → RAGService
├── deps.get_cache_repository() → ICacheRepository
│
├── _get_cached_explanation()
│
├── RAGService.retrieve_security_context()
│   └── RAGService.query_attacker_knowledge()
│       ├── SentenceTransformer.encode([query])
│       └── ChromaDB.query(attacker_knowledge collection)
│
├── Build explanation_prompt with knowledge_context
├── LLMService.client.post(Ollama /api/chat)
│
└── _cache_explanation()
```

### Dependency Injection (deps.py)

```
get_llm_service() [@lru_cache singleton]
└── LLMService()
    ├── httpx.AsyncClient(timeout, limits)
    └── IntelligentOpenAPIWorkflow(self)

get_agent_manager(llm_service)
└── AgentManager(llm_service)
    ├── CoordinatorAgent()
    ├── DomainAnalyzerAgent(llm_service)
    ├── SchemaGeneratorAgent(llm_service)
    ├── PathGeneratorAgent(llm_service)
    └── _register_agents()

get_rag_service() [@lru_cache singleton]
└── RAGService()
    ├── SentenceTransformer("all-MiniLM-L6-v2")
    ├── chromadb.PersistentClient(path)
    └── _initialize_vector_stores()

get_cache_repository() [async singleton]
└── create_cache_repository()
    ├── [Try] RedisCacheRepository(redis_url)
    └── [Fallback] InMemoryCacheRepository()

get_llm_provider() [async singleton]
└── create_provider()
    └── OllamaProvider(config) → LLMProviderAdapter → ILLMProvider

get_security_workflow(llm_service)
└── SecurityAnalysisWorkflow(llm_service)
```

### External Integrations

```
Ollama LLM (OllamaProvider)
├── Base URL: localhost:11434
├── POST /api/chat     - Chat completions (streaming & non-streaming)
├── POST /api/generate - Text generation
└── GET  /api/tags     - Health check / list models

ChromaDB Vector Store (ChromaDBRepository)
├── Persist Directory: {ai_service_data_dir}/chroma_db
├── Embedding Model: sentence-transformers/all-MiniLM-L6-v2 (local)
└── Collections:
    ├── attacker_knowledge - Offensive security (OWASP, MITRE ATT&CK)
    └── governance_knowledge - Risk frameworks (CVSS, DREAD, GDPR, HIPAA)

Redis/In-Memory Cache (ICacheRepository)
├── Redis URL: settings.redis_url (optional)
├── Fallback: InMemoryCacheRepository with TTL support
├── cache.get(key) → Optional[Any]
├── cache.set(key, value, ttl)
└── cache.delete(key)
```

---

## Cross-Service Communication Summary

| Source | Target | Protocol | Purpose |
|--------|--------|----------|---------|
| UI → API Gateway | REST (axios) | Session, validation, analysis, hardening |
| UI → API Gateway | WebSocket (STOMP) | Real-time spec editing |
| UI → AI Service | REST (direct) | Security analysis (bypass gateway) |
| API Gateway → AI Service | REST (WebClient) | AI processing, patches, explanations |
| API Gateway → RepoMind | REST (WebClient) | Indexing, code context retrieval |
| AI Service → RepoMind | REST (httpx) | Code metrics, test finding, ownership analysis |
| AI Service → Ollama | REST | LLM inference |
| AI Service → ChromaDB | Local API | RAG vector queries |
| API Gateway → Redis | TCP | Session storage |

### API Gateway → AI Service Calls

| Java Method | AI Service Endpoint | Purpose |
|-------------|---------------------|---------|
| `AIService.processSpecification()` | `POST /ai/fix/smart` | Smart AI fix with patch/regen |
| `AIService.performMetaAnalysis()` | `POST /ai/meta-analysis` | Pattern detection |
| `AIService.analyzeDescriptionQuality()` | `POST /ai/analyze-descriptions` | Description quality scoring |
| `AIService.explainValidationIssue()` | `POST /ai/explain` | RAG-enhanced explanations |
| `QuickFixService (AI fix)` | `POST /ai/patch/generate` | JSON Patch generation |
| `AnalysisController` | `POST /ai/security/attack-path-simulation` | Attack chain discovery |
| `AnalysisController` | `POST /ai/security/attack-path-findings` | Findings-based analysis |
| `ImplementationController` | `POST /ai/security/confirm-finding` | Code-aware finding confirmation |
| `ImplementationController` | `POST /ai/findings/{id}/suggest-fix` | AI-powered code remediation |
| `SessionController (mock)` | `POST /mock/start` | Mock server startup |
| `RepositoryService` (old) | `POST /api/repository/*` | Git repository operations |

---

## Key Design Patterns

| Pattern | Location | Purpose |
|---------|----------|---------|
| **Facade** | `AnalysisService` (Java) | Unified interface to 7 analyzers |
| **Strategy** | `Analyzer<T>` interface (Java) | Interchangeable analysis algorithms |
| **Template Method** | `AbstractSchemaAnalyzer` (Java) | Shared analysis skeleton |
| **Coordinator** | `CoordinatorAgent` (Python) | Multi-agent workflow orchestration |
| **Slice Pattern** | Zustand store (React) | Domain-specific state management |
| **Repository** | `IRAGRepository`, `ICacheRepository` (Python) | Abstract data access |
| **Adapter** | `LLMProviderAdapter` (Python) | Legacy provider compatibility |
| **Factory** | `create_provider()`, `create_cache_repository()` (Python) | Infrastructure creation |
| **Singleton** | `@lru_cache` decorators (Python) | Service instance reuse |
| **Observer** | WebSocket subscription (React) | Real-time server updates |
| **Debounce** | Editor onChange (React) | 500ms delay before validation |

---

## Key File References

### Frontend (React)
| File | Purpose |
|------|---------|
| `ui/src/store/specStore.js` | Unified Zustand store |
| `ui/src/store/slices/coreSlice.js` | Core state (spec, session, WebSocket) |
| `ui/src/store/slices/validationSlice.js` | Validation state and actions |
| `ui/src/store/slices/aiSlice.js` | AI processing state |
| `ui/src/api/validationService.js` | Validation API calls |
| `ui/src/api/aiService.js` | AI API calls |
| `ui/src/api/analysisService.js` | Analysis API calls |
| `ui/src/api/websocketService.js` | WebSocket (STOMP/SockJS) |
| `ui/src/features/editor/SpecEditor.js` | Main editor orchestrator |

### API Gateway (Spring Boot)
| File | Purpose |
|------|---------|
| `api/src/.../controller/AnalysisController.java` | Analysis endpoints |
| `api/src/.../controller/SpecificationController.java` | Spec validation/transformation |
| `api/src/.../controller/HardeningController.java` | Security hardening |
| `api/src/.../service/AnalysisService.java` | Analyzer facade |
| `api/src/.../service/analyzer/Analyzer.java` | Strategy interface |
| `api/src/.../service/analyzer/base/AbstractSchemaAnalyzer.java` | Template base class |
| `api/src/.../service/analyzer/dependency/BlastRadiusAnalyzer.java` | Impact analysis |
| `api/src/.../service/analyzer/security/TaintAnalyzer.java` | Data flow analysis |
| `api/src/.../service/ai/AIService.java` | AI service integration |
| `api/src/.../service/impl/SessionServiceImpl.java` | Redis session management |

### AI Service (Python FastAPI)
| File | Purpose |
|------|---------|
| `ai_service/app/main.py` | FastAPI entry point |
| `ai_service/app/api/deps.py` | Dependency injection |
| `ai_service/app/api/v1/routers/ai_processing.py` | Core AI endpoints |
| `ai_service/app/api/v1/routers/security_analysis.py` | Security analysis endpoints |
| `ai_service/app/services/llm_service.py` | LLM orchestration |
| `ai_service/app/services/rag_service.py` | RAG knowledge retrieval |
| `ai_service/app/services/agent_manager.py` | Multi-agent orchestration |
| `ai_service/app/providers/ollama_provider.py` | Ollama integration |
| `ai_service/app/infrastructure/rag/chromadb_repository.py` | Vector store |

---

## Adding New Features

### Adding a New Analyzer (Java)

1. Create class in `api/src/.../service/analyzer/{category}/`
2. Extend `AbstractSchemaAnalyzer<YourResponseType>`
3. Implement `performAnalysis(OpenAPI openApi)`
4. Add `@Component` annotation
5. Inject into `AnalysisService` constructor
6. Add delegation method in `AnalysisService`
7. Add endpoint in `AnalysisController`

### Adding a New AI Endpoint (Python)

1. Create router in `ai_service/app/api/v1/routers/`
2. Add request/response models in `ai_service/app/models/`
3. Implement service logic in `ai_service/app/services/`
4. Register router in `ai_service/app/api/v1/api.py`

### Adding a New Frontend Feature

1. Create slice in `ui/src/store/slices/` if new state needed
2. Add API service in `ui/src/api/`
3. Create components in `ui/src/features/{feature}/`
4. Wire up in parent component (e.g., `RightPanel.js`)

---

*Generated: 2026-01-31*
