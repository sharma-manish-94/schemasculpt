# Full Deployment Testing Guide

This guide walks you through testing the complete Docker Compose deployment of SchemaSculpt.

## Prerequisites

Before starting, ensure:

1. **Docker Desktop is running** (check system tray - whale icon should be steady)
2. **Ollama is running locally** (optional for initial infrastructure test)
   ```bash
   ollama serve
   ollama pull mistral
   ```

---

## Step-by-Step Testing Procedure

### Step 1: Clean Slate (Optional)

Start fresh by removing any existing containers and volumes:

```bash
# Stop and remove all SchemaSculpt containers and volumes
docker-compose --profile full down -v

# Verify nothing is running
docker ps -a | grep schemasculpt
```

### Step 2: Build and Start Full Stack

```bash
# Navigate to project root
cd D:\Github\schemasculpt

# Build and start all services (this will take 5-10 minutes first time)
docker-compose --profile full up -d --build
```

**Expected Output:**
```
[+] Building ...
 => [postgres internal] load metadata for docker.io/library/postgres:16-alpine
 => [redis internal] load metadata for docker.io/library/redis:7-alpine
 => [api internal] load build definition from Dockerfile
 => [ai-service internal] load build definition from Dockerfile
 => [ui internal] load build definition from Dockerfile
 ...
[+] Running 5/5
 ✔ Container schemasculpt-postgres      Started
 ✔ Container schemasculpt-redis         Started
 ✔ Container schemasculpt-ai-service    Started
 ✔ Container schemasculpt-api           Started
 ✔ Container schemasculpt-ui            Started
```

### Step 3: Monitor Startup

Watch logs as services start up:

```bash
# Follow all logs
docker-compose --profile full logs -f

# Or follow specific service
docker-compose logs -f api
docker-compose logs -f ai-service
docker-compose logs -f ui
```

**What to look for:**

**PostgreSQL:**
```
database system is ready to accept connections
```

**Redis:**
```
Ready to accept connections
```

**AI Service:**
```
Uvicorn running on http://0.0.0.0:8000
Application startup complete
```

**API Gateway:**
```
Flyway: Migrating schema...
Flyway: Successfully applied 2 migrations
Started SchemaSculptApplication in X seconds
```

**UI:**
```
/docker-entrypoint.sh: Launching /docker-entrypoint.d/...
Nginx started successfully
```

### Step 4: Verify Service Health

Check that all services are healthy:

```bash
docker-compose --profile full ps
```

**Expected Output:**
```
NAME                          STATUS                    PORTS
schemasculpt-postgres         Up (healthy)              0.0.0.0:5432->5432/tcp
schemasculpt-redis            Up (healthy)              0.0.0.0:6379->6379/tcp
schemasculpt-ai-service       Up (healthy)              0.0.0.0:8000->8000/tcp
schemasculpt-api              Up (healthy)              0.0.0.0:8080->8080/tcp
schemasculpt-ui               Up (healthy)              0.0.0.0:3000->80/tcp
```

**All services should show "Up (healthy)"**

If any service shows "unhealthy" or "starting", wait 30-60 seconds and check again. The API service takes longest to start (60-90 seconds) due to Flyway migrations.

### Step 5: Test Service Endpoints

#### 5.1 Test PostgreSQL

```bash
# Connect to PostgreSQL
docker exec -it schemasculpt-postgres psql -U postgres -d schemasculpt

# List tables (should show Flyway migrations)
\dt

# Expected output:
# public | flyway_schema_history
# public | users
# public | projects
# public | specifications
# public | validation_snapshots
# public | operation_test_cases
# public | operation_mock_data
# public | test_data_generation_history

# Exit
\q
```

#### 5.2 Test Redis

```bash
# Connect to Redis
docker exec -it schemasculpt-redis redis-cli

# Test connection
PING
# Expected: PONG

# Check memory usage
INFO memory

# Exit
exit
```

#### 5.3 Test AI Service

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"healthy"} or similar
```

**Note:** If Ollama is not running, the AI service may start but show warnings in logs. This is expected - the service will still respond to health checks.

#### 5.4 Test API Gateway

```bash
# Health check (if Spring Actuator is enabled)
curl http://localhost:8080/actuator/health

# Or test API root
curl http://localhost:8080/api/v1/health

# Expected: 200 OK response
```

#### 5.5 Test UI

Open browser and navigate to:
- **http://localhost:3000**

You should see the SchemaSculpt UI load successfully.

**Check browser console** (F12 → Console) for any errors.

### Step 6: Test Inter-Service Communication

#### 6.1 API → PostgreSQL

```bash
# Check API logs for database connection
docker-compose logs api | grep -i "hikari\|database\|postgres"

# Expected: "HikariPool-1 - Start completed"
```

#### 6.2 API → Redis

```bash
# Check API logs for Redis connection
docker-compose logs api | grep -i "redis"

# Expected: No connection errors
```

#### 6.3 API → AI Service

```bash
# Check API logs for AI service calls
docker-compose logs api | grep -i "ai.*service"

# Check AI service logs for incoming requests
docker-compose logs ai-service | grep -i "request\|endpoint"
```

#### 6.4 AI Service → Ollama (if running)

```bash
# Check AI service logs for Ollama connection
docker-compose logs ai-service | grep -i "ollama"

# Expected (if Ollama running): Successful connection
# Expected (if Ollama NOT running): Connection timeout warnings (this is OK for testing)
```

### Step 7: Test Full Workflow (End-to-End)

If all services are healthy, test a complete workflow:

1. **Open UI**: http://localhost:3000
2. **Create a project** (if authentication is not required) or **Login with GitHub**
3. **Load a sample OpenAPI spec**
4. **Run validation** - Should see real-time feedback
5. **Try AI analysis** (if Ollama is running)

---

## Troubleshooting

### Service Won't Start (Unhealthy)

```bash
# Check specific service logs
docker-compose logs <service-name>

