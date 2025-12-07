# RAG Knowledge Base - Complete Guide

## 📚 Overview

This directory contains the source documents that populate the RAG (Retrieval-Augmented Generation) system. Documents are embedded using **sentence-transformers** and stored in **ChromaDB** vector database.

## 🏗️ Architecture

```
Knowledge Base Flow:
┌─────────────────────┐
│   Source Documents  │
│  (JSON, PDF, TXT)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Embedding Model    │
│  sentence-trans-    │
│  formers/all-       │
│  MiniLM-L6-v2       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   ChromaDB Vector   │
│      Database       │
│  ┌───────────────┐  │
│  │ Attacker KB   │  │  (For ThreatModelingAgent)
│  ├───────────────┤  │
│  │ Governance KB │  │  (For SecurityReporterAgent)
│  └───────────────┘  │
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│   RAG Service       │
│   Queries KB for    │
│   relevant context  │
└─────────────────────┘
```

## 📂 Current Documents

### 1. `security_knowledge.json` (Primary Source)

**Size:** ~45 documents (after embedding)

**Content:**
- **OWASP API Security Top 10 2023** (10 vulnerabilities)
  - API1: BOLA
  - API2: Broken Authentication
  - API3: Broken Object Property Level Authorization
  - API4: Unrestricted Resource Consumption
  - API5: Broken Function Level Authorization
  - API6: Unrestricted Access to Sensitive Business Flows
  - API7: Server Side Request Forgery
  - API8: Security Misconfiguration
  - API9: Improper Inventory Management
  - API10: Unsafe Consumption of APIs

- **Common Vulnerabilities** (5 patterns)
  - SQL Injection via API Parameters
  - JWT Token Tampering
  - GraphQL Introspection Exposure
  - API Key Leakage
  - XXE (XML External Entity) Injection

- **Attack Patterns** (4 multi-step chains)
  - BOLA + Mass Assignment → Privilege Escalation
  - Resource Exhaustion via Nested Pagination
  - JWT None Algorithm Bypass
  - Parameter Pollution for Business Logic Bypass

**Structure:**
```json
{
  "owasp_vulnerabilities": [
    {
      "category": "API1:2023 BOLA",
      "risk_level": "CRITICAL",
      "description": "...",
      "attack_scenarios": ["..."],
      "remediation": ["..."],
      "technical_indicators": ["..."]
    }
  ],
  "common_vulnerabilities": [...],
  "attack_patterns": [...]
}
```

### 2. `OWASP_Application_Security_Verification_Standard_5.0.0_en.pdf`

**Size:** 516 KB, 165 pages

**Content:**
- OWASP ASVS (Application Security Verification Standard)
- Comprehensive security requirements
- Governance and compliance guidelines
- Used for **Governance Knowledge Base**

**Processing:**
- PDF parsed into ~1200 chunks (if pypdf installed)
- Each chunk ~500 characters
- Embedded with page number metadata

## 🔄 How Documents Get Embedded

### Step 1: Source Files → Text Extraction

```python
# For JSON (security_knowledge.json)
with open('security_knowledge.json') as f:
    knowledge = json.load(f)

# Format each OWASP vulnerability as text
for vuln in knowledge['owasp_vulnerabilities']:
    document_text = f"""
    OWASP {vuln['category']}
    Risk Level: {vuln['risk_level']}

    Description: {vuln['description']}

    Attack Scenarios:
    - {scenario1}
    - {scenario2}
    ...

    Remediation:
    - {fix1}
    - {fix2}
    ...
    """
```

### Step 2: Text → Vector Embeddings

```python
from sentence_transformers import SentenceTransformer

# Load embedding model (runs locally, no API calls)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Convert text to 384-dimensional vector
embedding = model.encode(document_text)
# Result: [0.123, -0.456, 0.789, ...] (384 numbers)
```

### Step 3: Vectors → ChromaDB Storage

