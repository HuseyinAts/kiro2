# KIRO2 — Capability Matrix (öğrenci tam kapsam planı)

**Plan:** `.cursor/plans/20260421_student_ready_autonomous_master.md`  
**Son güncelleme:** 2026-04-23 — CI §1: `backend-test` içinde **P0 Golden** (uvicorn+**9** test: GF1, GF3, GF3b, GF3c, **GF1x**, **GF3d**, **GF6w**, **GF1w**, **GF3w**) — J1 çıkış, J4 complete, K4 admin soru, K2/K3 BKT/regresyon. Önceki: 6 test. Matris: `git log -1 -- CAPABILITY_MATRIX.md`.  

Sütunlar: `Journey | API/Route | FE route | Son test (SHA) | Durum | Not`

| Journey | API/Route | FE route | Son test | Durum | Not |
|---------|-----------|----------|----------|-------|-----|
| **J1** Kayıt / giriş / çıkış / refresh | `api.auth` — `POST /api/v1/auth/giris`, `/api/v1/auth/login` (EN), `POST /api/v1/auth/kayit`, `/register`, `POST /api/v1/auth/cikis`, refresh/cookie path `backend/api/auth.py` | `/login`, `/register` (`App.tsx`) | `3ebcfff` — **`test_gf1_login_and_me`** + **`test_gf1x_logout_invalidates_bearer_token`** (P0) | **Yeşil (CI P0)** | Çıkış + blacklist **GF1x** ile kilitli. Kayıt / cookie-refresh ayrı golden isteyebilir. |
| **J2** Profil, STUDENT | `api.auth` — `GET /api/v1/auth/profil`, `/api/v1/auth/me`, `PUT /api/v1/auth/profile` | `/profile` (çok rollü `ProfilePage`) | `3ebcfff` — **GF1** içinde `GET /api/v1/auth/me` 200, `test@kiro2.com` | **Yeşil (CI P0 / GF1)** | `PUT /profile` ve FE sayfası ayrı doğrulama isteyebilir. |
| **J3** Soru bankası (liste / çöz / kaydet) | Liste: `GET /api/v1/osym/subjects`. Çöz+kaydet: `POST /api/v1/osym-exam/{id}/save-answer` (oturum: `create` → `start` → `current-question`) | `/learning-path` (FE duman: `j3-learning-path-smoke.spec.ts`); Not: `/soru-meydani` = **Soru Meydanı forumu** (sosyal), OSYM bankası değil. | **GF3b+GF3c** `PASS` lokal; FE: `npx playwright test j3-learning-path-smoke` + `E2E_TEST_PASSWORD` | **Yeşil (lokal: liste + save smoke; FE isteğe bağlı)** | BKT/detay: `test_gf1w_save_answer_updates_mastery` (daha sıkı). |
| **J4** Sınav oturumu + cevaplar | `api.sinav` — `/api/v1/osym-exam/...`, `api.exam_answer_tracking`, `api.exam_performance` | `/exam/start`, `/exam/:sinavId`, `/exam/history`, `/exams` | `3ebcfff` — **GF3** (config) + **GF3c** (save-answer) + **GF3d** (`POST .../complete`, P0) | **Yeşil (CI P0)** | Tam oturum smoke: oluştur → cevap → **complete** (`test_gf3d_exam_session_complete_smoke`). |
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
| **Kod (GF koşuldu)** | `3ebcfff` — P0 golden seti (bkz. `ci.yml` + `run_p0_golden_local.ps1`). |
| **Matris / doküman** | **İlk** `95b6122` (Kanıt kilidi bölümü eklendi). Sonraki: `4ac61c3` (Kod vs matris SHA ayrımı) ve yalnız metin commit’leri — migration **yok**. Anlık: `git log -1 --format=%h` bu dosyada. |
| **Backend** | `http://localhost:8000` (lokal; koşu anında çalışır durumda) |
| **Seed** | `python scripts/seed_mvp_data.py` — `DATABASE_URL` `backend/.env` ile; `test@kiro2.com` zaten mevcuttu (idempotent) |
| **Komut (API)** | `cd backend`; `$env:BACKEND_URL="http://localhost:8000"`; **9** test — tam liste: `.github/workflows/ci.yml` `P0 Golden Flow smoke` veya `scripts/run_p0_golden_local.ps1` |
| **Sonuç** | **9 passed** (GF1, GF3, GF3b, GF3c, GF1x, GF3d, GF6w, GF1w, GF3w; lokal/CI) |
| **FE (opsiyonel)** | `cd frontend` → `E2E_TEST_PASSWORD=...` → `npx playwright test j3-learning-path-smoke` — dev sunucu `VITE_APP_URL` / :3001 |
| **Tek komut (lokal, optimum)** | `powershell -ExecutionPolicy Bypass -File scripts/run_p0_golden_local.ps1` — önce :8000 health; **9** P0 test (J1/J4/K4 + K2/K3). **CI’da** aynı set `uvicorn` + `seed` sonrası `backend-test` job’unda koşar. |

