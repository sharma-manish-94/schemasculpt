# SchemaSculpt 🗿

<div align="center">

**Your AI-Powered Co-Pilot for Building Production-Ready APIs**

[![License](https://img.shields.io/badge/License-All_Rights_Reserved-red)](LICENSE)
[![Java](https://img.shields.io/badge/Java-25-orange)](https://openjdk.org/)
[![Spring Boot](https://img.shields.io/badge/Spring%20Boot-4-green)](https://spring.io/projects/spring-boot)
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
- [RepoMind Integration](#-repomind-integration)
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

### 🏛️ Odysseus: Code-Aware API Analysis

Bridge the gap between API design and its actual implementation. The Odysseus feature connects your OpenAPI specification directly to your source code, enabling a new dimension of validation and security analysis.

#### 1. **Repository Intelligence**

- **Link Local Repositories**: Connect your `SchemaSculpt` project to a local git repository to establish a single source of truth.
- **View Implementing Code**: When you select an API endpoint in the editor, instantly see the corresponding function or method in a dedicated "Implementation" tab. No more context-switching between your editor and IDE.

#### 2. **Code-Confirmed Security Findings**

- **Reduce False Positives**: Security vulnerabilities identified in the API specification (e.g., potential Broken Object Level Authorization - BOLA) are automatically validated against the actual source code.
- **Enriched Context**: Findings are augmented with code-level details like cyclomatic complexity, test coverage, and code authors, providing a holistic view of the risk.
- **Evidence-Based Reporting**: Each confirmed finding includes a code snippet highlighting the exact location of the vulnerability, turning vague warnings into actionable issues.

#### 3. **AI-Powered Remediation**

- **Actionable Code Fixes**: For confirmed vulnerabilities, SchemaSculpt's AI can suggest language-specific code fixes.
- **Visual Diff Viewer**: See a clear, side-by-side comparison of the vulnerable code and the AI-suggested fix, making it easy to understand and apply the remediation.

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

SchemaSculpt uses a **four-tier microservices architecture** that integrates API specification analysis with source code intelligence, powered by the **Odysseus** feature set.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (UI)                            │
│  React 19 • Monaco Editor • Zustand • WebSockets               │
│  ├─ Advanced Analysis UI (Taint, AuthZ, Schema, Zombie APIs)   │
│  ├─ Attack Path Visualization (Multi-step chain explorer)      │
│  └─ Implementation Viewer (Code-aware analysis)                │
└────────────────┬────────────────────────────────────────────────┘
                 │ REST API + WebSocket
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   API Gateway (Backend)                         │
│  Java 21 • Spring Boot 4 • WebFlux • Redis Sessions            │
│  ├─ Validation Service (swagger-parser)                        │
│  ├─ Linter Engine (11+ rules)                                  │
│  ├─ RepoMindService (Client for Code Analysis) ───────────────┐
│  ├─ Security Findings Extractor (deterministic)                │
│  └─ Analysis Controller (Orchestrates all analysis)            │
└────────────────┬──────────────────┬─────────────────────────────┘
                 │ HTTP (AI reqs)   │ HTTP (Code context)
                 ▼                  │
┌──────────────────────────────────▼──────────────────────────────┐
│                    AI Service (Python)                          │
│  Python 3.10+ • FastAPI • Ollama • LangChain • ChromaDB        │
│                                                                 │
│  📊 Core Services & 🧠 RAG-Enhanced Intelligence (Unchanged)    │
│                                                                 │
│  🏛️ Code-Aware Intelligence (Odysseus):                         │
│  ├─ Code-Aware Validator (Confirms spec findings in code)      │
│  ├─ Remediation Agent (Suggests code fixes)                    │
│  └─ RepoMind Client (Fetches code, metrics, tests) ───────────┐
└────────────────┬──────────────────┬─────────────────────────────┘
                 │                  │
                 ▼                  ▼
    ┌────────────────┬───────────┬───────────────────┬────────────┐
    │                │           │                   │            │
    ▼                ▼           ▼                   ▼            ▼
┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  ┌───────────┐
│ Ollama   │  │ ChromaDB │  │ RepoMind  │  │ Redis Cache   │  │ GitHub/   │
│ (LLM)    │  │ (Vector  │  │ (Code     │  │ Sessions +    │  │ GitLab    │
│ mistral/ │  │ Store)   │  │ Analysis) │  │ Attack Chain  │  │ (via MCP) │
│ llama3   │  │          │  │           │  │ Cache         │  │           │
└──────────┘  └──────────┘  └───────────┘  └───────────────┘  └───────────┘
```

### Service Communication

| From                                      | To                | Protocol                     | Purpose                                          |
| ----------------------------------------- | ----------------- | ---------------------------- | ------------------------------------------------ |
| **UI** → **API Gateway**                  | REST              | `axios`                      | CRUD operations on specs                         |
| **UI** → **API Gateway**                  | WebSocket         | `SockJS`/`STOMP`             | Real-time validation updates                     |
| **API Gateway** → **AI Service**          | HTTP              | `WebClient` (Spring WebFlux) | AI editing, mock data, analysis                  |
| **API Gateway** → **RepoMind**            | HTTP              | `WebClient` (Spring WebFlux) | Trigger indexing, get code context for an endpoint |
| **API Gateway** → **Redis**               | TCP               | Spring Data Redis            | Session storage, attack chain caching            |
| **AI Service** → **Ollama**               | HTTP              | `httpx`                      | LLM inference for all AI features                |
| **AI Service** → **ChromaDB**             | Local/HTTP        | LangChain + ChromaDB client  | RAG knowledge base queries (vector store)        |
| **AI Service** → **RepoMind**             | HTTP              | `httpx`                      | Get code metrics, find tests, analyze ownership  |
| **AI Service** → **GitHub/GitLab**        | HTTP              | MCP client + REST APIs       | Repository browsing & spec discovery (future)    |
| **RAG Service** → **Agents**              | Python in-process | Direct function calls        | Knowledge augmentation for security agents       |
| **Attack Path Orchestrator** → **Agents** | Python in-process | Direct function calls        | Multi-agent coordination for attack analysis     |

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

#### Example 3: Code-Aware Security Analysis (Odysseus)

```
1. User links a local repository via the UI.
2. UI → API Gateway: POST /projects/{id}/repository (path)
3. API Gateway → RepoMind: POST /index_repo (path)
   (RepoMind starts indexing the repository code in the background)
4. User selects a security finding (e.g., "Potential BOLA on GET /users/{id}").
5. The finding is based on the spec only and is marked as [POTENTIAL].
6. API Gateway → RepoMind: GET /get_context?symbol=getUserById
   (Looks up the code that implements the 'getUserById' operationId)
7. RepoMind returns the file path, source code, and other metrics.
8. API Gateway → AI Service: POST /ai/security/confirm-finding
   (Payload includes the spec finding AND the source code from RepoMind)
9. AI Service (Code-Aware Validator) analyzes the code snippet.
   (Prompt: "Does this code check if the current user owns the requested resource?")
10. AI Service → Ollama: LLM inference request.
11. Ollama confirms the lack of an ownership check.
12. AI Service → API Gateway: Returns { "isConfirmed": true, "confirmationDetail": "No ownership check found on line 52" }.
13. UI updates the finding badge from [POTENTIAL] to [CONFIRMED] and displays the code evidence.
```

#### Example 4: Comprehensive Architecture Analysis
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
| **Java**                         | 21      | Programming language              |
| **Spring Boot**                  | 4.x     | Application framework             |
| **Spring WebFlux**               | 4.x     | Reactive HTTP client (AI service) |
| **Spring WebSockets**            | 4.x     | Real-time validation updates      |
| **Spring Data Redis**            | 4.x     | Session storage                   |
| **swagger-parser**               | Latest  | OpenAPI validation                |
| **JUnit 5** + **Testcontainers** | Latest  | Testing                           |

### AI Service (Python)

| Technology                 | Version | Purpose                                         |
| -------------------------- | ------- | ----------------------------------------------- |
| **Python**                 | 3.10+   | Programming language                            |
| **FastAPI**                | Latest  | Web framework                                   |
| **Ollama**                 | Latest  | Local LLM inference                             |
| **LangChain**              | 0.1.0+  | RAG orchestration & agent coordination          |
| **LangChain Community**    | 0.0.20+ | Additional integrations (ChromaDB, HuggingFace) |
| **ChromaDB**               | 0.4.0+  | Vector database for RAG knowledge bases         |
| **Sentence Transformers**  | 2.2.0+  | Text embeddings for semantic search             |
| **prance**                 | Latest  | OpenAPI spec parsing & validation               |
| **openapi-spec-validator** | Latest  | OpenAPI validation                              |
| **httpx**                  | Latest  | Async HTTP client                               |

### Infrastructure

| Technology   | Purpose                                                        |
| ------------ | -------------------------------------------------------------- |
| **Redis**    | Session storage, attack chain caching                          |
| **Docker**   | Redis containerization                                         |
| **Ollama**   | Local LLM hosting (mistral, llama3, etc.)                      |
| **ChromaDB** | Persistent vector store for RAG knowledge bases (local SQLite) |

---

## 🚦 Getting Started

### Prerequisites

Before starting, ensure you have:

- ✅ **Java 25+** ([Download](https://jdk.java.net/))
- ✅ **Node.js 18+** and **npm** ([Download](https://nodejs.org/))
- ✅ **Python 3.10+** and **pip** ([Download](https://www.python.org/))
- ✅ **Docker** ([Download](https://www.docker.com/)) — for PostgreSQL and Redis
- ✅ **Ollama** ([Download](https://ollama.com/)) — for local LLM inference

---

### 🏃 Local Development Setup

Run each service in a **separate terminal window**.

#### 1️⃣ Start Infrastructure (PostgreSQL + Redis)

```bash
# Start PostgreSQL and Redis via Docker Compose
docker-compose up -d

# Verify both containers are healthy
docker-compose ps
```

- **PostgreSQL** → `localhost:5432` (used by the Java backend)
- **Redis** → `localhost:6379` (used for session storage)

---

#### 2️⃣ Start Ollama & Pull the LLM Model

```bash
# Pull the Mistral model (only needed once, ~4 GB download)
ollama pull mistral

# Verify Ollama is running and the model is available
ollama list
```

Ollama runs as a background service at `http://localhost:11434`.

---

#### 3️⃣ Start the AI Service

```bash
cd ai_service

# First time only: create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# First time only: copy environment template
cp .env.example .env

# First time only: initialize RAG knowledge bases
# Ingests OWASP, MITRE ATT&CK, CVSS, and compliance frameworks
python app/scripts/ingest_knowledge.py

# Start the AI service
uvicorn app.main:app --reload
```

✅ **AI Service** running at `http://localhost:8000`

---

#### 4️⃣ Start the Java Backend

```bash
cd api

# Start the Spring Boot API gateway
./gradlew bootRun
```

✅ **API Gateway** running at `http://localhost:8080`

**First run**: Flyway will auto-create all database tables.

---

#### 5️⃣ Start the React Frontend

```bash
cd ui

# First time only: install dependencies
npm install

# Start the development server
npm start
```

✅ **Frontend** opens automatically at `http://localhost:3000`

---

#### 6️⃣ (Optional) Start RepoMind — Code Intelligence

RepoMind enables **Code-Aware Analysis**: AI that understands your actual implementation, not just your spec.

```bash
# Install RepoMind (first time only)
pip install repomind
# OR from source:
# git clone https://github.com/sharma-manish-94/repomind.git
# cd repomind && pip install -e ".[dev]"

# Start RepoMind MCP server
REPOMIND_ENABLED=true repomind serve
```

Then set the following in `ai_service/.env`:

```env
REPOMIND_ENABLED=true
REPOMIND_COMMAND=repomind
REPOMIND_ARGS=serve
```

✅ **RepoMind** running (MCP stdio) — ready for code indexing

To link your codebase: open SchemaSculpt → **Repository** tab → **Connect a Local Repository** → Browse and select your project folder → **Link & Index**.

---

### 📊 Service Summary

| Service       | Technology           | Port  | Required |
|---------------|----------------------|-------|----------|
| PostgreSQL    | Docker               | 5432  | ✅ Yes   |
| Redis         | Docker               | 6379  | ✅ Yes   |
| Ollama        | Local binary         | 11434 | ✅ Yes   |
| AI Service    | Python / FastAPI     | 8000  | ✅ Yes   |
| API Gateway   | Java / Spring Boot   | 8080  | ✅ Yes   |
| Frontend      | React / Node.js      | 3000  | ✅ Yes   |
| RepoMind      | Python / MCP stdio   | —     | ⚡ Optional |

---

### First Steps

1. **Open** `http://localhost:3000`
2. **Load an Example Spec** or paste your OpenAPI YAML/JSON into the editor
3. **See Real-time Validation** — the right panel shows errors and suggestions
4. **Run AI Analysis** — click "Run AI Analysis" for intelligent insights
5. **Try Auto-fix** — click ⚡ or ✨ on any suggestion to apply it
6. **Advanced Analysis** — navigate to the "Advanced Analysis" tab for:
   - **Attack Path Simulation** — RAG-enhanced multi-step attack chain detection
   - **Taint Analysis** — track sensitive data flow through your API
   - **Authorization Matrix** — visualize access control patterns
   - **Zombie API Detection** — find shadowed and orphaned endpoints
7. **Code Intelligence** (optional) — link your repository via the Repository tab to enable code-aware attack chain validation with RepoMind


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

   - Uses Jaggard Similarity to detect duplicate and near-duplicate schemas
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

## 🔗 RepoMind Integration

SchemaSculpt integrates with [RepoMind](https://github.com/sharma-manish-94/repomind), an AI-powered code intelligence MCP server, to bridge the gap between **what your OpenAPI spec says** and **what your code actually does**.

When connected, RepoMind provides four specialized tools that transform SchemaSculpt's AI-generated attack chains from spec-level hypotheses into code-confirmed (or code-disputed) findings.

### How It Works

```
SchemaSculpt AI ──generates──► Attack Chain (spec-level analysis)
                                        │
                            RepoMind MCP Server (37 tools)
                                        │
               ┌────────────────────────▼───────────────────────────┐
               │  correlate_spec_to_code     — Find the code handler │
               │  verify_auth_contract_deep  — Compare auth schemes  │
               │  validate_attack_chain      — Confirm chain in code │
               │  trace_schema_field_to_sink — Trace injection risk  │
               └────────────────────────┬───────────────────────────┘
                                        │
                            Code-Level Evidence
                   (CODE_CONFIRMED / CODE_DISPUTED / PARTIAL)
```

### Setup

**Step 1: Install and Start RepoMind**

```bash
# Install via pip (recommended)
pip install repomind

# OR install from source
git clone https://github.com/sharma-manish-94/repomind.git
cd repomind && pip install -e ".[dev]"

# Start the MCP server
REPOMIND_ENABLED=true repomind serve
```

**Step 2: Enable RepoMind in the AI Service**

In `ai_service/.env`, add:

```env
REPOMIND_ENABLED=true
REPOMIND_COMMAND=repomind
REPOMIND_ARGS=serve
```

Then restart the AI service (`uvicorn app.main:app --reload`).

**Step 3: Link your codebase in the UI**

Open SchemaSculpt → **Repository** tab → **Connect a Local Repository** → click **Browse** to navigate to your project folder → **Link & Index**.

RepoMind will index your code using tree-sitter AST parsing and BGE-base embeddings — 100% locally.

**Step 4: Run code-aware analysis**

Navigate to the **Advanced Analysis** tab. Attack chain findings are now enriched with code-level evidence (CODE_CONFIRMED / CODE_DISPUTED / PARTIAL).

### The Four Integration Tools

#### `correlate_spec_to_code` — Spec-to-Code Mapping

Given an OpenAPI path and HTTP method, finds the implementing route handler in indexed source code.

```json
Input:  { "openapi_path": "/users/{id}", "http_method": "DELETE" }
Output: {
  "handler": "delete_user",
  "file": "src/routes/users.py",
  "start_line": 87,
  "confidence": 1.0,
  "has_auth": true,
  "auth_mechanisms": ["jwt"],
  "callees": ["verify_token", "db.delete"]
}
```

Path normalization handles all framework syntaxes automatically:
- `{id}` (FastAPI / Spring / OpenAPI)
- `:id` (Express / NestJS)
- `<int:id>` (Flask)

**Use case in SchemaSculpt:** When you select an endpoint in the editor, the Implementation tab instantly shows the corresponding code, file path, and line number — no IDE context-switching.

#### `verify_auth_contract_deep` — Auth Contract Audit

Compares OpenAPI security scheme declarations against what the code actually enforces.

| Verdict | Meaning |
|---------|---------|
| `PASS` | Spec and code agree — same auth type enforced |
| `NO AUTH IN CODE` | Spec requires Bearer JWT, handler has no auth check |
| `WRONG AUTH SCHEME` | Spec says OAuth2, code uses API key |
| `SCOPE NOT ENFORCED` | OAuth2 scope required in spec, not checked in code |

**Use case in SchemaSculpt:** Security findings marked as [POTENTIAL] are automatically promoted to [CONFIRMED] or [DISPUTED] with code-level evidence instead of relying on spec-only analysis.

#### `validate_attack_chain` — Attack Chain Code Validation

Takes the multi-step attack chain generated by SchemaSculpt's AI agents and validates each step against real code.

```json
Input: {
  "attack_steps": [
    {
      "step": 1, "endpoint": "/users/{id}", "method": "GET",
      "vulnerability_type": "bola", "owasp": "API1:2023"
    },
    {
      "step": 2, "endpoint": "/users/{id}/orders", "method": "GET",
      "vulnerability_type": "excessive_data_exposure", "owasp": "API3:2023"
    }
  ]
}
Output: {
  "chain_verdict": "FULLY_EXPLOITABLE",
  "steps": [
    { "step": 1, "verdict": "CODE_CONFIRMED", "evidence": "No ownership check found" },
    { "step": 2, "verdict": "CODE_CONFIRMED", "evidence": "Full model serialized" }
  ]
}
```

**Chain verdicts:**
- `FULLY_EXPLOITABLE` — All steps confirmed in code
- `PARTIALLY_EXPLOITABLE` — Some steps confirmed, others disputed
- `MITIGATED` — Majority of steps have code-level mitigations
- `INSUFFICIENT_DATA` — Handler not indexed or too many unknowns

**Use case in SchemaSculpt:** Attack chains generated by the RAG-enhanced Attack Path Orchestrator are validated against real code before being presented, dramatically reducing false positives.

#### `trace_schema_field_to_sink` — Injection Risk Tracing

Traces a request schema field (e.g., `user_id`, `query`, `filename`) from the route handler to dangerous code sinks.

**Sinks detected:**
- `SQL_QUERY` — raw SQL with user input (injection risk)
- `OS_COMMAND` — subprocess/exec with user data (RCE risk)
- `FILE_OPERATION` — file read/write with user path (traversal risk)
- `TEMPLATE_RENDER` — template with user data (SSTI/XSS risk)
- `EVAL` — eval/exec with user input (RCE risk)
- `HTTP_REQUEST` — outbound request with user URL (SSRF risk)
- `DATABASE_WRITE` — ORM save with unfiltered fields (mass assignment risk)

**Special cases:**
- Fields named `role`, `is_admin` → mass assignment CRITICAL
- Fields named `password`, `token` flowing to logs → HIGH

**Use case in SchemaSculpt:** Taint Analysis findings from the Advanced Analysis tab are enriched with a direct code path from the request field to the dangerous sink, including whether sanitization was detected between them.

### Example: Code-Confirmed BOLA Attack Chain

**Before RepoMind integration** (spec-only):
```
[POTENTIAL] API1:2023 BOLA: GET /users/{id} may expose other users' data
Chain: GET /users/{id} → GET /users/{id}/orders → DELETE /users/{id}
Confidence: 65% (spec-level reasoning only)
```

**After RepoMind integration** (code-confirmed):
```
[CONFIRMED] API1:2023 BOLA: GET /users/{id} exposes other users' data
Chain: FULLY_EXPLOITABLE (3/3 steps confirmed in code)

Step 1 — GET /users/{id}: CODE_CONFIRMED
  Handler: get_user() @ src/routes/users.py:52
  Evidence: No ownership check between token.user_id and path param id

Step 2 — GET /users/{id}/orders: CODE_CONFIRMED
  Handler: get_orders() @ src/routes/orders.py:89
  Evidence: Returns full Order model with payment details (no field filtering)

Step 3 — DELETE /users/{id}: CODE_CONFIRMED
  Handler: delete_user() @ src/routes/users.py:134
  Evidence: Deletes by path param id without checking requester ownership
```

### Supported Frameworks

RepoMind's route linker recognizes handlers from:

| Language | Frameworks |
|----------|-----------|
| Python | Flask, FastAPI, Django REST Framework |
| JavaScript/TypeScript | Express.js, NestJS |
| Java | Spring MVC, Spring Boot (`@GetMapping`, `@RestController`) |

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
