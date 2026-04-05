@echo off
REM Claude Code Cache Temizleme Scripti
REM Bu script Claude Code'un "restoreCheckpoint" hatasini cozar

echo ====================================
echo Claude Code Cache Temizleme Basladi
echo ====================================
echo.

echo [1/5] Checkpoint dosyalari temizleniyor...
if exist "c:\Users\husey\.claude\projects\*.jsonl" (
    del /F /Q "c:\Users\husey\.claude\projects\*.jsonl" 2>nul
    echo   - Checkpoint JSONL dosyalari silindi
)

echo [2/5] Proje cache klasoru temizleniyor...
if exist "c:\Users\husey\.claude\projects\C--Users-husey-kiro2" (
    rmdir /S /Q "c:\Users\husey\.claude\projects\C--Users-husey-kiro2" 2>nul
    echo   - Proje cache klasoru silindi
)

echo [3/5] Todo cache dosyalari temizleniyor...
if exist "c:\Users\husey\.claude\todos\*.json" (
    del /F /Q "c:\Users\husey\.claude\todos\*.json" 2>nul
    echo   - Todo cache dosyalari silindi
)

echo [4/5] Shell snapshot dosyalari temizleniyor...
if exist "c:\Users\husey\.claude\shell-snapshots\*" (
    del /F /Q "c:\Users\husey\.claude\shell-snapshots\*" 2>nul
    echo   - Shell snapshot dosyalari silindi
)

echo [5/5] Debug cache dosyalari temizleniyor...
if exist "c:\Users\husey\.claude\debug\*" (
    del /F /Q "c:\Users\husey\.claude\debug\*" 2>nul
    echo   - Debug cache dosyalari silindi
)

echo.
echo ====================================
echo Temizleme Tamamlandi!
echo ====================================
echo.
echo SONRAKI ADIMLAR:
echo 1. VSCode'u tamamen kapatin (tum pencereleri)
echo 2. VSCode'u yeniden baslatın
echo 3. Claude Code chat'i tekrar deneyin
echo.
pause
