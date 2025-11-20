# Attack Path Simulation - Implementation Guide

## Overview

The **Attack Path Simulation** is an AI-powered security feature that thinks like a real hacker. Unlike traditional linters that find isolated vulnerabilities, this system discovers **multi-step attack chains** where vulnerabilities can be combined to achieve high-impact outcomes like privilege escalation, data exfiltration, or account takeover.

## The "Wow" Factor

### Traditional Linting vs. Attack Path Simulation

**Traditional Security Linting:**

```
❌ Issue 1: GET /users/{id} returns sensitive 'role' field
❌ Issue 2: PUT /users/{id} accepts 'role' in request body
```

**Attack Path Simulation:**

```
🚨 CRITICAL ATTACK CHAIN: Privilege Escalation to Admin

An attacker can become an admin in 2 steps:

Step 1 (Reconnaissance): Call GET /users/123 to discover their own role
  → Gains: user_id, current_role

Step 2 (Privilege Escalation): Call PUT /users/123 with {"role": "admin"}
  → Result: Regular user becomes admin!

Business Impact: Attackers gain full system control, can access all data,
modify other users, and perform administrative actions.

Fix Priority: IMMEDIATE
```

This contextual insight is **impossible** without an agentic AI system.

---

## Architecture

### Agentic Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                Attack Path MCP Context                       │
│           (Shared "War Room" Memory)                         │
│                                                              │
│  • OpenAPI Specification                                     │
│  • Individual Vulnerabilities (from Scanner Agent)          │
│  • Attack Chains (from Threat Modeling Agent)               │
│  • Executive Report (from Reporter Agent)                   │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Scanner Agent   │  │ Threat Agent    │  │ Reporter Agent  │
│                 │  │                 │  │                 │
│ Finds 20+ vulns │→ │ Chains vulns    │→ │ Executive       │
│ using existing  │  │ into 3 attack   │  │ summary with    │
│ OWASP analyzers │  │ paths using LLM │  │ prioritized     │
│                 │  │ reasoning       │  │ findings        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         ▲                    ▲                    ▲
         └────────────────────┴────────────────────┘
                              │
                   ┌──────────┴──────────┐
                   │ AttackPathOrchestrator│
                   │   (Planner Agent)     │
                   │                       │
                   │ Coordinates workflow  │
                   │ + manages MCP context │
                   └───────────────────────┘
