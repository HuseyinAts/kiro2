@echo off
chcp 65001 > nul
cd /d C:\Users\husey\kiro2

echo ========================================
echo   KIRO2 SORU IMPORT - 36,967 Soru
echo ========================================
echo.

set PGPASSWORD=1470
set PSQL="C:\Program Files\PostgreSQL\18\bin\psql.exe"

echo [1/5] Veritabani baglantisi test ediliyor...
%PSQL% -h localhost -p 5434 -U postgres -d kiro2 -c "SELECT 'Baglanti OK' as durum;"
if %errorlevel% neq 0 (
    echo HATA: Veritabanina baglanilamadi!
    pause
    exit /b 1
)

echo.
echo [2/5] Mevcut soru sayisi...
%PSQL% -h localhost -p 5434 -U postgres -d kiro2 -c "SELECT COUNT(*) as onceki_soru_sayisi FROM question_bank;"

echo.
echo [3/5] Topic'ler olusturuluyor...
%PSQL% -h localhost -p 5434 -U postgres -d kiro2 -c "INSERT INTO topic_hierarchy (id, level, code, name_tr, meb_code, is_active, created_at, updated_at) VALUES (gen_random_uuid(), 1, 'MAT', 'Matematik', 'MAT', true, NOW(), NOW()), (gen_random_uuid(), 1, 'GEO', 'Geometri', 'GEO', true, NOW(), NOW()), (gen_random_uuid(), 1, 'FIZ', 'Fizik', 'FIZ', true, NOW(), NOW()), (gen_random_uuid(), 1, 'KIM', 'Kimya', 'KIM', true, NOW(), NOW()), (gen_random_uuid(), 1, 'BIO', 'Biyoloji', 'BIO', true, NOW(), NOW()), (gen_random_uuid(), 1, 'TUR', 'Turkce', 'TUR', true, NOW(), NOW()), (gen_random_uuid(), 1, 'EDB', 'Edebiyat', 'EDB', true, NOW(), NOW()), (gen_random_uuid(), 1, 'TAR', 'Tarih', 'TAR', true, NOW(), NOW()), (gen_random_uuid(), 1, 'COG', 'Cografya', 'COG', true, NOW(), NOW()), (gen_random_uuid(), 1, 'PAR', 'Paragraf', 'PAR', true, NOW(), NOW()), (gen_random_uuid(), 1, 'GEN', 'Genel', 'GEN', true, NOW(), NOW()) ON CONFLICT (code) DO NOTHING;"

echo.
echo [4/5] SQL script calistiriliyor...
%PSQL% -h localhost -p 5434 -U postgres -d kiro2 -f "C:\Users\husey\kiro2\IMPORT_QUICK.sql"

echo.
echo [5/5] Sonuc kontrol ediliyor...
%PSQL% -h localhost -p 5434 -U postgres -d kiro2 -c "SELECT COUNT(*) as toplam_soru FROM question_bank;"

echo.
echo ========================================
echo   IMPORT TAMAMLANDI!
echo ========================================
pause
