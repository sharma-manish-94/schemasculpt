# Phase 1: Database Setup - COMPLETED ✅

## What We've Implemented

### 1. Dependencies Added to `pom.xml`
- ✅ `spring-boot-starter-data-jpa` - JPA/Hibernate support
- ✅ `postgresql` - PostgreSQL driver
- ✅ `flyway-core` + `flyway-database-postgresql` - Database migrations
- ✅ `spring-boot-starter-oauth2-client` - GitHub OAuth support
- ✅ `jjwt-api`, `jjwt-impl`, `jjwt-jackson` - JWT token support

### 2. Database Configuration (`application.properties`)
- ✅ PostgreSQL connection settings
- ✅ JPA/Hibernate configuration
- ✅ Flyway migration settings
- ✅ OAuth2 GitHub client configuration (placeholders)
- ✅ JWT secret configuration (placeholders)

### 3. Database Schema (Flyway Migration)
Created `V1__initial_schema.sql` with:
- ✅ **users** table - GitHub authenticated users
- ✅ **projects** table - User projects
- ✅ **specifications** table - Versioned OpenAPI specs
- ✅ **validation_snapshots** table - Historical validation results
- ✅ All necessary indexes for performance
- ✅ Foreign key constraints and cascading deletes

### 4. JPA Entity Classes
- ✅ `User.java` - User entity with GitHub OAuth fields
- ✅ `Project.java` - Project entity with user relationship
- ✅ `Specification.java` - Versioned specification entity
- ✅ `ValidationSnapshot.java` - Validation history entity

### 5. Repository Interfaces
- ✅ `UserRepository.java` - User data access
- ✅ `ProjectRepository.java` - Project data access
- ✅ `SpecificationRepository.java` - Specification data access with custom queries
- ✅ `ValidationSnapshotRepository.java` - Validation history data access

### 6. Helper Scripts
- ✅ `setup-database.sh` - Automated PostgreSQL database setup script

---

## 📋 Next Steps - Before Starting Spring Boot

### Step 1: Install and Start PostgreSQL

**Option A: Using Docker (Recommended)**
```bash
docker run --name schemasculpt-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=schemasculpt \
  -p 5432:5432 \
  -d postgres:15
```

