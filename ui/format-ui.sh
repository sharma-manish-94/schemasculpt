#!/bin/bash
# Format React/TypeScript code using Prettier and ESLint

set -e

echo "⚛️  Formatting React/TypeScript code..."

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run ESLint with auto-fix
echo "🔧 Running ESLint..."
npm run lint 2>/dev/null || npx eslint "src/**/*.{js,jsx,ts,tsx}" --fix --max-warnings=0 || echo "⚠️  ESLint found some issues (see above)"

# Run Prettier
echo "🎨 Running Prettier..."
npx prettier --write "src/**/*.{js,jsx,ts,tsx,json,css,scss}" --tab-width 2 --print-width 80

echo ""
echo "✓ UI formatting complete!"
echo ""
echo "To check formatting without applying changes:"
echo "  npx prettier --check \"src/**/*.{js,jsx,ts,tsx,json,css,scss}\""
echo "  npx eslint \"src/**/*.{js,jsx,ts,tsx}\""
