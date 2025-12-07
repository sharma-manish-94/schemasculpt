# Debugging CORS Error - Repository Integration

## Common CORS Issues & Fixes

### Issue 1: Preflight Request Failing

**Symptoms:**
- Browser console shows: `Access to XMLHttpRequest has been blocked by CORS policy`
- Network tab shows OPTIONS request in red

**Solution - Check AI Service CORS:**

The AI service might not be allowing the API Gateway's requests. Let me verify:

1. **Check AI Service is running:**
```bash
curl http://localhost:8000/
```

Expected: Should return JSON with service info

2. **Check AI Service allows requests:**
```bash
curl -X OPTIONS http://localhost:8000/api/repository/connect \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Session-ID, Content-Type" \
  -v
```

Expected: Should see `Access-Control-Allow-Origin` in response headers

### Issue 2: AI Service Not Started

**Check AI Service logs:**
```bash
# In the terminal running AI service, you should see:
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

If not running:
```bash
cd ai_service
source venv/bin/activate
uvicorn app.main:app --reload
```

### Issue 3: Missing X-Session-ID Header

**Check browser Network tab:**
1. Open DevTools (F12)
2. Go to Network tab
3. Try connecting to GitHub again
4. Look for request to `/api/v1/repository/connect`
5. Click on it and check "Headers" tab
6. Under "Request Headers", verify `X-Session-ID` is present

If missing, the session might not be created properly.

## Detailed Debugging Steps

### Step 1: Verify All Services

```bash
# Test UI → API Gateway
curl http://localhost:8080/api/v1/sessions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"specText": "{}"}' \
  -v

# Test API Gateway → AI Service
curl http://localhost:8000/ -v

# Test AI Service health
curl http://localhost:8000/api/repository/health \
  -H "X-Session-ID: test-123" \
  -v
```

### Step 2: Check Browser Console Error

Open browser DevTools (F12) and look for exact error message. Common patterns:

**Pattern 1: CORS Preflight**
```
Access to XMLHttpRequest at 'http://localhost:8080/api/v1/repository/connect'
from origin 'http://localhost:3000' has been blocked by CORS policy:
Response to preflight request doesn't pass access control check
```

**Fix:** Already handled in WebConfig.java, but restart API Gateway:
```bash
cd api
./mvnw spring-boot:run
```

**Pattern 2: Network Error**
```
POST http://localhost:8080/api/v1/repository/connect net::ERR_CONNECTION_REFUSED
```

**Fix:** API Gateway not running. Start it:
```bash
cd api
./mvnw spring-boot:run
```

**Pattern 3: 500 Internal Server Error**
```
POST http://localhost:8080/api/v1/repository/connect 500 (Internal Server Error)
```

**Fix:** Check API Gateway logs for stack trace. Likely AI service not responding.

### Step 3: Test Direct AI Service Call

```bash
curl -X POST http://localhost:8000/api/repository/connect \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{
    "provider": "github",
    "accessToken": "ghp_YOUR_TOKEN"
  }' \
  -v
```

**Expected response:**
```json
{
  "success": true,
  "message": "Successfully connected to github",
  "provider": "github"
}
```

**If this fails:**
- Check MCP is installed: `pip show mcp`
- Check Node.js is installed: `node --version`
- Check AI service logs for errors

### Step 4: Check Network Tab Details

In browser:
1. F12 → Network tab
2. Try connecting to GitHub
3. Find the failing request
4. Click on it
5. Check:
   - **Status Code**: Should be 200, not 0 or 4xx/5xx
   - **Request Headers**: Should include `X-Session-ID`, `Content-Type`
   - **Response Headers**: Should include `Access-Control-Allow-Origin`
   - **Response**: Error message if any

## Quick Fix: Restart Everything

Sometimes services get into a bad state:

```bash
# Stop everything
pkill -f uvicorn
pkill -f spring-boot
# Stop Redis if needed
docker stop schemasculpt-redis

# Start fresh
docker start schemasculpt-redis

# Terminal 1: AI Service
cd ai_service
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: API Gateway
cd api
./mvnw spring-boot:run

# Terminal 3: UI
cd ui
npm start
```

Wait for all services to fully start (look for "started" messages).

## Still Getting CORS Error?

### Verify AI Service CORS in main.py

The AI service should have this CORS configuration:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Let me check if this is correct...
