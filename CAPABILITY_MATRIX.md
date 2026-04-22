# KIRO2 — Capability Matrix (öğrenci tam kapsam planı)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`  
**Son güncelleme:** 2026-04-23 — **Kanıt kilidi** (GF1+GF3, kod ağacı `2a1aa56`); bu satırları içeren `CAPABILITY_MATRIX` sürümleri: `95b6122` (kanıt kilidi commit) → `4ac61c3` (SHA/HEAD netliği) — aşağı §.  

Sütunlar: `Journey | API/Route | FE route | Son test (SHA) | Durum | Not`

| Journey | API/Route | FE route | Son test | Durum | Not |
|---------|-----------|----------|----------|-------|-----|
| **J1** Kayıt / giriş / çıkış / refresh | `api.auth` — `POST /api/v1/auth/giris`, `/api/v1/auth/login` (EN), `POST /api/v1/auth/kayit`, `/register`, refresh/cookie path `backend/api/auth.py` | `/login`, `/register` (`App.tsx`) | `2a1aa56` — **`test_gf1_login_and_me` PASS** (lokal :8000) | **Yeşil (lokal golden)** | GF1 yalnızca **giriş** + token; **kayıt / çıkış / refresh** ayrı golden/CI yok. **CI hâlâ** uvicorn olmadan skip; prod kanıtı ayrı. |
| **J2** Profil, STUDENT | `api.auth` — `GET /api/v1/auth/profil`, `/api/v1/auth/me`, `PUT /api/v1/auth/profile` | `/profile` (çok rollü `ProfilePage`) | `2a1aa56` — **GF1** içinde `GET /api/v1/auth/me` 200, `test@kiro2.com` | **Yeşil (lokal golden)** | Aynı koşu; `PUT /profile` ve FE sayfası ayrı doğrulama isteyebilir. |
| **J3** Soru bankası (liste / çöz / kaydet) | `api.question_bank_v2_routes` (`/api/v2/...`), `api.question_crud` (search vb.), `api.osym_questions_api` | `/soru-meydani`, `/learning-path` (ilgili akışlar) | `2a1aa56` (kod) | **Sarı** | Ayrı golden yok; öğrenci soru bankası uçtan uca hâlâ kilitlenmedi. |
| **J4** Sınav oturumu + cevaplar | `api.sinav` — `/api/v1/osym-exam/...`, `api.exam_answer_tracking`, `api.exam_performance` | `/exam/start`, `/exam/:sinavId`, `/exam/history`, `/exams` | `2a1aa56` — **`test_gf3_exam_configs_list` PASS** → `GET /api/v1/osym-exam/exam-configs` 200 | **Yeşil (lokal golden, giriş yüzeyi)** | Sınav **başlat / cevap gönder** için ayrı golden veya E2E gerekir; bu satır config listesini kilitle. |
| J10–J13 Chroma | `api.v1.semantic_search`, clustering, recommendation, duplicate | TBD | `b59f511`+GF150/38/37/47/152 | **Yeşil (health+API smoke)** | F4: `content_recommendation` gövde `user_id` yalnızca kendisi veya staff (admin/super_admin/öğretmen). Profil `GET .../user/{id}/profile` rol kontrolü `UserRole` ile düzeltildi. Health: GF150. Arama GF38, clustering GF37, recommendations GF47, duplicates/check GF152. Tohum: `scripts/chroma_seed_kiro2_questions.py`. |
| J6 Offline | `api.offline_sync_api` | TBD | `c401e35` | **Yeşil** | `GET /api/v1/offline/health` (200, DB ping). Canlı: S1 `sync-status`, S2 `sync-package?limit=5` → `package_id` + `total_questions=5` (2026-04-23). `tests/unit/services/test_offline_sync_service.py` (6 PASS). Tam HTTP matrisi (S1–S6): `.cursor/plans/20260420_offline_sync_debt_2_RESULT.md` (Round 2). Plan: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md`. |
| J7 PWA | `api.pwa_sync_api` — `GET /api/v1/sync/health`, `GET /api/v1/push/health`, `POST /api/v1/sync/*`, `POST /api/v1/push/subscribe` | `backgroundSyncService.ts`, `sw.ts` | GF150, `2ec932f`+ | **Yeşil** (health) | Public path yok: `/api/pwa-sync-api` sadece eski log yanlışlığı; `routers/loader` kök `APIRouter` için boş prefix artık default’a dönmüyor. Subscribe stub, mutating uç F4. |
| Live session | `api.live_session_routes` | TBD | `44f9fc6` + GF150 | **Yeşil** (health) | `GET /api/v1/live-sessions/health` 200, `database: true` (GF150). ORM/ tablo: `session_participants` (önceki pilot); tam oturum journey F4+ |
| Router log | `loader` + `ROUTER_CATEGORIES` | — | — | **Yeşil** | `"search"` kategorisi eklendi |

**Durum:** Kırmızı / Sarı / Yeşil — plan §3 terimleri.

---

## Kanıt kilidi (lokal golden, 2026-04-23)

| Öğe | Değer |
|-----|--------|
| **Kod (GF koşuldu)** | `2a1aa56` / `2a1aa56dac34ec19aee88a1ec79ae0f2dce82a6e` — golden’ların dayandığı ağaç. |
| **Matris / doküman (en son)** | `4ac61c3` / `4ac61c3786a2bf01aff89719a485d87876e64b5d` — `CAPABILITY_MATRIX.md` (önce `95b6122` ile kilit, sonra `4ac61c3` ile SHA ayrımı). |
| **Backend** | `http://localhost:8000` (lokal; koşu anında çalışır durumda) |
| **Seed** | `python scripts/seed_mvp_data.py` — `DATABASE_URL` `backend/.env` ile; `test@kiro2.com` zaten mevcuttu (idempotent) |
| **Komut** | `cd backend` → `$env:BACKEND_URL="http://localhost:8000"` → `python -m pytest tests/e2e/test_golden_flows.py::test_gf1_login_and_me tests/e2e/test_golden_flows.py::test_gf3_exam_configs_list -v --tb=short` |
| **Sonuç** | **2 passed** (süre ~1.5–2s) |

---

## Otomatik üçlü doğrulama (2026-04-23)

- **Güncel repo `HEAD`:** `4ac61c3` / `4ac61c3786a2bf01aff89719a485d87876e64b5d`.  
- **Aşağıdaki tarama** (`alembic` / `loader`) o oturumda **kod ağacı** `2a1aa56…` iken alındı. `2a1aa56` → `4ac61c3` arası yalnız **doküman** (migration yok) ise `alembic heads` sonucu aynı kalmalıdır; migration dosyaları eklendiyse yeniden çalıştır.

### 1) CI son durumu (tanım + bu ortamda sınır)

- **Kaynak:** `.github/workflows/ci.yml`.
- **Zincir:** `quality` (ruff, mypy, bandit, safety, semgrep) → `backend-test` (Postgres hizmeti, `alembic upgrade head`, `pytest tests/` `--cov-fail-under=60`, `-x`) → `frontend-test` (lint, `type-check`, `npm test` coverage eşiği, `build`). `summary` job başarısız job’larda fail.
- **`e2e-test` (Playwright):** yalnızca `pull_request` ve `backend-test` + `frontend-test` sonrası; `push` pipeline’ında koşmaz.
- **Bu makinede:** `gh` CLI yok — GitHub’daki **son run** manuel açılmalı: [Actions](https://github.com/HuseyinAts/kiro2/actions/workflows/ci.yml).
- **Kritik bulgu:** `backend-test` **uvicorn başlatmaz**; `tests/e2e/test_golden_flows.py` `httpx` ile `localhost:8000`’e bağlanamazsa testler **skip**. J1–J2 “yeşil” iddiası **CI backend job’u ile tek başına kanıtlanmaz**; lokal veya ayrı E2E job gerekir.

### 2) `alembic heads` + taze DB hipotezi

- **Çalıştırılan:** `cd backend && python -m alembic heads` → **tek head:** `diary_drift_recovery_20260422` (`KIRO2_SESSION_BRIEFING` ile uyumlu).
- **`alembic branches`:** Geçmişteki merge/branchpoint satırları; **çift head** anlamına gelmez.
- **Taze DB:** CI adımı `cd backend && alembic upgrade head` → boş `kiro2_test` üzerinde tam zincir. `20260422_diary_drift_recovery.py` docstring: idempotent/IF NOT EXISTS, taze kurulumda diary şeması oluşur — **briefing’deki eski “diary sadece dev DB’de” drifti bu revision ile taze-DB yoluna alınmış**.

### 3) J1–J4 route / FE taraması (kaynak)

- **Backend:** `backend/routers/loader.py` `ROUTER_MAPPING` → `api.auth`, `api.question_bank_v2_routes`, `api.sinav`, `api.exam_*`; `backend/api/auth.py` `prefix=/api/v1/auth`, `/giris` `/login` `/kayit` `/me` `/profil` `/profile`.
- **Frontend:** `frontend/src/App.tsx` — `/login`, `/register`, `/profile`, `/soru-meydani`, `/learning-path`, `/exam/...`, `/exams`.
- **Golden referans:** `backend/tests/e2e/test_golden_flows.py` — `test_gf1_login_and_me`, `test_gf3_exam_configs_list`, vb. (canlı backend varsayar).

---

**Chroma notu:** Ortamda `CHROMADB_HOST` tanımlıysa duplicate / content recommendation / semantic search v1 **HttpClient** kullanır; `GET /api/v1/duplicates/health`, `GET /api/v1/recommendations/health`, `GET /api/v1/search/health` yanıtlarında `chroma_connection_mode`. MCP: `health_check` / `chromadb://health` JSON’da aynı alan (`http` \| `embedded`). Dev: `docker compose -f docker-compose.dev.yml --profile chroma up` + `.env` içinde `CHROMADB_HOST=chroma` (ağda `chroma:8000`, host `localhost:8001`).
