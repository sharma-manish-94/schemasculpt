#!/bin/bash

echo "======================================"
echo "Repository Integration Diagnostic Test"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if AI Service is running
echo "Test 1: Checking AI Service..."
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ AI Service is running${NC}"
else
    echo -e "${RED}✗ AI Service is NOT running${NC}"
    echo "  Start it with: cd ai_service && source venv/bin/activate && uvicorn app.main:app --reload"
    exit 1
fi
echo ""

# Test 2: Check if API Gateway is running
echo "Test 2: Checking API Gateway..."
if curl -s http://localhost:8080/actuator/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API Gateway is running${NC}"
else
    echo -e "${RED}✗ API Gateway is NOT running${NC}"
    echo "  Start it with: cd api && ./mvnw spring-boot:run"
    exit 1
fi
echo ""

# Test 3: Check Redis
echo "Test 3: Checking Redis..."
if docker ps | grep schemasculpt-redis > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠ Redis might not be running${NC}"
    echo "  Start it with: docker run -d --name schemasculpt-redis -p 6379:6379 redis"
fi
echo ""

# Test 4: Check MCP installation
echo "Test 4: Checking MCP installation..."
if [ -f "ai_service/venv/bin/python" ]; then
    if ai_service/venv/bin/python -c "import mcp" 2>/dev/null; then
        echo -e "${GREEN}✓ MCP is installed${NC}"
    else
        echo -e "${RED}✗ MCP is NOT installed${NC}"
        echo "  Install it with: cd ai_service && source venv/bin/activate && pip install mcp aiofiles"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ Cannot find venv${NC}"
fi
echo ""

# Test 5: Check Node.js (required for MCP GitHub server)
echo "Test 5: Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✓ Node.js is installed ($NODE_VERSION)${NC}"
else
    echo -e "${RED}✗ Node.js is NOT installed${NC}"
    echo "  MCP GitHub server requires Node.js 16+"
    exit 1
fi
echo ""

# Test 6: Test AI Service health endpoint
echo "Test 6: Testing AI Service health endpoint..."
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/repository/health -H "X-Session-ID: test-123")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
BODY=$(echo "$HEALTH_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Health endpoint responding (HTTP $HTTP_CODE)${NC}"
    echo "  Response: $BODY"
else
    echo -e "${RED}✗ Health endpoint failed (HTTP $HTTP_CODE)${NC}"
    echo "  Response: $BODY"
fi
echo ""

# Test 7: Test API Gateway connect endpoint (without actual token)
echo "Test 7: Testing API Gateway repository endpoint..."
CONNECT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST http://localhost:8080/api/v1/repository/connect \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: test-session-123" \
  -d '{"provider":"github","accessToken":"dummy"}' 2>&1)
HTTP_CODE=$(echo "$CONNECT_RESPONSE" | tail -n1)
BODY=$(echo "$CONNECT_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ API Gateway endpoint is accessible (HTTP $HTTP_CODE)${NC}"
    echo "  Response: $BODY"
    if echo "$BODY" | grep -q "success.*false"; then
        echo -e "${YELLOW}  Note: Connection failed (expected with dummy token)${NC}"
    fi
else
    echo -e "${RED}✗ API Gateway endpoint failed (HTTP $HTTP_CODE)${NC}"
    echo "  Response: $BODY"
fi
echo ""

# Test 8: CORS headers test
echo "Test 8: Testing CORS headers..."
CORS_RESPONSE=$(curl -s -I -X OPTIONS http://localhost:8000/api/repository/connect \
  -H "Origin: http://localhost:8080" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: X-Session-ID, Content-Type")

if echo "$CORS_RESPONSE" | grep -i "access-control-allow-origin" > /dev/null; then
    echo -e "${GREEN}✓ CORS headers are present${NC}"
    echo "$CORS_RESPONSE" | grep -i "access-control"
else
    echo -e "${RED}✗ CORS headers missing${NC}"
    echo "  AI Service might need to be restarted"
fi
echo ""

echo "======================================"
echo "Diagnostic Complete"
echo "======================================"
echo ""
echo "If all tests pass but you still get CORS error in browser:"
echo "1. Check browser console (F12) for exact error message"
echo "2. Check Network tab to see which request is failing"
echo "3. Try hard refresh (Ctrl+Shift+R)"
echo "4. Check that sessionId is being sent in headers"
echo ""
echo "Common issues:"
echo "- Session not created: Make sure you opened a project first"
echo "- Invalid token: Get a fresh token from GitHub"
echo "- Port conflict: Make sure nothing else is running on 8000/8080"
