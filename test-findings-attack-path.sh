#!/bin/bash
# Test script for the new Linter-Augmented AI Analyst attack path feature

set -e

echo "═══════════════════════════════════════════════════════════"
echo " Testing Linter-Augmented AI Analyst - Attack Path Analysis"
echo "═══════════════════════════════════════════════════════════"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="${BASE_URL:-http://localhost:8080}"
SESSION_ID="${SESSION_ID:-test-session}"

echo ""
echo -e "${BLUE}Step 1: Create a test session with a vulnerable spec${NC}"
echo "-------------------------------------------------------------"

# Create a vulnerable OpenAPI spec for testing
SPEC_CONTENT=$(cat <<'EOF'
{
  "openapi": "3.0.0",
  "info": {
    "title": "Vulnerable API",
    "version": "1.0.0"
  },
  "paths": {
    "/users/all": {
      "get": {
        "summary": "Get all users (PUBLIC!)",
        "responses": {
          "200": {
            "description": "List of users",
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/User"
                }
              }
            }
          }
        }
      }
    },
    "/users/{id}": {
      "put": {
        "summary": "Update user",
        "parameters": [
          {
            "name": "id",
            "in": "path",
            "required": true,
            "schema": {
              "type": "string"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/User"
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "User updated"
          }
        }
      }
    }
  },
  "components": {
    "schemas": {
      "User": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string"
          },
          "name": {
            "type": "string"
          },
          "email": {
            "type": "string"
          },
          "role": {
            "type": "string",
            "description": "User role: user, admin, superadmin"
          }
        }
      }
    }
  }
}
EOF
)

# Create session
echo "Creating session..."
curl -X POST "${BASE_URL}/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d "{\"specContent\": $(echo "$SPEC_CONTENT" | jq -c .)}" \
  -s | jq '.'

echo ""
echo -e "${BLUE}Step 2: Run OLD approach (may timeout with large specs)${NC}"
echo "-------------------------------------------------------------"
echo "Endpoint: POST ${BASE_URL}/api/v1/sessions/${SESSION_ID}/analysis/attack-path-simulation"
echo ""
echo "⏱️  This sends the ENTIRE spec to the AI service..."
echo ""

START_TIME=$(date +%s)
curl -X POST "${BASE_URL}/api/v1/sessions/${SESSION_ID}/analysis/attack-path-simulation?analysisDepth=quick" \
  -H "Content-Type: application/json" \
  -s -w "\nHTTP Status: %{http_code}\n" || true
END_TIME=$(date +%s)
OLD_DURATION=$((END_TIME - START_TIME))
echo "⏱️  Duration: ${OLD_DURATION} seconds"

echo ""
echo -e "${GREEN}Step 3: Run NEW approach (Linter-Augmented AI Analyst)${NC}"
echo "-------------------------------------------------------------"
echo "Endpoint: POST ${BASE_URL}/api/v1/sessions/${SESSION_ID}/analysis/attack-path-findings"
echo ""
echo "✅ This sends ONLY the factual findings (tiny payload)"
echo ""

START_TIME=$(date +%s)
RESPONSE=$(curl -X POST "${BASE_URL}/api/v1/sessions/${SESSION_ID}/analysis/attack-path-findings?analysisDepth=quick" \
  -H "Content-Type: application/json" \
  -s -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

END_TIME=$(date +%s)
NEW_DURATION=$((END_TIME - START_TIME))

echo ""
echo "Response:"
echo "$BODY" | jq '.'

echo ""
echo "HTTP Status: $HTTP_STATUS"
echo "⏱️  Duration: ${NEW_DURATION} seconds"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}Performance Comparison${NC}"
echo "═══════════════════════════════════════════════════════════"
echo "OLD approach: ${OLD_DURATION}s (sends full 5MB spec)"
echo "NEW approach: ${NEW_DURATION}s (sends only findings)"
if [ $NEW_DURATION -lt $OLD_DURATION ]; then
  IMPROVEMENT=$((100 - (NEW_DURATION * 100 / OLD_DURATION)))
  echo -e "${GREEN}✅ NEW approach is ${IMPROVEMENT}% faster!${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "${GREEN}Expected AI Analysis${NC}"
echo "═══════════════════════════════════════════════════════════"
echo "The AI should identify the following attack chain:"
echo ""
echo "🔴 CRITICAL: Privilege Escalation via Mass Assignment"
echo ""
echo "Chain:"
echo "1. Attacker calls public GET /users/all (no security)"
echo "2. Attacker obtains User schema including 'role' field"
echo "3. Attacker crafts payload: {\"role\": \"admin\"}"
echo "4. Attacker calls PUT /users/{id} with admin role"
echo "5. Result: Regular user escalates to admin privileges!"
echo ""
echo "═══════════════════════════════════════════════════════════"
