#!/bin/bash

# Test script to verify AI service integration with Spring Boot

echo "🔍 Testing AI Service Integration..."

# Test 1: Check AI service health
echo -e "\n1. Testing AI Service Health:"
AI_HEALTH=$(curl -s http://localhost:8000/ai/health)
if [[ $? -eq 0 ]]; then
    echo "✅ AI Service is accessible"
    echo "   Status: $(echo $AI_HEALTH | jq -r '.status' 2>/dev/null || echo 'unknown')"
else
    echo "❌ AI Service is not accessible at http://localhost:8000"
    exit 1
fi

# Test 2: Check Spring Boot health
echo -e "\n2. Testing Spring Boot Health:"
SPRING_HEALTH=$(curl -s http://localhost:8080/api/v1/ai/health)
if [[ $? -eq 0 ]]; then
    echo "✅ Spring Boot AI endpoint is accessible"
    echo "   Response: $(echo $SPRING_HEALTH | jq -r '.status' 2>/dev/null || echo 'unknown')"
else
    echo "❌ Spring Boot AI endpoint is not accessible at http://localhost:8080"
    exit 1
fi

# Test 3: Test AI processing through Spring Boot
echo -e "\n3. Testing AI Processing through Spring Boot:"
AI_PROCESS_RESPONSE=$(curl -s -X POST http://localhost:8080/api/v1/ai/process \
    -H "Content-Type: application/json" \
    -d '{
        "spec_text": "{\"openapi\": \"3.0.3\", \"info\": {\"title\": \"Test API\", \"version\": \"1.0.0\"}}",
        "prompt": "Add a description to this API",
        "operation_type": "modify"
    }')

if [[ $? -eq 0 ]]; then
    SUCCESS=$(echo $AI_PROCESS_RESPONSE | jq -r '.success' 2>/dev/null)
    if [[ "$SUCCESS" == "true" ]]; then
        echo "✅ AI Processing successful through Spring Boot"
        echo "   Operation: $(echo $AI_PROCESS_RESPONSE | jq -r '.operation_type' 2>/dev/null)"
        echo "   Processing Time: $(echo $AI_PROCESS_RESPONSE | jq -r '.processing_time_ms' 2>/dev/null)ms"
        echo "   Model Used: $(echo $AI_PROCESS_RESPONSE | jq -r '.model_used' 2>/dev/null)"
    else
        echo "❌ AI Processing failed"
        echo "   Error: $(echo $AI_PROCESS_RESPONSE | jq -r '.error_message' 2>/dev/null)"
        echo "   Full Response: $AI_PROCESS_RESPONSE"
        exit 1
    fi
else
    echo "❌ Failed to connect to Spring Boot AI processing endpoint"
    exit 1
fi

echo -e "\n🎉 All integration tests passed! The AI service integration is working correctly."