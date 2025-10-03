#!/bin/bash

# Quick fix for ValidationSuggestion constructor calls
echo "🔧 Quick fixing ValidationSuggestion constructors..."

LINTER_DIR="api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/linter"

# Create backup
echo "Creating backup..."
cp -r "$LINTER_DIR" "${LINTER_DIR}_backup"

# Fix the 3-parameter constructor calls (message, ruleId, Map<String, Object>)
echo "Fixing 3-parameter constructors..."
find "$LINTER_DIR" -name "*.java" -exec sed -i 's/new ValidationSuggestion(\([^,]*\),\s*\([^,]*\),\s*Map\.of([^)]*)\s*)/new ValidationSuggestion(\1, \2, "warning", "general", Map.of(), true)/g' {} \;

# Fix the simple 1-parameter constructor calls (message only)
echo "Fixing 1-parameter constructors..."
find "$LINTER_DIR" -name "*.java" -exec sed -i 's/new ValidationSuggestion(\([^)]*\))/new ValidationSuggestion(\1, null, "info", "general", Map.of(), true)/g' {} \;

echo "✅ Quick fixes applied. Please review and adjust severity/category as needed."