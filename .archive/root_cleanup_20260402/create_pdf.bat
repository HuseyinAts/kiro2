@echo off
echo ========================================
echo PANDOC PDF OLUSTURMA BATCH SCRIPT
echo ========================================
echo.

REM Pandoc yollarini kontrol et
set PANDOC_PATH1="C:\Program Files\Pandoc\pandoc.exe"
set PANDOC_PATH2="C:\Program Files (x86)\Pandoc\pandoc.exe"
set PANDOC_PATH3="%LOCALAPPDATA%\Pandoc\pandoc.exe"

REM Pandoc'u bul
if exist %PANDOC_PATH1% (
    set PANDOC=%PANDOC_PATH1%
    echo Pandoc bulundu: %PANDOC%
) else if exist %PANDOC_PATH2% (
    set PANDOC=%PANDOC_PATH2%
    echo Pandoc bulundu: %PANDOC%
) else if exist %PANDOC_PATH3% (
    set PANDOC=%PANDOC_PATH3%
    echo Pandoc bulundu: %PANDOC%
) else (
    echo [HATA] Pandoc bulunamadi!
    echo Lutfen Pandoc'u su yerlerden birine yukleyin:
    echo - C:\Program Files\Pandoc\
    echo - C:\Program Files (x86)\Pandoc\
    echo - %LOCALAPPDATA%\Pandoc\
    pause
    exit /b 1
)

echo.
echo Calisma dizini: %~dp0
cd /d "%~dp0"

echo.
echo [1/3] Markdown dosyasini kontrol ediyorum...
if not exist "MASTER_PLAN_11_WEEKS_COMPLETE.md" (
    echo [HATA] MASTER_PLAN_11_WEEKS_COMPLETE.md bulunamadi!
    pause
    exit /b 1
)
echo [OK] Markdown dosyasi bulundu!

echo.
echo [2/3] PDF olusturuluyor...
echo Komut: pandoc MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf --toc --number-sections -V geometry:margin=1in

%PANDOC% MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf --toc --number-sections -V geometry:margin=1in

if %ERRORLEVEL% EQU 0 (
    echo [OK] PDF basariyla olusturuldu!
) else (
    echo [HATA] PDF olusturulamadi! Hata kodu: %ERRORLEVEL%
    echo.
    echo Olasi cozumler:
    echo 1. Pandoc'u yeniden yukleyin
    echo 2. PowerShell'de calistirmayi deneyin
    echo 3. VSCode Markdown PDF extension'ini kullanin
    pause
    exit /b 1
)

echo.
echo [3/3] PDF kontrol ediliyor...
if exist "MASTER_PLAN.pdf" (
    echo [BASARILI] PDF olusturuldu: MASTER_PLAN.pdf
    echo Dosya boyutu: 
    for %%A in (MASTER_PLAN.pdf) do echo %%~zA bytes
    echo.
    echo PDF'i acmak istiyor musunuz? (E/H)
    set /p OPEN_PDF=
    if /i "%OPEN_PDF%"=="E" (
        start MASTER_PLAN.pdf
    )
) else (
    echo [HATA] PDF dosyasi bulunamadi!
)

echo.
echo ========================================
echo ISLEM TAMAMLANDI
echo ========================================
pause
