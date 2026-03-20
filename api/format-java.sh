#!/bin/bash
# Format Java code using Spotless (Google Java Format)

set -e

echo "🎨 Formatting Java code with Google Java Format..."
./gradlew spotlessApply

echo "✓ Java code formatted successfully!"
echo ""
echo "To check formatting without applying changes:"
echo "  ./gradlew spotlessCheck"
echo ""
echo "To run Checkstyle validation:"
echo "  ./gradlew check"
