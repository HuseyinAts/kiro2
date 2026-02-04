@echo off
REM Celery Workers Startup Script for Windows
REM PHASE 1 Sprint 3: Async Processing

echo Starting Celery Workers for Kiro2...
echo.

REM Check if Redis is running
echo [1/3] Checking Redis connection...
py -c "import redis; r = redis.Redis(host='localhost', port=6379); r.ping(); print('Redis OK')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Redis is not running!
    echo Please start Redis first: docker run -d -p 6379:6379 redis:latest
    pause
    exit /b 1
)
echo Redis connection: OK
echo.

REM Start Celery Worker (all queues)
echo [2/3] Starting Celery Worker...
start "Celery Worker" cmd /k "cd backend && py -m celery -A core.celery_app worker --loglevel=info --pool=solo --concurrency=4"

timeout /t 3 >nul

REM Start Flower monitoring
echo [3/3] Starting Flower monitoring dashboard...
start "Flower Dashboard" cmd /k "cd backend && py -m celery -A core.celery_app flower --port=5555"

echo.
echo ================================================
echo   Celery Workers Started Successfully!
echo ================================================
echo   Worker Dashboard: http://localhost:5555
echo   Press Ctrl+C in worker windows to stop
echo ================================================
echo.
pause
