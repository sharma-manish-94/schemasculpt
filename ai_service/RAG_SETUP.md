# RAG Knowledge Base Setup

## Overview

The RAG (Retrieval-Augmented Generation) system in SchemaSculpt AI has been consolidated into a unified, automatic initialization system. All knowledge bases are now automatically populated when the application starts.

## Architecture

### Two Specialized Knowledge Bases

1. **Attacker Knowledge Base**: Offensive security expertise
   - OWASP API Security Top 10
   - MITRE ATT&CK patterns
   - Real-world exploit techniques

2. **Governance Knowledge Base**: Risk frameworks and compliance
   - CVSS v3.1 scoring framework
   - DREAD risk assessment
   - Compliance requirements (GDPR, HIPAA, PCI-DSS)

## Automatic Initialization

**Knowledge bases are automatically populated when the application starts.**

When you run the AI service:
```bash
cd ai_service
uvicorn app.main:app --reload
```

The application will:
1. Initialize the LLM provider
2. Check if RAG knowledge bases exist
3. If empty or missing, automatically populate them with security knowledge
4. Log the initialization status

You'll see log output like:
```
INFO:main:Initializing RAG knowledge bases...
INFO:rag_initializer:Initializing Attacker Knowledge Base...
INFO:rag_initializer:Ingesting OWASP API Security Top 10...
INFO:rag_initializer:Ingesting MITRE ATT&CK patterns...
INFO:rag_initializer:Initializing Governance Knowledge Base...
INFO:rag_initializer:Ingesting CVSS framework...
INFO:rag_initializer:Ingesting DREAD framework...
INFO:rag_initializer:Ingesting compliance frameworks...
INFO:main:RAG knowledge bases initialized successfully (24 documents)
```

## Manual Management

Use the `manage_rag.py` CLI tool for manual operations:

### Check Status
```bash
cd ai_service
python manage_rag.py status
```

### Force Re-ingestion
```bash
python manage_rag.py reingest
```

### Test Queries
```bash
# Query attacker knowledge base
python manage_rag.py query "SQL injection patterns"

# Query governance knowledge base
python manage_rag.py query "GDPR compliance requirements" --kb governance
```

### Manual Initialization
```bash
# Initialize (happens automatically on app startup)
python manage_rag.py init
```

## File Structure

### Core Files
- `app/services/rag_service.py` - RAG service for querying knowledge bases
- `app/services/rag_initializer.py` - Unified initialization module
- `app/main.py` - Application startup with automatic RAG initialization
- `manage_rag.py` - CLI management tool

### Utility Scripts
- `scripts/add_documents_to_rag.py` - Add custom documents to knowledge bases
- `scripts/init_knowledge_base.py` - Legacy initialization from JSON files (optional)

### Removed Files (Consolidation)
- ~~`scripts/ingest_knowledge.py`~~ (duplicate, removed)
- ~~`app/scripts/ingest_knowledge.py`~~ (duplicate, removed)
- ~~`ingest_data.py`~~ (outdated LangChain approach, removed)
- ~~`simple_ingest.py`~~ (outdated simple approach, removed)

## Dependencies

Required packages (already in requirements.txt):
```
chromadb
sentence-transformers
```

These are automatically installed when you run:
```bash
pip install -r requirements.txt
```

## How It Works

### Automatic Initialization Flow

1. **App Startup** (`app/main.py`)
   - FastAPI lifespan event triggered
   - Calls `initialize_rag_on_startup()`

2. **Check Existing KBs** (`rag_initializer.py`)
   - Queries vector store for existing collections
   - Checks document counts in each knowledge base

3. **Populate if Needed**
   - If Attacker KB is empty/missing → Ingest OWASP + MITRE
   - If Governance KB is empty/missing → Ingest CVSS + DREAD + Compliance
   - Skip if already populated (efficient startup)

4. **Ready for Use**
   - RAG service available for all agents
   - ThreatModelingAgent uses Attacker KB
   - SecurityReporterAgent uses Governance KB

### Knowledge Ingestion Process

