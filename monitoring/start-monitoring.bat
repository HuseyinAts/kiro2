@echo off
REM Monitoring Stack Startup Script (Windows)
REM Teknofest 2025 - Eğitim Eylemci Projesi

echo.
echo Starting Monitoring Stack...
echo ================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running. Please start Docker first.
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo WARNING: .env file not found. Creating from example...
    (
        echo # Slack Webhook URL for alerts
        echo SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
        echo.
        echo # Email configuration for critical alerts
        echo SMTP_USERNAME=your-email@gmail.com
        echo SMTP_PASSWORD=your-app-password
        echo.
        echo # Grafana admin password
        echo GRAFANA_PASSWORD=teknofest2025
    ) > .env
    echo .env file created. Please update with your credentials.
)

REM Create necessary directories
echo Creating directories...
if not exist prometheus\alerts mkdir prometheus\alerts
if not exist grafana\provisioning\datasources mkdir grafana\provisioning\datasources
if not exist grafana\provisioning\dashboards mkdir grafana\provisioning\dashboards
if not exist grafana\dashboards mkdir grafana\dashboards
if not exist alertmanager mkdir alertmanager

REM Start monitoring stack
echo Starting Docker containers...
docker-compose -f docker-compose.monitoring.yml up -d

REM Wait for services to be ready
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check service health
echo Checking service health...

curl -s http://localhost:9090/-/healthy >nul 2>&1
if errorlevel 1 (
    echo Prometheus is not responding
) else (
    echo Prometheus is healthy
)

curl -s http://localhost:3000/api/health >nul 2>&1
if errorlevel 1 (
    echo Grafana is not responding
) else (
    echo Grafana is healthy
)

curl -s http://localhost:9093/-/healthy >nul 2>&1
if errorlevel 1 (
    echo Alertmanager is not responding
) else (
    echo Alertmanager is healthy
)

echo.
echo ================================
echo Monitoring Stack Started!
echo ================================
echo.
echo Access URLs:
echo   - Grafana:      http://localhost:3000
echo   - Prometheus:   http://localhost:9090
echo   - Alertmanager: http://localhost:9093
echo.
echo Grafana Credentials:
echo   - Username: admin
echo   - Password: teknofest2025
echo.
echo Dashboard:
echo   Navigate to: Dashboards -^> Browse -^> Video API -^> Video API Monitoring Dashboard
echo.
echo View logs:
echo   docker-compose -f docker-compose.monitoring.yml logs -f
echo.
echo Stop monitoring:
echo   docker-compose -f docker-compose.monitoring.yml down
echo.
pause
