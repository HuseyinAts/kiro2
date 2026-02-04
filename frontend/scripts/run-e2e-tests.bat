@echo off
REM ###############################################################################
REM E2E Test Runner Script (Windows)
REM 
REM Bu script, Learning Path video loading E2E testlerini local ortamda
REM çalıştırmak için gerekli tüm adımları otomatikleştirir.
REM
REM Kullanım:
REM   scripts\run-e2e-tests.bat [options]
REM
REM Options:
REM   --headed        Tarayıcıyı görünür modda çalıştır
REM   --debug         Debug modunda çalıştır
REM   --ui            UI modunda çalıştır
REM   --browser       Belirli bir tarayıcıda çalıştır (chromium, firefox, webkit)
REM   --help          Bu yardım mesajını göster
REM ###############################################################################

setlocal enabledelayedexpansion

REM Default values
set HEADED=false
set DEBUG=false
set UI=false
set BROWSER=
set BACKEND_PORT=8001
set FRONTEND_PORT=3002

REM Parse command line arguments
:parse_args
if "%~1"=="" goto end_parse
if "%~1"=="--headed" (
  set HEADED=true
  shift
  goto parse_args
)
if "%~1"=="--debug" (
  set DEBUG=true
  shift
  goto parse_args
)
if "%~1"=="--ui" (
  set UI=true
  shift
  goto parse_args
)
if "%~1"=="--browser" (
  set BROWSER=%~2
  shift
  shift
  goto parse_args
)
if "%~1"=="--help" (
  echo E2E Test Runner
  echo.
  echo Usage: %~nx0 [options]
  echo.
  echo Options:
  echo   --headed        Run browser in headed mode
  echo   --debug         Run in debug mode
  echo   --ui            Run in UI mode
  echo   --browser       Run specific browser (chromium, firefox, webkit^)
  echo   --help          Show this help message
  exit /b 0
)
echo Unknown option: %~1
exit /b 1

:end_parse

echo ╔════════════════════════════════════════════════════════════╗
echo ║         E2E Test Runner - Video Loading Tests             ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if backend is running
echo [1/6] Checking backend server...
curl -s http://localhost:%BACKEND_PORT%/health >nul 2>&1
if %errorlevel% equ 0 (
  echo [✓] Backend is running on port %BACKEND_PORT%
) else (
  echo [✗] Backend is not running!
  echo Please start the backend server first:
  echo   cd backend ^&^& python -m uvicorn main:app --port %BACKEND_PORT%
  exit /b 1
)

REM Check if frontend is running
echo [2/6] Checking frontend server...
curl -s http://localhost:%FRONTEND_PORT% >nul 2>&1
if %errorlevel% equ 0 (
  echo [✓] Frontend is running on port %FRONTEND_PORT%
) else (
  echo [✗] Frontend is not running!
  echo Please start the frontend server first:
  echo   cd frontend ^&^& npm run dev
  exit /b 1
)

REM Check if Playwright is installed
echo [3/6] Checking Playwright installation...
if not exist "node_modules\@playwright\test" (
  echo [✗] Playwright is not installed!
  echo Installing Playwright...
  call npm install
)
echo [✓] Playwright is installed

REM Check if Playwright browsers are installed
echo [4/6] Checking Playwright browsers...
npx playwright --version >nul 2>&1
if %errorlevel% neq 0 (
  echo [✗] Playwright browsers are not installed!
  echo Installing Playwright browsers...
  call npx playwright install --with-deps
)
echo [✓] Playwright browsers are installed

REM Set environment variables
echo [5/6] Setting environment variables...
set VITE_API_URL=http://localhost:%BACKEND_PORT%
set VITE_APP_URL=http://localhost:%FRONTEND_PORT%
echo [✓] Environment variables set

REM Build test command
echo [6/6] Running E2E tests...
set TEST_CMD=npx playwright test

if "%UI%"=="true" (
  set TEST_CMD=!TEST_CMD! --ui
) else if "%DEBUG%"=="true" (
  set TEST_CMD=!TEST_CMD! --debug
) else if "%HEADED%"=="true" (
  set TEST_CMD=!TEST_CMD! --headed
)

if not "%BROWSER%"=="" (
  set TEST_CMD=!TEST_CMD! --project=%BROWSER%
)

echo Running: !TEST_CMD!
echo.

REM Run tests
call !TEST_CMD!
if %errorlevel% equ 0 (
  echo.
  echo ╔════════════════════════════════════════════════════════════╗
  echo ║                  ✓ All tests passed!                       ║
  echo ╚════════════════════════════════════════════════════════════╝
  echo.
  echo View test report:
  echo   npm run test:e2e:report
  exit /b 0
) else (
  echo.
  echo ╔════════════════════════════════════════════════════════════╗
  echo ║                  ✗ Some tests failed!                      ║
  echo ╚════════════════════════════════════════════════════════════╝
  echo.
  echo Debugging tips:
  echo   1. Check screenshots: test-results\screenshots\
  echo   2. Check videos: test-results\videos\
  echo   3. View test report: npm run test:e2e:report
  echo   4. Run in debug mode: %~nx0 --debug
  echo   5. Run in UI mode: %~nx0 --ui
  exit /b 1
)