```

### Four Specialized Agents

1. **VulnerabilityScannerAgent** ("The Linter")

   - Wraps existing security analyzers (Authentication, Authorization, DataExposure, OWASP)
   - Finds 20+ individual vulnerabilities
   - Execution time: ~2-3 seconds

2. **ThreatModelingAgent** ("The Hacker")

   - Uses LLM (Mistral) to think like an attacker
   - Analyzes how vulnerabilities can be chained together
   - Models realistic attack sequences with step-by-step exploitation
   - Execution time: ~10-15 seconds

3. **SecurityReporterAgent** ("The CISO")

   - Generates executive summaries in business terms
   - Prioritizes findings by risk level
   - Creates remediation roadmaps (immediate, short-term, long-term)
   - Execution time: ~3-5 seconds

4. **AttackPathOrchestrator** ("The Planner")
   - Coordinates all agents sequentially
   - Manages the MCP (Model Context Protocol) shared memory
   - Handles errors and progress tracking
   - Total orchestration time: ~15-25 seconds

---

## Implementation Details

### Backend (AI Service)

#### New Files Created

1. **`ai_service/app/schemas/attack_path_schemas.py`**

   - Data models for attack paths, chains, steps, and reports
   - Enums: `AttackStepType`, `AttackComplexity`
   - Models: `AttackStep`, `AttackChain`, `AttackPathContext`, `AttackPathAnalysisReport`

2. **`ai_service/app/services/agents/vulnerability_scanner_agent.py`**

   - Wraps `SecurityAnalysisWorkflow`
   - Converts findings into attack path format
   - Groups by OWASP category and severity

3. **`ai_service/app/services/agents/threat_modeling_agent.py`**

   - Core LLM-based agent
   - Builds detailed prompts for threat modeling
   - Parses LLM responses into structured `AttackChain` objects
   - Temperature: 0.4 (focused analysis)
   - Max tokens: 8000

4. **`ai_service/app/services/agents/security_reporter_agent.py`**

   - Generates executive summaries using LLM
   - Calculates security scores (0-100)
   - Determines risk levels (CRITICAL/HIGH/MEDIUM/LOW)
   - Creates remediation roadmaps

5. **`ai_service/app/services/agents/attack_path_orchestrator.py`**
   - Main coordinator
   - Manages MCP context lifecycle
   - Sequential workflow execution
   - Progress tracking for WebSocket updates (future)

#### API Endpoint

**Endpoint:** `POST /ai/security/attack-path-simulation`

**Request:**

```json
{
  "spec_text": "OpenAPI spec as JSON/YAML string",
  "analysis_depth": "quick | standard | comprehensive | exhaustive",
  "max_chain_length": 5,
  "exclude_low_severity": false
}
```

**Response:**

```json
{
  "report_id": "uuid",
  "risk_level": "CRITICAL",
  "overall_security_score": 45.5,
  "executive_summary": "This API has CRITICAL security vulnerabilities...",
  "critical_chains": [...],
  "high_priority_chains": [...],
  "all_chains": [
    {
      "chain_id": "uuid",
      "name": "Privilege Escalation via Mass Assignment",
      "severity": "CRITICAL",
      "complexity": "low",
      "likelihood": 0.85,
      "impact_score": 9.5,
      "attack_goal": "Escalate to admin privileges",
      "business_impact": "Attackers gain full system control",
      "steps": [
        {
          "step_number": 1,
          "step_type": "reconnaissance",
          "endpoint": "/users/{id}",
          "http_method": "GET",
          "description": "Discover own user ID and role",
          "information_gained": ["user_id", "current_role"],
          "requires_authentication": true
        },
        {
          "step_number": 2,
          "step_type": "privilege_escalation",
          "endpoint": "/users/{id}",
          "http_method": "PUT",
          "description": "Update own role to admin",
          "example_payload": {"role": "admin"},
          "requires_previous_steps": [1]
        }
      ],
      "remediation_steps": [
        "Remove 'role' field from GET /users/{id} response",
        "Add server-side validation to reject 'role' updates in PUT /users/{id}",
        "Implement proper authorization checks"
      ],
      "remediation_priority": "IMMEDIATE"
    }
  ],
  "top_3_risks": [
    "Privilege Escalation via Mass Assignment: An attacker can..."
  ],
  "immediate_actions": ["Fix critical chains now"],
  "short_term_actions": ["Fix high-severity chains in 1-2 weeks"],
  "long_term_actions": ["Implement API security framework"]
}
```

**Caching:** 24-hour TTL (same as other security analyses)

#### Modified Files

- **`ai_service/app/api/endpoints.py`**
  - Added `/ai/security/attack-path-simulation` endpoint (line 1843)

---

### Backend (Spring Boot API Gateway)

#### Modified Files

1. **`api/src/main/java/.../service/ai/AIService.java`**

   - Added `runAttackPathSimulation()` method (line 308)
   - Makes HTTP POST to AI service
   - Returns report as `Map<String, Object>`

2. **`api/src/main/java/.../controller/AnalysisController.java`**
   - Added `@PostMapping("/attack-path-simulation")` endpoint (line 64)
   - Route: `POST /api/v1/sessions/{sessionId}/analysis/attack-path-simulation`
   - Query params: `analysisDepth`, `maxChainLength`

---

### Frontend (React UI)

#### New Files Created

1. **`ui/src/api/attackPathService.js`**

   - API client for attack path simulation
   - Helper functions: `formatSeverity()`, `formatRiskLevel()`, `getSecurityScoreColor()`

2. **`ui/src/components/security/AdvancedSecurityAudit.js`**

   - Main trigger button component
   - Shows feature description and benefits
   - Progress indicator with stages
   - Error handling

3. **`ui/src/components/security/AdvancedSecurityAudit.css`**

   - Beautiful gradient card design
   - Animated progress bar
   - Responsive layout

4. **`ui/src/components/security/AttackPathReport.js`**

   - Full-screen report viewer
   - Three tabs: Overview, Attack Chains, Remediation
   - Modal for detailed chain view
   - Step-by-step attack visualization

5. **`ui/src/components/security/AttackPathReport.css`**
   - Comprehensive styling for report
   - Severity badges, risk indicators
   - Attack chain cards with hover effects
   - Modal with overlay and animations

#### Modified Files

- **`ui/src/features/editor/components/ValidationPanel.js`**
  - Imported `AdvancedSecurityAudit` component (line 6)
  - Added component after validation header (line 205)

---

## How to Use

### For Developers

1. **Start all services:**

```bash
# Terminal 1: Redis
docker run -d --name schemasculpt-redis -p 6379:6379 redis

