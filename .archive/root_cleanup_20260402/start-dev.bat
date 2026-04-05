@echo off
REM Türkiye Üniversite Sınavları Hazırlık Platformu - Windows Development Başlatma Scripti

echo 🚀 Türkiye Üniversite Sınavları Hazırlık Platformu başlatılıyor...

REM Türkçe karakter desteği için environment ayarları
set LANG=tr_TR.UTF-8
set LC_ALL=tr_TR.UTF-8
set PYTHONIOENCODING=utf-8

REM Docker Compose ile servisleri başlat
echo 📦 Docker servisleri başlatılıyor...
docker-compose up -d postgres redis elasticsearch

REM Servislerin hazır olmasını bekle
echo ⏳ Servislerin hazır olması bekleniyor...
timeout /t 10 /nobreak > nul

REM Backend'i development modunda başlat
echo 🔧 Backend servisi başlatılıyor...
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo ✅ Platform başarıyla başlatıldı!
echo 🌐 API: http://localhost:8000
echo 📚 Docs: http://localhost:8000/docs

pause