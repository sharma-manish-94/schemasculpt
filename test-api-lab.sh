#!/bin/bash

# Test script for API Lab features
# Tests mock server, test case generation, and mock data generation

echo "🧪 Testing API Lab Features"
echo "============================"

# Sample OpenAPI spec for testing
SPEC='{
  "openapi": "3.0.0",
  "info": {
    "title": "Test API",
    "version": "1.0.0"
  },
  "paths": {
    "/users": {
      "get": {
        "summary": "List users",
        "responses": {
          "200": {
            "description": "Success",
            "content": {
              "application/json": {
                "schema": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "properties": {
                      "id": { "type": "integer" },
                      "name": { "type": "string" },
                      "email": { "type": "string", "format": "email" }
                    }
                  }
                }
              }
            }
          }
        }
      },
      "post": {
        "summary": "Create user",
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "required": ["name", "email"],
                "properties": {
                  "name": { "type": "string" },
                  "email": { "type": "string", "format": "email" }
                }
              }
            }
          }
        },
        "responses": {
          "201": {
            "description": "Created",
            "content": {
              "application/json": {
                "schema": {
                  "type": "object",
                  "properties": {
                    "id": { "type": "integer" },
                    "name": { "type": "string" },
                    "email": { "type": "string" }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}'

BASE_URL="http://localhost:8000/ai"

echo ""
echo "1️⃣  Testing Test Case Generation..."
echo "-----------------------------------"
curl -X POST "$BASE_URL/tests/generate" \
  -H "Content-Type: application/json" \
  -d "{\"spec_text\": $(echo "$SPEC" | jq -c), \"path\": \"/users\", \"method\": \"POST\", \"include_ai_tests\": false}" \
  2>/dev/null | jq '.total_tests, .happy_path_tests[0].name, .sad_path_tests[0].name' || echo "❌ Failed"

echo ""
echo "2️⃣  Testing Mock Data Generation..."
echo "-----------------------------------"
curl -X POST "$BASE_URL/mock/generate-data" \
  -H "Content-Type: application/json" \
  -d "{\"spec_text\": $(echo "$SPEC" | jq -c), \"path\": \"/users\", \"method\": \"GET\", \"use_ai\": false}" \
  2>/dev/null | jq '.mock_data[0]' || echo "❌ Failed"

echo ""
echo "3️⃣  Testing Mock Data Variations..."
echo "-----------------------------------"
curl -X POST "$BASE_URL/mock/generate-variations" \
  -H "Content-Type: application/json" \
  -d "{\"spec_text\": $(echo "$SPEC" | jq -c), \"path\": \"/users\", \"method\": \"GET\", \"count\": 2}" \
  2>/dev/null | jq '.count, .variations[0].name' || echo "❌ Failed"

echo ""
echo "4️⃣  Testing Mock Server Start..."
echo "-----------------------------------"
curl -X POST "$BASE_URL/mock/start" \
  -H "Content-Type: application/json" \
  -d "{\"spec_text\": $(echo "$SPEC" | jq -c), \"use_ai_responses\": false}" \
  2>/dev/null | jq '.mock_id, .base_url, .total_endpoints' || echo "❌ Failed"

echo ""
echo "✅ API Lab Testing Complete!"