# Terminal 2: AI Service
cd ai_service
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3: Backend API
cd api
./mvnw spring-boot:run

# Terminal 4: Frontend
cd ui
npm install
npm start
```

2. **Open SchemaSculpt:** Navigate to http://localhost:3000

3. **Load an OpenAPI spec:** Paste or upload your specification

4. **Run Attack Path Simulation:**

   - Look for the purple "Advanced Security Audit" card in the ValidationPanel
   - Click "🚀 Run Advanced Security Audit"
   - Wait 15-25 seconds while AI analyzes

5. **Review Results:**
   - **Overview Tab:** Executive summary, statistics, top 3 risks
   - **Attack Chains Tab:** Click any chain to see detailed exploitation steps
   - **Remediation Tab:** Prioritized action items

### For Users (Product Demo)

**The Pitch:**

> "Most security tools just give you a flat list of vulnerabilities. But real hackers don't exploit one bug—they chain multiple weaknesses together. Our AI agent thinks like a real attacker to find these attack paths **before** the bad guys do."

**Demo Script:**

1. Show a spec with security issues (e.g., mass assignment + information disclosure)

2. Click "Run Advanced Security Audit"

3. While it's running (15-25s), explain:

   - "Scanner Agent is finding all vulnerabilities..."
   - "Threat Agent is analyzing how they can be chained..."
   - "Reporter Agent is generating the executive summary..."

4. Show the report:

   - **Executive Summary:** "This is what you'd show your CEO"
   - **Attack Chains:** "Here's exactly how a hacker would exploit this"
   - **Remediation:** "Here's your prioritized to-do list"

5. Click into a CRITICAL chain to show the step-by-step attack

---

## Key Features

### 1. Multi-Step Attack Chains

- Not just isolated bugs, but **exploitation sequences**
- Each step builds on the previous one
- Shows information gained at each stage

### 2. Business-Focused Reporting

- Executive summary in non-technical language
- Risk levels: CRITICAL / HIGH / MEDIUM / LOW
- Security score: 0-100 (higher is better)

### 3. Realistic Threat Modeling

- LLM reasons about attacker capabilities
- Assesses complexity: low / medium / high
- Calculates likelihood (0-1) and impact (0-10)

### 4. Actionable Remediation

- **Immediate actions:** Fix right now
- **Short-term:** Fix within 1-2 weeks
- **Long-term:** Architectural improvements

### 5. Caching & Performance

- 24-hour cache for identical specs
- Parallel agent execution (future)
- WebSocket progress updates (future)

---

## Example Attack Chains

### Example 1: Privilege Escalation

**Vulnerabilities Found:**

- Information Disclosure: GET /users/{id} exposes 'role' field
- Mass Assignment: PUT /users/{id} accepts 'role' field

**Attack Chain:**

```
🚨 CRITICAL: Privilege Escalation to Admin

Step 1: GET /users/123
  → Attacker learns their user_id and current role

Step 2: PUT /users/123 with {"role": "admin"}
  → Attacker changes their own role to admin

Result: Regular user becomes admin!
```

### Example 2: Data Exfiltration

**Vulnerabilities Found:**

- Missing Authentication: GET /users endpoint unprotected
- Information Disclosure: Returns sensitive PII fields

**Attack Chain:**

```
🚨 HIGH: Mass Data Exfiltration

Step 1: GET /users (no auth required)
  → Attacker downloads all user records

Step 2: Extract PII (email, phone, SSN)
  → Attacker builds customer database

Result: Complete data breach!
```

### Example 3: Account Takeover

**Vulnerabilities Found:**

- IDOR: GET /users/{id} doesn't check authorization
- Broken Authorization: PUT /users/{id} allows cross-user updates

**Attack Chain:**

```
🚨 CRITICAL: Account Takeover

Step 1: GET /users/1 (admin user)
  → Attacker discovers admin email

Step 2: PUT /users/1 with {"email": "attacker@evil.com"}
  → Attacker changes admin email

Step 3: Password reset to attacker's email
  → Attacker resets admin password

