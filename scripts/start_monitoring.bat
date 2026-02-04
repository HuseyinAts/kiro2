@echo off
REM Start Monitoring Stack - Windows
REM Video API Monitoring - Task 19

echo.
echo ========================================
echo Teknofest Video API Monitoring Stack
echo ========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [INFO] Please update .env with your Slack webhook URL and SMTP credentials
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating directories...
if not exist monitoring\alertmanager mkdir monitoring\alertmanager
if not exist backend\config mkdir backend\config
if not exist backend\docs mkdir backend\docs

REM Stop existing containers
echo [INFO] Stopping existing monitoring containers...
docker-compose -f docker-compose.monitoring.yml down

REM Build Prometheus exporter image
echo [INFO] Building Prometheus exporter image...
docker-compose -f docker-compose.monitoring.yml build prometheus-exporter

REM Start monitoring stack
echo [INFO] Starting monitoring services...
docker-compose -f docker-compose.monitoring.yml up -d

REM Wait for services to be healthy
echo [INFO] Waiting for services to be healthy...
timeout /t 10 /nobreak >nul

REM Check service health
echo [INFO] Checking service health...
echo.

docker-compose -f docker-compose.monitoring.yml ps

echo.
echo ========================================
echo Monitoring Stack Started Successfully!
echo ========================================
echo.
echo Access URLs:
echo   - Prometheus:    http://localhost:9090
echo   - Alertmanager:  http://localhost:9093
echo   - Grafana:       http://localhost:3000 (admin/admin)
echo   - Metrics:       http://localhost:9091/metrics
echo.
echo Grafana Dashboards:
echo   - Video API Dashboard: http://localhost:3000/d/video-api
echo   - Database Dashboard:  http://localhost:3000/d/database
echo.
echo Alert Channels:
echo   - Slack: #backend-youtube-api, #backend-critical, #backend-health
echo   - Email: backend-team@teknofest-egitim.com
echo.
echo Documentation:
echo   - Setup Guide: backend\docs\MONITORING_ALERTING_SETUP.md
echo.
echo Next Steps:
echo   1. Open Grafana and import dashboards
echo   2. Configure Slack webhook URL in .env
echo   3. Test alerts: curl http://localhost:9093/api/v1/alerts
echo   4. Start backend application to generate metrics
echo.
echo To view logs: docker-compose -f docker-compose.monitoring.yml logs -f
echo To stop: docker-compose -f docker-compose.monitoring.yml down
echo.

pause
