@echo off
echo ================================================
echo Kiro IDE - Hizli Baslangic
echo ================================================
echo.

REM 1. Kiro'yu kapat
echo 1/5 - Kiro IDE kapaniyor...
taskkill /F /IM kiro.exe 2>nul
timeout /t 2 >nul

REM 2. Backup klasorlerini temizle
echo 2/5 - Backup klasorleri temizleniyor...
rd /s /q ".kiro\specs_backup_*" 2>nul
rd /s /q ".kiro\specs" 2>nul
mkdir ".kiro\specs" 2>nul

REM 3. Cache temizle
echo 3/5 - Cache temizleniyor...
rd /s /q "cache" 2>nul
rd /s /q "temp" 2>nul
rd /s /q "__pycache__" 2>nul

REM 4. Log dosyalarini temizle
echo 4/5 - Log dosyalari temizleniyor...
del /q "*.log" 2>nul
rd /s /q "logs" 2>nul

REM 5. Kiro'yu yeniden baslat
echo 5/5 - Kiro IDE baslatiliyor...
echo.
echo ================================================
echo Temizlik tamamlandi!
echo Simdi Kiro IDE'yi manuel olarak ac.
echo ================================================
echo.
pause
