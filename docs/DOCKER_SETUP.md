# Docker Setup Guide

This guide explains how to use Docker Compose to run SchemaSculpt services in different configurations.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Modes](#deployment-modes)
- [Configuration](#configuration)
- [Data Management](#data-management)
- [Troubleshooting](#troubleshooting)
- [Developer Workflow](#developer-workflow)
- [Useful Commands](#useful-commands)

---

## Overview

SchemaSculpt supports two deployment modes using Docker Compose profiles:

### Development Mode (Default)
**Infrastructure only** - For active development with live code reloading:

**Runs in Docker:**
- PostgreSQL 16 (Database)
- Redis 7 (Cache & Session Storage)

**Runs Locally:**
- UI (React on port 3000) - hot reload enabled
- API (Spring Boot on port 8080) - hot reload enabled
- AI Service (FastAPI on port 8000) - hot reload enabled
- Ollama (LLM on port 11434)

**Command:** `docker-compose up -d`

### Full Deployment Mode
**Complete stack** - For testing, demos, or production deployment:

**Runs in Docker:**
- PostgreSQL 16 (Database)
- Redis 7 (Cache & Session Storage)
- AI Service (Python/FastAPI container)
- API Gateway (Java/Spring Boot container)
- UI (React/Nginx container)

**Runs Locally:**
- Ollama (LLM on port 11434) - connects via `host.docker.internal`

**Command:** `docker-compose --profile full up -d`

This flexible approach provides:
- **Dev Mode**: Fast iteration with live code reloading
- **Full Mode**: One-command deployment of entire stack
- Data persistence across restarts
- Consistent environment across developers

---

## Prerequisites

**Required:**
- Docker Desktop 4.0+ (Windows/Mac) or Docker Engine 20.10+ (Linux)
- Docker Compose 2.0+ (included with Docker Desktop)

**For Application Services:**
- Java 21+
- Python 3.10+
- Node.js 18+
- Ollama

**Verify Installation:**
```bash
docker --version
docker-compose --version
```

---

## Quick Start

### 1. Start Infrastructure

```bash
# From project root
docker-compose up -d
```

This starts PostgreSQL and Redis with:
- Health checks to ensure services are ready
- Named volumes for data persistence
- Ports exposed to localhost for local services

### 2. Verify Services

```bash
# Check service status
docker-compose ps

# Expected output:
# NAME                      STATUS                    PORTS
# schemasculpt-postgres     Up (healthy)              0.0.0.0:5432->5432/tcp
# schemasculpt-redis        Up (healthy)              0.0.0.0:6379->6379/tcp
```

### 3. View Logs

```bash
# Follow logs for all services
docker-compose logs -f

# Follow logs for specific service
docker-compose logs -f postgres
docker-compose logs -f redis
```

### 4. Start Application Services

See the main [README.md](../README.md) for instructions on starting the API, AI Service, and UI locally.

---

## Deployment Modes

### Quick Reference

| Aspect | Development Mode | Full Deployment Mode |
|--------|------------------|---------------------|
| **Command** | `docker-compose up -d` | `docker-compose --profile full up -d --build` |
| **Docker Services** | PostgreSQL, Redis | PostgreSQL, Redis, API, AI Service, UI |
| **Local Services** | UI, API, AI Service, Ollama | Ollama only |
| **Hot Reload** | ✅ Yes | ❌ No (rebuild needed) |
| **Use Case** | Active development | Testing, demos, deployment |
| **Build Time** | ~10 seconds | ~5-10 minutes (first time) |
| **Resource Usage** | Low | Medium-High |
| **Debugging** | Full IDE support | Container logs only |

---

### Development Mode (Default)

**Use case:** Active development with hot code reloading

**Start services:**
```bash
# Infrastructure only
docker-compose up -d

# Then start application services locally (separate terminals):
cd api && ./gradlew bootRun
cd ai_service && uvicorn app.main:app --reload
cd ui && npm start

# Ensure Ollama is running
ollama serve
```

**Benefits:**
- Instant code changes without rebuilding containers
- Full debugging capabilities in your IDE
- Faster iteration cycle
- Lower resource usage

**Services running:**
- Docker: PostgreSQL, Redis
- Local: UI (3000), API (8080), AI Service (8000), Ollama (11434)

---

### Full Deployment Mode

**Use case:** Testing complete stack, demos, staging, or production deployment

**Prerequisites:**
1. Ensure Ollama is running on your host machine:
   ```bash
   ollama serve
   ollama pull mistral
   ```

2. Configure environment variables in `.env.docker`:
   ```bash
   # Required for full mode
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   JWT_SECRET=your_secure_secret
   ```

**Start all services:**
```bash
# Build and start everything (first time)
docker-compose --profile full up -d --build

# Subsequent starts (no rebuild)
docker-compose --profile full up -d
```

**Verify all services:**
```bash
docker-compose --profile full ps

# Expected output:
# NAME                          STATUS                    PORTS
# schemasculpt-postgres         Up (healthy)              0.0.0.0:5432->5432/tcp
# schemasculpt-redis            Up (healthy)              0.0.0.0:6379->6379/tcp
# schemasculpt-ai-service       Up (healthy)              0.0.0.0:8000->8000/tcp
# schemasculpt-api              Up (healthy)              0.0.0.0:8080->8080/tcp
# schemasculpt-ui               Up (healthy)              0.0.0.0:3000->80/tcp
```

**Access the application:**
- UI: http://localhost:3000
- API: http://localhost:8080
- AI Service: http://localhost:8000

**View logs:**
```bash
# All services
docker-compose --profile full logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ai-service
docker-compose logs -f ui
```

**Stop all services:**
```bash
docker-compose --profile full down
```

**Benefits:**
- One-command deployment
- Consistent environment across machines
- Production-like testing
- Easy to share with team (Docker images)
- No local Node/Java/Python setup needed

**Rebuilding after code changes:**
```bash
# Rebuild specific service
docker-compose --profile full up -d --build api

# Rebuild all services
docker-compose --profile full up -d --build
```

---

## Configuration

### Environment Variables

Infrastructure configuration is managed in `.env.docker`:

```bash
# Default configuration
DB_PASSWORD=postgres

# Optional overrides (uncomment to use)
# POSTGRES_DB=schemasculpt
# POSTGRES_USER=postgres
# POSTGRES_PORT=5432
# REDIS_PORT=6379
```

**Local Overrides:**

For machine-specific settings, create `.env.docker.local` (gitignored):

```bash
# .env.docker.local (example)
DB_PASSWORD=my_secure_password
POSTGRES_PORT=15432  # Use different port
```

### Port Configuration

**Default Ports:**
- PostgreSQL: `5432`
- Redis: `6379`

**Changing Ports (if conflicts occur):**

1. Edit `docker-compose.yml`:
   ```yaml
   postgres:
     ports:
       - "15432:5432"  # Host:Container
   ```

2. Update API configuration in `api/src/main/resources/application.properties`:
   ```properties
   spring.datasource.url=jdbc:postgresql://localhost:15432/schemasculpt
   ```

3. Update AI Service configuration:
   ```bash
   # Set environment variable
   export REDIS_URL=redis://localhost:16379
   ```

### Service Configuration

**PostgreSQL:**
- Image: `postgres:16-alpine`
- Database: `schemasculpt`
- User: `postgres`
- Password: From `DB_PASSWORD` env var (default: `postgres`)
- Data location: Docker volume `schemasculpt_postgres_data`

**Redis:**
- Image: `redis:7-alpine`
- Persistence: AOF (Append-Only File)
- Max Memory: 256MB
- Eviction Policy: `allkeys-lru` (Least Recently Used)
- Data location: Docker volume `schemasculpt_redis_data`

---

## Data Management

### Data Persistence

Data is stored in Docker named volumes:
- `schemasculpt_postgres_data` - PostgreSQL database files
- `schemasculpt_redis_data` - Redis persistence files

**These volumes persist even when containers are stopped or removed.**

### Backup Database

**PostgreSQL:**
```bash
# Backup to SQL file
docker exec schemasculpt-postgres pg_dump -U postgres schemasculpt > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec schemasculpt-postgres pg_dump -U postgres schemasculpt | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
```

**Redis:**
```bash
# Redis uses AOF persistence automatically
# To manually save current state:
docker exec schemasculpt-redis redis-cli BGSAVE

# Copy RDB file from container
docker cp schemasculpt-redis:/data/dump.rdb ./redis_backup_$(date +%Y%m%d_%H%M%S).rdb
```

### Restore Database

**PostgreSQL:**
```bash
# From SQL file
cat backup.sql | docker exec -i schemasculpt-postgres psql -U postgres -d schemasculpt

# From compressed file
gunzip -c backup.sql.gz | docker exec -i schemasculpt-postgres psql -U postgres -d schemasculpt
```

**Redis:**
```bash
# Stop Redis
docker-compose stop redis

# Copy RDB file to container
docker cp redis_backup.rdb schemasculpt-redis:/data/dump.rdb

# Start Redis
docker-compose start redis
```

### Inspect Volumes

```bash
# List all volumes
docker volume ls | grep schemasculpt

# Inspect volume details
docker volume inspect schemasculpt_postgres_data
docker volume inspect schemasculpt_redis_data

# View volume location on host
docker volume inspect schemasculpt_postgres_data --format='{{.Mountpoint}}'
```

### Reset Database (Delete All Data)

```bash
# WARNING: This deletes all data permanently!

# Stop and remove containers AND volumes
docker-compose down -v

# Restart with fresh databases
docker-compose up -d
```

---

## Troubleshooting

### Service Not Starting

**Check logs:**
```bash
docker-compose logs postgres
docker-compose logs redis
```

**Common issues:**
- Port already in use → Change port in `docker-compose.yml`
- Permission issues → Ensure Docker has access to volumes directory
- Insufficient memory → Adjust Docker Desktop memory settings

### Port Already in Use

**Find process using port:**

Windows:
```cmd
netstat -ano | findstr :5432
```

Linux/Mac:
```bash
lsof -i :5432
```

**Solution:** Either stop the conflicting service or change the Docker port mapping.

### Connection Tests

**PostgreSQL:**
```bash
# Test connection
docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "SELECT version();"

# Connect to PostgreSQL CLI
docker exec -it schemasculpt-postgres psql -U postgres -d schemasculpt

# Common psql commands:
# \dt          - List tables
# \d tablename - Describe table
# \q           - Quit
```

**Redis:**
```bash
# Test connection
docker exec schemasculpt-redis redis-cli ping
# Expected: PONG

# Connect to Redis CLI
docker exec -it schemasculpt-redis redis-cli

# Common Redis commands:
# PING         - Test connection
# KEYS *       - List all keys (use carefully in production)
# GET key      - Get value
# INFO         - Server info
# exit         - Quit
```

### Health Check Failing

**PostgreSQL health check:**
```bash
docker exec schemasculpt-postgres pg_isready -U postgres -d schemasculpt
```

**Redis health check:**
```bash
docker exec schemasculpt-redis redis-cli ping
```

### API Cannot Connect to Database

**Verify PostgreSQL is running:**
```bash
docker-compose ps postgres
```

**Check API configuration:**
Ensure `api/src/main/resources/application.properties` has:
```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/schemasculpt
spring.datasource.username=postgres
spring.datasource.password=postgres  # Or your custom password
```

**Check Flyway migrations:**
```bash
# Start API and look for Flyway logs
cd api
./gradlew bootRun

# Expected logs:
# "Flyway: Migrating schema..."
# "Flyway: Successfully applied 2 migrations"
```

### Viewing Database Schema

```bash
# List all tables
docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "\dt"

# View table structure
docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "\d users"

# Count records
docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "SELECT COUNT(*) FROM users;"
```

---

## Developer Workflow

### Daily Development

**Start infrastructure:**
```bash
docker-compose up -d
```

**Start application services (in separate terminals):**
```bash
# Terminal 1: API
cd api
./gradlew bootRun

# Terminal 2: AI Service
cd ai_service
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload

# Terminal 3: UI
cd ui
npm start

# Ensure Ollama is running
ollama serve
```

**End of day:**
```bash
# Stop infrastructure (data persists)
docker-compose down

# Or leave running - Docker containers use minimal resources when idle
```

### Fresh Start

**Complete reset (deletes all data):**
```bash
docker-compose down -v
docker-compose up -d
```

### Updating Services

**Pull latest images:**
```bash
docker-compose pull
docker-compose up -d
```

**Rebuild services:**
```bash
docker-compose up -d --build
```

---

## Useful Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services (preserves data)
docker-compose down

# Stop services and delete data
docker-compose down -v

# Restart services
docker-compose restart

# Restart specific service
docker-compose restart postgres
```

### Monitoring

```bash
# View running containers
docker-compose ps

# View resource usage
docker stats schemasculpt-postgres schemasculpt-redis

# Follow logs
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### Database Access

```bash
# PostgreSQL CLI
docker exec -it schemasculpt-postgres psql -U postgres -d schemasculpt

# Redis CLI
docker exec -it schemasculpt-redis redis-cli

# Execute SQL file
docker exec -i schemasculpt-postgres psql -U postgres -d schemasculpt < script.sql
```

### Cleanup

```bash
# Remove stopped containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove unused volumes
docker volume prune

# Remove unused images
docker image prune
```

---

## Production Considerations

For production deployment, consider:

1. **Security:**
   - Use strong passwords (set in environment variables)
   - Enable Redis authentication
   - Don't expose ports to public network
   - Use Docker secrets for sensitive data

2. **Networking:**
   - Remove port mappings (services communicate via Docker network)
   - Use `docker-compose.prod.yml` for production overrides

3. **Performance:**
   - Increase Redis max memory
   - Tune PostgreSQL configuration
   - Use connection pooling

4. **Backup:**
   - Automated daily backups
   - Store backups off-server
   - Test restore procedures

5. **Monitoring:**
   - Add health check endpoints
   - Integrate with monitoring tools (Prometheus, Grafana)
   - Set up alerting

Example production override:
```yaml
# docker-compose.prod.yml
services:
  postgres:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}  # Required from env
    # Don't expose port
    ports: []

  redis:
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 512mb
    ports: []
```

---

## Getting Help

- **Project Issues:** [GitHub Issues](https://github.com/sharma-manish-94/schemasculpt/issues)
- **Docker Documentation:** [docs.docker.com](https://docs.docker.com/)
- **PostgreSQL Documentation:** [postgresql.org/docs](https://www.postgresql.org/docs/)
- **Redis Documentation:** [redis.io/docs](https://redis.io/docs/)

For main setup instructions, see [README.md](../README.md)
