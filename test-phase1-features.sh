#!/bin/bash

# Phase 1 Features Testing Script
# Tests all implemented features and identifies issues

set -e

echo "🧪 SchemaSculpt Phase 1 Testing Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
ISSUES_FOUND=()

log_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((TESTS_FAILED++))
    ISSUES_FOUND+=("$1")
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if required services are running
check_services() {
    log_test "Checking service availability..."

    # Check Redis
    if ! docker ps | grep -q schemasculpt-redis; then
        log_warn "Redis not running. Starting Redis..."
        docker run -d --name schemasculpt-redis -p 6379:6379 redis || {
            log_fail "Failed to start Redis"
            return 1
        }
        sleep 3
    fi
    log_pass "Redis is running"

    # Check if ports are available
    if ! nc -z localhost 8000 2>/dev/null; then
        log_warn "AI Service (port 8000) not running - some tests will fail"
    else
        log_pass "AI Service is running on port 8000"
    fi

    if ! nc -z localhost 8080 2>/dev/null; then
        log_warn "Backend API (port 8080) not running - some tests will fail"
    else
        log_pass "Backend API is running on port 8080"
    fi

    if ! nc -z localhost 3000 2>/dev/null; then
        log_warn "Frontend (port 3000) not running - manual testing required"
    else
        log_pass "Frontend is running on port 3000"
    fi
}

# Test compilation and basic syntax
test_compilation() {
    log_test "Testing Java compilation..."

    cd api
    if ./mvnw compile -q; then
        log_pass "Java backend compiles successfully"
    else
        log_fail "Java backend compilation failed"
    fi
    cd ..

    log_test "Testing AI Service dependencies..."
    cd ai_service
    if [ -f "requirements.txt" ]; then
        # Check if virtual environment exists
        if [ -d "venv" ]; then
            source venv/bin/activate
            if python -c "import fastapi, pydantic, httpx" 2>/dev/null; then
                log_pass "AI Service dependencies are available"
            else
                log_fail "AI Service dependencies missing"
            fi
            deactivate
        else
            log_warn "AI Service virtual environment not found"
        fi
    fi
    cd ..

    log_test "Testing Frontend dependencies..."
    cd ui
    if [ -f "package.json" ] && [ -d "node_modules" ]; then
        if npm run build > /dev/null 2>&1; then
            log_pass "Frontend builds successfully"
        else
            log_fail "Frontend build failed"
        fi
    else
        log_warn "Frontend dependencies not installed"
    fi
    cd ..
}

# Test API endpoints
test_api_endpoints() {
    log_test "Testing API endpoints..."

    BASE_URL="http://localhost:8080/api/v1"

    # Test health endpoints
    if curl -s "$BASE_URL/explanations/health" | grep -q "healthy"; then
        log_pass "Explanation Controller health check"
    else
        log_fail "Explanation Controller health check failed"
    fi

    # Test hardening patterns endpoint
    if curl -s "$BASE_URL/sessions/dummy/hardening/patterns" | grep -q "patterns"; then
        log_pass "Hardening patterns endpoint accessible"
    else
        log_fail "Hardening patterns endpoint failed"
    fi
}

# Test AI Service endpoints
test_ai_service() {
    log_test "Testing AI Service endpoints..."

    AI_BASE_URL="http://localhost:8000"

    # Test health endpoint
    if curl -s "$AI_BASE_URL/ai/health" | grep -q "status"; then
        log_pass "AI Service health check"
    else
        log_fail "AI Service health check failed"
    fi

    # Test explanation endpoint
    if curl -s -X POST "$AI_BASE_URL/ai/explain" \
        -H "Content-Type: application/json" \
        -d '{"rule_id":"test","message":"test","spec_text":"{}"}' | grep -q "explanation"; then
        log_pass "AI explanation endpoint functional"
    else
        log_fail "AI explanation endpoint failed"
    fi
}

# Check file structure and consistency
check_file_structure() {
    log_test "Checking file structure and consistency..."

    # Check if all implemented files exist
    FILES_TO_CHECK=(
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ValidationSuggestion.java"
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationRequest.java"
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationResponse.java"
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/HardeningService.java"
        "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/controller/HardeningController.java"
        "ui/src/components/validation/ValidationSuggestion.js"
        "ui/src/components/validation/ValidationSuggestion.css"
        "ui/src/components/demo/Phase1Demo.js"
        "ui/src/components/demo/Phase1Demo.css"
    )

    for file in "${FILES_TO_CHECK[@]}"; do
        if [ -f "$file" ]; then
            log_pass "File exists: $(basename $file)"
        else
            log_fail "Missing file: $file"
        fi
    done

    # Check for syntax errors in key files
    log_test "Checking for obvious syntax issues..."

    # Check JavaScript files for basic syntax
    if command -v node >/dev/null 2>&1; then
        for js_file in ui/src/components/validation/ValidationSuggestion.js ui/src/components/demo/Phase1Demo.js; do
            if [ -f "$js_file" ]; then
                if node -c "$js_file" 2>/dev/null; then
                    log_pass "JavaScript syntax OK: $(basename $js_file)"
                else
                    log_fail "JavaScript syntax error in: $js_file"
                fi
            fi
        done
    fi
}

# Test database connections
test_database() {
    log_test "Testing Redis connection..."

    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping | grep -q "PONG"; then
            log_pass "Redis connection successful"
        else
            log_fail "Redis connection failed"
        fi
    else
        log_warn "redis-cli not available - cannot test Redis connection"
    fi
}

# Main testing routine
main() {
    echo
    log_info "Starting Phase 1 comprehensive testing..."
    echo

    check_services
    echo

    test_compilation
    echo

    check_file_structure
    echo

    test_database
    echo

    # Only test API endpoints if services are running
    if nc -z localhost 8080 2>/dev/null; then
        test_api_endpoints
        echo
    fi

    if nc -z localhost 8000 2>/dev/null; then
        test_ai_service
        echo
    fi

    # Summary
    echo "======================================"
    echo "🧪 Test Results Summary"
    echo "======================================"
    log_info "Tests Passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        echo -e "${RED}Tests Failed: $TESTS_FAILED${NC}"
        echo
        echo -e "${RED}Issues Found:${NC}"
        for issue in "${ISSUES_FOUND[@]}"; do
            echo -e "  ${RED}• $issue${NC}"
        done
    else
        echo -e "${GREEN}Tests Failed: 0${NC}"
        echo -e "${GREEN}🎉 All tests passed!${NC}"
    fi
    echo

    # Next steps
    echo "======================================"
    echo "📋 Next Steps for Manual Testing"
    echo "======================================"
    echo "1. Start all services:"
    echo "   docker run -d --name schemasculpt-redis -p 6379:6379 redis"
    echo "   cd ai_service && uvicorn app.main:app --reload"
    echo "   cd api && ./mvnw spring-boot:run"
    echo "   cd ui && npm start"
    echo
    echo "2. Open browser to http://localhost:3000"
    echo "3. Test Phase1Demo component"
    echo "4. Load an OpenAPI spec and test features"
    echo
    echo "📝 Report any issues found during manual testing"
}

# Run main function
main