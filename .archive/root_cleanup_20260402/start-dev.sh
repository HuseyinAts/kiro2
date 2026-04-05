#!/bin/bash
# Türkiye Üniversite Sınavları Hazırlık Platformu - Development Başlatma Scripti

echo "🚀 Türkiye Üniversite Sınavları Hazırlık Platformu başlatılıyor..."

# Türkçe karakter desteği için environment ayarları
export LANG=tr_TR.UTF-8
export LC_ALL=tr_TR.UTF-8
export PYTHONIOENCODING=utf-8

# Docker Compose ile servisleri başlat
echo "📦 Docker servisleri başlatılıyor..."
docker-compose up -d postgres redis elasticsearch

# Servislerin hazır olmasını bekle
echo "⏳ Servislerin hazır olması bekleniyor..."
sleep 10

# Backend'i development modunda başlat
echo "🔧 Backend servisi başlatılıyor..."
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Platform başarıyla başlatıldı!"
echo "🌐 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"