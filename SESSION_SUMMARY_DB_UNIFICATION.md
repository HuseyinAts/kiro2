# KIRO2 Veritabani Yapilandirmasi Birlestirme

## Tarih: 2026-01-13

## Problem
3 farkli DB config vardi:
- config.py: teknofest_db:5432
- alembic/env.py: kiro2:5434 (HARDCODED)
- docker-compose.yml: turkiye_sinav_db:5432

## Cozum
Tek .env dosyasi (kok dizin) - tum dosyalar buradan okuyor

## Guncellenen Dosyalar
1. backend/alembic/env.py - hardcoded URL kaldirildi
2. backend/core/config.py - default URL kaldirildi
3. docker-compose.yml - kiro2 adi ve kiro2_* container isimleri
4. .gitignore - .env.example commit edilebilir

## Yeni Standart
- DB adi: kiro2
- Local port: 5434
- Docker port: 5432
- Tek kaynak: .env dosyasi

## Dogrulama
- Config: OK
- Alembic: e73a8e0797c1 (head)
