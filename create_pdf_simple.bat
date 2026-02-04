@echo off
chcp 65001 >nul

REM Scriptin bulundugu dizine git (onemli!)
cd /d "%~dp0"

echo ========================================
echo PANDOC PDF OLUSTURMA
echo ========================================
echo.
echo Calisma dizini: %CD%
echo.

REM Pandoc kontrol
where pandoc >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [HATA] Pandoc PATH'de bulunamadi!
    echo.
    echo COZUM: PowerShell'i yeniden baslat veya bilgisayari yeniden baslat
    echo ALTERNATIF: VSCode Markdown PDF extension kullan
    pause
    exit /b 1
)

echo [OK] Pandoc bulundu!
pandoc --version | findstr "pandoc"
echo.

REM Markdown dosyasi kontrol
if not exist "MASTER_PLAN_11_WEEKS_COMPLETE.md" (
    echo [HATA] MASTER_PLAN_11_WEEKS_COMPLETE.md bulunamadi!
    echo Dosya bu konumda olmali: %CD%
    echo.
    dir /b *.md
    pause
    exit /b 1
)

echo [OK] Markdown dosyasi bulundu!
echo.

REM PDF olustur
echo PDF olusturuluyor...
echo.

pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo [BASARILI] PDF OLUSTURULDU!
    echo ========================================
    echo.
    echo Konum: %CD%\MASTER_PLAN.pdf
    for %%A in (MASTER_PLAN.pdf) do echo Boyut: %%~zA bytes
    echo.
    start MASTER_PLAN.pdf
) else (
    echo [HATA] PDF olusturulamadi!
)

pause