Each knowledge base ingests structured security knowledge:

```python
# Example: OWASP knowledge ingestion
documents = [
    "OWASP API1:2023 - Broken Object Level Authorization...",
    "OWASP API2:2023 - Broken Authentication...",
    # ... more documents
]

metadatas = [
    {"source": "OWASP", "category": "API1:2023", "type": "vulnerability_pattern"},
    # ... matching metadata
]

rag_service.ingest_documents(
    documents=documents,
    metadatas=metadatas,
    knowledge_base="attacker"  # or "governance"
)
```

### Embeddings and Vector Storage

- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2`
  - Runs locally (no API calls, free)
  - GPU-accelerated if available
  - Fast and efficient

- **Vector Store**: ChromaDB
  - Persistent storage in `ai_service/vector_store/`
  - Automatic indexing for fast retrieval
  - Survives application restarts

## Usage in Agents

Agents query RAG knowledge bases for expertise:

```python
# Example: ThreatModelingAgent querying attacker knowledge
context = await rag_service.query_attacker_knowledge(
    query="broken authentication vulnerabilities in APIs",
    n_results=5
)

# Use context.context in LLM prompt
prompt = f"""
You are a security expert. Using this knowledge:

{context['context']}

Analyze this API specification for broken authentication issues...
"""
```

## Troubleshooting

### Knowledge bases not initializing

Check logs for errors:
```bash
# Run with verbose logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

### Dependencies missing

Install RAG dependencies:
```bash
pip install chromadb sentence-transformers
```

### Vector store corruption

Delete and reinitialize:
```bash
rm -rf ai_service/vector_store
python manage_rag.py init
```

### Test RAG is working

```bash
# Check status
python manage_rag.py status

# Test query
python manage_rag.py query "authentication vulnerabilities"
```

## Adding Custom Knowledge

Use the `add_documents_to_rag.py` utility:

```bash
# Add PDF to attacker KB
python scripts/add_documents_to_rag.py --file exploit_patterns.pdf --kb attacker

# Add directory of documents to governance KB
python scripts/add_documents_to_rag.py --directory ./compliance_docs --kb governance

# Add with metadata
python scripts/add_documents_to_rag.py --file cvss.pdf --kb governance --metadata '{"version": "3.1"}'
```

## Performance

- **First startup**: ~5-10 seconds to ingest all documents
- **Subsequent startups**: <1 second (knowledge bases already exist)
- **Query latency**: ~100-300ms per query
- **GPU acceleration**: Automatic if CUDA available

## Summary of Changes

### What Changed
✅ **Consolidated**: Multiple duplicate scripts into one unified system
✅ **Automated**: Knowledge bases populate automatically on app startup
✅ **Simplified**: Single CLI tool (`manage_rag.py`) for all manual operations
✅ **Consistent**: All knowledge ingestion uses the same service

### What Was Removed
❌ Duplicate `ingest_knowledge.py` files (2 locations)
❌ Outdated `ingest_data.py` (LangChain-based)
❌ Outdated `simple_ingest.py` (basic JSON creator)

### What's New
✨ `app/services/rag_initializer.py` - Unified initialization module
✨ `manage_rag.py` - Comprehensive CLI management tool
✨ Automatic initialization in `app/main.py` lifespan

### Migration Guide

**Before** (manual, inconsistent):
```bash
# Had to run different scripts
python scripts/ingest_knowledge.py --all
# or
python ingest_data.py
# or
python app/scripts/ingest_knowledge.py --all
```

**After** (automatic, consistent):
```bash
# Just start the application - RAG initializes automatically
uvicorn app.main:app --reload

# Optional: use CLI for management
python manage_rag.py status
python manage_rag.py reingest  # force re-ingestion
```

## Next Steps

1. Start the application - RAG will initialize automatically
2. Check status with `python manage_rag.py status`
3. Test queries with `python manage_rag.py query "your test query"`
4. Add custom documents with `scripts/add_documents_to_rag.py` if needed

The RAG system is now fully automated and ready to enhance your AI security analysis!
