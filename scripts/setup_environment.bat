@echo off
REM Environment Setup Script for Windows
REM Sets up the complete development/production environment

echo ========================================================================
echo Turkiye Universite Sinavlari Hazirlık Platformu - Environment Setup
echo ========================================================================
echo.

REM Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from .env.example...
    copy .env.example .env
    echo [SUCCESS] .env file created. Please edit it with your actual values!
    echo.
    echo Required API keys:
    echo   - YOUTUBE_API_KEY ^(Get from: https://console.cloud.google.com/apis/credentials^)
    echo   - OPENAI_API_KEY ^(Get from: https://platform.openai.com/api-keys^)
    echo   - SECRET_KEY ^(Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"^)
    echo   - JWT_SECRET_KEY ^(Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"^)
    echo.
    pause
)

echo [INFO] Step 1: Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

echo [SUCCESS] Docker and Docker Compose are installed
echo.

echo [INFO] Step 2: Starting PostgreSQL...
docker-compose up -d postgres
echo [SUCCESS] PostgreSQL started
echo.

echo [INFO] Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul

echo [INFO] Step 3: Starting Redis...
docker-compose up -d redis
echo [SUCCESS] Redis started
echo.

echo [INFO] Step 4: Starting Elasticsearch...
docker-compose up -d elasticsearch
echo [SUCCESS] Elasticsearch started
echo.

echo [INFO] Step 5: Starting Zemberek NLP...
docker-compose up -d zemberek
echo [SUCCESS] Zemberek NLP started
echo.

echo [INFO] Step 6: Starting Monitoring Stack (Prometheus + Grafana)...
docker-compose up -d prometheus grafana node-exporter cadvisor
echo [SUCCESS] Monitoring stack started
echo.

echo [INFO] Waiting for services to be fully ready...
timeout /t 10 /nobreak >nul

echo [INFO] Step 7: Initializing Database...
if exist backend\init_db.py (
    cd backend
    python init_db.py
    cd ..
    echo [SUCCESS] Database initialized
) else (
    echo [WARNING] backend\init_db.py not found. Skipping database initialization.
)
echo.

echo [INFO] Step 8: Running Database Migrations...
if exist backend\alembic.ini (
    cd backend
    alembic upgrade head
    cd ..
    echo [SUCCESS] Database migrations applied
) else (
    echo [WARNING] Alembic not configured. Skipping migrations.
)
echo.

echo [INFO] Step 9: Verifying Services...
echo.
echo Service Status:
echo ---------------

docker ps | findstr turkiye_sinav_postgres >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] PostgreSQL: Running ^(port 5432^)
) else (
    echo [ERROR] PostgreSQL: Not running
)

docker ps | findstr turkiye_sinav_redis >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Redis: Running ^(port 6379^)
) else (
    echo [ERROR] Redis: Not running
)

docker ps | findstr turkiye_sinav_elasticsearch >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Elasticsearch: Running ^(port 9200^)
) else (
    echo [ERROR] Elasticsearch: Not running
)

docker ps | findstr turkiye_sinav_zemberek >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Zemberek NLP: Running ^(port 8081^)
) else (
    echo [ERROR] Zemberek NLP: Not running
)

docker ps | findstr turkiye_sinav_prometheus >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Prometheus: Running ^(port 9090^)
) else (
    echo [ERROR] Prometheus: Not running
)

docker ps | findstr turkiye_sinav_grafana >nul 2>&1
if not errorlevel 1 (
    echo [SUCCESS] Grafana: Running ^(port 3001^)
) else (
    echo [ERROR] Grafana: Not running
)

echo.
echo ========================================================================
echo [SUCCESS] Environment setup complete!
echo ========================================================================
echo.
echo Next steps:
echo   1. Start backend: cd backend ^&^& uvicorn main:app --reload
echo   2. Start frontend: cd frontend ^&^& npm run dev
echo   3. Access Grafana: http://localhost:3001 ^(admin/changeme_grafana_password^)
echo   4. Access Prometheus: http://localhost:9090
echo.
echo To stop all services: docker-compose down
echo To view logs: docker-compose logs -f [service-name]
echo.
pause
