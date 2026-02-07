# KIRO2 Claude Code Özel Komutları

## /kiro2:status
Proje durumunu kontrol et:
```bash
# Backend durumu
curl -s http://localhost:8000/health | jq

# Frontend durumu  
curl -s http://localhost:3001/api/health | jq

# Database durumu
psql -U postgres -d kiro2 -c "SELECT COUNT(*) FROM questions;"

# Redis durumu
redis-cli ping
```

## /kiro2:test
Testleri çalıştır:
```bash
# Unit testler
cd backend && pytest tests/unit -v --tb=short

# Integration testler
cd backend && pytest tests/integration -v

# Frontend testler
cd frontend && npm test -- --watchAll=false
```

## /kiro2:lint
Kod kalitesini kontrol et:
```bash
# Python
cd backend && black . --check && isort . --check && flake8 . && mypy .

# TypeScript
cd frontend && npm run lint && npm run type-check
```

## /kiro2:content
İçerik durumunu kontrol et:
```bash
# Soru sayısı
psql -U postgres -d kiro2 -c "SELECT subject, COUNT(*) FROM questions GROUP BY subject;"

# Cevap eşleşme oranı
psql -U postgres -d kiro2 -c "SELECT COUNT(*) FROM questions WHERE correct_answer IS NOT NULL;"

# d-dataset durumu
ls -la C:\Users\husey\d-dataset\extracted\ | wc -l
```

## /kiro2:deploy
Deploy hazırlığı:
```bash
# Build frontend
cd frontend && npm run build

# Migrations
cd backend && alembic upgrade head

# Docker build
docker-compose build

# Health check
docker-compose up -d && sleep 10 && curl http://localhost:8000/health
```

## /kiro2:fix-critical
Kritik sorunları çöz:
```bash
# 1. emergency_content.sql yükle
psql -U postgres -d kiro2 -f C:\Users\husey\kiro2\emergency_content.sql

# 2. WebSocket deprecated kod kaldır (manuel)
# examService.ts L123-145 kontrol et

# 3. DB bağlantısı doğrula
cd backend && python -c "from database.connection import get_db; print('OK')"
```

## /kiro2:ocr
OCR pipeline işlemleri:
```bash
# d-dataset'e git
cd C:\Users\husey\d-dataset

# YOLO cevap crop'larını işle
python cevap_crop_ocr.py

# Eşleştirme çalıştır
python matching_engine.py
```

## Kullanım

Bu komutlar Claude Code içinde `/kiro2:<command>` formatında çalıştırılabilir.
Örnek: `/kiro2:status` tüm servislerin durumunu gösterir.
