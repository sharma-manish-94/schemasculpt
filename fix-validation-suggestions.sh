#!/bin/bash

# Script to fix ValidationSuggestion constructor calls
echo "🔧 Fixing ValidationSuggestion constructor calls..."

LINTER_DIR="api/src/main/java/io/github/sharma_manish_94/schemasculpt_api/service/linter"

# Files that need fixing
FILES=(
    "HttpsOnlyRule.java"
    "MissingDescriptionRule.java"
    "MissingOperationIdRule.java"
    "OperationTagsRule.java"
    "PathNamingRule.java"
    "ResponseSuccessRule.java"
    "SchemaNamingConventionRule.java"
    "UnusedComponentRule.java"
)

# Fix pattern: Replace old constructor with new one
for file in "${FILES[@]}"; do
    if [ -f "$LINTER_DIR/$file" ]; then
        echo "Fixing $file..."

        # First, let's see what needs to be fixed
        if grep -q "new ValidationSuggestion(" "$LINTER_DIR/$file"; then
            echo "  Found ValidationSuggestion calls in $file - manual fix needed"
        fi
    else
        echo "  File not found: $file"
    fi
done

echo "Manual fixes required for the remaining files."