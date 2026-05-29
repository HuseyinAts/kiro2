## Session Handoff — 2026-05-29 (KVKK Faz 2 IMPLEMENTASYON)

**Branch:** feat/kvkk-faz2 | **Son commit:** ca234b3a8
**Stratejik yön:** Kurumsal/okul (B2B) — roadmap A+B+C+D (auto-memory: project_go-to-market.md)

### ✅ KVKK Faz 2 veli onay akışı — 11/11 TASK TAMAM (inline TDD, dispatch yok)
Plan: `docs/superpowers/plans/2026-05-29-kvkk-faz2-veli-onay.md`

| Task | Commit | Doğrulama |
|---|---|---|
| 1 model+token (önceki S) | 669e75e3d | 3/3 unit |
| 2 migration | 6672132a9 | DB 15 kolon+2 idx (5434) |
| 3 email_util | fcae9ca7a | 2/2 unit |
| 4 VeliOnayService | 2bca028fd | 4/4 @5434 |
| 5 endpoints verify/withdraw/status/resend | 024bfbf1d | 2/2 |
| 6 register→consent tetikleme | 55cf64e96 | 1/1 |
| 7 require_veli_consent dep | b7fea5e7f | 2/2 |
| 8 study_rooms create/join enforcement | 62afb89e5 | 1/1 smoke |
| 9 frontend VeliOnayPage+route+authService | 50e97ed57 | tsc OK |
| 10 golden flow + wave history | d0bcd0368 | collect OK |
| 11 lint fix | ca234b3a8 | full suite **15/15 PASS** |

### 🔧 State
- **Integration test deseni:** `KVKK_VERIFY_DSN` env (5434 prod şeması) + strict-rollback fixture (`join_transaction_mode=create_savepoint`). HER koşuda sıfır pollution doğrulandı. Çalıştırma: `export KVKK_VERIFY_DSN="$(grep ^DATABASE_URL= backend/.env|cut -d= -f2-|tr -d '\r')" && USE_POSTGRES_TESTS=true pytest tests/integration/test_veli_*.py tests/integration/test_require_veli_consent.py`
- **Kalıcı:** `psycopg2-binary` kuruldu (alembic sync driver). DB'de `veli_consent` tablosu canlı (5434, alembic head=kvkk2_veli_consent_20260529).
- Kök conftest `db_session` fixture PRE-EXISTING BROKEN (ScopeMismatch) — dokunulmadı; KVKK testleri kendi inline fixture'ını kullanıyor.

### ⏳ Bekleyen (operatör / sonraki session)
- **Backend redeploy** — canlı backend (localhost:8000) STALE; `/api/v1/auth/veli-onay/*` = 404. Redeploy sonrası GF testi + Docker E2E (Task 11 Step 3) canlı doğrulanmalı.
- **PR/merge:** feat/kvkk-faz2 → clean-main (8 commit bu session).
- GEMINI_API_KEY rotate (AUP), A1 PG restart (shared_buffers 4GB) — önceki backlog.

### ⚠️ Bilinen (benim değil — cerrahi müdahale, dokunulmadı)
- 5 pre-existing ruff: `auth.py:533,1708` E501, `dependencies.py:23,33` E402 + `:87` E501. KVKK kodu değil.

### 📌 Ders (formatter tuzağı ×3)
Import-only edit + import'u sonraki edit'te kullan → ruff/isort "unused" sanıp siler (text, AsyncSession, require_veli_consent → NameError). **Çözüm:** import + kullanımı AYNI edit'te ekle, veya kullanımdan sonra import varlığını tekrar doğrula.

### Kararlar (kalıcı)
- Yaklaşım A: amaca-özel `veli_consent` tablosu. Token 7g DB-kalıcı, SHA-256 (plaintext sadece email); granted'da hash KORUNUR. Enforcement: sosyal/PII gated, çekirdek öğrenme açık. veli_onay UPDATE raw `text()`.
