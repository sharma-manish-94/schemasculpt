#!/bin/bash
# Format all code in the SchemaSculpt project

set -e

echo "🎨 Formatting SchemaSculpt codebase..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Format Java (Backend API)
echo -e "\n${BLUE}📝 Formatting Java code...${NC}"
cd api
./gradlew spotlessApply
echo -e "${GREEN}✓ Java code formatted${NC}"
cd ..

# Format Python (AI Service)
echo -e "\n${BLUE}🐍 Formatting Python code...${NC}"
cd ai_service
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install formatters if not present
pip install -q black isort flake8

# Format Python
black .
isort .
echo -e "${GREEN}✓ Python code formatted${NC}"

# Deactivate virtual environment if activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi
cd ..

# Format JavaScript/TypeScript (Frontend)
echo -e "\n${BLUE}⚛️  Formatting JavaScript/TypeScript code...${NC}"
cd ui
npm run format 2>/dev/null || npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,scss}" --tab-width 2 --print-width 80
echo -e "${GREEN}✓ JavaScript/TypeScript code formatted${NC}"
cd ..

echo -e "\n${GREEN}✨ All code formatted successfully!${NC}"
echo -e "${BLUE}💡 Tip: Install pre-commit hooks to auto-format on commit:${NC}"
echo -e "   pip install pre-commit && pre-commit install"
