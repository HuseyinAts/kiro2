@echo off
echo Teknofest 2025 - Education Platform Docker Setup
echo ================================================
echo.

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found!
    echo Creating from .env.example...
    copy .env.example .env
    echo .env file created. Please edit it with your API keys.
    echo.
)

REM Menu
echo Select an option:
echo 1) Run minimal setup (optimized for current implementation)
echo 2) Run development setup (with hot reload)
echo 3) Run full setup (with all services)
echo 4) Stop all containers
echo 5) Clean up (remove containers and volumes)
echo.

set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" (
    echo Starting minimal setup...
    docker-compose -f docker-compose.minimal.yml up --build
) else if "%choice%"=="2" (
    echo Starting development setup with hot reload...
    docker-compose -f docker-compose.dev.yml up
) else if "%choice%"=="3" (
    echo Starting full setup...
    docker-compose up --build
) else if "%choice%"=="4" (
    echo Stopping containers...
    docker-compose -f docker-compose.minimal.yml down
    docker-compose -f docker-compose.dev.yml down
    docker-compose down
) else if "%choice%"=="5" (
    echo Cleaning up...
    docker-compose -f docker-compose.minimal.yml down -v
    docker-compose -f docker-compose.dev.yml down -v
    docker-compose down -v
    echo All containers and volumes removed
) else (
    echo Invalid option. Exiting.
    pause
    exit /b 1
)

pause