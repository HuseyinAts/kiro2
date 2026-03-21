# FAZ 2: Entegrasyon Tarama Raporu

**Tarih:** 2026-03-21
**Branch:** audit/fullstack-20260321

---

## 1. nginx Proxy Konfigurasyonu

### Location Bloklari

| Location | Hedef | Notlar |
|----------|-------|--------|
| `/api/` | `backend:8000` | Genel API proxy |
| `/api/v1/stream/` | `backend:8000` | SSE (buffering off, timeout 300s) |
| `/api/v1/streaming/` | `backend:8000` | SSE (buffering off, timeout 300s) |
| `/healthz` | local | nginx healthcheck |
| `/static/` | `backend:8000` | Statik dosyalar |
| `/health` | `backend:8000` | Backend health |
| `/` | local | SPA fallback (index.html) |

**Durum:** OK — `/api/v1/streaming/` blogu onceki session'da eklendi.

### Eksik Security Header'lar
- `X-Content-Type-Options: nosniff` — YOK
- `X-Frame-Options: DENY` — YOK
- `Referrer-Policy` — YOK
- `Strict-Transport-Security` — YOK (prod icin gerekli)

**Ciddiyet:** MEDIUM (prod deploy oncesi eklenmeli)

---

## 2. CORS Konfigurasyonu

**Mevcut:**
```python
allow_origins=["http://localhost:3000", "http://localhost:3001"]
```

**Sorun:** Production origin eklenmemis. `docker-compose.mvp.yml` icinde `ALLOWED_ORIGINS` env var yok.

**Fix onerisi:** `.env.mvp` dosyasina production origin ekle, `application.py`'da env var'dan oku.

**Ciddiyet:** HIGH (prod deploy'da CORS hatasi verecek)

---

## 3. VersionRedirectMiddleware

**Kural sayisi:** 32 (28 `/api/X` → `/api/v1/X` + 4 prefix-siz)

**Eksik redirect'ler (frontend cagiriyor ama redirect yok):**

| Frontend Path | Backend Path | Redirect Var mi? |
|--------------|-------------|-----------------|
| `/api/v1/...` (cogu) | `/api/v1/...` | Gerek yok (direkt) |
| `/api/sync/progress` (sw.ts) | `/api/v1/sync/progress` | Onceki session'da FIX (sw.ts'de v1 eklendi) |

**Durum:** OK — Buyuk cogunluk direkt `/api/v1/` kullaniyor, redirect'ler backward compat icin.

---

## 4. Hardcoded URL'ler

### Gercek Hardcoded (env var olmadan):
| Dosya | Satir | URL | Ciddiyet |
|-------|-------|-----|----------|
| SystemSettings.tsx | 31 | `https://localhost:3000` | LOW |

### Fallback (env var ile):
| Dosya | Satir | URL | Durum |
|-------|-------|-----|-------|
| AIChatAssistant.tsx | 11 | `localhost:8000` | OK (VITE_API_URL fallback) |
| DepartmentInfo.tsx | 11 | `localhost:8000` | OK (VITE_API_URL fallback) |
| StudentReviews.tsx | 11 | `localhost:8000` | OK (VITE_API_URL fallback) |
| TeacherPool.tsx | 11 | `localhost:8000` | OK (VITE_API_URL fallback) |
| UniversityInfo.tsx | 11 | `localhost:8000` | OK (VITE_API_URL fallback) |
| config/index.ts | 14-17 | `localhost:8000/3000` | OK (dev config) |

**Not:** Test dosyalarindaki hardcoded URL'ler (test.config.ts, setup.ts, mvp-smoke.spec.ts) kabul edilir.

---

## 5. v2 Endpoint Durumu

| Frontend Cagrisi | Backend | Durum |
|-----------------|---------|-------|
| `/api/v2/...` (KnowledgeGraphViz) | `question_bank_v2_routes.py` prefix `/api/v2` | VAR |
| `/api/v2/quality/...` | `wave2b_quality_routes.py` prefix `/api/v2/quality` | VAR |

**Durum:** OK — v2 router'lar yuklu ve calisiyor.

---

## 6. Frontend-Backend URL Mismatch

### Onceki session'da duzeltilen:
- `/api/v1/user/export-data` → `/api/v1/users/export-data` (ModernSettingsPage)
- `/api/v1/user/delete-account` → `/api/v1/users/delete-account` (ModernSettingsPage)
- `/api/sync/progress` → `/api/v1/sync/progress` (sw.ts)

### Kontrol edilen ama sorun bulunmayan:
- Frontend `credentials: 'include'` buyuk cogunlukta mevcut (152/268 fetch)

---

## 7. Docker Compose

**docker-compose.mvp.yml durumu:**
- Backend: `host.docker.internal` ile DB/Redis baglantisi
- Frontend: nginx port 3000
- Volume: `/static/crops:ro` mount

**Eksikler:**
- `ALLOWED_ORIGINS` env var eksik
- Health check timeout optimizasyonu yapilabilir

---

## STATUS: TAMAM
