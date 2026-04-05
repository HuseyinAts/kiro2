@echo off
chcp 65001 >nul
echo ========================================
echo PANDOC PDF OLUSTURMA - GELISMIS SCRIPT
echo ========================================
echo.

cd /d "%~dp0"

REM Pandoc'u PATH'den dene
echo [1/5] Pandoc kontrol ediliyor...
where pandoc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Pandoc PATH'de bulundu
    set PANDOC=pandoc
    goto :check_markdown
)

REM PATH'de yoksa, bilinen konumlarda ara
echo [UYARI] Pandoc PATH'de bulunamadi, bilinen konumlarda araniyor...

REM Konum 1: Program Files
if exist "C:\Program Files\Pandoc\pandoc.exe" (
    echo [OK] Pandoc bulundu: C:\Program Files\Pandoc\
    set "PANDOC=C:\Program Files\Pandoc\pandoc.exe"
    goto :check_markdown
)

REM Konum 2: Program Files (x86)
if exist "C:\Program Files (x86)\Pandoc\pandoc.exe" (
    echo [OK] Pandoc bulundu: C:\Program Files (x86)\Pandoc\
    set "PANDOC=C:\Program Files (x86)\Pandoc\pandoc.exe"
    goto :check_markdown
)

REM Konum 3: User AppData
if exist "%LOCALAPPDATA%\Pandoc\pandoc.exe" (
    echo [OK] Pandoc bulundu: %LOCALAPPDATA%\Pandoc\
    set "PANDOC=%LOCALAPPDATA%\Pandoc\pandoc.exe"
    goto :check_markdown
)

REM Konum 4: Chocolatey
if exist "C:\ProgramData\chocolatey\bin\pandoc.exe" (
    echo [OK] Pandoc bulundu: Chocolatey
    set "PANDOC=C:\ProgramData\chocolatey\bin\pandoc.exe"
    goto :check_markdown
)

REM Pandoc bulunamadi
echo.
echo [HATA] Pandoc hiçbir yerde bulunamadi!
echo.
echo Pandoc kurulu degil veya kurulum tamamlanmadi.
echo.
echo COZUMLER:
echo 1. Pandoc'u yukleyin: https://pandoc.org/installing.html
echo 2. Kurulumdan sonra bu pencereyi kapatip yeniden acin
echo 3. VEYA VSCode Markdown PDF extension kullanin
echo 4. VEYA online: https://dillinger.io
echo.
pause
exit /b 1

:check_markdown
echo.
echo [2/5] Markdown dosyasi kontrol ediliyor...
if not exist "MASTER_PLAN_11_WEEKS_COMPLETE.md" (
    echo [HATA] MASTER_PLAN_11_WEEKS_COMPLETE.md bulunamadi!
    echo Dosya bu konumda olmali: %CD%
    pause
    exit /b 1
)
echo [OK] Markdown dosyasi bulundu!

echo.
echo [3/5] Pandoc versiyonu kontrol ediliyor...
"%PANDOC%" --version | findstr "pandoc"
if %ERRORLEVEL% NEQ 0 (
    echo [UYARI] Pandoc versiyonu alinamadi
)

echo.
echo [4/5] PDF olusturuluyor...
echo Komut: "%PANDOC%" MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf --toc --number-sections -V geometry:margin=1in
echo.

"%PANDOC%" MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf --toc --number-sections -V geometry:margin=1in 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [BASARILI] PDF olusturuldu!
) else (
    echo.
    echo [HATA] PDF olusturulamadi! Hata kodu: %ERRORLEVEL%
    echo.
    echo BASIT PDF DENENIYOR (içindekiler olmadan)...
    "%PANDOC%" MASTER_PLAN_11_WEEKS_COMPLETE.md -o MASTER_PLAN.pdf 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [BASARILI] Basit PDF olusturuldu!
    ) else (
        echo [HATA] Basit PDF de olusturulamadi!
        echo.
        echo Olasi sebepler:
        echo - LaTeX yuklu degil (--toc icin gerekli)
        echo - Dosya izinleri sorunu
        echo - Pandoc version uyumsuzlugu
        pause
        exit /b 1
    )
)

echo.
echo [5/5] PDF kontrol ediliyor...
if exist "MASTER_PLAN.pdf" (
    echo [BASARILI] PDF olusturuldu!
    echo.
    echo Dosya: %CD%\MASTER_PLAN.pdf
    for %%A in (MASTER_PLAN.pdf) do (
        echo Boyut: %%~zA bytes
        echo Tarih: %%~tA
    )
    echo.
    echo PDF'i acmak istiyor musunuz? (E/H)
    set /p OPEN_PDF=
    if /i "%OPEN_PDF%"=="E" (
        start MASTER_PLAN.pdf
    )
) else (
    echo [HATA] PDF dosyasi olusturulmasina ragmen bulunamadi!
)

echo.
echo ========================================
echo ISLEM TAMAMLANDI
echo ========================================
echo.
pause
