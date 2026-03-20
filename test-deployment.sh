#!/bin/bash

# SchemaSculpt Full Deployment Test Script
# This script tests the complete Docker Compose deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emoji for better visibility
SUCCESS="✅"
FAILED="❌"
WARNING="⚠️"
INFO="ℹ️"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SchemaSculpt Deployment Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored messages
print_success() {
    echo -e "${GREEN}${SUCCESS} $1${NC}"
}

print_error() {
    echo -e "${RED}${FAILED} $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}${WARNING} $1${NC}"
}

print_info() {
    echo -e "${BLUE}${INFO} $1${NC}"
}

# Function to check if Docker is running
check_docker() {
    print_info "Checking Docker status..."
    if ! docker ps > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if Ollama is running (optional)
check_ollama() {
    print_info "Checking Ollama status..."
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        print_success "Ollama is running"
        OLLAMA_RUNNING=true
    else
        print_warning "Ollama is not running. AI features will be limited."
        OLLAMA_RUNNING=false
    fi
}

# Function to build and start services
build_and_start() {
    print_info "Building and starting all services..."
    echo "This may take 5-10 minutes on first run..."

    if docker-compose --profile full up -d --build; then
        print_success "All services started"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Function to wait for services to be healthy
wait_for_health() {
    print_info "Waiting for services to become healthy..."
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        local status=$(docker-compose --profile full ps --format json | jq -r '.[].Health' | grep -v "healthy" | wc -l)

        if [ "$status" -eq "0" ]; then
            print_success "All services are healthy"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    print_warning "Some services may not be healthy yet"
    docker-compose --profile full ps
}

# Function to test PostgreSQL
test_postgres() {
    print_info "Testing PostgreSQL..."

    if docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "SELECT version();" > /dev/null 2>&1; then
        print_success "PostgreSQL is accessible"

        # Check for Flyway migrations
        local table_count=$(docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" | xargs)

        if [ "$table_count" -gt "0" ]; then
            print_success "Database tables created (count: $table_count)"
        else
            print_warning "No tables found - migrations may not have run"
        fi
    else
        print_error "Cannot connect to PostgreSQL"
        return 1
    fi
}

# Function to test Redis
test_redis() {
    print_info "Testing Redis..."

    if docker exec schemasculpt-redis redis-cli PING | grep -q "PONG"; then
        print_success "Redis is accessible"
    else
        print_error "Cannot connect to Redis"
        return 1
    fi
}

# Function to test AI Service
test_ai_service() {
    print_info "Testing AI Service..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

    if [ "$response" = "200" ]; then
        print_success "AI Service is accessible (HTTP $response)"
    else
        print_warning "AI Service returned HTTP $response"
        if [ "$OLLAMA_RUNNING" = false ]; then
            print_info "This may be expected since Ollama is not running"
        fi
    fi
}

# Function to test API Gateway
test_api() {
    print_info "Testing API Gateway..."

    # Try health endpoint
    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/actuator/health 2>/dev/null)

    if [ "$response" = "200" ]; then
        print_success "API Gateway is accessible (HTTP $response)"
    else
        # Try alternative endpoint
        response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/ 2>/dev/null)
        if [ "$response" = "200" ] || [ "$response" = "404" ]; then
            print_success "API Gateway is accessible (HTTP $response)"
        else
            print_warning "API Gateway returned HTTP $response"
        fi
    fi
}

# Function to test UI
test_ui() {
    print_info "Testing UI..."

    local response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/)

    if [ "$response" = "200" ]; then
        print_success "UI is accessible (HTTP $response)"
    else
        print_warning "UI returned HTTP $response"
    fi
}

# Function to show service status
show_status() {
    echo ""
    print_info "Service Status:"
    docker-compose --profile full ps
}

# Function to show resource usage
show_resources() {
    echo ""
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" $(docker ps --filter "name=schemasculpt" -q)
}

# Function to show access URLs
show_urls() {
    echo ""
    print_info "Access URLs:"
    echo -e "  ${GREEN}UI:${NC}          http://localhost:3000"
    echo -e "  ${GREEN}API Gateway:${NC} http://localhost:8080"
    echo -e "  ${GREEN}AI Service:${NC}  http://localhost:8000"
    echo -e "  ${GREEN}PostgreSQL:${NC}  localhost:5432 (schemasculpt/postgres/postgres)"
    echo -e "  ${GREEN}Redis:${NC}       localhost:6379"
}

# Main execution
main() {
    check_docker
    check_ollama

    echo ""
    read -p "Start full deployment? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        build_and_start
        wait_for_health

        echo ""
        echo -e "${BLUE}Running service tests...${NC}"
        echo ""

        test_postgres
        test_redis
        test_ai_service
        test_api
        test_ui

        show_status
        show_resources
        show_urls

        echo ""
        print_success "Deployment test complete!"
        echo ""
        print_info "To view logs: docker-compose --profile full logs -f"
        print_info "To stop: docker-compose --profile full down"
        print_info "To stop and remove data: docker-compose --profile full down -v"
        echo ""
    else
        print_info "Deployment cancelled"
    fi
}

# Run main function
main
