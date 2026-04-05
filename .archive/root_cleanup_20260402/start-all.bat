@echo off
echo ===============================================
echo   Teknofest 2025 - Tüm Servisleri Başlat
echo ===============================================
echo.

echo Backend başlatılıyor...
start cmd /k "cd backend && py main.py"

timeout /t 5 /nobreak > nul

echo Frontend başlatılıyor...
start cmd /k "cd frontend && npm run dev"

echo.
echo ===============================================
echo Servisler başlatıldı:
echo - Backend: http://localhost:8000
echo - Frontend: http://localhost:3000 veya http://localhost:3001
echo - API Dokümantasyonu: http://localhost:8000/docs
echo ===============================================
echo.
pause