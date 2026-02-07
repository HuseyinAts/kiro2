@echo off
echo ============================================
echo KIRO2 ACIL ICERIK YUKLEME
echo ============================================
echo.

REM PostgreSQL şifrenizi girin
set PGPASSWORD=postgres

echo [1/4] Veritabani kontrol ediliyor...
psql -U postgres -c "CREATE DATABASE kiro2;" 2>nul
echo Veritabani hazir

echo.
echo [2/4] SQL dosyasi yukleniyor...
psql -U postgres -d kiro2 -f emergency_content.sql
echo SQL yuklendi

echo.
echo [3/4] Python loader calistiriliyor...
python load_emergency_content.py
echo Python loader tamamlandi

echo.
echo [4/4] Istatistikler...
psql -U postgres -d kiro2 -c "SELECT 'Toplam Soru: ' || COUNT(*) FROM questions;"

echo.
echo ============================================
echo YUKLEME TAMAMLANDI!
echo ============================================
echo.
echo Admin Panel: http://localhost:3000/admin
echo Email: admin@kiro2.com
echo Sifre: admin123
echo.
pause