```python
import chromadb

client = chromadb.PersistentClient(path="./vector_store")

# Create collection with embedding function
collection = client.create_collection(
    name="attacker_knowledge",
    embedding_function=embedding_function
)

# Add documents (embeddings computed automatically)
collection.add(
    documents=[document_text],
    metadatas=[{"type": "owasp_vulnerability", "category": "BOLA"}],
    ids=["unique_id_12345"]
)
```

### Step 4: Query → Retrieval

```python
# When AI needs context
results = collection.query(
    query_texts=["SQL injection attack patterns"],
    n_results=3  # Top 3 most relevant documents
)

# Returns documents with highest cosine similarity
# AI receives: Attack patterns, indicators, remediation steps
```

## 🚀 Initialization (First Time)

Run this once to populate the vector database:

```bash
cd ai_service

# Make sure dependencies are installed
pip install chromadb sentence-transformers pypdf

# Run initialization
python scripts/init_knowledge_base.py
```

**Expected Output:**
```
======================================================================
SchemaSculpt Knowledge Base Initialization
======================================================================

📦 Initializing embedding model...
✅ Embedding model loaded on cpu

📦 Initializing ChromaDB...
✅ ChromaDB initialized at /path/to/vector_store

🔍 Initializing Attacker Knowledge Base...
  Adding 45 documents to attacker_knowledge...
✅ Attacker KB initialized with 45 documents

🔐 Initializing Governance Knowledge Base...
  Parsing OWASP_Application_Security_Verification_Standard_5.0.0_en.pdf...
  Found 165 pages
  Added batch 1/12
  ...
✅ Governance KB initialized with 1240 chunks from OWASP ASVS

🔍 Verifying installation...
✅ Attacker KB: 45 documents
✅ Governance KB: 1240 documents

🎉 Knowledge base initialization complete!
```

## ➕ Adding New Documents

### Quick Add (Simple Files)

```bash
# Add a single PDF to attacker knowledge base
python scripts/add_documents_to_rag.py \
  --file ./knowledge_base/raw_documents/mitre_attack_api.pdf \
  --kb attacker

# Add a directory of compliance docs to governance KB
python scripts/add_documents_to_rag.py \
  --directory ./knowledge_base/governance \
  --kb governance \
  --recursive
```

### Add with Metadata

```bash
# Add CVSS scoring guide with metadata
python scripts/add_documents_to_rag.py \
  --file cvss_v3.1_guide.pdf \
  --kb governance \
  --metadata '{"source": "FIRST", "version": "3.1", "type": "risk_scoring"}'
```

### Supported Formats

| Format | Extension | Processing |
|--------|-----------|------------|
| Plain Text | `.txt` | Direct embedding |
| Markdown | `.md` | Direct embedding |
| PDF | `.pdf` | Text extraction → chunking → embedding |
| JSON | `.json` | Structure parsing → formatting → embedding |

## 📝 Creating Custom Knowledge JSON

### Format 1: Simple List

```json
[
  {
    "topic": "API Rate Limiting",
    "content": "Rate limiting prevents API abuse by restricting request frequency...",
    "category": "security"
  },
  {
    "topic": "OAuth 2.0",
    "content": "OAuth 2.0 is an authorization framework that enables...",
    "category": "authentication"
  }
]
```

### Format 2: Structured Knowledge (Recommended)

```json
{
  "owasp_vulnerabilities": [
    {
      "category": "API11:2024 Custom Vulnerability",
      "risk_level": "HIGH",
      "description": "Your custom vulnerability description",
      "attack_scenarios": [
        "Scenario 1",
        "Scenario 2"
      ],
      "remediation": [
        "Fix 1",
        "Fix 2"
      ],
      "technical_indicators": [
        "Indicator 1",
        "Indicator 2"
      ]
    }
  ],
  "attack_patterns": [
    {
      "name": "Your Attack Pattern",
      "type": "Multi-Step Attack Chain",
      "description": "Pattern description",
      "prerequisites": ["Prereq 1", "Prereq 2"],
      "steps": ["Step 1", "Step 2", "Step 3"],
      "indicators": ["Indicator 1"],
      "defenses": ["Defense 1", "Defense 2"]
    }
  ]
}
```

