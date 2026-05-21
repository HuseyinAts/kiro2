# KIRO2 Backend Audit — 2026-05-21 Session 178

## Executive Summary

KIRO2 backend is a mature FastAPI codebase (~109K satır, 143+ API dosyası, 174 Golden Flow testi) with solid architectural foundations: dual auth (Cookie + Bearer), Pydantic v2 validation, async SQLAlchemy 2.x, and a well-implemented 4-algorithm learning pipeline (BKT+IRT+FSRS+ZPD). **Beta için 5 P0 sorun kritik** — bunların 3'ü auth eksikliği/hardcoded credential, 2'si middleware güvenlik ihlali.

**Toplam:** 5 P0 / 8 P1 / 6 P2

---

## P0 — Beta-blocker

**B-P0-1: `api/soru_bankasi.py` — 3 endpoint auth eksik (IDOR/data leak)**
- `backend/api/soru_bankasi.py:244` (`rastgele_sorular_sec`), `:459` (`konu_listesi_getir`), `:492` (`soru_bankasi_istatistikleri`) — `Depends(get_current_user)` yok
- Anonim erişim → YKS soru bankası ifşa, platform istatistikleri görünür
- Fix: Her üçüne `current_user: AuthenticatedUser = Depends(get_current_user)` ekle

**B-P0-2: `core/api_optimizer.py:131` — Middleware'den `raise HTTPException` (GF99 ihlali)**
- `RateLimitMiddleware.dispatch()` `raise HTTPException(429)` → client 500 görür
- `.claude/rules/middleware.md` ihlali
- Fix: `return JSONResponse(status_code=429, content={...})`

**B-P0-3: `seed_admin.py:84` — Kaynak kodda hardcoded admin şifresi**
- `admin_password = "Admin123!"` — git tracked
- Repo erişimi olan herkes admin'i ele geçirir
- Fix: `ADMIN_PASSWORD = os.environ["ADMIN_SEED_PASSWORD"]` zorunlu

**B-P0-4: 53+ quality script + setup_database.py — hardcoded DSN fallback**
- `DSN = os.getenv("DATABASE_URL", "postgresql://postgres:1470@localhost:5434/kiro2")` pattern
- Repo paylaşımında DB password leak
- Fix: Fallback kaldır, `if not DSN: sys.exit(1)`

**B-P0-5: `core/auth_rate_limiting.py:155,183` — Middleware HTTPException pattern tutarsız**
- `AuthRateLimiter.check_rate_limit()` `raise HTTPException(429)` ediyor
- Dispatch level'da `except` ile yakalanıyor (geçici fix), ama caller doğrudan çağırırsa kırılır
- Fix: `check_rate_limit()` `bool` dönsün, caller `JSONResponse` üretsin

---

## P1 — Production-quality

**B-P1-1: `api/enhanced_user_management_api.py:64` — Deprecated KullaniciServisi üretim API'sinde**
- `from services.user_service import KullaniciServisi as UserService` — in-memory, restart'ta veri kaybı
- Fix: DB-backed `User` ORM + AsyncSession

**B-P1-2: Migration tree multi-head riski**
- `20260126_irt_4pl` + `20260123_cascade` paralel branch'ler
- `001_create_performance_indexes.py` ayrı root
- Verify: `alembic heads` çıktısı doğrulanmalı, gerekirse `alembic merge heads`

**B-P1-3: `api_optimizer.py:124` — `X-User-ID` header trust → rate limit bypass**
- Client istediği user_id ile rate limit bucket'ı değiştirebilir
- Fix: `request.state.user.id` veya auth context'ten al

**B-P1-4: `soru_bankasi_service.py:20` — Legacy enum import**
- `from models.database import ExamType, QuestionDifficulty, SubjectArea` (legacy `questions` modelinden)
- Coupling sorunlu
- Fix: Canonical enum kaynağına ayır (`models.enums_db`)

**B-P1-5: `api/veli.py` + benzer TR-named files — auth pattern tutarsızlığı**
- `veli_yetkisi_kontrol` vs `get_current_user` karışımı
- Audit dışı kalmış endpoint'ler olabilir
- Fix: TR-named files toplu audit

**B-P1-6: `bkt_service.py:get_params()` — None subject_slug AttributeError riski**
- `if subject_slug.lower() in SOZEL_SUBJECTS` — None gelirse crash
- Fix: `if (subject_slug or "").lower() in SOZEL_SUBJECTS`

**B-P1-7: `algorithms/irt_model.py` — Newton-Raphson edge case**
- 2. türev sıfır ise break (var), ama `responses` boş ise `IndexError` riski (mevcut guard ile geçici)
- Fix: Defensive empty-list check satır 186'da

**B-P1-8: `question_bank.py` ORM — `QuestionDifficultyLevel` lowercase vs DB UPPERCASE**
- Enum: `"very_easy"` | DB: bilinmiyor (audit gerek)
- Verify: `SELECT DISTINCT difficulty_level FROM question_bank LIMIT 10`

---

## P2 — Improvement

