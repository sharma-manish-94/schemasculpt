#!/bin/bash
# Format Java code using Spotless (Google Java Format)

set -e

echo "🎨 Formatting Java code with Google Java Format..."
./mvnw spotless:apply

echo "✓ Java code formatted successfully!"
echo ""
echo "To check formatting without applying changes:"
echo "  ./mvnw spotless:check"
echo ""
echo "To run Checkstyle validation:"
echo "  ./mvnw checkstyle:check"