Result: Complete account takeover!
```

---

## Technical Considerations

### LLM Requirements

- **Model:** Mistral (via Ollama)
- **Temperature:** 0.4 (focused, deterministic)
- **Max Tokens:** 8000
- **Prompt Engineering:** Detailed system prompts with examples

### Error Handling

- Graceful fallback if LLM parsing fails
- Continue analysis if one agent fails
- Detailed logging for debugging

### Performance

- Scanner Agent: ~2-3s (deterministic)
- Threat Agent: ~10-15s (LLM-based)
- Reporter Agent: ~3-5s (LLM-based)
- **Total:** ~15-25 seconds

### Scalability

- Caching reduces repeated analysis
- Future: Parallel agent execution
- Future: Streaming results via WebSocket
- Future: Background job queue for large specs

---

## Future Enhancements

### Phase 2 Features

1. **Real-time Progress Updates**

   - WebSocket integration for live progress
   - Stream attack chains as they're discovered

2. **Interactive Attack Simulation**

   - "Try This Attack" button
   - Shows actual HTTP requests/responses
   - Explains why it works

3. **Fix Generation**

   - Auto-generate code fixes for chains
   - JSON Patch operations for spec fixes
   - Before/after comparison

4. **Export & Sharing**

   - PDF report generation
   - Share reports with stakeholders
   - Integration with Jira/GitHub Issues

5. **Custom Attack Patterns**

   - User-defined attack pattern library
   - Industry-specific threat models (fintech, healthcare, etc.)
   - Historical attack pattern learning

6. **Comparison Mode**
   - Compare specs before/after changes
   - Show improvement in security score
   - Track remediation progress over time

---

## Testing

### Manual Testing

1. **Test with vulnerable spec:**

```yaml
openapi: 3.0.0
paths:
  /users/{id}:
    get:
      responses:
        "200":
          content:
            application/json:
              schema:
                properties:
                  id: { type: integer }
                  role: { type: string } # ← Information Disclosure
    put:
      requestBody:
        content:
          application/json:
            schema:
              properties:
                name: { type: string }
                role: { type: string } # ← Mass Assignment
      responses:
        "200": { description: Updated }
```

Expected: 1 CRITICAL attack chain (Privilege Escalation)

2. **Test with secure spec:**

```yaml
openapi: 3.0.0
paths:
  /users/{id}:
    get:
      security:
        - bearerAuth: []
      responses:
        "200":
          content:
            application/json:
              schema:
                properties:
                  id: { type: integer }
                  name: { type: string }
                  # NO role field
```

Expected: 0 attack chains, LOW risk level

### Integration Testing

```bash
# Test AI service endpoint directly
curl -X POST http://localhost:8000/ai/security/attack-path-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "spec_text": "...",
    "analysis_depth": "standard",
    "max_chain_length": 5
  }'

# Test via Spring Boot API
curl -X POST "http://localhost:8080/api/v1/sessions/{sessionId}/analysis/attack-path-simulation?analysisDepth=standard&maxChainLength=5"
```

---

## Troubleshooting

### Common Issues

1. **"AI service unavailable"**

   - Check Ollama is running: `ollama list`
   - Check AI service is running: `curl http://localhost:8000/health`
   - Check mistral model is installed: `ollama pull mistral`

2. **"No attack chains found"**

   - This is normal for well-secured specs
   - The Scanner Agent still finds individual vulnerabilities
   - Report will show isolated vulnerabilities

3. **"Analysis taking too long"**

   - Standard analysis: 15-25 seconds
   - Comprehensive analysis: 30-45 seconds
   - Check LLM performance (CPU/GPU usage)

4. **"Invalid JSON from LLM"**
   - LLM occasionally returns malformed JSON
   - Retry the analysis
   - Check logs: `tail -f ai_service/logs/app.log`

---

## Conclusion

The **Attack Path Simulation** feature is a groundbreaking addition to SchemaSculpt that elevates it from a simple linter to a sophisticated security analysis tool. By using an agentic AI system with shared memory (MCP), we can discover attack chains that would be impossible to find with static analysis alone.

This feature demonstrates:

- ✅ Advanced AI agent orchestration
- ✅ Real-world threat modeling
- ✅ Executive-level reporting
- ✅ Actionable remediation guidance
- ✅ Beautiful, intuitive UI

It's the kind of feature that makes security teams say **"Wow, I need this!"**

---

## Credits

- **Agent Architecture:** Inspired by Model Context Protocol (MCP)
- **Threat Modeling:** Based on MITRE ATT&CK and OWASP API Top 10
- **LLM:** Mistral via Ollama
- **UI Design:** Gradient-based modern design system

Built with ❤️ for SchemaSculpt
