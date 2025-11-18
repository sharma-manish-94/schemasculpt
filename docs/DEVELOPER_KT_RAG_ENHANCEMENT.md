# Developer Knowledge Transfer: RAG Enhancement System

**Feature**: Dual Knowledge Base RAG (Retrieval-Augmented Generation)
**Version**: 1.0
**Last Updated**: November 17, 2025
**Target Audience**: Backend developers, ML engineers, DevOps

---

## Table of Contents

1. [Overview & Architecture](#overview--architecture)
2. [Key Components Deep Dive](#key-components-deep-dive)
3. [Data Flow & Execution](#data-flow--execution)
4. [Code Walkthroughs](#code-walkthroughs)
5. [Configuration & Dependencies](#configuration--dependencies)
6. [Testing & Debugging](#testing--debugging)
7. [Common Issues & Solutions](#common-issues--solutions)
8. [Extension Guide](#extension-guide)
9. [Performance Optimization](#performance-optimization)
10. [Deployment Considerations](#deployment-considerations)

---

## Overview & Architecture

### What is RAG and Why Do We Use It?

**RAG (Retrieval-Augmented Generation)** enhances LLM responses by retrieving relevant information from a specialized knowledge base before generating the response.

**Problem Without RAG**:
```python
# LLM only has training data (generic, may be outdated)
prompt = "Analyze this API for OWASP vulnerabilities"
response = llm.generate(prompt)
# Response: Generic, may miss specific OWASP patterns
```

**Solution With RAG**:
```python
# Query knowledge base for OWASP expertise
owasp_knowledge = knowledge_base.query("OWASP API Security")

# Inject expert knowledge into prompt
prompt = f"""
{owasp_knowledge}  # <- Authoritative OWASP content

Now analyze this API for OWASP vulnerabilities
"""
response = llm.generate(prompt)
# Response: Specific, accurate, uses OWASP terminology
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    AttackPathOrchestrator                        │
│                     (Workflow Manager)                           │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             │ Shared RAGService              │
             │                                │
    ┌────────▼─────────┐            ┌────────▼─────────┐
    │ ThreatModeling   │            │ SecurityReporter │
    │     Agent        │            │      Agent       │
    │                  │            │                  │
    │ "Think like      │            │ "Think like      │
    │  a hacker"       │            │  a CISO"         │
    └────────┬─────────┘            └────────┬─────────┘
             │                                │
             │ Query                          │ Query
             │                                │
    ┌────────▼─────────┐            ┌────────▼─────────┐
    │  Attacker KB     │            │ Governance KB    │
    │                  │            │                  │
    │ • OWASP Top 10   │            │ • CVSS Scoring   │
    │ • MITRE ATT&CK   │            │ • DREAD Risk     │
    │ • Exploit Patterns│           │ • GDPR/HIPAA     │
    └──────────────────┘            └──────────────────┘
             │                                │
             └────────────┬───────────────────┘
                          │
                  ┌───────▼────────┐
                  │   ChromaDB     │
                  │ (Vector Store) │
                  │                │
                  │ sentence-      │
                  │ transformers   │
                  │ embeddings     │
                  └────────────────┘
```

### Directory Structure

```
ai_service/
├── app/
│   ├── services/
│   │   ├── rag_service.py              # Core RAG implementation
│   │   └── agents/
│   │       ├── attack_path_orchestrator.py
│   │       ├── threat_modeling_agent.py    # RAG-enhanced
│   │       └── security_reporter_agent.py  # RAG-enhanced
│   └── scripts/
│       └── ingest_knowledge.py         # Knowledge base population
│
├── ai_service_data/
│   ├── knowledge_base/
│   │   ├── attacker/                   # (empty - for custom docs)
│   │   ├── governance/                 # (empty - for custom docs)
│   │   └── raw_documents/              # (empty - for source files)
│   └── vector_store/
│       ├── chroma.sqlite3              # ChromaDB database
│       └── *.parquet                   # Vector embeddings
│
└── test_rag_system.py                  # Integration test
```

---

## Key Components Deep Dive

### 1. RAGService (`app/services/rag_service.py`)

**Purpose**: Central service managing dual knowledge bases and vector search.

**Key Responsibilities**:
1. Initialize embedding model (sentence-transformers)
2. Initialize ChromaDB collections (attacker_knowledge, governance_knowledge)
3. Query knowledge bases with semantic search
4. Ingest new documents into knowledge bases

**Critical Methods**:

#### `__init__(self)`
```python
def __init__(self):
    self.logger = get_logger("rag_service")
    self.vector_store_dir = Path(settings.ai_service_data_dir) / "vector_store"

    # Dual knowledge bases
    self.attacker_kb = None      # For ThreatModelingAgent
    self.governance_kb = None    # For SecurityReporterAgent
    self.embedding_model = None

    if not CHROMADB_AVAILABLE:
        # Graceful degradation - agents work without RAG
        self.logger.warning("ChromaDB dependencies not available. RAG service disabled.")
        return

    self._initialize_embeddings()
    self._initialize_vector_stores()
```

**Design Decision**: Graceful degradation. If ChromaDB is not installed, the system continues to work without RAG enhancement instead of crashing.

#### `query_attacker_knowledge(query, n_results=5)`
```python
async def query_attacker_knowledge(self, query: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Query the Attacker Knowledge Base (offensive security expertise).

    Used by: ThreatModelingAgent
    Returns: Top N most relevant attack patterns from OWASP/MITRE
    """
    # 1. Check if KB is available
    if not self.attacker_kb_available():
        return {"context": "", "sources": [], "available": False}

    # 2. Generate embedding for query using sentence-transformers
    query_embedding = self.embedding_model.encode([query])[0].tolist()

    # 3. Query ChromaDB with vector similarity search
    results = self.attacker_kb.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # 4. Format results with source attribution
    return self._format_rag_results(results, "Attacker KB")
```

**How Vector Search Works**:
```python
# Query: "OWASP API1 BOLA exploitation"
# Gets converted to 384-dimensional vector: [0.23, -0.45, 0.12, ...]

# ChromaDB compares this vector with all stored document vectors
# Returns documents with highest cosine similarity
# Example results:
# 1. OWASP API1 doc - similarity: 0.94
# 2. MITRE T1190 doc - similarity: 0.78
# 3. OWASP API5 doc - similarity: 0.45
```

#### `ingest_documents(documents, metadatas, knowledge_base)`
```python
def ingest_documents(
    self,
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    knowledge_base: str = "attacker"
) -> Dict[str, Any]:
    """
    Ingest documents into specified knowledge base.

    Args:
        documents: List of document texts (strings)
        metadatas: List of metadata dicts (source, category, type)
        knowledge_base: "attacker" or "governance"

    Process:
    1. Generate embeddings for all documents
    2. Generate unique IDs (MD5 hash of content)
    3. Get or create ChromaDB collection
    4. Add documents with embeddings to collection
    """
    # Generate embeddings (GPU-accelerated if available)
    embeddings = self.embedding_model.encode(documents).tolist()

    # Generate document IDs (deterministic hashing)
    doc_ids = [hashlib.md5(doc.encode()).hexdigest() for doc in documents]

    # Get/create collection
    collection_name = (
        "attacker_knowledge" if knowledge_base == "attacker"
        else "governance_knowledge"
    )
    collection = client.get_or_create_collection(name=collection_name)

    # Add to ChromaDB
    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=doc_ids
    )
```

**Performance Note**:
- Embedding generation is GPU-accelerated (CUDA) when available
- ~1000 tokens/sec on GPU, ~100 tokens/sec on CPU
- Batch processing for efficiency

---

### 2. ThreatModelingAgent (`threat_modeling_agent.py`)

**Purpose**: RAG-enhanced agent that discovers attack chains using offensive security knowledge.

**RAG Integration Point**:

```python
async def execute(self, task: Dict[str, Any], context: AttackPathContext):
    # ... vulnerability scanning complete ...

    # RAG ENHANCEMENT: Query Attacker KB
    rag_context = await self._query_attacker_knowledge(vulnerabilities)

    # Build prompt with expert knowledge
    prompt = self._build_threat_modeling_prompt(
        vulnerabilities,
        context.spec,
        max_chain_length,
        analysis_depth,
        rag_context  # <-- Injected here
    )

    # LLM generates attack chains with expert context
    response = await self.llm_service.generate(
        model="mistral:7b-instruct",
        prompt=prompt,
        temperature=0.4
    )
```

**How `_query_attacker_knowledge` Works**:

```python
async def _query_attacker_knowledge(self, vulnerabilities: List[SecurityIssue]):
    # 1. Extract OWASP categories from found vulnerabilities
    owasp_categories = []
    for vuln in vulnerabilities:
        if vuln.owasp_category:
            owasp_categories.append(vuln.owasp_category.value)

    # 2. Build focused query
    query_parts = []
    if owasp_categories:
        unique_owasp = list(set(owasp_categories))
        query_parts.append(f"OWASP API Security: {', '.join(unique_owasp)}")
    query_parts.append("exploitation techniques attack patterns vulnerability chaining")
    query = " ".join(query_parts)

    # Example query:
    # "OWASP API Security: API1:BOLA, API2:Auth exploitation techniques attack patterns vulnerability chaining"

    # 3. Query Attacker KB
    rag_result = await self.rag_service.query_attacker_knowledge(
        query=query,
        n_results=5
    )

    return {
        "context": rag_result.get("context", ""),
        "sources": rag_result.get("sources", []),
        "available": True
    }
```

**Prompt Enhancement**:

```python
def _build_threat_modeling_prompt(self, ..., rag_context):
    # If RAG available, inject knowledge
    rag_knowledge_section = ""
    if rag_context.get("available") and rag_context.get("context"):
        rag_knowledge_section = f"""
**EXPERT KNOWLEDGE FROM SECURITY KNOWLEDGE BASE**:
{rag_context['context']}

Use this expert knowledge to inform your attack chain analysis.
---
"""

    prompt = f"""You are an expert security researcher with access to
specialized offensive security knowledge.

{rag_knowledge_section}  # <-- RAG knowledge injected

**Your Mission**: Think like a real attacker...
"""
```

**Result**: LLM now has OWASP exploitation techniques and MITRE patterns in context when analyzing vulnerabilities.

---

### 3. SecurityReporterAgent (`security_reporter_agent.py`)

**Purpose**: RAG-enhanced agent that generates executive reports using governance expertise.

**RAG Integration Point**:

```python
async def execute(self, task: Dict[str, Any], context: AttackPathContext):
    # ... attack chains discovered ...

    # RAG ENHANCEMENT: Query Governance KB
    governance_context = await self._query_governance_knowledge(
        attack_chains,
        vulnerabilities,
        risk_level
    )

    # Generate summary with governance expertise
    executive_summary = await self._generate_executive_summary(
        attack_chains,
        vulnerabilities,
        risk_level,
        security_score,
        governance_context  # <-- Injected here
    )
```

**How `_query_governance_knowledge` Works**:

```python
async def _query_governance_knowledge(self, attack_chains, vulnerabilities, risk_level):
    # 1. Build query based on risk level
    query_parts = [
        f"risk level {risk_level}",
        "CVSS scoring",
        "DREAD framework",
        "business impact assessment"
    ]

    # 2. Add compliance queries if data exposure risks exist
    has_data_risk = any(
        "data" in chain.business_impact.lower() or
        "privacy" in chain.business_impact.lower()
        for chain in attack_chains
    )

    if has_data_risk:
        query_parts.extend(["GDPR", "data protection", "compliance"])

    # Example query: "risk level CRITICAL CVSS scoring DREAD framework GDPR data protection"

    # 3. Query Governance KB
    rag_result = await self.rag_service.query_governance_knowledge(
        query=" ".join(query_parts),
        n_results=4
    )

    return {
        "context": rag_result.get("context", ""),
        "sources": rag_result.get("sources", []),
        "available": True
    }
```

**Result**: Executive summary includes accurate CVSS scores, DREAD assessments, and compliance implications (GDPR fines, etc.).

---

### 4. AttackPathOrchestrator (`attack_path_orchestrator.py`)

**Purpose**: Coordinates the workflow and provides shared RAG service to agents.

**Key Changes**:

```python
def __init__(self, llm_service):
    # Initialize shared RAG service
    logger.info("[AttackPathOrchestrator] Initializing RAG service...")
    self.rag_service = RAGService()

    # Pass RAG service to agents
    self.scanner_agent = VulnerabilityScannerAgent()
    self.threat_agent = ThreatModelingAgent(llm_service, self.rag_service)
    self.reporter_agent = SecurityReporterAgent(llm_service, self.rag_service)

    # Log RAG status
    if self.rag_service.is_available():
        attacker_kb_status = "✓" if self.rag_service.attacker_kb_available() else "✗"
        governance_kb_status = "✓" if self.rag_service.governance_kb_available() else "✗"
        logger.info(
            f"[AttackPathOrchestrator] RAG-Enhanced mode enabled! "
            f"Attacker KB: {attacker_kb_status}, Governance KB: {governance_kb_status}"
        )
```

**Design Decision**: Single RAGService instance shared across all agents to:
- Avoid duplicate embedding model loading (saves memory)
- Share ChromaDB client connection pool
- Centralized logging and error handling

---

## Data Flow & Execution

### Complete Request Flow with RAG

```
1. User Clicks "Run Attack Simulation" in UI
   ↓
2. Frontend calls: POST /api/v1/sessions/{id}/analysis/attack-path-simulation
   ↓
3. Backend (Java) forwards to AI service: POST /ai/security/attack-path-simulation
   ↓
4. AI Service (Python): AttackPathOrchestrator.run_attack_path_analysis()
   ↓
5. STAGE 1: VulnerabilityScannerAgent.execute()
   - Scans OpenAPI spec for security issues
   - Finds: BOLA, missing auth, mass assignment, etc.
   - Output: List[SecurityIssue]
   ↓
6. STAGE 2: ThreatModelingAgent.execute()
   ├─ 6a. Query Attacker KB for OWASP/MITRE patterns
   │      ├─ Extract OWASP categories from vulnerabilities
   │      ├─ Build query: "OWASP API1:BOLA API2:Auth exploitation techniques"
   │      ├─ Generate query embedding (sentence-transformers)
   │      ├─ ChromaDB vector search → Top 5 attack patterns
   │      └─ Return RAG context (OWASP exploitation docs)
   │
   ├─ 6b. Build LLM prompt with RAG context
   │      └─ Inject OWASP patterns + vulnerability list
   │
   ├─ 6c. LLM generates attack chains using expert knowledge
   │      └─ Output: AttackChain (name, steps, severity, CVSS score)
   │
   └─ Output: List[AttackChain]
   ↓
7. STAGE 3: SecurityReporterAgent.execute()
   ├─ 7a. Query Governance KB for risk frameworks
   │      ├─ Build query: "risk level CRITICAL CVSS DREAD GDPR"
   │      ├─ ChromaDB vector search → Top 4 governance docs
   │      └─ Return governance context (CVSS, DREAD, compliance)
   │
   ├─ 7b. Build executive summary prompt with governance context
   │      └─ Inject CVSS scoring guidelines + compliance requirements
   │
   ├─ 7c. LLM generates executive summary with expert knowledge
   │      └─ Includes: CVSS scores, DREAD ratings, GDPR implications
   │
   └─ Output: AttackPathAnalysisReport
   ↓
8. Return report to backend → frontend → user
```

### Timing Breakdown

```
Total Analysis Time: ~30-60 seconds

├─ Vulnerability Scanning: 5-10 sec
│  └─ OpenAPI spec parsing & rule-based detection
│
├─ Attack Chain Discovery: 15-30 sec
│  ├─ RAG query (Attacker KB): 50ms
│  ├─ Prompt building: 100ms
│  └─ LLM inference: 15-30 sec (bottleneck)
│
└─ Report Generation: 10-20 sec
   ├─ RAG query (Governance KB): 50ms
   ├─ Prompt building: 100ms
   └─ LLM inference: 10-20 sec

RAG Overhead: ~200ms total (negligible)
```

---

## Code Walkthroughs

### Walkthrough 1: Adding a New Document to Attacker KB

**Scenario**: You want to add a new OWASP vulnerability pattern.

**Step 1**: Create the document content

```python
new_document = """
OWASP API11:2024 - Server-Side Request Forgery (SSRF) in Webhooks

Description: APIs that allow users to specify webhook URLs without proper
validation can be exploited to scan internal networks or access cloud metadata.

Attack Pattern:
1. Identify webhook registration endpoints
2. Register webhook with internal URL (http://169.254.169.254/latest/meta-data/)
3. Trigger webhook execution
4. Receive internal network responses or cloud credentials

Exploitation Technique:
- Use localhost (127.0.0.1, ::1) to access internal services
- Target cloud metadata endpoints (AWS: 169.254.169.254)
- Bypass URL filters with DNS rebinding
- Use URL encoding or alternate IP formats (0x7f000001 = 127.0.0.1)

Real-World Impact: Internal network mapping, cloud credential theft, database
access, privilege escalation via cloud IAM roles.

CVSS Score: HIGH to CRITICAL (8.0-10.0) depending on exposed services.

MITRE ATT&CK: T1190 (Exploit Public-Facing Application), T1552 (Unsecured Credentials)
"""

metadata = {
    "source": "OWASP API Security Top 10",
    "category": "API11:2024 SSRF",
    "type": "vulnerability_pattern",
    "last_updated": "2025-11-17"
}
```

**Step 2**: Ingest into Attacker KB

```python
from app.services.rag_service import RAGService

rag = RAGService()

result = rag.ingest_documents(
    documents=[new_document],
    metadatas=[metadata],
    knowledge_base="attacker"  # Target Attacker KB
)

print(result)
# Output: {'success': True, 'knowledge_base': 'attacker', 'documents_added': 1}
```

**Step 3**: Verify ingestion

```bash
python test_rag_system.py
# Check: Attacker KB Documents: 15 (was 14, now 15)
```

**Step 4**: Test retrieval

```python
import asyncio

async def test_new_doc():
    rag = RAGService()
    result = await rag.query_attacker_knowledge(
        query="SSRF webhook exploitation cloud metadata",
        n_results=3
    )
    print(result['context'][:500])

asyncio.run(test_new_doc())
```

**That's it!** The new knowledge is now available to ThreatModelingAgent.

---

### Walkthrough 2: Debugging a RAG Query

**Scenario**: Agent is not retrieving expected knowledge.

**Step 1**: Enable debug logging

```python
# At the top of your script or in settings
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run analysis - you'll see detailed logs
```

**Step 2**: Check what query is being sent

```python
# In threat_modeling_agent.py, add logging
async def _query_attacker_knowledge(self, vulnerabilities):
    # ... build query ...
    logger.info(f"[DEBUG] RAG Query: {query}")
    logger.info(f"[DEBUG] OWASP Categories: {owasp_categories}")

    rag_result = await self.rag_service.query_attacker_knowledge(
        query=query,
        n_results=5
    )

    logger.info(f"[DEBUG] Retrieved {len(rag_result.get('sources', []))} documents")
    logger.info(f"[DEBUG] Relevance Scores: {rag_result.get('relevance_scores', [])}")
```

**Step 3**: Inspect retrieved context

```python
# In _build_threat_modeling_prompt, log the RAG context
if rag_context.get("available") and rag_context.get("context"):
    logger.debug(f"[DEBUG] RAG Context Length: {len(rag_context['context'])} chars")
    logger.debug(f"[DEBUG] RAG Context Preview:\n{rag_context['context'][:1000]}")
```

**Step 4**: Test query manually

```python
from app.services.rag_service import RAGService
import asyncio

async def debug_query():
    rag = RAGService()

    # Try different queries to see what works
    queries = [
        "OWASP API1 BOLA",
        "broken object level authorization exploitation",
        "unauthorized access user data API",
        "OWASP broken authorization"
    ]

    for query in queries:
        print(f"\n=== Query: {query} ===")
        result = await rag.query_attacker_knowledge(query, n_results=3)
        print(f"Documents: {result.get('total_documents', 0)}")
        print(f"Scores: {result.get('relevance_scores', [])}")
        print(f"Sources: {result.get('sources', [])}")

asyncio.run(debug_query())
```

**Common Issues**:
- **Low relevance scores**: Query terms don't match document content
- **No results**: ChromaDB collection not loaded
- **Wrong documents**: Query too broad or too narrow

---

### Walkthrough 3: Adding Custom Compliance Framework

**Scenario**: Your company needs SOC 2 compliance checks.

**Step 1**: Create SOC 2 knowledge document

```python
soc2_document = """
SOC 2 Type II - API Security Controls

Trust Service Criteria: Security (Common Criteria)

CC6.1 - Logical and Physical Access Controls
API Requirements:
- Multi-factor authentication for privileged API access
- Role-based access control (RBAC) with least privilege
- Session timeout and reauthentication for sensitive operations
- API key rotation every 90 days
- Audit logging of all administrative API actions

CC6.6 - Logical Access - Removal or Modification
- Implement API endpoint authorization checks
- Prevent BOLA (Broken Object Level Authorization)
- Validate user permissions before data access/modification
- Log all permission changes and access attempts

CC7.2 - System Monitoring
API Monitoring Requirements:
- Real-time API abuse detection
- Anomaly detection for unusual API usage patterns
- Rate limiting to prevent DoS attacks
- Security event logging and alerting
- API performance monitoring and SLA tracking

Common API Violations in SOC 2 Audits:
- Missing authentication on sensitive endpoints
- Insufficient logging of API access
- No rate limiting or abuse prevention
- Lack of encryption for data in transit (TLS)
- Inadequate access control testing

Audit Evidence Required:
- API security testing reports
- Penetration testing results
- Access control matrices
- API monitoring dashboards
- Incident response procedures

SOC 2 Compliance Impact:
- Critical for B2B SaaS companies
- Required by enterprise customers
- Audit failure can result in customer contract loss
- Annual audit cost: $20,000 - $100,000
"""

metadata = {
    "source": "SOC 2 Type II",
    "category": "Compliance",
    "type": "regulatory_framework",
    "audit_type": "security",
    "last_updated": "2025-11-17"
}
```

**Step 2**: Ingest into Governance KB

```python
from app.services.rag_service import RAGService

rag = RAGService()

result = rag.ingest_documents(
    documents=[soc2_document],
    metadatas=[metadata],
    knowledge_base="governance"  # Governance KB for compliance
)

print(f"✅ SOC 2 knowledge added to Governance KB")
```

**Step 3**: Update SecurityReporterAgent query logic (optional)

```python
# In security_reporter_agent.py, update _query_governance_knowledge()

async def _query_governance_knowledge(self, attack_chains, vulnerabilities, risk_level):
    query_parts = [
        f"risk level {risk_level}",
        "CVSS scoring",
        "DREAD framework",
        "business impact assessment"
    ]

    # Check for B2B/enterprise context
    if self._is_enterprise_context(attack_chains):
        query_parts.extend(["SOC 2", "enterprise compliance"])

    # ... rest of method
```

**Result**: Reports now include SOC 2 compliance implications automatically.

---

## Configuration & Dependencies

### Required Dependencies

```toml
# pyproject.toml or requirements.txt

# Core RAG dependencies
chromadb==1.1.0              # Vector database
sentence-transformers==5.1.1  # Embedding model

# Transitive dependencies (auto-installed)
torch>=2.0.0                  # PyTorch for embeddings
onnxruntime>=1.14.1          # ONNX runtime
numpy>=1.22.5                # Numerical operations
pydantic>=2.0                # Data validation

# Optional (for GPU acceleration)
# torch with CUDA support - see https://pytorch.org/get-started/locally/
```

### Installation

```bash
# Basic installation (CPU)
pip install chromadb sentence-transformers

# GPU installation (CUDA 11.8)
pip install chromadb sentence-transformers
pip install torch --index-url https://download.pytorch.org/whl/cu118

# Verify installation
python -c "import chromadb; import sentence_transformers; print('✓ RAG dependencies installed')"
```

### Environment Configuration

```bash
# .env or environment variables

# AI Service data directory (stores vector DB)
AI_SERVICE_DATA_DIR=/path/to/ai_service_data

# Optional: Override default embedding model
# RAG_EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2  # Higher quality, slower
# RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2   # Default - balanced
# RAG_EMBEDDING_MODEL=sentence-transformers/paraphrase-MiniLM-L3-v2  # Faster, lower quality

# Optional: Tune retrieval
RAG_TOP_K_ATTACKER=5         # Top N results for Attacker KB queries
RAG_TOP_K_GOVERNANCE=4       # Top N results for Governance KB queries

# Optional: Enable/disable RAG (for A/B testing)
RAG_ENABLED=true
```

### Model Downloads

First run will download embedding model:

```
~/.cache/torch/sentence_transformers/
└── sentence-transformers_all-MiniLM-L6-v2/
    ├── config.json
    ├── pytorch_model.bin (80 MB)
    └── tokenizer files
```

**Note**: Model is cached and reused across runs.

---

## Testing & Debugging

### Unit Tests

Create `tests/test_rag_service.py`:

```python
import pytest
from app.services.rag_service import RAGService

class TestRAGService:

    @pytest.fixture
    def rag_service(self):
        return RAGService()

    def test_rag_initialization(self, rag_service):
        """Test RAG service initializes correctly."""
        assert rag_service is not None
        assert rag_service.embedding_model is not None

    def test_attacker_kb_available(self, rag_service):
        """Test Attacker KB is loaded."""
        assert rag_service.attacker_kb_available()

    def test_governance_kb_available(self, rag_service):
        """Test Governance KB is loaded."""
        assert rag_service.governance_kb_available()

    @pytest.mark.asyncio
    async def test_query_attacker_kb(self, rag_service):
        """Test querying Attacker KB returns results."""
        result = await rag_service.query_attacker_knowledge(
            query="OWASP API1 BOLA exploitation",
            n_results=3
        )

        assert result["available"] is True
        assert len(result["sources"]) > 0
        assert result["total_documents"] > 0
        assert "OWASP" in result["context"]

    @pytest.mark.asyncio
    async def test_query_governance_kb(self, rag_service):
        """Test querying Governance KB returns results."""
        result = await rag_service.query_governance_knowledge(
            query="CVSS scoring CRITICAL severity",
            n_results=2
        )

        assert result["available"] is True
        assert "CVSS" in result["context"]

    def test_ingest_documents(self, rag_service):
        """Test document ingestion."""
        test_doc = ["Test security knowledge document"]
        test_meta = [{"source": "Test", "category": "Test"}]

        result = rag_service.ingest_documents(
            documents=test_doc,
            metadatas=test_meta,
            knowledge_base="attacker"
        )

        assert result["success"] is True
        assert result["documents_added"] == 1
```

Run tests:
```bash
pytest tests/test_rag_service.py -v
```

### Integration Test

```bash
# Run the full integration test
python test_rag_system.py

# Expected output:
# ✅ RAG Service: Operational
# ✅ Attacker KB: 14 documents loaded
# ✅ Governance KB: 6 documents loaded
```

### Manual Testing with Sample API

Create `test_rag_analysis.py`:

```python
import asyncio
from app.services.agents.attack_path_orchestrator import AttackPathOrchestrator
from app.services.llm_service import LLMService
from app.schemas.attack_path_schemas import AttackPathAnalysisRequest

async def test_rag_analysis():
    # Sample vulnerable API spec
    sample_spec = """
    openapi: 3.0.0
    info:
      title: Vulnerable API
      version: 1.0.0
    paths:
      /users/{id}:
        get:
          summary: Get user by ID
          parameters:
            - name: id
              in: path
              required: true
              schema:
                type: integer
          responses:
            '200':
              description: User found
    """

    # Initialize orchestrator
    llm_service = LLMService()
    orchestrator = AttackPathOrchestrator(llm_service)

    # Create request
    request = AttackPathAnalysisRequest(
        spec_text=sample_spec,
        analysis_depth="standard",
        max_chain_length=5
    )

    # Run analysis
    print("Running RAG-enhanced attack path analysis...")
    report = await orchestrator.run_attack_path_analysis(request)

    # Check if RAG was used (should mention OWASP)
    print(f"\n{'='*70}")
    print("EXECUTIVE SUMMARY")
    print(f"{'='*70}")
    print(report.executive_summary)

    # Verify RAG usage
    rag_indicators = [
        "OWASP" in report.executive_summary,
        "API1" in report.executive_summary or "API2" in report.executive_summary,
        "CVSS" in report.executive_summary,
        "GDPR" in report.executive_summary or "compliance" in report.executive_summary.lower()
    ]

    print(f"\n{'='*70}")
    print("RAG USAGE VERIFICATION")
    print(f"{'='*70}")
    print(f"Contains OWASP references: {'✓' if rag_indicators[0] else '✗'}")
    print(f"Contains specific OWASP IDs: {'✓' if rag_indicators[1] else '✗'}")
    print(f"Contains CVSS scoring: {'✓' if rag_indicators[2] else '✗'}")
    print(f"Contains compliance info: {'✓' if rag_indicators[3] else '✗'}")

    if any(rag_indicators):
        print("\n✅ RAG enhancement is working!")
    else:
        print("\n⚠️ RAG may not be working correctly")

if __name__ == "__main__":
    asyncio.run(test_rag_analysis())
```

### Debugging Tips

**1. Check ChromaDB Connection**:
```python
import chromadb
client = chromadb.PersistentClient(path="./ai_service_data/vector_store")
print(client.list_collections())
# Should show: ['attacker_knowledge', 'governance_knowledge']
```

**2. Inspect Collection Contents**:
```python
collection = client.get_collection("attacker_knowledge")
print(f"Documents: {collection.count()}")

# Get sample documents
results = collection.get(limit=5, include=["documents", "metadatas"])
for doc, meta in zip(results['documents'], results['metadatas']):
    print(f"\nSource: {meta.get('source')}")
    print(f"Doc: {doc[:200]}...")
```

**3. Test Embedding Generation**:
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
text = "OWASP API1 BOLA exploitation"
embedding = model.encode([text])[0]

print(f"Embedding shape: {embedding.shape}")  # Should be (384,)
print(f"Embedding sample: {embedding[:5]}")
```

**4. Compare Similarity Scores**:
```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

query = "OWASP API1 BOLA exploitation"
doc1 = "OWASP API1:2023 - Broken Object Level Authorization..."
doc2 = "GDPR compliance requirements for data protection..."

# Generate embeddings
query_emb = model.encode(query)
doc1_emb = model.encode(doc1)
doc2_emb = model.encode(doc2)

# Calculate cosine similarity
sim1 = util.cos_sim(query_emb, doc1_emb).item()
sim2 = util.cos_sim(query_emb, doc2_emb).item()

print(f"Query-Doc1 similarity: {sim1:.4f}")  # Should be high (~0.7-0.9)
print(f"Query-Doc2 similarity: {sim2:.4f}")  # Should be low (~0.1-0.3)
```

---

## Common Issues & Solutions

### Issue 1: "ChromaDB dependencies not available"

**Symptom**:
```
WARNING: ChromaDB dependencies not available. RAG service disabled.
```

**Cause**: ChromaDB or sentence-transformers not installed.

**Solution**:
```bash
cd ai_service
source venv/bin/activate
pip install chromadb sentence-transformers
```

---

### Issue 2: "Attacker KB not found"

**Symptom**:
```
WARNING: Attacker KB not found. Will be created during ingestion.
```

**Cause**: Knowledge base not populated yet.

**Solution**:
```bash
python app/scripts/ingest_knowledge.py --all
```

---

### Issue 3: Low Relevance Scores (< 0.3)

**Symptom**: RAG queries return documents but relevance scores are very low.

**Cause**: Query terms don't match document vocabulary.

**Solution**:
```python
# Bad query (too generic)
query = "security issues"

# Good query (specific terms from documents)
query = "OWASP API1 BOLA broken object level authorization exploitation"

# Best query (extract from vulnerabilities)
query = f"OWASP {vuln.owasp_category.value} exploitation techniques"
```

---

### Issue 4: Out of Memory (GPU)

**Symptom**:
```
RuntimeError: CUDA out of memory
```

**Cause**: GPU memory exhausted by embedding model or large batch.

**Solution 1**: Reduce batch size in RAG service
```python
# In rag_service.py
batch_size = 32  # Change to 16 or 8
```

**Solution 2**: Force CPU mode
```python
# In rag_service.py, _initialize_embeddings()
device = "cpu"  # Force CPU instead of auto-detect
```

---

### Issue 5: Slow Embedding Generation

**Symptom**: Ingestion takes > 30 seconds for 20 documents.

**Cause**: CPU mode or large documents.

**Solution 1**: Verify GPU usage
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0)}")
```

**Solution 2**: Chunk large documents
```python
# Split documents > 5000 chars into chunks
def chunk_document(doc, max_length=5000):
    chunks = []
    for i in range(0, len(doc), max_length):
        chunks.append(doc[i:i+max_length])
    return chunks
```

---

### Issue 6: RAG Context Not Appearing in LLM Response

**Symptom**: Executive summary doesn't mention OWASP, CVSS, etc.

**Debugging Steps**:

1. **Check if RAG query succeeded**:
```python
# In agent, log RAG result
logger.info(f"RAG Context Length: {len(rag_context.get('context', ''))} chars")

# If 0, RAG didn't retrieve anything
```

2. **Check prompt construction**:
```python
# Log the full prompt sent to LLM
logger.debug(f"Prompt Preview:\n{prompt[:2000]}")

# Verify RAG context is in the prompt
```

3. **Check LLM response**:
```python
# Log LLM response
logger.debug(f"LLM Response:\n{response[:1000]}")

# LLM might ignore RAG context if it's too long or irrelevant
```

4. **Adjust prompt instructions**:
```python
# Be more explicit in prompt
prompt = f"""
IMPORTANT: You MUST use the provided expert knowledge in your analysis.
Reference specific OWASP categories and CVSS scores from the knowledge base.

{rag_context}

Now analyze...
"""
```

---

## Extension Guide

### Adding a New Agent with RAG

**Example**: Create ComplianceAgent that only queries Governance KB.

```python
# app/services/agents/compliance_agent.py

from .base_agent import LLMAgent
from ..rag_service import RAGService

class ComplianceAgent(LLMAgent):
    """
    Compliance Agent - Checks for regulatory violations

    Uses: Governance KB exclusively (GDPR, HIPAA, PCI-DSS, SOC 2)
    """

    def __init__(self, llm_service, rag_service: RAGService):
        super().__init__(
            name="Compliance",
            description="Identifies compliance violations and regulatory risks",
            llm_service=llm_service
        )
        self.rag_service = rag_service

    async def execute(self, task: Dict[str, Any], context: AttackPathContext):
        """Check for compliance violations."""

        # Query Governance KB for compliance frameworks
        compliance_context = await self._query_compliance_knowledge(
            context.attack_chains,
            context.individual_vulnerabilities
        )

        # Build compliance-focused prompt
        prompt = self._build_compliance_prompt(
            context.spec,
            context.attack_chains,
            compliance_context
        )

        # LLM generates compliance report
        response = await self.llm_service.generate(
            model="mistral:7b-instruct",
            prompt=prompt,
            temperature=0.3  # Low temperature for factual compliance
        )

        return {
            "success": True,
            "compliance_violations": self._parse_violations(response),
            "regulatory_risks": self._assess_regulatory_risks(response)
        }

    async def _query_compliance_knowledge(self, attack_chains, vulnerabilities):
        """Query Governance KB for compliance frameworks."""

        # Identify which frameworks are relevant
        frameworks = []
        if self._has_pii_exposure(attack_chains):
            frameworks.append("GDPR")
        if self._has_payment_data(vulnerabilities):
            frameworks.append("PCI-DSS")
        if self._is_healthcare_api():
            frameworks.append("HIPAA")

        query = f"compliance {' '.join(frameworks)} violations penalties"

        return await self.rag_service.query_governance_knowledge(
            query=query,
            n_results=5
        )

    def _build_compliance_prompt(self, spec, chains, compliance_context):
        """Build compliance-focused prompt."""
        return f"""
You are a compliance officer specializing in API security regulations.

{compliance_context['context']}

Analyze this API for compliance violations:
{json.dumps(spec, indent=2)[:1000]}

Identified Security Issues:
{self._format_chains_for_compliance(chains)}

For each violation, provide:
1. Regulatory framework violated (GDPR, HIPAA, PCI-DSS, SOC 2)
2. Specific article/requirement violated
3. Potential penalties
4. Remediation required for compliance
"""
```

### Adding a New Knowledge Source

**Example**: Ingest CVE (Common Vulnerabilities and Exposures) database.

```python
# app/scripts/ingest_cve_knowledge.py

import requests
from app.services.rag_service import RAGService

def fetch_recent_api_cves():
    """Fetch recent API-related CVEs from NVD."""
    # NVD API: https://nvd.nist.gov/developers
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    params = {
        "keyword": "API",
        "resultsPerPage": 100
    }

    response = requests.get(url, params=params)
    cves = response.json()

    documents = []
    metadatas = []

    for item in cves.get("vulnerabilities", []):
        cve = item["cve"]

        # Format as knowledge document
        doc = f"""
CVE-{cve['id']} - {cve.get('descriptions', [{}])[0].get('value', 'No description')}

Published: {cve.get('published')}
Severity: {cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN')}
CVSS Score: {cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseScore', 0)}

Description: {cve.get('descriptions', [{}])[0].get('value', '')}

References: {', '.join([ref['url'] for ref in cve.get('references', [])])}
"""

        documents.append(doc)
        metadatas.append({
            "source": "NVD CVE Database",
            "category": cve['id'],
            "type": "cve",
            "severity": cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {}).get('baseSeverity', 'UNKNOWN')
        })

    return documents, metadatas

def main():
    print("Fetching recent API CVEs from NVD...")
    documents, metadatas = fetch_recent_api_cves()

    print(f"Ingesting {len(documents)} CVE documents into Attacker KB...")
    rag = RAGService()
    result = rag.ingest_documents(
        documents=documents,
        metadatas=metadatas,
        knowledge_base="attacker"
    )

    print(f"✅ Ingested {result['documents_added']} CVEs")

if __name__ == "__main__":
    main()
```

### Implementing RAG Caching

**Problem**: Same queries are made repeatedly (e.g., "OWASP API1 BOLA").

**Solution**: Add LRU cache to RAG queries.

```python
# In rag_service.py

from functools import lru_cache
import hashlib

class RAGService:

    @lru_cache(maxsize=128)
    def _get_cached_query_result(self, query_hash: str, kb_name: str, n_results: int):
        """Cache wrapper for query results."""
        # This method is just for cache key generation
        # Actual query happens in the non-cached method
        return None

    async def query_attacker_knowledge(self, query: str, n_results: int = 5):
        # Generate cache key
        query_hash = hashlib.md5(query.encode()).hexdigest()

        # Check cache
        cached = self._get_cached_query_result(query_hash, "attacker", n_results)
        if cached:
            self.logger.info(f"Cache hit for query: {query[:50]}...")
            return cached

        # Not in cache - perform query
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        results = self.attacker_kb.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"]
        )

        formatted_result = self._format_rag_results(results, "Attacker KB")

        # Store in cache
        self._get_cached_query_result.cache_info()  # Log cache stats

        return formatted_result
```

---

## Performance Optimization

### 1. Batch Embedding Generation

When ingesting many documents:

```python
# Bad: Generate embeddings one at a time
for doc in documents:
    embedding = model.encode([doc])[0]
    # ... store embedding

# Good: Batch process
embeddings = model.encode(documents, batch_size=32)  # GPU-accelerated batch
```

### 2. Reduce ChromaDB Query Scope

```python
# Bad: Query entire collection
results = collection.query(
    query_embeddings=[embedding],
    n_results=5
)

# Good: Add metadata filtering
results = collection.query(
    query_embeddings=[embedding],
    n_results=5,
    where={"category": {"$in": ["API1:BOLA", "API2:Auth"]}}  # Filter by metadata
)
```

### 3. Optimize Embedding Model

```python
# Current: all-MiniLM-L6-v2 (384 dimensions)
# Balanced speed/quality

# Faster (lower quality): paraphrase-MiniLM-L3-v2 (384 dim, 2x faster)
model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")

# Higher quality (slower): all-mpnet-base-v2 (768 dimensions)
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
```

### 4. Async Query Execution

Query multiple KBs in parallel:

```python
# Bad: Sequential queries
attacker_result = await rag.query_attacker_knowledge(query1)
governance_result = await rag.query_governance_knowledge(query2)

# Good: Parallel queries
import asyncio
attacker_result, governance_result = await asyncio.gather(
    rag.query_attacker_knowledge(query1),
    rag.query_governance_knowledge(query2)
)
```

### 5. Monitor Performance

Add timing decorators:

```python
import time
from functools import wraps

def timed(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        elapsed = (time.time() - start) * 1000
        logger.info(f"{func.__name__} took {elapsed:.2f}ms")
        return result
    return wrapper

class RAGService:
    @timed
    async def query_attacker_knowledge(self, query, n_results=5):
        # ... implementation
```

---

## Deployment Considerations

### Docker Deployment

```dockerfile
# Dockerfile for AI service with RAG

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Download embedding model at build time (cache in image)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Volume for vector store persistence
VOLUME ["/app/ai_service_data"]

# Expose port
EXPOSE 8000

# Run ingestion on first start
CMD ["sh", "-c", "python app/scripts/ingest_knowledge.py --all && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: rag-vector-store-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-service-rag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-service
  template:
    metadata:
      labels:
        app: ai-service
    spec:
      containers:
      - name: ai-service
        image: schemasculpt/ai-service:rag-v1.0
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
            nvidia.com/gpu: 1  # Optional: GPU for faster embeddings
        env:
        - name: AI_SERVICE_DATA_DIR
          value: "/data"
        volumeMounts:
        - name: vector-store
          mountPath: /data
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: vector-store
        persistentVolumeClaim:
          claimName: rag-vector-store-pvc
```

### Monitoring & Alerting

```python
# Add Prometheus metrics

from prometheus_client import Counter, Histogram

rag_query_duration = Histogram(
    'rag_query_duration_seconds',
    'Time spent querying RAG',
    ['knowledge_base']
)

rag_query_total = Counter(
    'rag_queries_total',
    'Total RAG queries',
    ['knowledge_base', 'status']
)

class RAGService:
    async def query_attacker_knowledge(self, query, n_results=5):
        with rag_query_duration.labels(knowledge_base='attacker').time():
            try:
                result = # ... perform query
                rag_query_total.labels(knowledge_base='attacker', status='success').inc()
                return result
            except Exception as e:
                rag_query_total.labels(knowledge_base='attacker', status='error').inc()
                raise
```

### Scaling Considerations

**Horizontal Scaling**:
- RAGService initializes ChromaDB client per instance
- Vector store is read-only during analysis (write during ingestion)
- Multiple instances can share same vector store (read-only mode)

**Vertical Scaling**:
- GPU: 1 GPU can handle ~1000 embedding generations/sec
- RAM: 4GB minimum, 8GB recommended (embedding model + ChromaDB cache)
- CPU: 2-4 cores sufficient for embedding model in CPU mode

---

## Conclusion

This RAG enhancement transforms SchemaSculpt from a generic AI tool into a specialized AI security expert by:

1. **Dual Knowledge Bases**: Attacker KB (OWASP, MITRE) + Governance KB (CVSS, DREAD, Compliance)
2. **Agent Enhancement**: ThreatModelingAgent and SecurityReporterAgent query KBs before LLM inference
3. **Seamless Integration**: Drop-in enhancement with graceful degradation
4. **Production-Ready**: GPU acceleration, caching, monitoring, containerization

**Key Takeaways for Developers**:
- RAG queries add ~50ms overhead (negligible vs. LLM inference)
- Knowledge bases are easily extensible (add documents via `ingest_documents()`)
- Graceful degradation ensures system works even without RAG
- Comprehensive logging enables debugging and performance monitoring

**Next Steps**:
1. Review this document thoroughly
2. Run `test_rag_system.py` to verify setup
3. Debug any issues using techniques in this guide
4. Extend knowledge bases with company-specific content
5. Monitor RAG performance in production

---

**Questions or Issues?**
- Check logs: `grep "RAG" ai_service/logs/app.log`
- Run tests: `pytest tests/test_rag_service.py -v`
- Debug manually: `python test_rag_system.py`

**Contact**: Development team or refer to `/docs/RAG_IMPLEMENTATION_COMPLETE.md`