Save as `custom_knowledge.json` in `knowledge_base/` and run:

```bash
python scripts/add_documents_to_rag.py \
  --file knowledge_base/custom_knowledge.json \
  --kb attacker
```

## 🔍 Testing RAG Retrieval

### Test Query

```bash
# Query attacker knowledge base
python scripts/add_documents_to_rag.py \
  --query "SQL injection attack patterns" \
  --kb attacker
```

**Output:**
```
🔍 Query: SQL injection attack patterns
📚 Knowledge Base: attacker_knowledge
----------------------------------------------------------------------

Result 1:
Source: security_knowledge.json
Type: common_vulnerability
Content: SQL Injection via API Parameters

API parameters directly interpolated into SQL queries without
sanitization, allowing attackers to execute arbitrary SQL commands.

Indicators:
- Database error messages in API responses
- API accepts complex query parameters
...
----------------------------------------------------------------------
```

### Query via Python

```python
import chromadb
from sentence_transformers import SentenceTransformer

# Connect to vector store
client = chromadb.PersistentClient(path="./vector_store")
attacker_kb = client.get_collection("attacker_knowledge")

# Query for relevant documents
results = attacker_kb.query(
    query_texts=["How to chain BOLA with mass assignment?"],
    n_results=3
)

# Print results
for doc in results['documents'][0]:
    print(doc)
    print("-" * 70)
```

## 📁 Directory Structure

```
knowledge_base/
├── README.md                    # This file
├── security_knowledge.json      # Primary source (OWASP + attacks)
├── OWASP_ASVS_5.0.0_en.pdf     # Governance source
│
├── attacker/                    # Optional: Attacker-specific docs
│   ├── mitre_attack_api.pdf
│   ├── exploit_techniques.md
│   └── real_world_cases.json
│
├── governance/                  # Optional: Governance-specific docs
│   ├── cvss_guide.pdf
│   ├── gdpr_api_requirements.md
│   └── pci_dss_api.pdf
│
└── raw_documents/               # Optional: Unprocessed documents
    ├── research_papers/
    ├── vendor_advisories/
    └── compliance_standards/
```

## 🔄 Update Workflow

### Adding New OWASP Vulnerabilities

1. Edit `security_knowledge.json`
2. Add new entry to `owasp_vulnerabilities` array
3. Re-run initialization or add incrementally:

```bash
# Option 1: Re-initialize everything (slow but complete)
rm -rf ../vector_store
python scripts/init_knowledge_base.py

# Option 2: Add just the new file (faster)
python scripts/add_documents_to_rag.py \
  --file knowledge_base/security_knowledge.json \
  --kb attacker
```

### Adding Research Papers

```bash
# Add a new research paper to attacker KB
python scripts/add_documents_to_rag.py \
  --file knowledge_base/raw_documents/api_security_research_2024.pdf \
  --kb attacker \
  --metadata '{"year": "2024", "source": "IEEE", "type": "research"}'
```

### Bulk Import

```bash
# Add all PDFs from a directory
python scripts/add_documents_to_rag.py \
  --directory knowledge_base/governance \
  --kb governance \
  --recursive
```

## 🧪 Verification

### Check Collection Statistics

```python
import chromadb

client = chromadb.PersistentClient(path="./vector_store")

# Attacker KB
attacker = client.get_collection("attacker_knowledge")
print(f"Attacker KB: {attacker.count()} documents")

# Governance KB
governance = client.get_collection("governance_knowledge")
print(f"Governance KB: {governance.count()} documents")
```

### Check Embedding Quality

```bash
# Query for specific topic
python scripts/add_documents_to_rag.py \
  --query "privilege escalation attack chains" \
  --kb attacker

# Should return relevant attack patterns
```

