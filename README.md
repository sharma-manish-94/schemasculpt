# SchemaSculpt 🗿

<div align="center">

**Your AI-Powered Co-Pilot for Building Production-Ready APIs**

[![License](https://img.shields.io/badge/License-All_Rights_Reserved-red)](LICENSE)
[![Java](https://img.shields.io/badge/Java-25-orange)](https://openjdk.org/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-3-green)](https://spring.io/projects/spring-boot)
[![React](https://img.shields.io/badge/React-19-blue)](https://react.dev/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-teal)](https://fastapi.tiangolo.com/)

_Transform OpenAPI specification authoring from tedious to effortless with intelligent linting, AI-powered editing, and real-time validation._

[Features](#-key-features) • [Getting Started](#-getting-started) • [Architecture](#-architecture) • [Documentation](#-documentation) • [Roadmap](#-roadmap)

</div>

---

## 📋 Table of Contents

- [About SchemaSculpt](#-about-schemasculpt)
- [Why SchemaSculpt?](#-why-schemasculpt)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Advanced Features](#-advanced-features)
- [Documentation](#-documentation)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 About SchemaSculpt

SchemaSculpt is an **intelligent, locally-run IDE** for crafting perfect OpenAPI 3.x specifications. It combines the power of **Large Language Models (LLMs)** with **deterministic linting** and **real-time validation** to help developers, architects, and API designers build production-ready APIs faster and with fewer errors.

Unlike traditional API design tools, SchemaSculpt:

- ✅ Runs **100% locally** - Your API specifications never leave your machine
- ✅ Uses **AI for intelligent suggestions** - Not just syntax checking
- ✅ Provides **one-click auto-fixes** - Save hours of manual editing
- ✅ Offers **AI-friendly API analysis** - Optimize your APIs for AI agent consumption (MCP-ready)
- ✅ Generates **realistic mock data** - Test your APIs immediately with AI-powered mocks

### Intended Audience

SchemaSculpt is designed for:

- **Backend Developers** building RESTful APIs
- **API Architects** designing microservices ecosystems
- **DevOps Engineers** implementing API gateways
- **QA Engineers** validating API contracts
- **Technical Writers** documenting API specifications
- **AI/ML Engineers** building AI-friendly APIs for agent consumption

---

## 💡 Why SchemaSculpt?

### The Problem

Writing and maintaining OpenAPI specifications is **tedious and error-prone**:

- ❌ Manual validation catches only syntax errors, not design issues
- ❌ Unused components accumulate as APIs evolve
- ❌ Inconsistent naming conventions across teams
- ❌ Missing descriptions, examples, and security definitions
- ❌ No guidance for building AI-agent-friendly APIs
- ❌ Testing requires deploying servers or using external tools

### The SchemaSculpt Solution

SchemaSculpt acts as your **intelligent API design partner**:

- ✅ **AI-Augmented Linting**: Combines deterministic rules with AI reasoning to detect patterns human developers miss
- ✅ **Natural Language Editing**: "Add a health check endpoint" → Done ✨
- ✅ **Instant Feedback**: See errors, warnings, and suggestions as you type
- ✅ **Built-in Testing**: Interactive API Lab with AI-powered mock server
- ✅ **MCP Compliance**: Ensures your APIs are optimized for AI agent consumption
- ✅ **Zero Configuration**: Works out of the box with sensible defaults

---

## 🚀 Key Features

### 🧠 AI-Powered Intelligence

#### 1. **Linter-Augmented AI Analyst**

The flagship feature that sets SchemaSculpt apart. Instead of just finding basic issues, the AI performs **meta-analysis** on linter findings to detect higher-order patterns:

- 🔴 **Security Threat Detection**: "This public endpoint returns PII without authentication"
- 🎨 **Design Pattern Analysis**: "Inconsistent naming conventions detected across 12 endpoints"
- ⚡ **Performance Insights**: "Missing pagination on collection endpoints will cause timeouts"
- 📋 **Governance Violations**: "API lacks standardized error responses"

**How it works:**

1. Deterministic linters find factual issues (fast & accurate)
2. AI analyzes linter findings to connect dots (intelligent reasoning)
3. Get actionable insights that individual rules can't detect

#### 2. **MCP-Ready API Analysis** 🤖

Optimize your APIs for consumption by AI agents (Model Context Protocol):

- **Batch Endpoint Suggestions**: "Add `POST /users/batch-get` to reduce 100 calls to 1"
- **Pagination Detection**: Prevent AI agents from fetching massive datasets
- **Standardized Response Formats**: RFC 7807 compliance for machine-readable errors
- **AI-Friendly Scoring**: See how well your API works with AI agents

#### 3. **Natural Language API Editing**

Use plain English to modify your specifications:

```
"Add a GET endpoint for /health that returns a 200 status"
"Create a User schema with email, name, and createdAt fields"
"Add OAuth2 security to all /admin/* endpoints"
```

The AI understands context and follows OpenAPI best practices.

### ⚡ Intelligent Linting & Auto-Fix

#### 11+ Built-in Linter Rules:

- ✅ **Unused Component Detection**: Remove dead schemas, parameters, and responses
- ✅ **Security Requirements**: Enforce authentication on sensitive endpoints
- ✅ **Naming Conventions**: PascalCase for schemas, kebab-case for paths
- ✅ **Missing Metadata**: Detect missing operationIds, summaries, descriptions
- ✅ **Best Practices**: HTTPS-only, proper HTTP methods, response schemas
- ✅ **AI-Friendliness**: Pagination support, batch endpoints, error formatting

#### One-Click Quick Fixes:

Each linter suggestion includes an **⚡ Auto-Fix** or **✨ AI-Fix** button:

- **Auto-Fix** (⚡): Deterministic, instant fixes (remove unused schema, generate operationId)
- **AI-Fix** (✨): Context-aware AI edits (add missing descriptions, improve examples)

### 🧪 Built-in API Lab & Testing

**Test your APIs without deploying servers:**

1. **Interactive Request Builder**

   - Visual form for building requests
   - Auto-completion from your spec
   - Support for path params, query params, headers, body

2. **AI-Powered Mock Server**

   - One-click mock server startup
   - LLM generates realistic, context-aware mock data
   - Stays in sync with your latest spec changes

3. **Dual Target Mode**

   - Test against AI mocks (instant feedback)
   - Test against your real server (integration testing)

4. **Response Visualization**
   - Syntax-highlighted JSON/XML responses
   - HTTP status code validation
   - Response time tracking

### 🎨 Professional Developer Experience

- **Monaco Editor Integration**: Same editor that powers VS Code
- **Real-time Validation**: Instant feedback as you type (powered by `swagger-parser`)
- **JSON ⟷ YAML Conversion**: Seamless format switching
- **Live Swagger UI**: Interactive API documentation in a separate panel
- **Resizable Panels**: Customize your workspace layout
- **Syntax Highlighting**: Full OpenAPI 3.x support
- **Auto-completion**: Context-aware suggestions

### 🔐 Security & Privacy First

- **100% Local Execution**: All AI processing happens on your machine via Ollama
- **No Data Transmission**: Your specifications never leave your network
- **No Telemetry**: Zero tracking or analytics
- **No Cloud Dependencies**: Works completely offline (except optional OAuth login)

---

## 🏗️ Architecture

SchemaSculpt uses a **three-tier microservices architecture** optimized for AI workloads with RAG-enhanced security analysis:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (UI)                            │
│  React 19 • Monaco Editor • Zustand • WebSockets               │
│  ├─ Advanced Analysis UI (Taint, AuthZ, Schema, Zombie APIs)   │
│  ├─ Attack Path Visualization (Multi-step chain explorer)      │
│  └─ Repository Browser (GitHub/GitLab integration via MCP)     │
└────────────────┬────────────────────────────────────────────────┘
                 │ REST API + WebSocket
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway (Backend)                         │
│  Java 25 • Spring Boot 3 • WebFlux • Redis Sessions            │
│  ├─ Validation Service (swagger-parser)                        │
│  ├─ Linter Engine (11+ rules)                                  │
│  ├─ Session Manager (Redis)                                    │
│  ├─ WebSocket Handler (real-time validation)                   │
│  ├─ Security Findings Extractor (deterministic analysis)       │
│  ├─ Analysis Controller (advanced features orchestration)      │
│  └─ Repository Controller (spec discovery)                     │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP (AI requests)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Service (Python)                          │
│  Python 3.10+ • FastAPI • Ollama • LangChain • ChromaDB        │
│                                                                 │
│  📊 Core Services:                                              │
│  ├─ LLM Service (mistral, llama3, etc.)                        │
│  ├─ Prompt Engineering (optimized for OpenAPI)                 │
│  ├─ JSON Patch Generator (precise edits)                       │
│  ├─ Smart Fix Service (AI + deterministic)                     │
│  ├─ Meta-Analysis Engine (linter augmentation)                 │
│  └─ Mock Data Generator (context-aware)                        │
│                                                                 │
│  🧠 RAG-Enhanced Intelligence:                                  │
│  ├─ RAG Service (dual knowledge base architecture)             │
│  │   ├─ Attacker KB: OWASP API Top 10, MITRE ATT&CK           │
│  │   └─ Governance KB: CVSS, DREAD, GDPR/HIPAA/PCI-DSS        │
│  ├─ Multi-Agent System (coordinated security analysis)         │
│  │   ├─ Vulnerability Scanner Agent                            │
│  │   ├─ Threat Modeling Agent (RAG-augmented)                  │
│  │   ├─ Security Reporter Agent (RAG-augmented)                │
│  │   └─ Attack Path Orchestrator (manages agent coordination)  │
│  └─ Attack Chain Cache (80-90% AI call reduction)              │
│                                                                 │
│  🔍 Advanced Analyzers:                                         │
│  ├─ Taint Analysis (data flow security vulnerabilities)        │
│  ├─ Authorization Matrix (access control patterns)             │
│  ├─ Schema Similarity (code quality & duplication)             │
│  ├─ Zombie API Detection (shadowed/orphaned endpoints)         │
│  └─ Comprehensive Architecture Analysis (holistic health)      │
│                                                                 │
│  🌐 Repository Integration:                                     │
│  ├─ MCP Client (Model Context Protocol for repo browsing)      │
│  └─ Repository Service (GitHub/GitLab spec discovery)          │
└────────────────┬────────────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────┬───────────────┬──────────────────┐
    │                │               │                  │
    ▼                ▼               ▼                  ▼
┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────────┐
│ Ollama   │  │ ChromaDB │  │ Redis Cache  │  │ GitHub/      │
│ (LLM)    │  │ (Vector  │  │ Sessions +   │  │ GitLab       │
│ mistral/ │  │ Store)   │  │ Attack Chain │  │ Repositories │
│ llama3   │  │          │  │ Cache        │  │ (via MCP)    │
└──────────┘  └──────────┘  └──────────────┘  └──────────────┘
```

### Service Communication

| From                             | To                 | Protocol                     | Purpose                                   |
| -------------------------------- | ------------------ | ---------------------------- | ----------------------------------------- |
| **UI** → **API Gateway**         | REST               | `axios`                      | CRUD operations on specs                  |
| **UI** → **API Gateway**         | WebSocket          | `SockJS`/`STOMP`             | Real-time validation updates              |
| **API Gateway** → **AI Service** | HTTP               | `WebClient` (Spring WebFlux) | AI editing, mock data, analysis           |
| **API Gateway** → **Redis**      | TCP                | Spring Data Redis            | Session storage, attack chain caching     |
| **AI Service** → **Ollama**      | HTTP               | `httpx`                      | LLM inference for all AI features         |
| **AI Service** → **ChromaDB**    | Local/HTTP         | LangChain + ChromaDB client  | RAG knowledge base queries (vector store) |
| **AI Service** → **GitHub/GitLab** | HTTP             | MCP client + REST APIs       | Repository browsing & spec discovery      |
| **RAG Service** → **Agents**     | Python in-process  | Direct function calls        | Knowledge augmentation for security agents|
| **Attack Path Orchestrator** → **Agents** | Python in-process | Direct function calls | Multi-agent coordination for attack analysis |

### Data Flow Examples

#### Example 1: AI Meta-Analysis (Linter-Augmented)

```
1. User clicks "Run AI Analysis" in UI
2. UI → API Gateway: POST /sessions/{id}/spec/ai-analysis
3. API Gateway runs all linter rules → Collects errors + suggestions
4. API Gateway → AI Service: POST /ai/meta-analysis (spec + findings)
5. AI Service builds augmented prompt with linter results
6. AI Service → Ollama: LLM inference request
7. Ollama returns insights about patterns detected
8. AI Service structures response → Returns JSON
9. API Gateway → UI: AI insights with severity, category, affected paths
10. UI displays insights in dedicated "AI Insights" panel with blue theme
```

#### Example 2: RAG-Enhanced Attack Path Simulation

```
1. User clicks "Attack Path Simulation" in Advanced Analysis tab
2. UI → API Gateway: POST /sessions/{id}/analysis/attack-path-findings
3. API Gateway extracts security findings deterministically (Java-based)
   ├─ Public endpoints without authentication
   ├─ Sensitive schema fields (PII, credentials)
   ├─ Authorization patterns per endpoint
   └─ Data flow relationships
4. API Gateway → AI Service: POST /ai/security/attack-path-findings
   (Sends findings payload instead of full spec - reduces size 90%)
5. AI Service receives findings → Initializes Attack Path Orchestrator
6. Orchestrator spawns 3 agents in parallel:
   ├─ Vulnerability Scanner Agent (identifies attack surface)
   ├─ Threat Modeling Agent → RAG Service (Attacker KB query)
   │   └─ ChromaDB: Retrieves OWASP API Top 10 & MITRE ATT&CK patterns
   └─ Security Reporter Agent → RAG Service (Governance KB query)
       └─ ChromaDB: Retrieves CVSS, DREAD, compliance frameworks
7. Orchestrator checks Attack Chain Cache (Redis)
   ├─ Cache hit (80% of cases) → Returns cached chains
   └─ Cache miss → Proceeds to LLM generation
8. AI Service → Ollama: Multi-step attack chain generation
   (Augmented with RAG knowledge: exploitation techniques, risk scoring)
9. Orchestrator coordinates agent outputs:
   ├─ Vulnerability findings + Attack chains + Risk assessment
   └─ Compliance implications (GDPR/HIPAA/PCI-DSS)
10. AI Service caches results → Returns AttackPathReport JSON
11. API Gateway → UI: Attack chains with steps, severity, complexity
12. UI renders interactive attack path visualization with expandable steps
```

#### Example 3: Comprehensive Architecture Analysis

```
1. User clicks "Run Comprehensive Analysis" in Advanced Analysis tab
2. UI → API Gateway: POST /sessions/{id}/analysis/comprehensive-architecture
3. API Gateway → AI Service: POST /ai/analyze/comprehensive-architecture
4. AI Service runs 4 analyzers in parallel:
   ├─ Taint Analysis: Tracks sensitive data flow (PII exposure risks)
   ├─ Authorization Matrix: Maps scopes/roles to endpoints (access control gaps)
   ├─ Schema Similarity: Detects duplicate/near-duplicate schemas (code quality)
   └─ Zombie API Detection: Finds shadowed/orphaned endpoints (technical debt)
5. Each analyzer → Ollama: Specialized prompts for domain-specific analysis
6. AI Service aggregates results:
   ├─ Calculates overall health score (0-100)
   ├─ Generates executive summary
   └─ Prioritizes action items by severity & business impact
7. AI Service → API Gateway: ArchitectureAnalysisReport JSON
8. API Gateway → UI: Comprehensive report with 4 sub-analyses + health score
9. UI displays tabbed interface with detailed findings per analyzer
```

---

## 🛠️ Tech Stack

### Frontend (React)

| Technology                 | Version | Purpose                       |
| -------------------------- | ------- | ----------------------------- |
| **React**                  | 19      | UI framework                  |
| **Monaco Editor**          | Latest  | Code editor (same as VS Code) |
| **Zustand**                | Latest  | State management              |
| **react-resizable-panels** | Latest  | Resizable layout              |
| **SockJS** + **STOMP**     | Latest  | WebSocket communication       |
| **swagger-ui-react**       | Latest  | API documentation rendering   |
| **axios**                  | Latest  | HTTP client                   |
| **js-yaml**                | Latest  | YAML parsing/serialization    |

### Backend (Java)

| Technology                       | Version | Purpose                           |
| -------------------------------- | ------- | --------------------------------- |
| **Java**                         | 25      | Programming language              |
| **Spring Boot**                  | 3.x     | Application framework             |
| **Spring WebFlux**               | 3.x     | Reactive HTTP client (AI service) |
| **Spring WebSockets**            | 3.x     | Real-time validation updates      |
| **Spring Data Redis**            | 3.x     | Session storage                   |
| **swagger-parser**               | Latest  | OpenAPI validation                |
| **JUnit 5** + **Testcontainers** | Latest  | Testing                           |

### AI Service (Python)

| Technology                   | Version | Purpose                                      |
| ---------------------------- | ------- | -------------------------------------------- |
| **Python**                   | 3.10+   | Programming language                         |
| **FastAPI**                  | Latest  | Web framework                                |
| **Ollama**                   | Latest  | Local LLM inference                          |
| **LangChain**                | 0.1.0+  | RAG orchestration & agent coordination       |
| **LangChain Community**      | 0.0.20+ | Additional integrations (ChromaDB, HuggingFace) |
| **ChromaDB**                 | 0.4.0+  | Vector database for RAG knowledge bases      |
| **Sentence Transformers**    | 2.2.0+  | Text embeddings for semantic search          |
| **prance**                   | Latest  | OpenAPI spec parsing & validation            |
| **openapi-spec-validator**   | Latest  | OpenAPI validation                           |
| **httpx**                    | Latest  | Async HTTP client                            |

### Infrastructure

| Technology | Purpose                                                        |
| ---------- | -------------------------------------------------------------- |
| **Redis**  | Session storage, attack chain caching                          |
| **Docker** | Redis containerization                                         |
| **Ollama** | Local LLM hosting (mistral, llama3, etc.)                      |
| **ChromaDB** | Persistent vector store for RAG knowledge bases (local SQLite) |

---

## 🚦 Getting Started

### Prerequisites

Before starting, ensure you have:

- ✅ **Java 25+** ([Download](https://jdk.java.net/))
- ✅ **Maven 3.9+** (included with `./mvnw`)
- ✅ **Node.js 18+** and **npm** ([Download](https://nodejs.org/))
- ✅ **Python 3.10+** and **pip** ([Download](https://www.python.org/))
- ✅ **Docker** ([Download](https://www.docker.com/))
- ✅ **Ollama** ([Download](https://ollama.com/))

### Quick Start (5 Minutes)

Follow these steps in **separate terminal windows**:

#### 1️⃣ Start Redis

```bash
docker run -d --name schemasculpt-redis -p 6379:6379 redis
```

Verify: `docker ps` should show the running container.

#### 2️⃣ Start Ollama & Pull Model

```bash
# Download the Mistral model (first time only)
ollama pull mistral

# Verify Ollama is running
ollama list
```

#### 3️⃣ Start AI Service

```bash
cd ai_service

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Copy environment template (first time only)
cp .env.example .env

# Initialize RAG knowledge bases (first time only)
# This ingests OWASP, MITRE ATT&CK, CVSS, DREAD, and compliance frameworks
python app/scripts/ingest_knowledge.py

# Start the service
uvicorn app.main:app --reload
```

✅ AI Service running at `http://localhost:8000`
✅ RAG knowledge bases initialized at `data/vector_store/`

#### 4️⃣ Start Java Backend

```bash
cd api

# Start Spring Boot application
./mvnw spring-boot:run
```

✅ API Gateway running at `http://localhost:8080`

#### 5️⃣ Start React Frontend

```bash
cd ui

# Install dependencies (first time only)
npm install

# Start development server
npm start
```

✅ Browser opens automatically at `http://localhost:3000`

### First Steps

1. **Create a New Project** or **Load an Example Spec**
2. **See Real-time Validation** - The right panel shows errors and suggestions
3. **Click "Run AI Analysis"** - Get intelligent insights about your API
4. **Try a Quick Fix** - Click ⚡ or ✨ on any suggestion
5. **Ask the AI** - Use natural language to edit: "Add a GET /health endpoint"
6. **Test Your API** - Click the "API Lab" tab and send test requests
7. **Advanced Analysis** - Navigate to the "Advanced Analysis" tab for:
   - **Attack Path Simulation** - RAG-enhanced multi-step attack chain detection
   - **Taint Analysis** - Track sensitive data flow through your API
   - **Authorization Matrix** - Visualize access control patterns
   - **Schema Similarity** - Detect duplicate/near-duplicate schemas
   - **Zombie API Detection** - Find shadowed and orphaned endpoints
   - **Comprehensive Architecture Analysis** - Get an overall health score (0-100)

---

## 🎓 Advanced Features

### 🧪 API Hardening

Automatically enhance your API's production-readiness:

- **Add Security Schemes**: OAuth2, API Key, JWT
- **Add Rate Limiting**: `X-RateLimit-*` headers
- **Add Caching**: `Cache-Control`, `ETag` headers
- **Add Pagination**: `limit`, `offset`, `cursor` parameters
- **Add Error Responses**: Standardized error formats (RFC 7807)

### 📊 Validation Categories

Suggestions are grouped by category for easy prioritization:

| Category            | Icon | Description                    | Examples                                       |
| ------------------- | ---- | ------------------------------ | ---------------------------------------------- |
| **AI-Friendliness** | 🤖   | MCP-ready API design           | Pagination, batch endpoints, error formats     |
| **Security**        | 🔐   | Authentication & authorization | Missing security schemes, public PII endpoints |
| **Best Practices**  | 💡   | OpenAPI conventions            | HTTPS-only, proper HTTP methods                |
| **Naming**          | 🏷️   | Consistency & conventions      | PascalCase schemas, kebab-case paths           |
| **Documentation**   | 📝   | Completeness                   | Missing descriptions, examples                 |
| **Performance**     | ⚡   | Scalability concerns           | Missing pagination, large responses            |

### 🎯 Smart Fix System

SchemaSculpt uses a **hybrid fix approach**:

1. **Deterministic Fixes (⚡ Auto-Fix)**

   - Fast, reliable, reversible
   - Examples: Remove unused schema, generate operationId
   - No LLM needed

2. **AI-Powered Fixes (✨ AI-Fix)**

   - Context-aware, intelligent
   - Examples: Add descriptions, improve examples
   - Uses Ollama for generation

3. **Hybrid Smart Fix**
   - Chooses best method automatically
   - Small changes → JSON Patch (fast)
   - Large changes → Full regeneration (comprehensive)

### 🔍 Explanation System

Every suggestion is **explainable**:

- Click **?** button on any suggestion
- Get AI-generated explanation with:
  - **Why** this matters
  - **Best practices** related to the issue
  - **Example solutions** with code
  - **Additional resources** (links to specs, RFCs)
  - **Knowledge sources** (RAG-powered)

Explanations are **cached** for performance.

### 🧠 RAG-Enhanced Security Analysis

SchemaSculpt uses **Retrieval-Augmented Generation (RAG)** to transform from a basic AI tool into a domain expert with specialized security knowledge:

#### Dual Knowledge Base Architecture

1. **Attacker Knowledge Base** (Offensive Security)
   - **OWASP API Security Top 10**: All 10 vulnerabilities with exploitation techniques
   - **MITRE ATT&CK Patterns**: API-specific attack techniques (T1190, T1557, T1212, T1550)
   - Real-world attack scenarios and payloads
   - Used by: Threat Modeling Agent

2. **Governance Knowledge Base** (Defensive Security)
   - **CVSS v3.1**: Complete scoring methodology for risk assessment
   - **DREAD Framework**: Threat modeling and risk rating
   - **Compliance Frameworks**: GDPR, HIPAA, PCI-DSS requirements
   - Used by: Security Reporter Agent

#### Multi-Agent Security Analysis

When you run "Attack Path Simulation", three specialized agents work together:

```
┌─────────────────────────────────────────────────────────────┐
│           Attack Path Orchestrator (Coordinator)            │
└──────────┬─────────────────┬─────────────────┬──────────────┘
           │                 │                 │
           ▼                 ▼                 ▼
  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐
  │ Vulnerability  │  │   Threat     │  │    Security      │
  │ Scanner Agent  │  │  Modeling    │  │    Reporter      │
  │                │  │   Agent      │  │     Agent        │
  │ • Finds attack │  │ (RAG-powered)│  │  (RAG-powered)   │
  │   surface      │  │              │  │                  │
  │ • Identifies   │  │ • Queries    │  │ • Queries        │
  │   weak points  │  │   Attacker   │  │   Governance     │
  │ • Extracts     │  │   KB         │  │   KB             │
  │   patterns     │  │ • Builds     │  │ • Scores risks   │
  │                │  │   attack     │  │   (CVSS/DREAD)   │
  │                │  │   chains     │  │ • Compliance     │
  │                │  │              │  │   implications   │
  └────────────────┘  └──────────────┘  └──────────────────┘
           │                 │                 │
           └─────────────────┴─────────────────┘
                             ▼
              ┌─────────────────────────────┐
              │   Comprehensive Report      │
              │ • Multi-step attack chains  │
              │ • Risk scores & severity    │
              │ • Compliance violations     │
              │ • Remediation guidance      │
              └─────────────────────────────┘
```

#### Advanced Architectural Analyzers

Beyond attack paths, SchemaSculpt provides four specialized analyzers:

1. **🔍 Taint Analysis**
   - Tracks sensitive data (PII, credentials, tokens) through your API
   - Identifies data exposure vulnerabilities
   - Maps data flow from sources to sinks
   - Example: "User email exposed in GET /users/{id} without authentication"

2. **🔐 Authorization Matrix**
   - Visualizes access control patterns across all endpoints
   - Maps OAuth scopes, API keys, and roles to operations
   - Detects missing or inconsistent authorization
   - Example: "Admin endpoints accessible with 'user:read' scope"

3. **🧬 Schema Similarity Analysis**
   - Uses AI to detect duplicate and near-duplicate schemas
   - Identifies opportunities for schema reuse
   - Improves API maintainability and consistency
   - Example: "UserResponse and UserDTO are 90% similar - consider merging"

4. **👻 Zombie API Detection**
   - Finds shadowed endpoints (newer version makes old one obsolete)
   - Detects orphaned endpoints (referenced but not implemented)
   - Identifies technical debt and maintenance issues
   - Example: "GET /api/v1/users shadowed by GET /api/v2/users"

5. **📊 Comprehensive Architecture Analysis**
   - Combines all 4 analyzers into a holistic view
   - Calculates overall API health score (0-100)
   - Generates executive summary with prioritized action items
   - Provides business impact assessment

#### Performance Optimizations

- **Attack Chain Caching**: 80-90% reduction in AI calls during iterative development
- **Multi-level Cache Strategy**: Spec cache → Finding signature cache → Graph structure cache
- **24-hour TTL**: Automatic cache expiration
- **Deterministic Findings Extraction**: Java-based pre-processing reduces payload size by 90%

---

## 📚 Documentation

### 🎯 Feature Guides

Comprehensive guides for each major feature:

- **[🛡️ API Hardening](./docs/features/API_HARDENING.md)** - One-click security and performance patterns (OAuth2, rate limiting, caching, idempotency, validation, error handling)
- **[🔍 Intelligent Linter](./docs/features/LINTER.md)** - 11+ built-in rules with auto-fix capabilities for OpenAPI best practices
- **[✅ Real-time Validator](./docs/features/VALIDATOR.md)** - Instant validation feedback as you type with detailed error reporting
- **[🔐 Security Analysis](./docs/features/SECURITY_ANALYSIS.md)** - AI-powered security auditing for authentication, authorization, and data exposure
- **[⚔️ Attack Path Simulation](./docs/features/ATTACK_SIMULATION.md)** - Discover multi-step vulnerability chains and attack vectors
- **[🤖 AI Assistant](./docs/features/AI_ASSISTANT.md)** - Natural language API editing and intelligent spec generation

[Submit a feature request →](https://github.com/sharma-manish-94/schemasculpt/issues/new)

---

## 🤝 Contributing

**Status**: Currently in active development by the core team.

We're not accepting external contributions yet while we stabilize the architecture and establish contribution guidelines. However, we **welcome feedback**:

- 🐛 **Report Bugs**: [Open an issue](https://github.com/sharma-manish-94/schemasculpt/issues/new)
- 💡 **Suggest Features**: [Open a discussion](https://github.com/sharma-manish-94/schemasculpt/discussions/new)
- 📝 **Improve Documentation**: Typos? Unclear sections? Let us know!

### Future Contribution Areas

Once we open contributions, we'll be looking for help with:

- Additional linter rules
- New AI prompts for specific use cases
- UI/UX improvements
- Documentation and tutorials
- Test coverage
- Performance optimizations

---

## 🙏 Acknowledgments

SchemaSculpt stands on the shoulders of giants:

- **[Ollama](https://ollama.com/)** - Making local LLMs accessible and easy
- **[Spring Boot](https://spring.io/projects/spring-boot)** - Excellent Java framework
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[Monaco Editor](https://microsoft.github.io/monaco-editor/)** - The editor that powers VS Code
- **[Swagger UI](https://swagger.io/tools/swagger-ui/)** - Beautiful API documentation
- **[OpenAPI Initiative](https://www.openapis.org/)** - The standard that makes this all possible

Special thanks to:

- The **Anthropic Claude** team for AI assistance during development
- The **open-source community** for countless libraries and tools
- **Early users** providing feedback and bug reports

---

## 📞 Support & Contact

- 📧 **Email**: code.manish94@gmail.com
- 💬 **Discussions**: [GitHub Discussions](https://github.com/sharma-manish-94/schemasculpt/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/sharma-manish-94/schemasculpt/issues)
- 📖 **Documentation**: [Project Wiki](https://github.com/sharma-manish-94/schemasculpt/wiki)

---

<div align="center">

**Built with ❤️ using AI-assisted development**

If SchemaSculpt helps you build better APIs, consider starring the repo! ⭐

[⬆ Back to Top](#schemasculpt-)

</div>
