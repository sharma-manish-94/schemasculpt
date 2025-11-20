# SchemaSculpt AI Service - Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "MCP SDK not installed. Repository features will be disabled."

**Problem:**
The Model Context Protocol (MCP) SDK is not installed, which disables GitHub repository integration features.

**Impact:**
- Repository Explorer tab won't work
- Cannot import OpenAPI specs from GitHub
- Other core features (AI analysis, validation, etc.) still work fine

**Solution 1: Install MCP SDK (Recommended)**
```bash
cd ai_service
source venv/bin/activate

# Try installing MCP SDK (pre-release)
pip install mcp --pre

# If that fails, install from GitHub
pip install git+https://github.com/modelcontextprotocol/python-sdk.git

# Verify installation
python -c "import mcp; print('MCP SDK installed successfully')"
```

**Solution 2: Ignore the Warning (If you don't need repository features)**
The warning is informational only. All other features will work normally. You can safely ignore it if you don't plan to use GitHub integration.

**Solution 3: Check Python Version**
MCP SDK requires Python 3.10+:
```bash
python3 --version  # Should be 3.10 or higher
```

---

### Issue 2: Vector DB (ChromaDB) Not Populated

**Problem:**
The knowledge base for RAG (Retrieval-Augmented Generation) is empty, so AI explanations won't have context.

**Impact:**
- AI explanation system won't work properly
- No security knowledge base for enhanced analysis
- Basic AI features still work (editing, mock generation)

**Solution: Initialize the Knowledge Base**

**Step 1: Ensure dependencies are installed**
```bash
cd ai_service
source venv/bin/activate

# Install required packages
pip install chromadb sentence-transformers pypdf beautifulsoup4
```

**Step 2: Run initialization script**
```bash
# Make script executable
chmod +x scripts/init_knowledge_base.py

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

**Step 3: Verify**
```bash
# Check if vector_store directory has data
ls -la vector_store/

# Should see ChromaDB files
# chroma.sqlite3
# (and other database files)
```

---

### Issue 3: Multiple Dependencies Not Installing

**Problem:**
Some packages in `requirements.txt` fail to install due to version conflicts or missing system libraries.

**Solution: Use the Fixed Requirements File**

```bash
cd ai_service
source venv/bin/activate

# Option 1: Use the fixed requirements file
pip install -r requirements-fixed.txt

# Option 2: Install in stages
# Stage 1: Core dependencies
pip install fastapi uvicorn httpx requests pydantic python-dotenv PyYAML

# Stage 2: OpenAPI processing
pip install prance openapi-spec-validator jsonpatch jsonschema

# Stage 3: RAG dependencies (optional but recommended)
pip install langchain langchain-community chromadb sentence-transformers

# Stage 4: Additional RAG tools
pip install pypdf beautifulsoup4 html2text

# Stage 5: MCP (optional)
pip install mcp --pre
```

---

### Issue 4: ChromaDB Import Error

**Problem:**
```python
ImportError: cannot import name 'xxx' from 'chromadb'
```

**Solution:**
```bash
# Uninstall and reinstall ChromaDB with specific version
pip uninstall chromadb -y
pip install chromadb==0.4.22

# If still failing, install with no dependencies and manually add them
pip install --no-deps chromadb==0.4.22
pip install pydantic>=2.0 requests
```

---

### Issue 5: Sentence-Transformers CUDA/GPU Errors

**Problem:**
```
RuntimeError: Attempting to deserialize object on a CUDA device but torch.cuda.is_available() is False
```

**Solution:**
```bash
# Force CPU-only installation
pip uninstall torch -y
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Reinstall sentence-transformers
pip install sentence-transformers
```

---

### Issue 6: "vector_store directory is empty"

**Problem:**
The vector database directory exists but has no data.

**Solution:**
```bash
# Check if knowledge_base directory has source files
ls -la knowledge_base/

# Should contain:
# - security_knowledge.json
# - OWASP_Application_Security_Verification_Standard_5.0.0_en.pdf

# If missing, the files should be part of the repository
# If present, run initialization:
python scripts/init_knowledge_base.py
```

---

### Issue 7: Ollama Connection Errors

**Problem:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**Solution:**
```bash
# Check if Ollama is installed
ollama --version

# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start Ollama
# On Linux/Mac:
ollama serve

# On Windows:
# Ollama runs as a service, check Task Manager

# Pull required model
ollama pull mistral

# Verify model is available
ollama list
```

---

## Complete Setup Script

For a fresh installation, use the automated setup script:

```bash
cd ai_service

# Make script executable
chmod +x setup_ai_service.sh

# Run setup
./setup_ai_service.sh
```

This script will:
1. ✅ Check Python version
2. ✅ Create virtual environment
3. ✅ Install all dependencies
4. ✅ Attempt MCP installation (optional)
5. ✅ Create necessary directories
6. ✅ Initialize knowledge base
7. ✅ Create .env file
8. ✅ Verify Ollama installation

---

## Manual Verification Checklist

### 1. Check Python Environment
```bash
python --version  # Should be 3.10+
which python      # Should be in venv
```

### 2. Check Installed Packages
```bash
pip list | grep fastapi
pip list | grep chromadb
pip list | grep sentence-transformers
pip list | grep mcp
```

### 3. Check Directory Structure
```bash
ls -la vector_store/      # Should have chroma.sqlite3
ls -la knowledge_base/    # Should have JSON and PDF files
ls -la logs/              # Should exist
```

### 4. Test Imports
```bash
python << EOF
import fastapi
print("✅ FastAPI OK")

import chromadb
print("✅ ChromaDB OK")

import sentence_transformers
print("✅ Sentence Transformers OK")

try:
    import mcp
    print("✅ MCP SDK OK")
except ImportError:
    print("⚠️  MCP SDK not available (optional)")
EOF
```

### 5. Test Knowledge Base
```bash
python << EOF
import chromadb
client = chromadb.PersistentClient(path="./vector_store")

try:
    attacker = client.get_collection("attacker_knowledge")
    print(f"✅ Attacker KB: {attacker.count()} documents")
except:
    print("⚠️  Attacker KB not initialized")

try:
    governance = client.get_collection("governance_knowledge")
    print(f"✅ Governance KB: {governance.count()} documents")
except:
    print("⚠️  Governance KB not initialized")
EOF
```

---

## Environment Variables

Ensure your `.env` file is properly configured:

```bash
# Required
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
AI_SERVICE_DATA_DIR=./data
LOG_LEVEL=INFO

# Optional (for repository features)
GITHUB_TOKEN=your_github_personal_access_token

# Optional (for advanced features)
ENABLE_RAG=true
VECTOR_STORE_DIR=./vector_store
```

---

## Testing the Setup

### Test 1: Start the Service
```bash
cd ai_service
source venv/bin/activate
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Test 2: Check Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "ollama_available": true,
  "rag_available": true,
  "mcp_available": false
}
```

### Test 3: Test AI Endpoint
```bash
curl -X POST http://localhost:8000/ai/spec/generate \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "Create a simple health check endpoint",
    "current_spec": "{}"
  }'
