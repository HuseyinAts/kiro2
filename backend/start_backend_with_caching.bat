@echo off
echo ============================================
echo Redis Caching Backend Baslat
echo ============================================
echo.

REM Tum Python processlerini kapat
echo [1/4] Eski backend processleri kapatiliyor...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM py.exe >nul 2>&1
timeout /t 3 /nobreak >nul

REM Port temizligi dogrula
echo [2/4] Port 9000 temizleniyor...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :9000 ^| findstr LISTENING') do (
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Backend klasorune git
echo [3/4] Backend klasorune gidiliyor...
cd /d C:\Users\husey\kiro2\backend

REM Backend baslat
echo [4/4] Backend baslat iliyor (CACHING AKTIF)...
echo.
echo ============================================
echo Backend http://localhost:9000 adresinde basliyor...
echo CTRL+C ile durdurun
echo ============================================
echo.

REM UTF-8 encoding ayarla (emoji sorununu coz)
chcp 65001 >nul

REM Backend'i baslat
py -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
