@echo off
echo Kiro IDE Backup Sorunu Duzeltiliyor...
echo.

REM Kiro IDE'yi kapat
echo 1. Kiro IDE'yi kapat (Ctrl+Q)
echo 2. Bu scripti calistir
echo 3. Kiro IDE'yi yeniden ac
echo.
pause

REM .kiro klasorundeki cache'i temizle
echo Cache temizleniyor...
rd /s /q ".kiro\specs_backup_*" 2>nul
rd /s /q ".kiro\specs" 2>nul
mkdir ".kiro\specs"

echo.
echo Cache temizlendi!
echo Kiro IDE'yi yeniden baslatabilirsin.
echo.
pause