**Option B: Using System PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS (Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Then run the setup script
./setup-database.sh
```

### Step 2: Verify PostgreSQL is Running
```bash
# Check if PostgreSQL is running
pg_isready

# Connect to the database
psql -U postgres -d schemasculpt

# Inside psql, check tables (after first Spring Boot run):
\dt
```

### Step 3: Set Environment Variables (Optional)
```bash
# For development, create a .env file or export:
export DB_PASSWORD=postgres
export GITHUB_CLIENT_ID=your-github-client-id
export GITHUB_CLIENT_SECRET=your-github-client-secret
export JWT_SECRET=your-secret-key-min-256-bits
```

### Step 4: Build and Test
```bash
cd api

# Clean and compile (this will download new dependencies)
./mvnw clean compile

# Expected output:
# - Dependencies downloaded
# - Compilation successful
# - 79 + 4 new entity files = 83 files compiled
```

### Step 5: Start Spring Boot
```bash
# Start the application
./mvnw spring-boot:run

# Expected logs:
# - Flyway migrating schema...
# - V1__initial_schema.sql executed successfully
# - Tables created: users, projects, specifications, validation_snapshots
# - Application started on port 8080
```

### Step 6: Verify Database Schema
```bash
# Connect to database
psql -U postgres -d schemasculpt

# Check tables were created
\dt

# Expected output:
# public | projects              | table | postgres
# public | specifications        | table | postgres
# public | users                 | table | postgres
# public | validation_snapshots  | table | postgres
# public | flyway_schema_history | table | postgres

# Check table structure
\d users
\d projects
\d specifications
```

---

## 🚨 Common Issues & Solutions

### Issue 1: PostgreSQL not running
**Error:** `org.postgresql.util.PSQLException: Connection refused`
**Solution:** Start PostgreSQL using one of the methods above

### Issue 2: Database doesn't exist
**Error:** `FATAL: database "schemasculpt" does not exist`
**Solution:**
```bash
# Create manually
createdb -U postgres schemasculpt

# Or run setup script
./setup-database.sh
```

### Issue 3: Permission denied
**Error:** `FATAL: role "postgres" does not exist`
**Solution:**
```bash
# Create postgres user
sudo -u postgres createuser --superuser $USER

# Or use docker (no permissions needed)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres:15
```

### Issue 4: Port 5432 already in use
**Error:** `Port 5432 is already in use`
**Solution:**
```bash
# Check what's using the port
lsof -i :5432

# Stop existing PostgreSQL
brew services stop postgresql
# OR
sudo systemctl stop postgresql

# OR use different port in application.properties
spring.datasource.url=jdbc:postgresql://localhost:5433/schemasculpt
```

### Issue 5: Flyway migration fails
**Error:** `FlywayException: Validate failed`
**Solution:**
```bash
# Reset database (WARNING: deletes all data)
psql -U postgres -c "DROP DATABASE schemasculpt;"
psql -U postgres -c "CREATE DATABASE schemasculpt;"

# Restart Spring Boot (Flyway will recreate tables)
./mvnw spring-boot:run
```

---

## ✅ Validation Checklist

Before moving to Phase 2, verify:

- [ ] PostgreSQL is installed and running
- [ ] Database `schemasculpt` exists
- [ ] Spring Boot compiles without errors
- [ ] Spring Boot starts successfully
- [ ] Flyway migration V1 executes successfully
- [ ] 4 tables created: users, projects, specifications, validation_snapshots
- [ ] Can connect to database: `psql -U postgres -d schemasculpt`
- [ ] No errors in Spring Boot console logs

---

## 📊 Database Schema Diagram

```
┌─────────────┐
│   users     │
│─────────────│
│ id (PK)     │
│ github_id   │◄──────┐
│ username    │       │
│ email       │       │
│ avatar_url  │       │
└─────────────┘       │
                      │
                      │
┌─────────────┐       │
│  projects   │       │
│─────────────│       │
│ id (PK)     │       │
│ user_id (FK)├───────┘
│ name        │
│ description │
│ is_public   │◄──────┐
└─────────────┘       │
                      │
                      │
┌──────────────────┐  │
│ specifications   │  │
│──────────────────│  │
│ id (PK)          │  │
│ project_id (FK)  ├──┘
│ version          │
│ spec_content     │
│ spec_format      │
│ commit_message   │
│ is_current       │◄──────┐
│ created_by (FK)  │       │
└──────────────────┘       │
                           │
                           │
┌──────────────────────┐   │
│ validation_snapshots │   │
│──────────────────────│   │
│ id (PK)              │   │
│ specification_id(FK) ├───┘
│ errors (JSONB)       │
│ suggestions (JSONB)  │
└──────────────────────┘
```

---

## 🎯 What's Next: Phase 2 - GitHub OAuth

Once database is working, we'll implement:
1. Security configuration with OAuth2
2. GitHub login flow
3. JWT token generation
4. User authentication
5. Protected API endpoints

---

## 📝 Files Modified/Created

**Modified:**
- `api/pom.xml` - Added dependencies
- `api/src/main/resources/application.properties` - Database & OAuth config

**Created:**
- `api/src/main/resources/db/migration/V1__initial_schema.sql`
- `api/src/main/java/.../entity/User.java`
- `api/src/main/java/.../entity/Project.java`
- `api/src/main/java/.../entity/Specification.java`
- `api/src/main/java/.../entity/ValidationSnapshot.java`
- `api/src/main/java/.../repository/UserRepository.java`
- `api/src/main/java/.../repository/ProjectRepository.java`
- `api/src/main/java/.../repository/SpecificationRepository.java`
- `api/src/main/java/.../repository/ValidationSnapshotRepository.java`
- `setup-database.sh`

**Total:** 2 modified, 10 new files

---

Ready to continue with Phase 2 (GitHub OAuth) once database is verified! 🚀
