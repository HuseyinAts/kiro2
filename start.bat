@echo off
echo ========================================
echo   TEKNOFEST 2025 - Egitim Eylemci
echo   AI-Powered Education Platform
echo ========================================
echo.

:: Environment kontrolü
if not exist ".env" (
    echo [!] .env dosyasi bulunamadi, .env.example'dan kopyalaniyor...
    copy .env.example .env
    echo [+] .env dosyasi olusturuldu. Lutfen API key'leri ekleyin.
    echo.
)

:: Docker kontrolü
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker yuklu degil! Lutfen Docker'i yukleyin.
    echo     https://www.docker.com/get-started
    pause
    exit /b 1
)

:: Docker servisinin çalıştığını kontrol et
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Docker servisi calismiyor! Docker Desktop'i baslatin.
    pause
    exit /b 1
)

echo [1] Development Mode (Minimal)
echo [2] Production Mode (Full Stack)
echo [3] Test Mode (Run Tests)
echo [4] Stop All Services
echo.
set /p choice="Seciminizi yapin (1-4): "

if "%choice%"=="1" (
    echo.
    echo [+] Development mode baslatiliyor...
    docker-compose -f docker-compose.minimal.yml up --build
) else if "%choice%"=="2" (
    echo.
    echo [+] Production mode baslatiliyor...
    docker-compose -f docker-compose.production.yml up --build -d
    echo.
    echo [+] Servisler baslatildi:
    echo     - Frontend: http://localhost
    echo     - Backend API: http://localhost/api
    echo     - API Docs: http://localhost/api/docs
    echo     - Grafana: http://localhost:3001
    echo     - Prometheus: http://localhost:9090
) else if "%choice%"=="3" (
    echo.
    echo [+] Testler calistiriliyor...
    cd backend
    python run_tests.py
    cd ..
) else if "%choice%"=="4" (
    echo.
    echo [+] Tum servisler durduruluyor...
    docker-compose down
    docker-compose -f docker-compose.minimal.yml down
    docker-compose -f docker-compose.production.yml down
    echo [+] Servisler durduruldu.
) else (
    echo [!] Gecersiz secim!
)

pause
