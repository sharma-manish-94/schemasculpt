#!/bin/bash
# Format Python code using Black and isort

set -e

echo "🐍 Formatting Python code..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install formatters if not present
echo "📦 Checking dependencies..."
pip install -q black isort flake8

# Format with Black
echo "🎨 Running Black formatter..."
black .

# Sort imports with isort
echo "📋 Sorting imports with isort..."
isort .

# Check with flake8
echo "🔍 Running flake8 linter..."
flake8 . || echo "⚠️  Flake8 found some issues (see above)"

# Deactivate virtual environment if activated
if [ -n "$VIRTUAL_ENV" ]; then
    deactivate
fi

echo ""
echo "✓ Python formatting complete!"
echo ""
echo "To check formatting without applying changes:"
echo "  black --check ."
echo "  isort --check-only ."
