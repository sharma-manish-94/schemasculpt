# Testing Guide: Repository Integration

## Quick Start Testing

Now that the UI integration is complete, you should see a **"🔗 Import from GitHub"** button in the editor toolbar (next to "Load File" and "Download" buttons).

## Prerequisites

Before testing, ensure all services are running:

### 1. Install MCP Dependencies (AI Service)
```bash
cd ai_service
source venv/bin/activate
pip install mcp aiofiles
```

### 2. Get GitHub Personal Access Token
1. Go to: https://github.com/settings/tokens/new
2. Description: `SchemaSculpt Testing`
3. Select scopes: `repo` (for private repos) or `public_repo` (for public only)
4. Click "Generate token"
5. **Copy the token** (starts with `ghp_`)

### 3. Start All Services

**Terminal 1 - Redis:**
```bash
docker run -d --name schemasculpt-redis -p 6379:6379 redis
```

**Terminal 2 - AI Service:**
```bash
cd ai_service
source venv/bin/activate
uvicorn app.main:app --reload
```
Should see: ✓ Application startup complete (http://localhost:8000)

**Terminal 3 - API Gateway:**
```bash
cd api
./mvnw spring-boot:run
```
Should see: Started SchemasculptApiApplication (http://localhost:8080)

**Terminal 4 - UI:**
```bash
cd ui
npm start
```
Should open browser at: http://localhost:3000

## Testing Steps

### Test 1: Basic UI Integration

1. **Open SchemaSculpt**
   - Navigate to http://localhost:3000
   - Login if required
   - Open or create a project

2. **Locate the Button**
   - Look at the editor toolbar (top of the middle panel)
   - You should see: `📁 Load File` | `🔗 Import from GitHub` | `💾 Download`
   - If you see the button, ✅ UI integration successful!

### Test 2: Connect to GitHub

1. **Click "🔗 Import from GitHub"**
   - A modal should appear with "Import from Repository" title

2. **Use Manual Token (Recommended for Testing)**
   - Click "Use Personal Access Token instead"
   - Paste your GitHub token (from prerequisites step 2)
   - Click "Connect"
   - Should see: ✅ "Connected to GitHub" with green checkmark

### Test 3: Browse Repository

1. **Quick Load from URL**
   - In the "Quick Load from URL" section
   - Paste: `https://github.com/OAI/OpenAPI-Specification`
   - Click "Load Repository"

2. **Browse Files**
   - Should see repository browser with files and folders
   - Navigate to: `examples` folder (click on it)
   - Should see various OpenAPI spec files

3. **Check Filtering**
   - Toggle "Show only OpenAPI specs" checkbox
   - Should filter to show only .yaml, .yml, .json files with OpenAPI content

### Test 4: Import Spec File

1. **Select a Spec**
   - In the file browser, find: `v3.0/petstore.yaml`
   - Files with OpenAPI content will have a green "OpenAPI" badge
   - Click on the file

2. **Verify Import**
   - Should see "Successfully loaded petstore.yaml" alert
   - Modal should close automatically
   - **Monaco Editor should now contain the Petstore spec content**
   - Left panel should update with API endpoints (e.g., `/pets`, `/pets/{id}`)

✅ If you can see the spec in the editor, **the integration is working!**

### Test 5: Browse Different Repository

1. **Click "🔗 Import from GitHub" again**
2. **Try another repository**
   - Example: `https://github.com/swagger-api/swagger-petstore`
   - Or use your own repository with OpenAPI specs
3. **Navigate and import a different spec**

## Troubleshooting

### Issue: Button Not Visible

**Check 1: Build the UI**
```bash
cd ui
npm install
npm start
```

**Check 2: Browser Cache**
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or clear cache in browser dev tools

### Issue: "MCP SDK not installed" Error

**Check AI Service logs** (Terminal 2):
```bash
# Should see MCP-related imports
# If error about mcp module, reinstall:
pip install mcp aiofiles
```

**Verify installation:**
```bash
cd ai_service
source venv/bin/activate
python -c "import mcp; print('MCP installed successfully')"
```

### Issue: "Failed to connect to GitHub"

**Check 1: Network**
- Ensure you have internet connection
- First-time MCP GitHub server will download via `npx`

**Check 2: Token**
- Verify token has correct scopes
- Try generating a new token

**Check 3: AI Service logs**
```bash
# Check Terminal 2 for errors like:
# "Failed to connect to MCP server"
# Look for Node.js installation issues
```

**Check Node.js:**
```bash
node --version  # Should be 16+
npx --version   # Should work
```

### Issue: Repository Browser Shows "Error browsing tree"

**Check API Gateway logs** (Terminal 3):
- Look for connection errors to AI Service
- Verify X-Session-ID header is being sent

**Check AI Service endpoint:**
```bash
# Test health endpoint
curl http://localhost:8000/api/repository/health \
  -H "X-Session-ID: test-123"

# Expected response:
# {"status":"healthy","mcp_available":true,"connected":false,"provider":null}
```

### Issue: File Content Not Loading

**Check 1: File size**
- Very large files (>1MB) might timeout
- Try a smaller spec file first

**Check 2: Session**
- Ensure session was created (check left panel for endpoints)
- Try refreshing the page and creating new session

**Check 3: Browser console**
- Open DevTools (F12)
- Check Console tab for JavaScript errors

## Manual API Testing

If UI testing fails, test the backend directly:

### Test 1: AI Service Health
```bash
curl http://localhost:8000/api/repository/health \
  -H "X-Session-ID: test-123"
```

**Expected:** `{"status":"healthy","mcp_available":true,...}`

### Test 2: Connect to GitHub
```bash
curl -X POST http://localhost:8080/api/v1/repository/connect \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "provider": "github",
    "accessToken": "ghp_YOUR_TOKEN_HERE"
  }'
```

**Expected:** `{"success":true,"message":"Successfully connected...","provider":"github"}`

### Test 3: Browse Repository
```bash
curl -X POST http://localhost:8080/api/v1/repository/browse \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "owner": "OAI",
    "repo": "OpenAPI-Specification",
    "path": "examples",
    "branch": "main"
  }'
```

**Expected:** JSON with list of files

### Test 4: Read File
```bash
curl -X POST http://localhost:8080/api/v1/repository/file \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "owner": "OAI",
    "repo": "OpenAPI-Specification",
    "path": "examples/v3.0/petstore.yaml"
  }'
```

**Expected:** JSON with file content

## Success Criteria

✅ **Phase 1 & 2 Complete if:**

1. ✅ "Import from GitHub" button visible in toolbar
2. ✅ Modal opens when button clicked
3. ✅ Can connect to GitHub with token
4. ✅ Can browse repository files
5. ✅ Can navigate folders
6. ✅ OpenAPI specs are highlighted with badge
7. ✅ Clicking spec file loads content into editor
8. ✅ Editor shows imported spec content
9. ✅ Left panel updates with API structure

## Next Steps After Successful Testing

1. **Test with Your Own Repositories**
   - Private repositories (requires `repo` scope)
   - Organizations repositories
   - Different OpenAPI spec structures

2. **Test Edge Cases**
   - Large spec files
   - Nested directory structures
   - Non-standard file names
   - YAML vs JSON formats

3. **Report Issues**
   - Note any errors in console
   - Check logs in all three terminals
   - Document steps to reproduce

4. **Ready for Phase 3?**
   - Once basic flow works, we can implement:
     - AI context from repository
     - Multi-spec analysis
     - Pattern detection

## Common Test Repositories

Use these public repos for testing:

1. **OpenAPI Examples**
   - `https://github.com/OAI/OpenAPI-Specification`
   - Path: `examples/v3.0/` or `examples/v3.1/`

2. **Swagger Petstore**
   - `https://github.com/swagger-api/swagger-petstore`
   - Root folder has `openapi.yaml`

3. **Stripe API**
   - `https://github.com/stripe/openapi`
   - File: `openapi/spec3.yaml`

4. **GitHub API**
   - `https://github.com/github/rest-api-description`
   - Path: `descriptions/api.github.com/`

## Video Walkthrough (What You Should See)

1. **Start**: Editor toolbar with Import button
2. **Click**: Modal opens with GitHub connection form
3. **Connect**: Enter token, click Connect → Green success message
4. **Browse**: Enter repo URL → File tree appears
5. **Navigate**: Click folders → Contents update
6. **Select**: Click spec file → Loading spinner
7. **Success**: Modal closes → Spec appears in editor → Endpoints appear in left panel

## Need Help?

If testing fails:

1. Check all three terminal windows for errors
2. Verify all prerequisites are met
3. Try manual API testing section
4. Check browser console for errors
5. Review logs in:
   - AI Service (Terminal 2)
   - API Gateway (Terminal 3)
   - Browser DevTools Console (F12)

## Success! 🎉

If you successfully imported a spec from GitHub into the editor, congratulations! The Phase 1 & 2 implementation is working. You can now:

- Import specs from any public GitHub repository
- Browse repository structures
- Load OpenAPI specifications directly into the editor
- Edit them with AI assistance using existing features

The foundation is ready for Phase 3 (AI Context Enhancement) and Phase 4 (Advanced Features).