**B-P2-1: Test coverage %53 — hedef %80**
- 12,607 PASS / 1,337 SKIP / 7 collection error
- BKT/IRT/FSRS dedicated parametrik unit test eksik
- 205 dosyada `assert True`/`pytest.skip` — çoğu skip guard, 30-50'si reward hacking riskli

**B-P2-2: Golden Flow 174 test, 2 SKIP — saturated suite**
- CSRF middleware (GF99), JWT blacklist, FSRS (GF12), CAT (GF13) covered
- Wave 15-16 %0 hit rate → mature

**B-P2-3: `setup_database.py` — wrong DB name `turkiye_sinav_db`**
- Production DB `kiro2`
- Legacy script — `_deprecated/` klasörüne taşı

**B-P2-4: `soru_bankasi_service.istatistikler_getir()` — in-memory mi?**
- DB-backed mi cache-backed mi netleştirilmeli

**B-P2-5: Phase 7 Gemini Batch — GEMINI_API_KEY boş kontrolü eksik**
- `GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")` — boş string ile devam ediyor
- Fix: `if not GEMINI_KEY: sys.exit(1)`

**B-P2-6: Phase 6 kNN — 250MB numpy yükü, Docker memory limit yok**
- 81K embedding × 768 float32 + chunked matmul = ~560MB peak
- Docker container OOM riski

---

## Domain Detail

### 1. API Layer
- **Endpoint sayısı (tahmini):** ~1,220+ (143 dosya × ~8 endpoint)
- **response_model kapsama:** 630 occurrence / 143 dosya
- **Auth dependency:** 883 occurrence / 135 dosya
- **Auth eksik (P0):** 3 endpoint (soru_bankasi)
- Path naming: 22 Turkish-only path baseline (Session 135) — accepted

### 2. Service Layer
- `soru_bankasi_service.py` doğru `QuestionBankItem` kullanıyor, `is_active=True` filtresi var
- `bkt_service.py` 4-algoritma pipeline tam entegre
- `KullaniciServisi` deprecated ama 1 API'de aktif

### 3. Models / Database
- SQLAlchemy 2.x Mapped/mapped_column pattern
- `Question` (legacy) vs `QuestionBankItem` (prod) ayrımı tam
- Curator `reviewed_at` migration (Session 179) eklendi
- ORM drift HIGH=203, MEDIUM=455, LOW=206

### 4. Algoritmalar
- **BKT:** Standart, numerical guard var, test az
- **IRT 4PL:** Clamp + Fisher info + MLE Newton-Raphson — sağlam
- **FSRS:** 17-param + Türk kültür faktörleri (Ramazan, YKS, hijri_converter graceful)
- **ZPD:** BKT bridge formula doğru

### 5. Auth / Security
- Bcrypt + JWT (15-min access + 7-day refresh) + Redis blacklist
- CSRF double-submit, Bearer early-return
- Sorunlar: P0-3 (hardcoded), P0-2 (middleware HTTPException)

### 6. Testing
- 12,607 PASS / 1,337 SKIP / coverage %53
- Golden Flow 174 test, 2 SKIP
- BKT/IRT/FSRS dedicated parametrik test eksik

### 7. Curator UI Backend
- Production-ready
- 3 endpoint admin-only, ORM refactored
- audit_logs raw SQL (model çakışması nedeniyle, acceptable)
- `reviewed_at` ORM eklendi, defansif `getattr` artık gereksiz (temizlenebilir)

### 8. Phase 5/6/7 Metadata Pipeline
- Phase 5: %100 Gold embedding coverage
- Phase 6: numpy bulk kNN (3000x speedup)
- Phase 7: Gemini Batch API, %99.85 coverage, MAX_OUTPUT_TOKENS=16000
- Scripts production-ready ama CI/CD entegre değil

---

## Metrics Snapshot

| Metrik | Değer |
|---|---|
| API endpoint (tahmin) | ~1,220+ |
| response_model kapsama | 630/143 dosya |
| Auth dependency | 883/135 dosya |
| Auth eksik (P0) | 3 |
| Test PASS | ~12,607 |
| Test SKIP | ~1,337 |
| Coverage statement | ~53% |
| Golden Flow | 174 (2 SKIP) |
| Migration dosyası | 65 |
| ORM HIGH drift | 203 |
| question_bank aktif | 167,559 |
| v_safe_for_beta | 22,325 (S178 R1 sonrası 12,362 yeni eklendi) |
| Middleware HTTPException ihlali | 2 |
| Hardcoded credential | 53+ script + 2 uygulama |

---

## Recommendations Priority

1. **B-P0-1** soru_bankasi.py auth (30 dk)
2. **B-P0-2** api_optimizer.py middleware fix (15 dk)
3. **B-P0-3** seed_admin.py env var (15 dk)
4. **B-P0-4** Script DSN fallback (1 saat)
5. **B-P0-5** auth_rate_limiting refactor (45 dk)
6. **B-P1-1** KullaniciServisi remove (30 dk)
7. **B-P1-2** Migration head verify (15 dk)
8. **B-P1-3** X-User-ID fix (20 dk)
