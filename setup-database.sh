#!/bin/bash

# Database setup script for SchemaSculpt
# This script creates the PostgreSQL database and user

echo "================================================"
echo "  SchemaSculpt Database Setup"
echo "================================================"
echo ""

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "❌ PostgreSQL is not running!"
    echo "Please start PostgreSQL first:"
    echo "  - Ubuntu/Debian: sudo systemctl start postgresql"
    echo "  - macOS (Homebrew): brew services start postgresql"
    echo "  - Docker: docker run --name schemasculpt-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15"
    exit 1
fi

echo "✅ PostgreSQL is running"
echo ""

# Default values
DB_NAME="schemasculpt"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Create database
echo "Creating database: $DB_NAME"
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists (this is OK)"

# Grant privileges
echo "Granting privileges..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null

echo ""
echo "================================================"
echo "  ✅ Database Setup Complete!"
echo "================================================"
echo ""
echo "Database Configuration:"
echo "  - Host: localhost"
echo "  - Port: 5432"
echo "  - Database: $DB_NAME"
echo "  - Username: $DB_USER"
echo "  - Password: $DB_PASSWORD"
echo ""
echo "To connect:"
echo "  psql -U $DB_USER -d $DB_NAME"
echo ""
echo "Spring Boot will automatically run Flyway migrations on startup."
echo ""