# Common issues:
# - Port conflicts (another service using 3000/8080/8000/5432/6379)
# - Build failures (check build logs)
# - Configuration errors (check environment variables)
```

### API Service Fails to Start

**Common causes:**

1. **Database migration failure:**
   ```bash
   docker-compose logs api | grep -i "flyway\|migration"
   ```

2. **Port 8080 already in use:**
   ```bash
   # Windows
   netstat -ano | findstr :8080

   # Change port in .env.docker
   API_PORT=8081
   ```

3. **Redis connection failure:**
   ```bash
   docker-compose logs api | grep -i "redis\|jedis"
   ```

### AI Service Fails to Start

**Common causes:**

1. **Ollama not accessible:**
   ```bash
   docker-compose logs ai-service | grep -i "ollama"
   ```

   **Solution:** This is expected if Ollama isn't running. The service should still start and be "healthy" but will fail when trying to use LLM features.

2. **Python dependency errors:**
   ```bash
   docker-compose logs ai-service | grep -i "error\|failed"
   ```

3. **Port 8000 already in use:**
   ```bash
   # Change port in .env.docker
   AI_SERVICE_PORT=8001
   ```

### UI Service Fails to Start

**Common causes:**

1. **Build failure:**
   ```bash
   docker-compose logs ui
   ```

2. **Nginx configuration error:**
   ```bash
   docker exec schemasculpt-ui nginx -t
   ```

3. **Port 3000 already in use:**
   ```bash
   # Change port in .env.docker
   UI_PORT=3001
   ```

### Ollama Connection Issues

If the AI service can't connect to Ollama on the host:

1. **Verify Ollama is running:**
   ```bash
   curl http://localhost:11434/api/version
   ```

2. **Check host.docker.internal resolution:**
   ```bash
   docker exec schemasculpt-ai-service ping host.docker.internal
   ```

3. **Alternative:** Run Ollama in Docker (not recommended due to GPU access):
   ```yaml
   # Add to docker-compose.yml
   ollama:
     image: ollama/ollama:latest
     ports:
       - "11434:11434"
     volumes:
       - ollama_data:/root/.ollama
   ```

---

## Performance Benchmarks

**Expected startup times (from cold start):**

| Service | Build Time (First) | Build Time (Cached) | Startup Time |
|---------|-------------------|---------------------|--------------|
| PostgreSQL | 10-20s (pull image) | N/A | 5-10s |
| Redis | 5-10s (pull image) | N/A | 2-5s |
| AI Service | 3-5 min | 10-30s | 30-45s |
| API Gateway | 5-10 min | 30-60s | 60-90s |
| UI | 2-4 min | 20-40s | 5-10s |
| **Total** | **10-20 min** | **1-3 min** | **2-3 min** |

**Resource usage (typical):**

| Service | CPU | Memory | Disk Space |
|---------|-----|--------|------------|
| PostgreSQL | 1-5% | 50-100 MB | 500 MB |
| Redis | 1-2% | 10-30 MB | 100 MB |
| AI Service | 2-10% | 200-500 MB | 1 GB |
| API Gateway | 5-15% | 300-600 MB | 500 MB |
| UI (Nginx) | 1-2% | 10-20 MB | 100 MB |
| **Total** | **10-35%** | **~1 GB** | **~2.2 GB** |

---

## Validation Checklist

Use this checklist to verify successful deployment:

### Infrastructure
- [ ] PostgreSQL container started and healthy
- [ ] Redis container started and healthy
- [ ] Can connect to PostgreSQL (port 5432)
- [ ] Can connect to Redis (port 6379)
- [ ] Database tables created by Flyway migrations
- [ ] Redis accepts PING command

### Application Services
- [ ] AI Service container started and healthy
- [ ] API Gateway container started and healthy
- [ ] UI container started and healthy
- [ ] AI Service accessible on http://localhost:8000
- [ ] API Gateway accessible on http://localhost:8080
- [ ] UI accessible on http://localhost:3000

### Service Communication
- [ ] API can connect to PostgreSQL (check logs)
- [ ] API can connect to Redis (check logs)
- [ ] API can connect to AI Service (check logs)
- [ ] AI Service can connect to Redis (check logs)
- [ ] UI can load in browser without errors
- [ ] UI can communicate with API (check browser console)

### Optional (Ollama)
- [ ] Ollama running on host (port 11434)
- [ ] AI Service can connect to Ollama (check logs)
- [ ] AI features work in UI

---

## Cleanup

### Stop Services (Keep Data)

```bash
docker-compose --profile full down
```

### Stop Services and Delete Data

```bash
docker-compose --profile full down -v
```

### Remove All Images (Free Disk Space)

```bash
docker rmi schemasculpt-api schemasculpt-ai-service schemasculpt-ui
docker image prune -a
```

---

## Next Steps

Once full deployment is verified:

1. **Configure production settings** in `.env.docker`
   - Change `JWT_SECRET`
   - Set strong `DB_PASSWORD`
   - Configure GitHub OAuth credentials

2. **Set up reverse proxy** (Nginx/Traefik) for production
3. **Enable HTTPS** with SSL certificates
4. **Configure monitoring** (Prometheus, Grafana)
5. **Set up automated backups** for PostgreSQL data
6. **Implement CI/CD pipeline** for automated deployments

---

## Support

For issues or questions:
- Check logs: `docker-compose --profile full logs -f`
- Review troubleshooting section above
- See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed configuration
- Report issues: [GitHub Issues](https://github.com/sharma-manish-94/schemasculpt/issues)
