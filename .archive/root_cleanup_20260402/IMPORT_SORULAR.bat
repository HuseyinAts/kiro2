@echo off
chcp 65001 > nul
echo ========================================
echo   KIRO2 Soru Import - 36,967 Soru
echo ========================================
echo.

cd /d C:\Users\husey\kiro2

echo [1/4] PostgreSQL baglantisi kontrol ediliyor...
set PGPASSWORD=1470

REM PostgreSQL'in yolunu bul
set PSQL_PATH=
for %%p in (
    "C:\Program Files\PostgreSQL\16\bin\psql.exe"
    "C:\Program Files\PostgreSQL\15\bin\psql.exe"
    "C:\Program Files\PostgreSQL\14\bin\psql.exe"
    "C:\Program Files\PostgreSQL\17\bin\psql.exe"
) do (
    if exist %%p set PSQL_PATH=%%p
)

if "%PSQL_PATH%"=="" (
    echo HATA: PostgreSQL bulunamadi!
    echo Lutfen PostgreSQL yukleyin veya PATH'e ekleyin.
    pause
    exit /b 1
)

echo PostgreSQL bulundu: %PSQL_PATH%
echo.

echo [2/4] Veritabani durumu kontrol ediliyor...
%PSQL_PATH% -h localhost -p 5434 -U postgres -d kiro2 -c "SELECT COUNT(*) as mevcut_soru FROM question_bank;" 2>nul
if %errorlevel% neq 0 (
    echo HATA: Veritabanina baglanilamadi!
    echo PostgreSQL servisinin calistigini kontrol edin.
    pause
    exit /b 1
)

echo.
echo [3/4] Topic'ler olusturuluyor...
%PSQL_PATH% -h localhost -p 5434 -U postgres -d kiro2 -c "
INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at)
VALUES 
    (gen_random_uuid(), 1, 'MAT', 'Matematik', 'MAT', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'GEO', 'Geometri', 'GEO', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'FIZ', 'Fizik', 'FIZ', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'KIM', 'Kimya', 'KIM', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'BIO', 'Biyoloji', 'BIO', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'TUR', 'Turkce', 'TUR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'EDB', 'Edebiyat', 'EDB', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'TAR', 'Tarih', 'TAR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'COG', 'Cografya', 'COG', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'PAR', 'Paragraf', 'PAR', true, NOW(), NOW()),
    (gen_random_uuid(), 1, 'GEN', 'Genel', 'GEN', true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
"

echo.
echo [4/4] Python ile sorular yukleniyor...
C:\Users\husey\kiro2\.venv\Scripts\python.exe C:\Users\husey\kiro2\import_direct.py

echo.
echo ========================================
echo   IMPORT TAMAMLANDI!
echo ========================================
pause
