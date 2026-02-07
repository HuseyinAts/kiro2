@echo off
REM WebSocket Load Test Runner for KIRO2 (Windows)
REM
REM Usage:
REM   run_websocket_load_test.bat [mode]
REM
REM Modes:
REM   smoke      - Quick CI test (50 users, 2min)
REM   dev        - Development test (100 users, 5min)
REM   staging    - Staging test (500 users, 10min)
REM   production - Production test (1000 users, 15min)
REM   stress     - Stress test (5000 users, 30min)
REM   pytest     - Run pytest smoke test

setlocal enabledelayedexpansion

set MODE=%1
if "%MODE%"=="" set MODE=dev

set HOST=%KIRO2_HOST%
if "%HOST%"=="" set HOST=http://localhost:8000

set RESULTS_DIR=results
if not exist "%RESULTS_DIR%" mkdir "%RESULTS_DIR%"

echo.
echo ============================================================
echo KIRO2 WebSocket + HTTP Load Test Runner
echo ============================================================
echo Mode: %MODE%
echo Host: %HOST%
echo ============================================================
echo.

REM Check if backend is running
echo [INFO] Checking if backend is running...
curl -s -f "%HOST%/health" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Backend is not running at %HOST%
    echo [INFO] Start backend with: cd backend ^&^& uvicorn main:app --reload --port 8000
    exit /b 1
)
echo [SUCCESS] Backend is running!
echo.

if "%MODE%"=="pytest" goto :pytest
if "%MODE%"=="smoke" goto :smoke
if "%MODE%"=="dev" goto :dev
if "%MODE%"=="staging" goto :staging
if "%MODE%"=="production" goto :production
if "%MODE%"=="stress" goto :stress

echo [ERROR] Unknown mode: %MODE%
echo.
echo Available modes:
echo   pytest       - Run pytest smoke test
echo   smoke        - Quick CI test (50 users, 2min)
echo   dev          - Development test (100 users, 5min)
echo   staging      - Staging test (500 users, 10min)
echo   production   - Production test (1000 users, 15min)
echo   stress       - Stress test (5000 users, 30min)
echo.
exit /b 1

:pytest
echo [INFO] Running pytest smoke test...
pytest tests\load\test_websocket_load.py -v --timeout=300
if errorlevel 1 (
    echo [ERROR] Pytest smoke test failed!
    exit /b 1
)
echo [SUCCESS] Pytest smoke test passed!
goto :end

:smoke
set USERS=50
set SPAWN_RATE=10
set DURATION=2m
set MODE_NAME=smoke
goto :run_locust

:dev
set USERS=100
set SPAWN_RATE=20
set DURATION=5m
set MODE_NAME=dev
goto :run_locust

:staging
set USERS=500
set SPAWN_RATE=50
set DURATION=10m
set MODE_NAME=staging
goto :run_locust

:production
set USERS=1000
set SPAWN_RATE=50
set DURATION=15m
set MODE_NAME=production
goto :run_locust

:stress
echo [WARNING] This will run a high-load stress test!
set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo [INFO] Stress test cancelled.
    goto :end
)
set USERS=5000
set SPAWN_RATE=100
set DURATION=30m
set MODE_NAME=stress
goto :run_locust

:run_locust
echo [INFO] Running %MODE_NAME% load test...
echo [INFO]   Users: %USERS%
echo [INFO]   Spawn Rate: %SPAWN_RATE% users/sec
echo [INFO]   Duration: %DURATION%
echo [INFO]   Host: %HOST%
echo.

REM Generate timestamp
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

set CSV_PREFIX=%RESULTS_DIR%\websocket_%MODE_NAME%_%TIMESTAMP%

echo [INFO] Results will be saved to: %CSV_PREFIX%*.csv
echo.

locust -f tests\load\locustfile_websocket.py ^
    --users %USERS% ^
    --spawn-rate %SPAWN_RATE% ^
    --run-time %DURATION% ^
    --host %HOST% ^
    --headless ^
    --csv=%CSV_PREFIX% ^
    --html=%CSV_PREFIX%.html ^
    --logfile=%CSV_PREFIX%.log

if errorlevel 1 (
    echo [ERROR] Load test failed!
    exit /b 1
)

echo.
echo [SUCCESS] Load test completed!
echo [INFO] Results:
echo [INFO]   CSV: %CSV_PREFIX%_stats.csv
echo [INFO]   HTML: %CSV_PREFIX%.html
echo [INFO]   Log: %CSV_PREFIX%.log
goto :end

:end
echo.
echo ============================================================
echo Test completed!
echo ============================================================
endlocal
