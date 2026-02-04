@echo off
echo ====================================
echo Teknofest 2025 - Production Deployment
echo ====================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Docker is running...

echo [2/4] Building and starting services...
docker-compose -f docker-compose.production.yml up -d --build

if errorlevel 1 (
    echo ERROR: Deployment failed!
    pause
    exit /b 1
)

echo [3/4] Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak >nul

echo [4/4] Checking service status...
docker-compose -f docker-compose.production.yml ps

echo.
echo ====================================
echo DEPLOYMENT COMPLETE!
echo ====================================
echo.
echo Access points:
echo - Frontend: https://localhost (accept self-signed certificate)
echo - API Health: https://localhost/health
echo - Grafana: http://localhost:3001
echo   Username: admin
echo   Password: GrafanaAdmin_494b68f7
echo - Prometheus: http://localhost:9090
echo.
echo To view logs: docker-compose -f docker-compose.production.yml logs -f
echo To stop: docker-compose -f docker-compose.production.yml down
echo.
pause