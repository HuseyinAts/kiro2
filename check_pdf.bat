@echo off
echo PDF Kontrol Scripti
echo ====================
echo.

cd /d "%~dp0"

if exist "MASTER_PLAN.pdf" (
    echo [OK] MASTER_PLAN.pdf bulundu!
    for %%A in (MASTER_PLAN.pdf) do (
        echo Boyut: %%~zA bytes
        echo Tarih: %%~tA
    )
    echo.
    echo PDF'i acmak ister misiniz? (E/H)
    set /p OPEN=
    if /i "%OPEN%"=="E" start MASTER_PLAN.pdf
) else (
    echo [HATA] MASTER_PLAN.pdf bulunamadi!
    echo.
    echo Lutfen once PDF'i olusturun:
    echo 1. create_pdf.bat calistirin
    echo 2. Veya manuel komut kullanin
)

pause
