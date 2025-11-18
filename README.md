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

SchemaSculpt uses a **three-tier microservices architecture** optimized for AI workloads:

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser (UI)                            │
│  React 19 • Monaco Editor • Zustand • WebSockets               │
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
│  └─ AI Service Proxy                                           │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP (AI requests)
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Service (Python)                          │
│  Python 3.10+ • FastAPI • Ollama Integration                   │
│  ├─ LLM Service (mistral, llama3, etc.)                        │
│  ├─ Prompt Engineering (optimized for OpenAPI)                 │
│  ├─ JSON Patch Generator (precise edits)                       │
│  ├─ Smart Fix Service (AI + deterministic)                     │
│  ├─ Meta-Analysis Engine (linter augmentation)                 │
│  ├─ RAG Service (OpenAPI best practices knowledge base)        │
│  └─ Mock Data Generator (context-aware)                        │
└─────────────────────────────────────────────────────────────────┘
                 │
                 ▼
         ┌───────────────┐         ┌──────────────┐
         │ Ollama (LLM)  │         │ Redis Cache  │
         │ mistral/llama │         │ Sessions     │
         └───────────────┘         └──────────────┘
```

### Service Communication

| From                             | To        | Protocol                     | Purpose                         |
| -------------------------------- | --------- | ---------------------------- | ------------------------------- |
| **UI** → **API Gateway**         | REST      | `axios`                      | CRUD operations on specs        |
| **UI** → **API Gateway**         | WebSocket | `SockJS`/`STOMP`             | Real-time validation updates    |
| **API Gateway** → **AI Service** | HTTP      | `WebClient` (Spring WebFlux) | AI editing, mock data, analysis |
| **API Gateway** → **Redis**      | TCP       | Spring Data Redis            | Session storage                 |
| **AI Service** → **Ollama**      | HTTP      | `httpx`                      | LLM inference                   |

### Data Flow Example: AI Meta-Analysis

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

| Technology                 | Version | Purpose               |
| -------------------------- | ------- | --------------------- |
| **Python**                 | 3.10+   | Programming language  |
| **FastAPI**                | Latest  | Web framework         |
| **Ollama**                 | Latest  | Local LLM inference   |
| **prance**                 | Latest  | OpenAPI spec parsing  |
| **openapi-spec-validator** | Latest  | OpenAPI validation    |
| **httpx**                  | Latest  | Async HTTP client     |
| **ChromaDB**               | Latest  | Vector database (RAG) |

### Infrastructure

| Technology | Purpose                                   |
| ---------- | ----------------------------------------- |
| **Redis**  | Session storage, caching                  |
| **Docker** | Redis containerization                    |
| **Ollama** | Local LLM hosting (mistral, llama3, etc.) |

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

# Start the service
uvicorn app.main:app --reload
```

✅ AI Service running at `http://localhost:8000`

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
