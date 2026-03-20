#!/bin/bash

# Quick health check script for SchemaSculpt deployment
# Usage: ./check-health.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SUCCESS="✅"
FAILED="❌"
WARNING="⚠️"

echo -e "${BLUE}SchemaSculpt Health Check${NC}"
echo "=========================="
echo ""

# Check Docker
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}${SUCCESS} Docker${NC} is running"
else
    echo -e "${RED}${FAILED} Docker${NC} is not running"
    exit 1
fi

# Check each service
services=("schemasculpt-postgres" "schemasculpt-redis" "schemasculpt-ai-service" "schemasculpt-api" "schemasculpt-ui")

for service in "${services[@]}"; do
    if docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
        # Check health status
        health=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null || echo "unknown")

        if [ "$health" = "healthy" ]; then
            echo -e "${GREEN}${SUCCESS} $service${NC} is healthy"
        elif [ "$health" = "starting" ]; then
            echo -e "${YELLOW}${WARNING} $service${NC} is starting..."
        elif [ "$health" = "unknown" ]; then
            echo -e "${GREEN}${SUCCESS} $service${NC} is running (no health check)"
        else
            echo -e "${RED}${FAILED} $service${NC} is unhealthy"
        fi
    else
        echo -e "${RED}${FAILED} $service${NC} is not running"
    fi
done

echo ""
echo "Service Endpoints:"
echo "==================="

# Test endpoints
endpoints=(
    "PostgreSQL|localhost:5432|docker exec schemasculpt-postgres pg_isready -U postgres"
    "Redis|localhost:6379|docker exec schemasculpt-redis redis-cli PING"
    "AI Service|http://localhost:8000|curl -sf http://localhost:8000/health"
    "API Gateway|http://localhost:8080|curl -sf http://localhost:8080/actuator/health"
    "UI|http://localhost:3000|curl -sf http://localhost:3000/"
)

for endpoint in "${endpoints[@]}"; do
    IFS='|' read -r name url cmd <<< "$endpoint"

    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "${GREEN}${SUCCESS} $name${NC} - $url"
    else
        echo -e "${RED}${FAILED} $name${NC} - $url (not accessible)"
    fi
done

echo ""
echo "Quick Commands:"
echo "==============="
echo "View logs:        docker-compose --profile full logs -f [service]"
echo "Restart service:  docker-compose --profile full restart [service]"
echo "Stop all:         docker-compose --profile full down"
echo ""