```

Should return a generated OpenAPI spec.

---

## Common Error Messages and Solutions

### "No module named 'mcp'"
**Severity:** Low (optional feature)
**Solution:** Install MCP SDK: `pip install mcp --pre`
**Alternative:** Ignore if not using repository features

### "chromadb not found"
**Severity:** Medium (RAG features disabled)
**Solution:** `pip install chromadb sentence-transformers`
**Alternative:** Basic AI features still work

### "Ollama connection refused"
**Severity:** High (AI features won't work)
**Solution:** Start Ollama service: `ollama serve`
**Verify:** `curl http://localhost:11434/api/tags`

### "No such collection: attacker_knowledge"
**Severity:** Medium (explanations won't work)
**Solution:** Run `python scripts/init_knowledge_base.py`
**Alternative:** AI features work without explanations

### "torch.cuda.is_available() is False"
**Severity:** Low (performance impact)
**Solution:** Install CPU-only torch (see Issue 5)
**Alternative:** Works on CPU, just slower

---

## Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   tail -f logs/ai_service.log
   ```

2. **Enable debug logging:**
   Edit `.env`:
   ```
   LOG_LEVEL=DEBUG
   ```

3. **Verify system requirements:**
   - Python 3.10+
   - 4GB RAM minimum
   - 10GB disk space for models
   - Ollama installed and running

4. **Create issue:**
   - Include Python version: `python --version`
   - Include package versions: `pip freeze > packages.txt`
   - Include error messages
   - Include relevant logs

---

## Quick Fixes Cheat Sheet

| Problem | Quick Fix |
|---------|-----------|
| MCP warning | `pip install mcp --pre` or ignore |
| Empty vector DB | `python scripts/init_knowledge_base.py` |
| ChromaDB error | `pip install chromadb==0.4.22` |
| Torch GPU error | `pip install torch --index-url https://download.pytorch.org/whl/cpu` |
| Ollama connection | `ollama serve` in separate terminal |
| Missing model | `ollama pull mistral` |
| Import errors | `pip install -r requirements-fixed.txt` |
| Permission denied | `chmod +x setup_ai_service.sh` |

---

## Success Criteria

Your AI service is properly set up when:

✅ Service starts without errors: `uvicorn app.main:app --reload`
✅ Health endpoint returns `"status": "healthy"`
✅ Ollama connection works (no connection refused errors)
✅ ChromaDB has data: `ls -la vector_store/` shows files
✅ Knowledge base initialized: Both collections have documents
✅ AI endpoints respond: Can generate specs and explanations
✅ (Optional) MCP features work: Repository endpoints respond

If all criteria are met, your setup is complete! 🎉
