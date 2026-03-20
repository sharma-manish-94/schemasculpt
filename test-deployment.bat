@echo off
REM SchemaSculpt Full Deployment Test Script (Windows)
REM This script tests the complete Docker Compose deployment

echo ========================================
echo   SchemaSculpt Deployment Test
echo ========================================
echo.

REM Check if Docker is running
echo [INFO] Checking Docker status...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop and try again.
    exit /b 1
)
echo [SUCCESS] Docker is running
echo.

REM Check if Ollama is running (optional)
echo [INFO] Checking Ollama status...
curl -s http://localhost:11434/api/version >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Ollama is running
    set OLLAMA_RUNNING=true
) else (
    echo [WARNING] Ollama is not running. AI features will be limited.
    set OLLAMA_RUNNING=false
)
echo.

REM Ask for confirmation
set /p CONFIRM="Start full deployment? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo [INFO] Deployment cancelled
    exit /b 0
)

echo.
echo [INFO] Building and starting all services...
echo This may take 5-10 minutes on first run...
echo.

docker-compose --profile full up -d --build
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start services
    exit /b 1
)
echo [SUCCESS] All services started
echo.

REM Wait for services to be healthy
echo [INFO] Waiting for services to become healthy (max 60 seconds)...
timeout /t 60 /nobreak >nul
echo.

REM Show service status
echo [INFO] Service Status:
docker-compose --profile full ps
echo.

REM Test PostgreSQL
echo [INFO] Testing PostgreSQL...
docker exec schemasculpt-postgres psql -U postgres -d schemasculpt -c "SELECT version();" >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] PostgreSQL is accessible
) else (
    echo [ERROR] Cannot connect to PostgreSQL
)
echo.

REM Test Redis
echo [INFO] Testing Redis...
docker exec schemasculpt-redis redis-cli PING >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Redis is accessible
) else (
    echo [ERROR] Cannot connect to Redis
)
echo.

REM Test AI Service
echo [INFO] Testing AI Service...
curl -s -o nul -w "%%{http_code}" http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] AI Service is accessible
) else (
    echo [WARNING] AI Service may not be ready yet
)
echo.

REM Test API Gateway
echo [INFO] Testing API Gateway...
curl -s -o nul http://localhost:8080/actuator/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] API Gateway is accessible
) else (
    echo [WARNING] API Gateway may not be ready yet
)
echo.

REM Test UI
echo [INFO] Testing UI...
curl -s -o nul http://localhost:3000/ >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] UI is accessible
) else (
    echo [WARNING] UI may not be ready yet
)
echo.

REM Show resource usage
echo [INFO] Resource Usage:
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" >nul 2>&1
echo.

REM Show access URLs
echo ========================================
echo   Access URLs
echo ========================================
echo   UI:          http://localhost:3000
echo   API Gateway: http://localhost:8080
echo   AI Service:  http://localhost:8000
echo   PostgreSQL:  localhost:5432 (schemasculpt/postgres/postgres)
echo   Redis:       localhost:6379
echo ========================================
echo.

echo [SUCCESS] Deployment test complete!
echo.
echo [INFO] Useful commands:
echo   - View logs:       docker-compose --profile full logs -f
echo   - Stop:            docker-compose --profile full down
echo   - Stop and clean:  docker-compose --profile full down -v
echo.

pause
