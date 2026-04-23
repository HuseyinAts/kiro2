# 2026-03-28 Infrastructure Audit — P0 Re-verification

**Tarih:** 2026-04-23  
**Yöntem:** Repo dosyalarının güncel içeriği ile audit maddeleri karşılaştırıldı (otomatik commit araması yok).  
**Durum anahtarı:** `acik` | `kismi` | `duzeldi` (audit iddiasına göre)

## Docker & Nginx (D1–D7)

| ID | Durum | Güncel kanıt |
|----|--------|----------------|
| D1 | kismi | [`docker-compose.dev.yml`](../../docker-compose.dev.yml) `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres123}` — env ile override edilebilir; **default hâlâ git’te**. |
| D2 | kismi | Aynı dosyada `JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret-not-for-production-32-chars}` — **fallback git’te**. |
| D3 | duzeldi | [`frontend/nginx.conf`](../../frontend/nginx.conf) satır 20: `Content-Security-Policy` mevcut. |
| D4 | duzeldi | Aynı dosya satır 21: `Strict-Transport-Security` mevcut. |
| D5 | duzeldi | [`backend/Dockerfile.minimal`](../../backend/Dockerfile.minimal) satır 34–37: `USER kiro2`. |
| D6 | kontrol | `Dockerfile.dev` ayrıca okunmalı (bu turda minimal doğrulandı). |
| D7 | kontrol | `Dockerfile.exporter` ayrıca okunmalı. |

## CI/CD (G1–G8)

| ID | Durum | Not |
|----|--------|-----|
| G1–G8 | kontrol | [`claude-review.yml`](../../.github/workflows/claude-review.yml), [`security.yml`](../../.github/workflows/security.yml), [`deploy.yml`](../../.github/workflows/deploy.yml), [`release.yml`](../../.github/workflows/release.yml) dosyalarında pin/env düzeltmeleri **bu belgede satır satır doğrulanmadı**; ayrı PR önerilir. |

## Alembic (A1–A6)

| ID | Durum | Not |
|----|--------|-----|
| A1–A6 | kontrol | İlgili `backend/alembic/versions/*` dosyaları tarihsel; **canlı DB’de upgrade dry-run** ve code review ile teyit gerekir. |

## Scripts & Config (X1–X5)

| ID | Durum | Not |
|----|--------|-----|
| X1–X5 | kontrol | [`seed_mvp_data.py`](../../backend/scripts/seed_mvp_data.py), [`config.py`](../../backend/core/config.py) vb. — zayıf default/print riski **audit ile uyumlu kontrol** için ayrı tarama. |

## Sonuç

- **D3, D4, D5** audit’e göre **iyileşmiş** görünüyor (nginx + minimal image).  
- **D1, D2** tipik dev compose pattern’i: production’da **`.env` zorunlu**, default’ları repodan kaldırma P1 olarak kalır.  
- **G*, A*, X*** maddeleri için bu dosya **re-verify başlangıcıdır**; kapanış = her madde için dosya+satır teyidi veya “wontfix” kararı.

**Sonraki adım:** P0 kalan maddeleri issue’lara böl; `security.yml` action pin ve `claude-review` env izolasyonunu önceliklendir.
