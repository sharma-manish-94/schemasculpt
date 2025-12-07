#!/bin/bash

# =====================================================================
# SchemaSculpt AI Service - Complete Setup Script
# =====================================================================
# This script sets up the AI service with all dependencies and
# initializes the knowledge base for RAG functionality.
#
# Usage: ./setup_ai_service.sh
# =====================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    print_error "Please run this script from the ai_service directory"
    exit 1
fi

print_header "SchemaSculpt AI Service Setup"

# =====================================================================
# Step 1: Check Python version
# =====================================================================
print_header "Step 1: Checking Python version"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python 3.10+ is required (found $PYTHON_VERSION)"
    exit 1
fi

print_success "Python $PYTHON_VERSION detected"

# =====================================================================
# Step 2: Create virtual environment
# =====================================================================
print_header "Step 2: Creating virtual environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual environment recreated"
    else
        print_info "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
source venv/bin/activate
print_success "Virtual environment activated"

# =====================================================================
# Step 3: Upgrade pip and setuptools
# =====================================================================
print_header "Step 3: Upgrading pip and setuptools"

pip install --upgrade pip setuptools wheel
print_success "pip and setuptools upgraded"

# =====================================================================
# Step 4: Install core dependencies
# =====================================================================
print_header "Step 4: Installing core dependencies"

print_info "Installing base requirements..."
pip install -r requirements.txt

print_success "Core dependencies installed"

# =====================================================================
# Step 5: Install MCP SDK (optional)
# =====================================================================
print_header "Step 5: Installing MCP SDK (optional)"

print_info "Attempting to install MCP SDK..."
print_info "Note: This may fail - that's OK, repository features will just be disabled"

# Try to install MCP SDK
if pip install mcp --pre 2>/dev/null; then
    print_success "MCP SDK installed successfully"
else
    print_warning "MCP SDK installation failed (this is optional)"
    print_info "To enable repository features later:"
    print_info "  1. pip install mcp --pre"
    print_info "  2. npm install -g @modelcontextprotocol/server-github"
fi

# =====================================================================
# Step 6: Verify dependencies
# =====================================================================
print_header "Step 6: Verifying dependencies"

print_info "Checking critical dependencies..."

# Check FastAPI
if python -c "import fastapi" 2>/dev/null; then
    print_success "FastAPI: OK"
else
    print_error "FastAPI: NOT FOUND"
    exit 1
fi

# Check httpx
if python -c "import httpx" 2>/dev/null; then
    print_success "httpx: OK"
else
    print_error "httpx: NOT FOUND"
    exit 1
fi

# Check ChromaDB
if python -c "import chromadb" 2>/dev/null; then
    print_success "ChromaDB: OK"
    CHROMADB_OK=true
else
    print_warning "ChromaDB: NOT FOUND (RAG features will be disabled)"
    CHROMADB_OK=false
fi

# Check sentence-transformers
if python -c "import sentence_transformers" 2>/dev/null; then
    print_success "sentence-transformers: OK"
    SENT_TRANS_OK=true
else
    print_warning "sentence-transformers: NOT FOUND"
    SENT_TRANS_OK=false
fi

# Check MCP
if python -c "import mcp" 2>/dev/null; then
    print_success "MCP SDK: OK (repository features enabled)"
else
    print_warning "MCP SDK: NOT FOUND (repository features disabled)"
fi

# =====================================================================
# Step 7: Create necessary directories
# =====================================================================
print_header "Step 7: Creating directories"

mkdir -p vector_store
mkdir -p knowledge_base
mkdir -p logs
mkdir -p data

print_success "Directories created"

# =====================================================================
# Step 8: Initialize knowledge base
# =====================================================================
print_header "Step 8: Initializing knowledge base"

if [ "$CHROMADB_OK" = true ] && [ "$SENT_TRANS_OK" = true ]; then
    print_info "ChromaDB and sentence-transformers are available"
    print_info "Initializing knowledge base..."

    if [ -f "scripts/init_knowledge_base.py" ]; then
        if python scripts/init_knowledge_base.py; then
            print_success "Knowledge base initialized successfully"
        else
            print_warning "Knowledge base initialization had issues (check output above)"
            print_info "You can retry later with: python scripts/init_knowledge_base.py"
        fi
    else
        print_warning "Initialization script not found"
        print_info "Knowledge base will be empty until initialized"
    fi
else
    print_warning "Cannot initialize knowledge base (missing dependencies)"
    print_info "Install missing packages and run: python scripts/init_knowledge_base.py"
fi

# =====================================================================
# Step 9: Create .env file if it doesn't exist
# =====================================================================
print_header "Step 9: Configuring environment"

if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success ".env file created from template"
        print_info "Please review and update .env with your settings"
    else
        print_warning ".env.example not found, creating basic .env"
        cat > .env << EOF
# AI Service Configuration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=mistral
AI_SERVICE_DATA_DIR=./data
LOG_LEVEL=INFO

# Repository Features (optional)
GITHUB_TOKEN=your_github_token_here
EOF
        print_success "Basic .env file created"
    fi
else
    print_info ".env file already exists"
fi

# =====================================================================
# Step 10: Check Ollama
# =====================================================================
print_header "Step 10: Checking Ollama"

if command -v ollama &> /dev/null; then
    print_success "Ollama command found"

    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama service is running"

        # Check for mistral model
        if ollama list | grep -q "mistral"; then
            print_success "Mistral model is available"
        else
            print_warning "Mistral model not found"
            print_info "Run: ollama pull mistral"
        fi
    else
        print_warning "Ollama service is not running"
        print_info "Start Ollama or ensure it's running in the background"
    fi
else
    print_warning "Ollama not found in PATH"
    print_info "Install from: https://ollama.com"
fi

# =====================================================================
# Summary
# =====================================================================
print_header "Setup Complete!"

echo -e "${GREEN}✅ Setup completed successfully${NC}\n"

echo "Summary:"
echo "--------"
echo "Core dependencies: ✅ Installed"
echo "MCP SDK: $(python -c 'import mcp; print("✅ Available")' 2>/dev/null || echo "⚠️  Not available (optional)")"
echo "ChromaDB: $(python -c 'import chromadb; print("✅ Available")' 2>/dev/null || echo "⚠️  Not available")"
echo "Knowledge base: $([ -d "vector_store" ] && [ "$(ls -A vector_store 2>/dev/null)" ] && echo "✅ Initialized" || echo "⚠️  Empty")"

echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Review and update .env file if needed"
echo "2. Ensure Ollama is running: ollama serve (or check if already running)"
echo "3. Pull required model: ollama pull mistral"
echo "4. Start the AI service: uvicorn app.main:app --reload"

echo -e "\n${BLUE}Troubleshooting:${NC}"
echo "- If MCP features fail: pip install mcp --pre"
echo "- If RAG features fail: python scripts/init_knowledge_base.py"
echo "- Check logs: tail -f logs/ai_service.log"

echo -e "\n${GREEN}🎉 Ready to go!${NC}\n"
