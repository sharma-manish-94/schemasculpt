#!/bin/bash

# Phase 1 Integration Test Script
# Tests all Phase 1 features end-to-end

echo "🧪 Phase 1 Integration Testing"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

print_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED++))
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test 1: Validation Script
print_test "Running Phase 1 validation script..."
cd /home/manish-sharma/Documents/Projects/schemasculpt
if python3 validate-phase1-implementation.py | grep -q "🎉 All Phase 1 components implemented correctly!"; then
    print_pass "All Phase 1 components validated"
else
    print_fail "Phase 1 validation script failed"
fi

# Test 2: Java API Compilation
print_test "Testing Java API compilation..."
cd /home/manish-sharma/Documents/Projects/schemasculpt/api
if ./mvnw compile -q 2>&1 | grep -qE "BUILD SUCCESS|Compilation succeeded"; then
    print_pass "Java API compiles successfully"
elif ./mvnw compile -q 2>/dev/null; then
    print_pass "Java API compiles successfully (warnings ignored)"
else
    print_fail "Java API compilation failed"
fi
cd /home/manish-sharma/Documents/Projects/schemasculpt

# Test 3: AI Service Import
print_test "Testing AI Service imports..."
cd /home/manish-sharma/Documents/Projects/schemasculpt/ai_service
if python3 -c "from app.main import app; print('✅ Import successful')" 2>/dev/null | grep -q "✅ Import successful"; then
    print_pass "AI Service imports successfully"
else
    print_fail "AI Service import failed"
fi
cd /home/manish-sharma/Documents/Projects/schemasculpt

# Test 4: Frontend Build
print_test "Testing Frontend build..."
cd /home/manish-sharma/Documents/Projects/schemasculpt/ui
if npm run build 2>&1 | grep -q "The build folder is ready to be deployed"; then
    print_pass "Frontend builds successfully"
else
    print_fail "Frontend build failed"
fi
cd /home/manish-sharma/Documents/Projects/schemasculpt

# Test 5: Check Critical Phase 1 Files Exist
print_test "Checking critical Phase 1 files..."
CRITICAL_FILES=(
    "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ValidationSuggestion.java"
    "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationRequest.java"
    "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/dto/ExplanationResponse.java"
    "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/HardeningService.java"
    "api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/ai/AIService.java"
    "ai_service/app/api/endpoints.py"
    "ai_service/app/services/rag_service.py"
    "ui/src/components/validation/ValidationSuggestion.js"
    "ui/src/components/demo/Phase1Demo.js"
    "ui/src/api/validationService.js"
)

missing_files=0
for file in "${CRITICAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        print_pass "✓ $file exists"
    else
        print_fail "✗ Missing: $file"
        ((missing_files++))
    fi
done

if [[ $missing_files -eq 0 ]]; then
    print_pass "All critical files present"
else
    print_fail "$missing_files critical files missing"
fi

# Test 6: Check AI Endpoints Implementation
print_test "Checking AI endpoints implementation..."
if grep -q "@router.post(\"/ai/explain\")" ai_service/app/api/endpoints.py; then
    print_pass "AI explain endpoint implemented"
else
    print_fail "AI explain endpoint missing"
fi

if grep -q "@router.post(\"/ai/test-cases/generate\")" ai_service/app/api/endpoints.py; then
    print_pass "AI test case generation endpoint implemented"
else
    print_fail "AI test case generation endpoint missing"
fi

# Test 7: Check Hardening Service Methods
print_test "Checking Hardening Service methods..."
hardening_methods=("applyOAuth2Security" "applyRateLimiting" "applyCaching" "applyIdempotency" "applyValidation" "applyErrorHandling")
for method in "${hardening_methods[@]}"; do
    if grep -q "$method" api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/HardeningService.java; then
        print_pass "✓ $method implemented"
    else
        print_fail "✗ $method missing"
    fi
done

# Test 8: Check Frontend API Services
print_test "Checking Frontend API services..."
frontend_services=("explainValidationIssue" "hardenOperation" "generateTestCases" "addOAuth2Security" "addRateLimiting")
for service in "${frontend_services[@]}"; do
    if grep -q "$service" ui/src/api/validationService.js; then
        print_pass "✓ $service implemented"
    else
        print_fail "✗ $service missing"
    fi
done

# Summary
echo
echo "=============================="
echo "🧪 Integration Test Summary"
echo "=============================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 All Phase 1 integration tests passed!${NC}"
    echo "Phase 1 is ready for functional testing."
    exit 0
else
    echo -e "${RED}⚠️ $FAILED tests failed. Review issues above.${NC}"
    exit 1
fi