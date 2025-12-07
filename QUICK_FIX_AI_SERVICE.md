# Quick Fix: AI Service Dependencies & Knowledge Base

## Issues You're Experiencing

1. ❌ **MCP SDK not installed** - Repository features disabled
2. ❌ **Vector DB not populated** - AI explanation system won't work
3. ❌ **Multiple dependencies not installing** - Some features broken

## Quick Fix (5 Minutes)

Run these commands to fix all issues:

```bash
cd ai_service

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Step 1: Install missing dependencies
pip install chromadb==0.4.22 sentence-transformers pypdf beautifulsoup4

# Step 2: Try installing MCP SDK (optional - OK if it fails)
pip install mcp --pre 2>/dev/null || echo "MCP install failed - this is OK, continuing..."

# Step 3: Initialize knowledge base
python scripts/init_knowledge_base.py
```

**Expected Output:**
```
======================================================================
SchemaSculpt Knowledge Base Initialization
======================================================================

📦 Initializing embedding model...
✅ Embedding model loaded on cpu

🔍 Initializing Attacker Knowledge Base...
✅ Attacker KB initialized with 45 documents

🔐 Initializing Governance Knowledge Base...
✅ Governance KB initialized with 3 basic documents

🎉 Knowledge base initialization complete!
```

## Verification

Check if everything is working:

```bash
# Test imports
python << 'EOF'
import chromadb
print("✅ ChromaDB: OK")

from sentence_transformers import SentenceTransformer
print("✅ Sentence Transformers: OK")

try:
    import mcp
    print("✅ MCP SDK: OK (repository features enabled)")
except ImportError:
    print("⚠️  MCP SDK: Not available (repository features disabled - this is OK)")

# Check vector database
client = chromadb.PersistentClient(path="./vector_store")
try:
    kb = client.get_collection("attacker_knowledge")
    print(f"✅ Knowledge Base: {kb.count()} documents")
except:
    print("❌ Knowledge Base: Not initialized")
EOF
```

## Alternative: Automated Setup (Recommended)

If manual steps don't work, use the automated script:

```bash
cd ai_service

# Make script executable
chmod +x setup_ai_service.sh

# Run complete setup
./setup_ai_service.sh
```

This will:
- ✅ Check Python version
- ✅ Install all dependencies properly
- ✅ Initialize knowledge base with progress indicators
- ✅ Verify everything is working
- ✅ Provide summary of what's available

## What Each Fix Does

### Fix 1: Install ChromaDB & Dependencies
**Problem:** Vector database and embedding model not installed
**Solution:** Install specific versions known to work
**Result:** AI explanation system and RAG features will work

### Fix 2: Install MCP SDK (Optional)
**Problem:** Model Context Protocol SDK missing
**Solution:** Install pre-release version from PyPI
**Result:** GitHub repository integration will work
**Note:** It's OK if this fails - repository features are optional

### Fix 3: Initialize Knowledge Base
**Problem:** Vector database is empty
**Solution:** Populate with security knowledge from JSON and PDF files
**Result:** AI can provide detailed explanations with context

## Common Issues & Solutions

### Issue: "No such file: knowledge_base/security_knowledge.json"

**Solution:**
Check if knowledge_base directory exists with files:
```bash
ls -la knowledge_base/
```

If empty, the files should be in your repository. Git pull to get them:
```bash
git pull origin dev
```

### Issue: "ModuleNotFoundError: No module named 'torch'"

**Solution:**
Install PyTorch CPU-only version:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers
```

### Issue: "chromadb.errors.NoIndexException"

**Solution:**
Delete and reinitialize vector store:
```bash
rm -rf vector_store
python scripts/init_knowledge_base.py
```

### Issue: MCP installation fails with "Could not find a version"

**Solution:**
This is expected and OK! MCP SDK is optional. The warning will appear but all other features work:
```
WARNING:root:MCP SDK not installed. Repository features will be disabled.
```

Just ignore this warning unless you specifically need GitHub integration.

## Verification Checklist

After running the fixes, verify:

- [ ] ChromaDB installs without errors
- [ ] `python -c "import chromadb"` works
- [ ] `python -c "import sentence_transformers"` works
- [ ] `ls vector_store/` shows `chroma.sqlite3` file
- [ ] `python scripts/init_knowledge_base.py` completes successfully
- [ ] Service starts: `uvicorn app.main:app --reload`
- [ ] No errors in startup logs

## What If It Still Doesn't Work?

1. **Check Python Version:**
   ```bash
   python --version  # Must be 3.10 or higher
   ```

2. **Check Virtual Environment:**
   ```bash
   which python  # Should point to venv/bin/python
   ```

3. **Reinstall Everything:**
   ```bash
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   python scripts/init_knowledge_base.py
   ```

4. **Check Logs:**
   ```bash
   # Start service with debug logging
   LOG_LEVEL=DEBUG uvicorn app.main:app --reload
   ```

5. **Consult Full Troubleshooting Guide:**
   See `ai_service/TROUBLESHOOTING.md` for detailed solutions

## Expected Result

After applying these fixes:

✅ **AI Service Starts:** No import errors
✅ **RAG Features Work:** AI explanations have context
✅ **Security Analysis Works:** Knowledge base provides insights
✅ **MCP Warning (Optional):** May still appear - that's OK if you don't need repository features

## Time Investment

- **Quick fix:** 5 minutes (manual steps)
- **Automated setup:** 10 minutes (full script)
- **Troubleshooting:** 30 minutes (if issues persist)

## Next Steps After Fix

1. Start the AI service:
   ```bash
   cd ai_service
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. Verify health:
   ```bash
   curl http://localhost:8000/health
   ```

3. Start other services (Backend, UI)

4. Test AI features in the UI

## Support

If issues persist after trying all fixes:
- Check `ai_service/TROUBLESHOOTING.md` for detailed solutions
- Review logs: `tail -f ai_service/logs/ai_service.log`
- Ensure Ollama is running: `ollama serve`
- Verify Ollama has models: `ollama list`

---

**TL;DR:** Run these 3 commands:
```bash
cd ai_service && source venv/bin/activate
pip install chromadb sentence-transformers pypdf beautifulsoup4
python scripts/init_knowledge_base.py
```

Or use the automated script:
```bash
cd ai_service && ./setup_ai_service.sh
```

Both will fix your issues! 🚀