### Verify in AI Service

```bash
# Start AI service
cd ai_service
uvicorn app.main:app --reload

# Test RAG endpoint
curl -X POST http://localhost:8000/ai/explain \
  -H "Content-Type: application/json" \
  -d '{
    "issue": "Missing pagination",
    "context": "GET /users returns all users"
  }'

# Response should include RAG-enhanced context
```

## 🎯 Best Practices

### 1. Document Quality

✅ **DO:**
- Use authoritative sources (OWASP, NIST, MITRE)
- Include practical examples and attack scenarios
- Provide remediation steps
- Add metadata for filtering

❌ **DON'T:**
- Add speculative or unverified content
- Mix attacker and governance knowledge in same file
- Create duplicate documents
- Add very short (<50 chars) content

### 2. Chunking Strategy

- **Small chunks (200-300 chars):** Better precision, more results needed
- **Medium chunks (500-700 chars):** Balanced (recommended)
- **Large chunks (1000+ chars):** More context, but less precise retrieval

### 3. Metadata

Always include:
- `source`: Where document came from
- `type`: Document category
- `date` or `version`: When/which version

Example:
```bash
--metadata '{"source": "OWASP", "type": "vulnerability", "version": "2023"}'
```

### 4. Maintenance

- **Monthly:** Add new vulnerabilities/attack patterns
- **Quarterly:** Update with new research
- **Yearly:** Review and remove outdated content

## 🐛 Troubleshooting

### Issue: "No such collection: attacker_knowledge"

**Solution:** Run initialization first:
```bash
python scripts/init_knowledge_base.py
```

### Issue: "pypdf not installed"

**Solution:**
```bash
pip install pypdf
```

### Issue: Poor retrieval quality

**Diagnosis:**
```bash
# Test queries with different phrasings
python scripts/add_documents_to_rag.py --query "BOLA attack" --kb attacker
python scripts/add_documents_to_rag.py --query "broken object authorization" --kb attacker
```

**Solutions:**
- Rephrase query to match document language
- Add more documents with varied terminology
- Reduce chunk size for better precision

### Issue: Embeddings slow

**Solution:**
- Use GPU if available (automatic detection)
- Reduce chunk size to process fewer, smaller chunks
- Use batch processing for large imports

## 📊 Performance Metrics

### Embedding Speed

- **CPU:** ~100-200 documents/second
- **GPU:** ~500-1000 documents/second

### Storage

- **Embeddings:** ~1.5 KB per document (384-dim float vectors)
- **Metadata:** ~0.5 KB per document
- **Total for 1000 docs:** ~2 MB

### Retrieval Speed

- **Query time:** ~10-50ms (depends on collection size)
- **Scales well:** O(log n) with HNSW index

## 🚀 Advanced Usage

### Custom Embedding Model

Edit `init_knowledge_base.py`:

```python
# Change from all-MiniLM-L6-v2 to larger model
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
# Better quality, but slower and larger
```

### Multi-lingual Support

```python
# Use multilingual model
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
```

### Hybrid Search (Dense + Sparse)

ChromaDB supports BM25 sparse retrieval:

```python
results = collection.query(
    query_texts=["SQL injection"],
    n_results=3,
    where={"type": "attack_pattern"}  # Metadata filter
)
```

## 📚 Resources

- **ChromaDB Docs:** https://docs.trychroma.com/
- **Sentence Transformers:** https://www.sbert.net/
- **OWASP API Security:** https://owasp.org/API-Security/
- **MITRE ATT&CK:** https://attack.mitre.org/

## 🆘 Getting Help

1. Check this README
2. Test with query tool: `add_documents_to_rag.py --query`
3. Review initialization logs
4. Check ChromaDB files: `ls -la ../vector_store/`

---

**Last Updated:** 2024-11-20
**Version:** 1.0
**Maintainer:** SchemaSculpt AI Team