---

## Otomatik üçlü doğrulama (2026-04-23)

- **Doküman** bu dosyadaki tarama notları: **kod ağacı** o oturumda `2a1aa56…` iken alındı. `2a1aa56`’dan sonraki commit’lerde yalnız `CAPABILITY_MATRIX.md` (ve benzeri dok) değiştiyseniz `alembic heads` sonucu aynı kalır; **migration** eklendiyse yeniden `alembic heads` çalıştır.  
- **Güncel `HEAD`:** repoda `git rev-parse HEAD` — doküman-only commit’ler matrix içeriğini değil, yalnız bu paragrafın “en son sürüm” anlamını etkiler.

### 1) CI son durumu (tanım + bu ortamda sınır)

- **Kaynak:** `.github/workflows/ci.yml`.
- **Zincir:** `quality` (ruff, mypy, bandit, safety, semgrep) → `backend-test` (Postgres hizmeti, `alembic upgrade head`, `pytest tests/` `--cov-fail-under=60`, `-x`) → `frontend-test` (lint, `type-check`, `npm test` coverage eşiği, `build`). `summary` job başarısız job’larda fail.
- **`e2e-test` (Playwright):** yalnızca `pull_request` ve `backend-test` + `frontend-test` sonrası; `push` pipeline’ında koşmaz.
- **Bu makinede:** `gh` CLI yok — GitHub’daki **son run** manuel açılmalı: [Actions](https://github.com/HuseyinAts/kiro2/actions/workflows/ci.yml).
- **P0 golden (güncel):** Aynı `backend-test` job’unda migration → **MVP seed** → tam `pytest` → **`P0 Golden Flow smoke`**: `uvicorn` :8000 + **9** `httpx` testi (GF1, GF3, GF3b, GF3c, GF1x, GF3d, GF6w, GF1w, GF3w). **Not:** İlk `pytest tests/` adımında sunucu yok; `test_golden_flows` içindeki **diğer** golden’lar çoğunlukla **skip** kalır — merge gate bu 9’luk paketle sınırlı.

### 2) `alembic heads` + taze DB hipotezi

- **Çalıştırılan:** `cd backend && python -m alembic heads` → **tek head:** `diary_drift_recovery_20260422` (`KIRO2_SESSION_BRIEFING` ile uyumlu).
- **`alembic branches`:** Geçmişteki merge/branchpoint satırları; **çift head** anlamına gelmez.
- **Taze DB:** CI adımı `cd backend && alembic upgrade head` → boş `kiro2_test` üzerinde tam zincir. `20260422_diary_drift_recovery.py` docstring: idempotent/IF NOT EXISTS, taze kurulumda diary şeması oluşur — **briefing’deki eski “diary sadece dev DB’de” drifti bu revision ile taze-DB yoluna alınmış**.

### 3) J1–J4 route / FE taraması (kaynak)

- **Backend:** `backend/routers/loader.py` `ROUTER_MAPPING` → `api.auth`, `api.question_bank_v2_routes`, `api.sinav`, `api.exam_*`; `backend/api/auth.py` `prefix=/api/v1/auth`, `/giris` `/login` `/kayit` `/me` `/profil` `/profile`.
- **Frontend:** `frontend/src/App.tsx` — `/login`, `/register`, `/profile`, `/soru-meydani`, `/learning-path`, `/exam/...`, `/exams`.
- **Golden referans:** `backend/tests/e2e/test_golden_flows.py` — `test_gf1_login_and_me`, `test_gf3_exam_configs_list`, `test_gf3b_osym_subjects_reachable`, `test_gf3c_exam_session_save_answer_smoke` (J3), vb. (canlı backend varsayar).

---

**Chroma notu:** Ortamda `CHROMADB_HOST` tanımlıysa duplicate / content recommendation / semantic search v1 **HttpClient** kullanır; `GET /api/v1/duplicates/health`, `GET /api/v1/recommendations/health`, `GET /api/v1/search/health` yanıtlarında `chroma_connection_mode`. MCP: `health_check` / `chromadb://health` JSON’da aynı alan (`http` \| `embedded`). Dev: `docker compose -f docker-compose.dev.yml --profile chroma up` + `.env` içinde `CHROMADB_HOST=chroma` (ağda `chroma:8000`, host `localhost:8001`).
