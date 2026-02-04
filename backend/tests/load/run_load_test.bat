@echo off
REM Learning Path Load Test Runner (Windows)
REM P1.3 Implementation - Quick load test execution
REM
REM Usage:
REM   run_load_test.bat smoke       - Quick 1-minute smoke test
REM   run_load_test.bat normal      - 5-minute normal load test
REM   run_load_test.bat peak        - 10-minute peak load test
REM   run_load_test.bat stress      - 5-minute stress test
REM   run_load_test.bat spike       - 2-minute spike test
REM   run_load_test.bat custom      - Custom parameters (interactive)

setlocal enabledelayedexpansion

echo ========================================
echo Learning Path Load Test Runner
echo P1.3 - Locust Load Testing
echo ========================================
echo.

REM Check if locust is installed
python -c "import locust" 2>nul
if errorlevel 1 (
    echo ERROR: Locust not installed!
    echo.
    echo Please install Locust:
    echo   pip install locust^>=2.20.0
    echo.
    pause
    exit /b 1
)

REM Get test type from argument or prompt
set TEST_TYPE=%1
if "%TEST_TYPE%"=="" (
    echo Select test type:
    echo   1. Smoke Test ^(5 users, 1 min^)
    echo   2. Normal Load Test ^(50 users, 5 min^)
    echo   3. Peak Load Test ^(100 users, 10 min^)
    echo   4. Stress Test ^(200 users, 5 min^)
    echo   5. Spike Test ^(500 users, 2 min^)
    echo   6. Custom parameters
    echo.
    set /p CHOICE="Enter choice (1-6): "

    if "!CHOICE!"=="1" set TEST_TYPE=smoke
    if "!CHOICE!"=="2" set TEST_TYPE=normal
    if "!CHOICE!"=="3" set TEST_TYPE=peak
    if "!CHOICE!"=="4" set TEST_TYPE=stress
    if "!CHOICE!"=="5" set TEST_TYPE=spike
    if "!CHOICE!"=="6" set TEST_TYPE=custom
)

REM Set test parameters based on type
set HOST=http://localhost:8001
set LOCUSTFILE=locustfile_learning_path.py

if "%TEST_TYPE%"=="smoke" (
    set USERS=5
    set SPAWN_RATE=1
    set RUN_TIME=1m
    set REPORT_NAME=smoke_test
    echo.
    echo Running SMOKE TEST...
    echo Users: 5, Duration: 1 minute
    echo.
) else if "%TEST_TYPE%"=="normal" (
    set USERS=50
    set SPAWN_RATE=5
    set RUN_TIME=5m
    set REPORT_NAME=normal_load_test
    echo.
    echo Running NORMAL LOAD TEST...
    echo Users: 50, Duration: 5 minutes
    echo.
) else if "%TEST_TYPE%"=="peak" (
    set USERS=100
    set SPAWN_RATE=10
    set RUN_TIME=10m
    set REPORT_NAME=peak_load_test
    echo.
    echo Running PEAK LOAD TEST...
    echo Users: 100, Duration: 10 minutes
    echo.
) else if "%TEST_TYPE%"=="stress" (
    set USERS=200
    set SPAWN_RATE=20
    set RUN_TIME=5m
    set REPORT_NAME=stress_test
    set USER_CLASS=--user-classes=StressTestUser
    echo.
    echo Running STRESS TEST...
    echo Users: 200 ^(aggressive^), Duration: 5 minutes
    echo.
) else if "%TEST_TYPE%"=="spike" (
    set USERS=500
    set SPAWN_RATE=100
    set RUN_TIME=2m
    set REPORT_NAME=spike_test
    set USER_CLASS=--user-classes=SpikeTestUser
    echo.
    echo Running SPIKE TEST...
    echo Users: 500 ^(burst^), Duration: 2 minutes
    echo.
) else if "%TEST_TYPE%"=="custom" (
    echo.
    echo Custom Load Test Configuration
    echo.
    set /p USERS="Number of users: "
    set /p SPAWN_RATE="Spawn rate (users/sec): "
    set /p RUN_TIME="Run time (e.g., 5m, 300s): "
    set /p REPORT_NAME="Report name: "
    echo.
) else (
    echo ERROR: Invalid test type: %TEST_TYPE%
    echo.
    echo Valid types: smoke, normal, peak, stress, spike, custom
    echo.
    pause
    exit /b 1
)

REM Generate timestamp for report
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%

REM Set report filename
set HTML_REPORT=reports\%REPORT_NAME%_%TIMESTAMP%.html
set CSV_PREFIX=reports\%REPORT_NAME%_%TIMESTAMP%

REM Create reports directory if not exists
if not exist reports mkdir reports

REM Check if backend is running
echo Checking if backend is running on %HOST%...
powershell -Command "try { Invoke-WebRequest -Uri '%HOST%/api/learning-path/health' -UseBasicParsing -TimeoutSec 3 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo.
    echo WARNING: Backend not responding at %HOST%
    echo.
    echo Please start the backend first:
    echo   cd backend
    echo   py -m uvicorn main:app --host 0.0.0.0 --port 8001
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        echo.
        echo Load test cancelled.
        pause
        exit /b 1
    )
)

REM Run locust
echo.
echo Starting Locust load test...
echo.
echo Host: %HOST%
echo Users: %USERS%
echo Spawn Rate: %SPAWN_RATE%/sec
echo Duration: %RUN_TIME%
echo Report: %HTML_REPORT%
echo.
echo Press Ctrl+C to stop the test early
echo.

locust -f %LOCUSTFILE% --host=%HOST% ^
       --users=%USERS% --spawn-rate=%SPAWN_RATE% --run-time=%RUN_TIME% ^
       %USER_CLASS% ^
       --headless ^
       --html=%HTML_REPORT% ^
       --csv=%CSV_PREFIX%

set EXIT_CODE=%ERRORLEVEL%

echo.
echo ========================================
echo Load Test Completed!
echo ========================================
echo.

if %EXIT_CODE% EQU 0 (
    echo Status: SUCCESS
    echo.
    echo Reports generated:
    echo   HTML: %HTML_REPORT%
    echo   CSV:  %CSV_PREFIX%_stats.csv
    echo         %CSV_PREFIX%_stats_history.csv
    echo         %CSV_PREFIX%_failures.csv
    echo.
    echo Opening HTML report...
    start %HTML_REPORT%
) else (
    echo Status: FAILED ^(exit code: %EXIT_CODE%^)
    echo.
    echo Check the output above for errors.
)

echo.
pause
