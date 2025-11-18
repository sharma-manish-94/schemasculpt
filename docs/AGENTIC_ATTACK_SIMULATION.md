# MCP-Based Agentic Attack Path Simulation - Developer Guide

**Author:** SchemaSculpt Team
**Last Updated:** November 2025
**Purpose:** Knowledge Transfer - Understanding the Agentic AI System for Security Analysis

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [The Agent Pattern](#the-agent-pattern)
4. [Attack Path Simulation Flow](#attack-path-simulation-flow)
5. [Key Components](#key-components)
6. [Agent Deep Dive](#agent-deep-dive)
7. [MCP Context System](#mcp-context-system)
8. [Code Walkthrough](#code-walkthrough)
9. [Extending the System](#extending-the-system)
10. [Debugging & Troubleshooting](#debugging--troubleshooting)

---

## Overview

### What is MCP?

**MCP (Model Context Protocol)** is a pattern for managing AI agent communication and state. Think of it like "Redux for AI agents" - it provides:
- **Centralized State Management**: All agents share a common context
- **Progress Tracking**: Real-time updates on what the AI is doing
- **Result Coordination**: Agents pass results through the context
- **Execution History**: Track what agents have done and in what order

### What are Agentic Systems?

Traditional AI: Give a prompt → Get a response → Done

Agentic AI:
1. Break complex task into sub-tasks
2. Specialized agents handle each sub-task
3. Agents collaborate by sharing context
4. Orchestrator coordinates the workflow
5. Each agent can call LLM independently

**Analogy**: Think of it like a software development team:
- **Scanner Agent** = QA Engineer finding bugs
- **Threat Modeling Agent** = Security Architect designing attack scenarios
- **Reporter Agent** = Technical Writer creating documentation
- **Orchestrator** = Project Manager coordinating the team

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Request                             │
│              "Analyze this API for attack chains"                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API Controller                          │
│     /api/v1/sessions/{id}/analysis/attack-path-simulation       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Service Endpoint                           │
│              POST /ai/security/attack-path-simulation            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Attack Path Orchestrator                       │
│   • Creates MCP Context (shared state)                          │
│   • Coordinates agent execution                                  │
│   • Manages workflow stages                                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Scanner    │    │   Threat     │    │   Reporter   │
│    Agent     │    │   Modeling   │    │    Agent     │
│              │    │    Agent     │    │              │
│ • Finds vulns│    │ • Builds     │    │ • Creates    │
│ • Uses LLM   │    │   chains     │    │   report     │
│ • Updates    │    │ • Uses LLM   │    │ • Uses LLM   │
│   context    │    │ • Updates    │    │ • Generates  │
│              │    │   context    │    │   summary    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │   MCP Context   │
                    │  (Shared State) │
                    │                 │
                    │ • Vulnerabilities│
                    │ • Attack Chains │
                    │ • Progress %    │
                    │ • Tokens Used   │
                    └─────────────────┘
```

---

## The Agent Pattern

### Base Agent Class

Every agent inherits from `LLMAgent`:

```python
# ai_service/app/services/agents/base_agent.py

class LLMAgent(ABC):
    """Base class for all LLM-powered agents"""

    def __init__(self, name: str, description: str, llm_service):
        self.name = name
        self.description = description
        self.llm_service = llm_service
        self._total_tokens_used = 0

    @abstractmethod
    async def execute(self, task: Dict, context: Any) -> Dict:
        """Execute the agent's task"""
        pass

    @abstractmethod
    def can_handle_task(self, task_type: str) -> bool:
        """Check if this agent can handle the task"""
        pass
```

### Why This Pattern?

1. **Separation of Concerns**: Each agent has ONE job
2. **Testability**: Mock LLM responses to test agent logic
3. **Extensibility**: Add new agents without modifying existing ones
4. **Reusability**: Agents can be used in different workflows
5. **Token Tracking**: Each agent tracks its LLM usage

---

## Attack Path Simulation Flow

### Step-by-Step Execution

```python
# File: ai_service/app/services/security/attack_path_orchestrator.py

async def run_attack_path_analysis(self, request: AttackPathAnalysisRequest):
    """
    Main orchestration method

    Flow:
    1. Parse OpenAPI spec
    2. Initialize MCP context
    3. Execute agents in sequence
    4. Return comprehensive report
    """

    # STAGE 1: INITIALIZATION
    context = AttackPathContext(
        spec_hash=hash(request.spec_text),
        spec_data=parsed_spec,
        analysis_depth=request.analysis_depth,
        context_id=str(uuid.uuid4())
    )

    # STAGE 2: VULNERABILITY SCANNING
    # Scanner Agent finds individual vulnerabilities
    scanner_result = await self.scanner_agent.execute(
        task={"type": "scan", "depth": request.analysis_depth},
        context=context
    )

    # Context now contains: individual_vulnerabilities = [...]

    # STAGE 3: THREAT MODELING
    # Threat Modeling Agent chains vulnerabilities into attack paths
    threat_result = await self.threat_modeling_agent.execute(
        task={
            "type": "model_threats",
            "max_chain_length": request.max_chain_length
        },
        context=context
    )

    # Context now contains: attack_chains = [...]

    # STAGE 4: REPORTING
    # Reporter Agent generates executive summary and recommendations
    report_result = await self.reporter_agent.execute(
        task={"type": "generate_report"},
        context=context
    )

    return report_result["attack_path_report"]
```

### Why Sequential Execution?

**Q:** Why not run agents in parallel?

**A:** Because each stage depends on the previous:
- **Threat Modeling** needs vulnerabilities from **Scanner**
- **Reporter** needs attack chains from **Threat Modeling**

**Q:** Can we optimize this?

**A:** Yes! Within each stage, we can parallelize:
- Scanner: Analyze multiple endpoints in parallel
- Threat Modeling: Build multiple chains in parallel
- Reporter: Generate multiple summaries and pick the best

---

## Key Components

### 1. AttackPathContext (MCP Context)

```python
# File: ai_service/app/schemas/attack_path_schemas.py

class AttackPathContext(BaseModel):
    """
    The 'Redux Store' for agents

    All agents read from and write to this shared context.
    """

    # Metadata
    context_id: str
    spec_hash: str
    spec_data: Dict[str, Any]

    # Analysis Configuration
    analysis_depth: str  # quick | standard | comprehensive | exhaustive
    max_chain_length: int = 5

    # Results (updated by agents)
    individual_vulnerabilities: List[SecurityIssue] = []
    attack_chains: List[AttackChain] = []

    # Progress Tracking
    current_stage: str = "initializing"  # scanning | threat_modeling | reporting
    current_activity: str = ""  # "Scanning POST /users endpoint..."
    progress_percentage: float = 0.0  # 0-100

    # Execution Metadata
    stages_completed: List[str] = []
    total_execution_time_ms: int = 0
    tokens_used: int = 0
```

**How It Works:**

```python
# Agent updates context
context.current_stage = "scanning"
context.current_activity = "Analyzing authentication endpoints..."
context.progress_percentage = 25.0

# Agent adds results
context.individual_vulnerabilities.append(SecurityIssue(...))

# Next agent reads results
vulnerabilities = context.individual_vulnerabilities
for vuln in vulnerabilities:
    # Build attack chains...
```

### 2. Scanner Agent

**Purpose:** Find individual security vulnerabilities in the OpenAPI spec

```python
# File: ai_service/app/services/agents/security_scanner_agent.py

class SecurityScannerAgent(LLMAgent):
    async def execute(self, task: Dict, context: AttackPathContext) -> Dict:
        """
        Scan OpenAPI spec for vulnerabilities

        Process:
        1. Extract all endpoints from spec
        2. For each endpoint, ask LLM: "What vulnerabilities exist?"
        3. Parse LLM response into structured SecurityIssue objects
        4. Store in context.individual_vulnerabilities
        """

        endpoints = self._extract_endpoints(context.spec_data)

        for endpoint in endpoints:
            # Build prompt for LLM
            prompt = f"""
            Analyze this API endpoint for security vulnerabilities:

            Path: {endpoint['path']}
            Method: {endpoint['method']}
            Parameters: {endpoint['parameters']}

            Find vulnerabilities in these categories:
            - Authentication/Authorization flaws
            - Input validation issues
            - Data exposure risks
            - Rate limiting gaps

            Return JSON array of vulnerabilities.
            """

            # Call LLM
            response = await self.llm_service.generate(
                model="mistral:7b-instruct",
                prompt=prompt,
                temperature=0.3  # Low temperature for factual analysis
            )

            # Parse and store
            vulnerabilities = self._parse_vulnerabilities(response)
            context.individual_vulnerabilities.extend(vulnerabilities)

        return {"success": True, "vulnerabilities_found": len(context.individual_vulnerabilities)}
```

**Key Techniques:**

1. **Low Temperature (0.3)**: For factual, consistent vulnerability detection
2. **Structured Output**: Ask LLM to return JSON for easy parsing
3. **Batch Processing**: Analyze multiple endpoints (not all at once to avoid token limits)
4. **Category-Based Scanning**: Guide LLM to check specific vulnerability types

### 3. Threat Modeling Agent

**Purpose:** Chain individual vulnerabilities into multi-step attack paths

```python
# File: ai_service/app/services/agents/threat_modeling_agent.py

class ThreatModelingAgent(LLMAgent):
    async def execute(self, task: Dict, context: AttackPathContext) -> Dict:
        """
        Build attack chains by combining vulnerabilities

        Process:
        1. Get all vulnerabilities from context
        2. For each vulnerability, ask LLM: "How can this be chained?"
        3. Build graph of vulnerability dependencies
        4. Generate multi-step attack scenarios
        """

        vulnerabilities = context.individual_vulnerabilities

        # Build attack chains using LLM
        prompt = f"""
        You are a penetration tester analyzing an API.

        Vulnerabilities found:
        {self._format_vulnerabilities(vulnerabilities)}

        Your task: Design multi-step attack chains.

        For each chain, specify:
        1. Attack Goal (what does the attacker achieve?)
        2. Steps (ordered list of vulnerabilities to exploit)
        3. Prerequisites (what must be true to start?)
        4. Impact (business consequences)
        5. Complexity (easy | medium | hard | expert)

        Think like a real attacker. How would you chain these together?

        Return JSON array of attack chains.
        """

        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            temperature=0.7,  # Higher for creative chain discovery
            max_tokens=3000
        )

        # Parse and validate chains
        chains = self._parse_attack_chains(response, vulnerabilities)
        context.attack_chains = chains

        return {"success": True, "chains_found": len(chains)}
```

**Why Higher Temperature (0.7)?**

- Vulnerability scanning: **Low temperature** (0.3) → Factual, consistent
- Attack chain discovery: **Higher temperature** (0.7) → Creative, explores multiple paths

**Graph-Based Chaining:**

```python
def _build_dependency_graph(self, vulnerabilities):
    """
    Build a graph of how vulnerabilities depend on each other

    Example:
    GET /users/{id} exposes "role" field
         ↓ (Information enables next step)
    PUT /users/{id} accepts "role" in body
         ↓ (Privilege escalation enables next step)
    GET /admin/users accesses sensitive data

    Chain: Information Disclosure → Mass Assignment → Privilege Escalation
    """
    graph = {}
    for vuln in vulnerabilities:
        # What does this vulnerability expose?
        # What vulnerabilities could use that exposure?
        dependencies = self._find_dependencies(vuln, vulnerabilities)
        graph[vuln.id] = dependencies

    return graph
```

### 4. Reporter Agent

**Purpose:** Generate executive-level security report

```python
# File: ai_service/app/services/agents/security_reporter_agent.py

class SecurityReporterAgent(LLMAgent):
    async def _generate_executive_summary(self, attack_chains, vulnerabilities, risk_level, security_score):
        """
        Generate professional security report

        Key: Explain HOW attack chains work, not just WHAT they are
        """

        # Build detailed context with step-by-step attack flows
        chains_detail = []
        for chain in attack_chains[:3]:  # Top 3 chains
            steps_text = []
            for step_num, step in enumerate(chain.steps, 1):
                steps_text.append(f"Step {step_num}: {step.action} - {step.description}")

            chain_detail = f"""
            Attack Chain: {chain.name}
            Goal: {chain.attack_goal}
            Steps:
            {chr(10).join(steps_text)}
            Impact: {chain.business_impact}
            """
            chains_detail.append(chain_detail)

        # Ask LLM to write like a security consultant
        prompt = f"""
        You are a Senior Security Consultant writing an executive summary.

        Analysis Results:
        - Risk Level: {risk_level}
        - Security Score: {security_score}/100
        - Attack Chains: {len(attack_chains)}

        Detailed Attack Chains:
        {chr(10).join(chains_detail)}

        Write a professional 3-4 paragraph summary that:
        1. States the security verdict upfront
        2. Explains the MOST CRITICAL attack chain step-by-step
        3. Translates technical findings into business impact
        4. Provides clear recommendations

        Write like a penetration tester explaining to a CEO exactly
        HOW their API would be compromised.
        """

        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            temperature=0.7,  # Natural, professional language
            max_tokens=1200
        )

        return response["response"]
```

---

## MCP Context System

### Why MCP?

**Problem:** AI agents need to coordinate and share state

**Traditional Approach:**
```python
# ❌ BAD: Agents pass results manually
scanner_result = scanner.scan(spec)
threat_result = threat_modeling.analyze(scanner_result)
report = reporter.generate(threat_result)
```

**Issues:**
- No progress tracking
- Hard to debug (what is each agent doing?)
- Tight coupling (agents depend on each other's return format)
- No shared state (can't access partial results)

**MCP Approach:**
```python
# ✅ GOOD: Shared context
context = AttackPathContext(spec_data=spec)

await scanner.execute(task, context)
# context.individual_vulnerabilities is now populated

await threat_modeling.execute(task, context)
# context.attack_chains is now populated

await reporter.execute(task, context)
# context has final report

# Benefits:
# - Real-time progress: context.progress_percentage
# - Debugging: context.current_activity
# - Loose coupling: Agents only depend on context schema
# - State inspection: Can view context at any point
```

### Progress Tracking Example

```python
# In UI, you see:
"Stage: Scanning (25%)
 Activity: Analyzing POST /users endpoint..."

# How it works:
async def execute(self, task, context):
    context.current_stage = "scanning"
    context.progress_percentage = 25.0

    for idx, endpoint in enumerate(endpoints):
        context.current_activity = f"Analyzing {endpoint.method} {endpoint.path}..."
        context.progress_percentage = 25.0 + (idx / len(endpoints)) * 50.0

        # Do analysis...
```

---

## Code Walkthrough

### Example: End-to-End Flow

Let's trace a request through the entire system:

#### 1. User Clicks "Run Attack Simulation" in UI

```javascript
// ui/src/components/security/AdvancedSecurityAudit.jsx

const runAnalysis = async () => {
  setIsAnalyzing(true);

  const result = await runAttackPathSimulation(sessionId, {
    analysisDepth: 'standard',
    maxChainLength: 5
  });

  setReport(result);
  setIsAnalyzing(false);
};
```

#### 2. Frontend Calls Backend API

```javascript
// ui/src/api/attackPathService.js

export const runAttackPathSimulation = async (sessionId, options) => {
  const response = await axios.post(
    `${API_BASE_URL}/sessions/${sessionId}/analysis/attack-path-simulation`,
    null,
    {
      params: {
        analysisDepth: options.analysisDepth,
        maxChainLength: options.maxChainLength
      },
      timeout: 300000  // 5 minutes
    }
  );

  return response.data;
};
```

#### 3. Backend Proxies to AI Service

```java
// api/.../controller/AnalysisController.java

@PostMapping("/attack-path-simulation")
public Mono<ResponseEntity<Map<String, Object>>> runAttackPathSimulation(
    @PathVariable String sessionId,
    @RequestParam String analysisDepth,
    @RequestParam int maxChainLength) {

    // Get OpenAPI spec from session
    String specText = sessionService.getSpecTextForSession(sessionId);

    // Forward to AI service
    Map<String, Object> requestBody = Map.of(
        "spec_text", specText,
        "analysis_depth", analysisDepth,
        "max_chain_length", maxChainLength
    );

    return webClient.post()
        .uri("/ai/security/attack-path-simulation")
        .bodyValue(requestBody)
        .retrieve()
        .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
        .timeout(Duration.ofMinutes(5))
        .map(ResponseEntity::ok);
}
```

#### 4. AI Service Orchestrates Agents

```python
# ai_service/app/api/endpoints.py

@router.post("/ai/security/attack-path-simulation")
async def run_attack_path_simulation(request: Dict[str, Any]):
    # Parse request
    analysis_request = AttackPathAnalysisRequest(
        spec_text=request["spec_text"],
        analysis_depth=request.get("analysis_depth", "standard"),
        max_chain_length=request.get("max_chain_length", 5)
    )

    # Run orchestration
    orchestrator = AttackPathOrchestrator(llm_service)
    report = await orchestrator.run_attack_path_analysis(analysis_request)

    return report.model_dump()
```

#### 5. Orchestrator Executes Agents

```python
# ai_service/app/services/security/attack_path_orchestrator.py

async def run_attack_path_analysis(self, request):
    # Initialize context
    context = AttackPathContext(
        spec_hash=hashlib.md5(request.spec_text.encode()).hexdigest(),
        spec_data=self._parse_spec(request.spec_text),
        analysis_depth=request.analysis_depth,
        max_chain_length=request.max_chain_length
    )

    # Stage 1: Scan for vulnerabilities
    logger.info("Stage 1: Vulnerability Scanning")
    await self.scanner_agent.execute(
        task={"type": "scan", "depth": request.analysis_depth},
        context=context
    )

    # Stage 2: Build attack chains
    logger.info("Stage 2: Threat Modeling")
    await self.threat_modeling_agent.execute(
        task={"type": "model_threats", "max_chain_length": request.max_chain_length},
        context=context
    )

    # Stage 3: Generate report
    logger.info("Stage 3: Report Generation")
    result = await self.reporter_agent.execute(
        task={"type": "generate_report"},
        context=context
    )

    return result["attack_path_report"]
```

#### 6. Scanner Agent Finds Vulnerabilities

```python
# ai_service/app/services/agents/security_scanner_agent.py

async def execute(self, task, context):
    context.current_stage = "scanning"
    context.current_activity = "Extracting API endpoints..."

    # Extract endpoints
    endpoints = self._extract_endpoints(context.spec_data)

    total_endpoints = len(endpoints)
    vulnerabilities = []

    for idx, endpoint in enumerate(endpoints):
        # Update progress
        context.current_activity = f"Scanning {endpoint.method} {endpoint.path}..."
        context.progress_percentage = (idx / total_endpoints) * 30  # 0-30% for scanning

        # Ask LLM to analyze endpoint
        prompt = self._build_scan_prompt(endpoint, context.analysis_depth)
        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            temperature=0.3
        )

        # Parse LLM response
        endpoint_vulns = self._parse_vulnerabilities(response, endpoint)
        vulnerabilities.extend(endpoint_vulns)

    # Store results in context
    context.individual_vulnerabilities = vulnerabilities
    context.stages_completed.append("scanning")

    return {"success": True, "vulnerabilities_found": len(vulnerabilities)}
```

#### 7. Threat Modeling Agent Builds Chains

```python
# ai_service/app/services/agents/threat_modeling_agent.py

async def execute(self, task, context):
    context.current_stage = "threat_modeling"
    context.current_activity = "Analyzing vulnerability relationships..."
    context.progress_percentage = 40.0

    vulnerabilities = context.individual_vulnerabilities

    # Build dependency graph
    graph = self._build_dependency_graph(vulnerabilities)

    # Discover attack chains using LLM
    context.current_activity = "Discovering attack chains..."
    prompt = self._build_threat_modeling_prompt(vulnerabilities, graph, task["max_chain_length"])

    response = await self.llm_service.generate(
        model="mistral:7b-instruct",
        prompt=prompt,
        temperature=0.7,  # Higher for creative chain discovery
        max_tokens=3000
    )

    # Parse chains
    chains = self._parse_attack_chains(response, vulnerabilities)

    # Validate and score chains
    validated_chains = []
    for chain in chains:
        if self._validate_chain(chain, graph):
            chain.impact_score = self._calculate_impact_score(chain)
            validated_chains.append(chain)

    # Store in context
    context.attack_chains = validated_chains
    context.stages_completed.append("threat_modeling")
    context.progress_percentage = 70.0

    return {"success": True, "chains_found": len(validated_chains)}
```

#### 8. Reporter Agent Generates Summary

```python
# ai_service/app/services/agents/security_reporter_agent.py

async def execute(self, task, context):
    context.current_stage = "reporting"
    context.current_activity = "Generating executive summary..."
    context.progress_percentage = 80.0

    attack_chains = context.attack_chains
    vulnerabilities = context.individual_vulnerabilities

    # Categorize chains
    critical_chains = [c for c in attack_chains if c.severity == SecuritySeverity.CRITICAL]
    high_chains = [c for c in attack_chains if c.severity == SecuritySeverity.HIGH]

    # Determine risk level
    risk_level = self._determine_risk_level(len(critical_chains), len(high_chains), len(vulnerabilities))

    # Calculate security score
    security_score = self._calculate_security_score(critical_chains, high_chains, attack_chains, vulnerabilities)

    # Generate executive summary with LLM
    executive_summary = await self._generate_executive_summary(
        attack_chains, vulnerabilities, risk_level, security_score
    )

    # Create report
    report = AttackPathAnalysisReport(
        executive_summary=executive_summary,
        risk_level=risk_level,
        overall_security_score=security_score,
        critical_chains=critical_chains,
        high_priority_chains=high_chains,
        all_chains=attack_chains,
        total_chains_found=len(attack_chains),
        total_vulnerabilities=len(vulnerabilities),
        # ... more fields
    )

    context.progress_percentage = 100.0
    context.current_activity = "Analysis complete!"

    return {"success": True, "attack_path_report": report}
```

---

## Extending the System

### Adding a New Agent

Let's add a "Compliance Agent" that checks for regulatory violations:

#### Step 1: Create Agent Class

```python
# ai_service/app/services/agents/compliance_agent.py

from .base_agent import LLMAgent
from ...schemas.attack_path_schemas import AttackPathContext

class ComplianceAgent(LLMAgent):
    """
    Checks for compliance violations (GDPR, PCI-DSS, HIPAA)
    """

    def __init__(self, llm_service):
        super().__init__(
            name="ComplianceAgent",
            description="Checks for regulatory compliance violations",
            llm_service=llm_service
        )

    def _define_capabilities(self):
        return ["gdpr_check", "pci_dss_check", "hipaa_check"]

    async def execute(self, task: Dict, context: AttackPathContext) -> Dict:
        """Check for compliance violations"""

        context.current_stage = "compliance_check"
        context.current_activity = "Checking GDPR compliance..."

        spec_data = context.spec_data
        vulnerabilities = context.individual_vulnerabilities

        # Check for GDPR violations
        prompt = f"""
        You are a privacy compliance expert.

        Analyze this API for GDPR violations:

        API Spec: {spec_data}

        Known Vulnerabilities: {vulnerabilities}

        Check for:
        1. PII exposure without consent
        2. Missing data minimization
        3. Lack of data deletion endpoints
        4. Missing consent management
        5. Cross-border data transfers

        Return JSON array of compliance violations.
        """

        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            temperature=0.3
        )

        violations = self._parse_violations(response)

        # Store in context (extend schema to add compliance_violations)
        context.compliance_violations = violations

        return {"success": True, "violations_found": len(violations)}

    def can_handle_task(self, task_type: str) -> bool:
        return task_type in ["compliance_check", "gdpr_check"]
```

#### Step 2: Update Context Schema

```python
# ai_service/app/schemas/attack_path_schemas.py

class AttackPathContext(BaseModel):
    # ... existing fields ...

    # Add new field for compliance violations
    compliance_violations: List[ComplianceViolation] = []
```

#### Step 3: Add to Orchestrator

```python
# ai_service/app/services/security/attack_path_orchestrator.py

class AttackPathOrchestrator:
    def __init__(self, llm_service):
        self.scanner_agent = SecurityScannerAgent(llm_service)
        self.threat_modeling_agent = ThreatModelingAgent(llm_service)
        self.reporter_agent = SecurityReporterAgent(llm_service)

        # Add new agent
        self.compliance_agent = ComplianceAgent(llm_service)

    async def run_attack_path_analysis(self, request):
        # ... existing stages ...

        # Add new stage after threat modeling
        logger.info("Stage 3: Compliance Check")
        await self.compliance_agent.execute(
            task={"type": "compliance_check"},
            context=context
        )

        # ... continue with reporting ...
```

### Adding a New Analysis Depth

Currently: `quick`, `standard`, `comprehensive`, `exhaustive`

Let's add `lightning` (< 10 seconds):

```python
# ai_service/app/services/agents/security_scanner_agent.py

def _get_endpoints_to_scan(self, all_endpoints, depth):
    """Select which endpoints to scan based on depth"""

    if depth == "lightning":
        # Only scan authentication endpoints (fastest)
        return [e for e in all_endpoints if "auth" in e.path.lower()]

    elif depth == "quick":
        # Sample 25% of endpoints
        return random.sample(all_endpoints, len(all_endpoints) // 4)

    elif depth == "standard":
        # Scan high-risk endpoints (auth, admin, data)
        priority_endpoints = [e for e in all_endpoints if self._is_high_risk(e)]
        return priority_endpoints

    elif depth == "comprehensive":
        # Scan all endpoints
        return all_endpoints

    elif depth == "exhaustive":
        # Scan all endpoints + parameter permutations
        return self._expand_with_permutations(all_endpoints)
```

---

## Debugging & Troubleshooting

### Common Issues

#### 1. LLM Returns Invalid JSON

**Problem:** LLM returns markdown-formatted JSON instead of raw JSON

```
LLM Output:
```json
{"vulnerabilities": [...]}
```
```

**Solution:** Post-process LLM response

```python
def _clean_llm_json_response(self, response: str) -> str:
    """Remove markdown formatting from LLM response"""

    # Remove markdown code blocks
    response = re.sub(r'```json\s*', '', response)
    response = re.sub(r'```\s*', '', response)

    # Find JSON object
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        return json_match.group(0)

    # Find JSON array
    array_match = re.search(r'\[.*\]', response, re.DOTALL)
    if array_match:
        return array_match.group(0)

    return response
```

#### 2. Token Limit Exceeded

**Problem:** Large OpenAPI specs exceed LLM context window

**Solution:** Chunk the spec

```python
async def _scan_in_batches(self, endpoints, batch_size=10):
    """Scan endpoints in batches to avoid token limits"""

    all_vulnerabilities = []

    for i in range(0, len(endpoints), batch_size):
        batch = endpoints[i:i+batch_size]

        # Scan this batch
        prompt = self._build_batch_scan_prompt(batch)
        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            max_tokens=2000
        )

        batch_vulns = self._parse_vulnerabilities(response)
        all_vulnerabilities.extend(batch_vulns)

    return all_vulnerabilities
```

#### 3. Agents Taking Too Long

**Problem:** Analysis times out after 5 minutes

**Solution 1:** Adjust depth dynamically

```python
def _adjust_depth_for_spec_size(self, spec_size: int, requested_depth: str) -> str:
    """Downgrade depth for large specs to meet timeout"""

    if spec_size > 1000:  # > 1000 endpoints
        if requested_depth == "exhaustive":
            logger.warning("Downgrading from exhaustive to comprehensive for large spec")
            return "comprehensive"

    if spec_size > 500:
        if requested_depth == "comprehensive":
            return "standard"

    return requested_depth
```

**Solution 2:** Add progress checkpoints

```python
async def execute(self, task, context):
    # Save progress every N endpoints
    CHECKPOINT_INTERVAL = 50

    for idx, endpoint in enumerate(endpoints):
        # Do analysis...

        if idx % CHECKPOINT_INTERVAL == 0:
            # Save intermediate results
            await self._save_checkpoint(context)
```

### Debugging Tips

#### 1. Enable Verbose Logging

```python
# ai_service/app/core/config.py

LOGGING_LEVEL = "DEBUG"  # Set to DEBUG for detailed logs

# In your agent:
logger.debug(f"Prompt sent to LLM: {prompt}")
logger.debug(f"LLM response: {response}")
logger.debug(f"Parsed vulnerabilities: {vulnerabilities}")
```

#### 2. Inspect MCP Context

```python
# Add a debug endpoint to view context
@router.get("/debug/context/{context_id}")
async def get_context_state(context_id: str):
    """Debug endpoint to view context state"""

    # Retrieve context from cache/database
    context = context_cache.get(context_id)

    return {
        "stage": context.current_stage,
        "progress": context.progress_percentage,
        "activity": context.current_activity,
        "vulnerabilities_found": len(context.individual_vulnerabilities),
        "chains_found": len(context.attack_chains),
        "tokens_used": context.tokens_used
    }
```

#### 3. Mock LLM for Testing

```python
# tests/test_scanner_agent.py

class MockLLMService:
    async def generate(self, model, prompt, **kwargs):
        """Return mock vulnerabilities for testing"""
        return {
            "response": json.dumps({
                "vulnerabilities": [
                    {
                        "type": "authentication",
                        "severity": "HIGH",
                        "description": "Missing authentication on POST /users",
                        "endpoint": "/users",
                        "method": "POST"
                    }
                ]
            }),
            "tokens_used": 100
        }

# Use mock in tests
async def test_scanner_agent():
    mock_llm = MockLLMService()
    scanner = SecurityScannerAgent(mock_llm)

    context = AttackPathContext(spec_data=sample_spec)
    result = await scanner.execute({"type": "scan"}, context)

    assert result["success"] == True
    assert len(context.individual_vulnerabilities) > 0
```

---

## Performance Optimization

### 1. Parallel Endpoint Scanning

```python
import asyncio

async def _scan_endpoints_parallel(self, endpoints, context):
    """Scan multiple endpoints in parallel"""

    # Create tasks for each endpoint
    tasks = [
        self._scan_single_endpoint(endpoint, context)
        for endpoint in endpoints
    ]

    # Run in parallel (limit concurrency to avoid overwhelming LLM)
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent requests

    async def scan_with_limit(endpoint, ctx):
        async with semaphore:
            return await self._scan_single_endpoint(endpoint, ctx)

    results = await asyncio.gather(*[
        scan_with_limit(ep, context) for ep in endpoints
    ])

    # Flatten results
    all_vulnerabilities = []
    for result in results:
        all_vulnerabilities.extend(result)

    return all_vulnerabilities
```

### 2. Caching LLM Responses

```python
from functools import lru_cache
import hashlib

class CachedLLMService:
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.cache = {}

    async def generate(self, model, prompt, **kwargs):
        # Create cache key from prompt
        cache_key = hashlib.md5(prompt.encode()).hexdigest()

        # Check cache
        if cache_key in self.cache:
            logger.debug(f"Cache hit for prompt: {prompt[:50]}...")
            return self.cache[cache_key]

        # Call actual LLM
        response = await self.llm_service.generate(model, prompt, **kwargs)

        # Cache response
        self.cache[cache_key] = response

        return response
```

### 3. Smart Batching

```python
def _create_optimal_batches(self, endpoints, max_tokens_per_batch=1500):
    """
    Create batches that maximize token usage without exceeding limits

    Each endpoint has a different token cost based on its complexity.
    """

    batches = []
    current_batch = []
    current_tokens = 0

    for endpoint in endpoints:
        # Estimate tokens for this endpoint
        endpoint_tokens = self._estimate_tokens(endpoint)

        if current_tokens + endpoint_tokens > max_tokens_per_batch:
            # Start new batch
            batches.append(current_batch)
            current_batch = [endpoint]
            current_tokens = endpoint_tokens
        else:
            # Add to current batch
            current_batch.append(endpoint)
            current_tokens += endpoint_tokens

    # Add final batch
    if current_batch:
        batches.append(current_batch)

    return batches
```

---

## Best Practices

### 1. Prompt Engineering

**Bad Prompt:**
```python
prompt = "Find vulnerabilities in this API"
```

**Good Prompt:**
```python
prompt = f"""
You are a security expert analyzing an API endpoint.

Endpoint Details:
- Path: {endpoint.path}
- Method: {endpoint.method}
- Parameters: {endpoint.parameters}
- Response Schema: {endpoint.response_schema}

Task: Identify security vulnerabilities in these categories:
1. Authentication/Authorization
2. Input Validation
3. Data Exposure
4. Rate Limiting

For each vulnerability found, provide:
- Type: (authentication | authorization | input_validation | data_exposure | rate_limiting)
- Severity: (LOW | MEDIUM | HIGH | CRITICAL)
- Description: Clear explanation of the issue
- Recommendation: How to fix it

Return ONLY valid JSON array. No markdown, no explanations:
[
  {{
    "type": "authentication",
    "severity": "HIGH",
    "description": "...",
    "recommendation": "..."
  }}
]
"""
```

**Why?**
- **Context**: Provide all relevant information
- **Structure**: Clear task and output format
- **Examples**: Show desired output format
- **Constraints**: "Return ONLY valid JSON" prevents markdown

### 2. Error Handling

```python
async def execute(self, task, context):
    """Execute with robust error handling"""

    try:
        # Main logic
        result = await self._do_analysis(task, context)
        return {"success": True, "result": result}

    except json.JSONDecodeError as e:
        # LLM returned invalid JSON
        logger.error(f"Failed to parse LLM response: {e}")
        return {
            "success": False,
            "error": "Invalid LLM response format",
            "fallback_result": self._get_fallback_result(context)
        }

    except asyncio.TimeoutError:
        # LLM took too long
        logger.error("LLM request timed out")
        return {
            "success": False,
            "error": "Analysis timed out",
            "partial_result": self._get_partial_result(context)
        }

    except Exception as e:
        # Unknown error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
```

### 3. Testing Strategies

```python
# Unit test: Test agent logic without LLM
def test_vulnerability_parsing():
    agent = SecurityScannerAgent(None)  # No LLM needed

    mock_response = {
        "response": '{"vulnerabilities": [{"type": "auth", "severity": "HIGH"}]}'
    }

    vulnerabilities = agent._parse_vulnerabilities(mock_response, endpoint)

    assert len(vulnerabilities) == 1
    assert vulnerabilities[0].severity == SecuritySeverity.HIGH

# Integration test: Test with real LLM
async def test_scanner_agent_integration():
    llm_service = OllamaService()
    agent = SecurityScannerAgent(llm_service)

    context = AttackPathContext(spec_data=load_sample_spec())
    result = await agent.execute({"type": "scan"}, context)

    assert result["success"] == True
    assert len(context.individual_vulnerabilities) > 0

# End-to-end test: Test full workflow
async def test_attack_path_analysis_e2e():
    orchestrator = AttackPathOrchestrator(llm_service)

    request = AttackPathAnalysisRequest(
        spec_text=load_sample_spec(),
        analysis_depth="quick"
    )

    report = await orchestrator.run_attack_path_analysis(request)

    assert report.risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert len(report.all_chains) > 0
    assert report.executive_summary != ""
```

---

## Conclusion

The MCP-based agentic system provides a powerful, extensible framework for complex AI-powered security analysis. Key takeaways:

1. **Agent Pattern**: Specialized agents with single responsibilities
2. **MCP Context**: Shared state management for coordination
3. **Sequential Workflow**: Stages build on each other's results
4. **LLM Integration**: Each agent uses LLM independently with custom prompts
5. **Progress Tracking**: Real-time visibility into what AI is doing
6. **Extensibility**: Easy to add new agents, stages, or analysis types

By understanding this architecture, you can:
- Debug issues by inspecting MCP context
- Optimize performance by parallelizing agent operations
- Extend functionality by adding new agents
- Improve results by refining prompts
- Monitor costs by tracking token usage per agent

---

## Further Reading

- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io)
- **Agent Patterns**: "Building LLM Agents" - OpenAI Cookbook
- **Prompt Engineering**: "Prompt Engineering Guide" - DAIR.AI
- **Security Testing**: OWASP API Security Top 10

## Questions?

If you have questions about this system, check:
1. Code comments in `ai_service/app/services/agents/`
2. Logs at `DEBUG` level for detailed execution traces
3. Context state via debug endpoint `/debug/context/{id}`
4. Create a GitHub issue for architecture questions
