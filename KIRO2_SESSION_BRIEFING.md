# KIRO2 SESSION BRIEFING — 28 Nisan 2026 (v17)

## YENİ SOHBET BAŞLATMAK İÇİN
```
KIRO2 projesine devam et. C:\Users\husey\kiro2\KIRO2_SESSION_BRIEFING.md dosyasini oku.
```

---

## PROJE
YKS hazırlık platformu. 100K+ eşzamanlı kullanıcı hedefi. TÜBİTAK 1512 BİGG planlı.
Konum: `C:\Users\husey\kiro2`
Stack: FastAPI + PostgreSQL(5434, native Windows) + Redis(6379) + React 18 + Docker + ES(9200) + Ollama(11434, qwen3:8b) + LangGraph v1.0.5
Backend DSN: `postgresql+asyncpg://postgres:1470@host.docker.internal:5434/kiro2`
Config authority: `.env.mvp` | Image: `Dockerfile.minimal` (py3.11-slim)

⚠️ **İKİ POSTGRESQL VAR — KARIŞTIRMA:**
- **5434 native Windows PostgreSQL 18** → DB `kiro2`, 236 tablo, **backend buraya bağlanır**
- **`kiro2_postgres` Docker container** → DB `kiro2_db`, 49 tablo, **KULLANILMIYOR** (orphan)

Parola doğrulama (MCP): `%APPDATA%\Claude\claude_desktop_config.json` → `1470`. Backend için `.env.mvp` otoriter (yukarıda `Config authority`).

---

## ERİŞİM
```
Admin:        admin@kiro2.com / Kiro2Beta2026@x
Test öğrenci: beta001@kiro2test.com / Test2026!
DB:           localhost:5434  user=postgres  pw=1470  db=kiro2
```

Token al (alan adı `access_token`, `.token` YANLIŞ):
```powershell
$body='{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
$t=((Invoke-WebRequest http://localhost:8000/api/v1/auth/giris -Method POST `
     -ContentType "application/json" -Body $body -UseBasicParsing).Content `
     | ConvertFrom-Json).access_token
```

psql:
```powershell
$env:PGPASSWORD='1470'
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2
```

Auth çift modlu:
- `/api/v1/auth/giris` → Bearer access_token
- `/api/v1/auth/login/secure` → httpOnly cookie set
- `/api/v1/auth/refresh/secure` → cookie ile yeniler (`/refresh` DEĞİL)

---

## VERİTABANI DURUMU (28 Nisan 2026)

### Aktif tablolar
```
question_bank: 77.445 toplam
  ├─ 57.920 aktif
  └─ 19.525 pasif
       ├─ 13.246 metadata yok
       ├─  6.278 K1_K2_K3_dead_data (28 Nis cleanup, Paket A)
       └─      1 prepilot dedup (Esen APS)

users: 65 | exam_sessions: 186 | kiro2_cat_sessions: 8
irt_calibration_history: 1.080 | topic_prerequisites: 90
fsrs_cards: 57 | zpd_history: 0   ← FSRS akışı başladı, ZPD organik birikim bekliyor
```

ES doc sayısı: `[DOĞRULA — 28 Nis cleanup sonrası ES reindex yapıldı mı?]`

### LEGACY — KULLANMAYIN
- `questions` tablosu (36.381 satır). **Platform bu tabloyu kullanmıyor.**
- `emergency_content.sql`: DEPRECATED, bu legacy tabloya yazıyor. **Çalıştırma.**
- `KullaniciServisi`: DEPRECATED, in-memory. `core.database.db_manager.get_session()` ile direkt SQLAlchemy kullan.

### D-Dataset (kriz çözüldü, Nis 2026)
- Yol: `C:\Users\husey\kiro2\d-dataset` (kök'teki `C:\Users\husey\d-dataset` yalnızca çıktı kalıntısı)
- Kaynak: `eslesmis_sorucevap.jsonl` — 77.336 record, v3.5 production, 405 kitap
- Doğrulama: 100% pass, 0 critical error, 99.86% match rate

### Alembic
HEAD: `prepilot_m2_indexes_20260428` (commit `36549f9`, 28 Nis prepilot M1+S1+M2)

**Kurallar:**
- ID 32 char sınırı (`alembic_version` kolon limiti). Daha uzun = truncate, zincir kırılır.
- `alembic revision --autogenerate` artık **izinli**. CLAUDE.md akışı: önce ORM modeli düzenle, sonra autogenerate. (v16'daki "kalıcı yasak" notu **geçersiz**.)
- Migration dosyaları lokalde yazılır → container'a `docker cp` ile kopyalanır (içeride yazma izni yok).

---

## PREPİLOT SCHEMA (28 Nis 2026, commit 36549f9)

İçerik pipeline'ının fizik temeli. M1 + S1 + M2 birlikte commit'lendi.

**`question_bank.soru_hash`**
- Tip: `VARCHAR(32) NOT NULL`
- Formül: `MD5(LOWER(TRIM(question_text)) || '|' || option_a..d || '|' || COALESCE(option_e,''))`

**İndeksler**
- `uq_qb_soru_hash_active`: partial UNIQUE WHERE `is_active=TRUE`
- `idx_qb_soru_hash`: lookup için (UNIQUE değil)

**Yeni tablolar**
- `manual_review_queue` → MRQ akışı
- `question_bank_staging` → pipeline staging katmanı

**Doğrulama snapshot'ı (28 Nis post-deploy)**
```
distinct hash    : 77.249
dup_excess       :    196   (hepsi pasif — partial UNIQUE çakışmıyor)
active_dup_pairs :      0   ✅
```

Esen Coğrafya dedup örneği:
- TYT `0d6e5dbe` → canonical, aktif kaldı
- APS `10e2304d` → pasifleştirildi

---

## KRİTİK KOLON ADLARI / TUZAKLAR

```
ExamSession             student_id (NOT user_id), raw_score (NOT score)
users.role              BÜYÜK HARF (STUDENT/TEACHER/PARENT/ADMIN)
                         require_role'daki .lower() input hoşgörüsü, DB enum BÜYÜK
users.id                VARCHAR — FK'ler sa.String, UUID DEĞİL
user_badges.id          VARCHAR — aynı kural
video_watch_sessions.id UUID
sub_problems.id         UUID (reasoning_api domeni — productive_failure_api'ye DEĞİL)
IRT kolonları           irt_discrimination(a), irt_difficulty(b), irt_guessing(c)
YKS field               "puan" (NOT "puan_tahmini")
CAT tablo               kiro2_cat_sessions (NOT cat_sessions)
```

`sa.Enum(create_type=False)` güvensiz → `sa.String(N)` kullan.

---

## SERVİS DURUMU (28 Nis)

```
kiro2-backend          :8000   healthy   118 router yüklü, 23 disabled, 0 fail
kiro2-celery-worker            healthy   concurrency=8, 30 task
kiro2-celery-beat              running   8 scheduled task
kiro2-frontend         :3000   healthy
kiro2-redis            :6379   AOF + save "60 1000", external volume kiro2_redis-data
ES                     :9200   yellow/normal
Ollama                 :11434  qwen3:8b
```

Orphan container'lar (kullanılmıyor): `kiro2-ollama`, `kiro2_postgres`, `turkiye_sinav_*`

Middleware (6): Timing + CORS + CSRF + CacheHeaders + GZip + VersionRedirect
Startup: DB → JWT Redis → ExamRecovery → OrphanCleanup → Agents → Blackboard → ANALYZE → Ready

Beat schedule:
```
02:00 daily    refresh_daily_plans
03:00 Pazar    irt_calibration (kwargs batch_size=200)
06:00 daily    daily_coaching
08:00 daily    daily_analytics_report
09:00 Pzt      weekly_summary
00:00 Pzt      weekly_league_reset
23:00 Pazar    weekly_error_cluster
00:05 daily    check_birlikte_streaks
```
`[DOĞRULA]` Üst iki task (refresh_daily_plans + irt_calibration) 28 Nis'te userMemories tarafından teyitli. Alt 6 task v16'dan taşındı, hâlâ aktif olduğu doğrulanmadı.

---

## DEPLOY AKIŞI

**Python dosya değişikliği** (image rebuild yok)
1. Host'ta düzenle
2. `docker cp C:\...\backend\path\dosya.py kiro2-backend:/app/path/dosya.py`
3. `docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"`
4. `docker restart kiro2-backend`
5. `Start-Sleep 22`
6. Health check (`curl localhost:8000/health`)

**Env değişikliği:** `docker compose up -d --no-deps backend`
**Kalıcı (image bake):** `docker compose build backend` + `docker compose up -d --no-deps backend`

**Türkçe SQL:** `psql -f dosya.sql` (inline `-c "..."` Türkçe karakteri bozar)
**Karmaşık Python:** Host'ta yaz → `docker cp` → `docker exec python /tmp/script.py`
**Bytecode:** Model/service edit sonrası `.pyc` temizle, aksi halde SQLAlchemy cached UUID kullanır.

**Endpoint smoke testi:** `powershell -ExecutionPolicy Bypass -File scripts\test_endpoints.ps1`

⚠️ `ENVIRONMENT=production` lokal'de = crash loop (postgres parola validasyonu + localhost CORS reddedilir). Geliştirme = `development`.

---

## PİLOT SİSTEMİ

Her pilot 3 dosya:
```
.cursor/plans/YYYYMMDD_<name>.md             → Plan
backend/_pilots/YYYYMMDD_<name>_state.md     → ADIM 0 durum tespiti
.cursor/plans/YYYYMMDD_<name>_RESULT.md      → Sonuç raporu
```

Akış: ADIM 0 (kod dokunmadan tespit) → Aşama kararı (insan onayı) → migration/kod → staging deploy → smoke → commit + rapor.

---

## ORCHESTRATOR
- Konum: `C:\Users\husey\kiro2\orchestrator\core\`
- Stack: LangGraph v1.0.5 — v2.5.0 STABLE phase (Oca 2026)
- Kapsam: 24 modül, 45 policy, 139 export. `graph.py` aktif.
- Test: `test_complete_system.py` OK.

---

## GİT DURUMU (28 Nis 2026)

Branch: `master`
Son commit zinciri (push sonrası):
- `docs(briefing): v17 — konsolide + 28 Nis durum`
- `docs(claude): v3.6 — Karpathy Behavioral Foundation + Hard Rules`
- `fix(infra): redis container + external volume (REDIS FIX kalıcılaştır)`
- `f05e5d6` chore: archive superseded migration + add behavior test doc *(28 Nis Pist 3 — kök dizin temizliği)*
- `36549f9` prepilot M1+S1+M2 (28 Nis, soru_hash + MRQ + staging)

Origin/master: senkron (28 Nis push sonrası).

**Untracked (WIP, atık değil):**
```
.cursor/plans/20260427_icerik_pipeline_v1_2.md
.cursor/plans/20260428_icerik_pipeline_prepilot_RESULT.md
.cursor/plans/20260428_paket_a_dead_data_cleanup_RESULT.md
backend/_pilots/20260428_icerik_pipeline_prepilot_state.md
backend/_pilots/20260428_paket_a_dead_data_cleanup_state.md
```

`[DOĞRULA: 23-27 Nis arası commit hash listesi — yakın commit özeti için git log --oneline]`

---

## AÇIK PİSTLER (28 Nis devir notu)

### Pist 1 — M3 / İçerik Pipeline İskeleti  **[ASIL İŞ]**
Önce şu 3 dosyayı oku (untracked):
- `.cursor/plans/20260427_icerik_pipeline_v1_2.md`
- `.cursor/plans/20260428_icerik_pipeline_prepilot_RESULT.md`
- `backend/_pilots/20260428_icerik_pipeline_prepilot_state.md`

Sonra: M1+S1+M2 (commit `36549f9`) ile uyumu doğrula. M3 iskeleti = staging tablosu → MRQ akışı, pipeline'ın `soru_hash` ile nasıl konuşacağı.

### Paket A RESULT commit  *(pilot sahibi sohbette)*
```
.cursor/plans/20260428_paket_a_dead_data_cleanup_RESULT.md
backend/_pilots/20260428_paket_a_dead_data_cleanup_state.md
```
K1_K2_K3_dead_data cleanup pilotunun kapanış commit'i.

### Pist 3 — KAPANDI ✅
Kök dizin temizliği. Commit `f05e5d6`. 49 path → 8 path.

### Pist 4 — KAPANDI ✅
CLAUDE.md (v3.6 Karpathy Behavioral Foundation) ve docker-compose.yml (Redis fix kalıcılaştırma) commit + push (28 Nis).

---

## DİĞER AÇIK İŞLER

**Bakım**
- IRT gerçek kalibrasyon: max 5 yanıt/soru, 50 eşiği için organik birikim bekliyor
- 23 disabled router `[DOĞRULA: liste toplamı 13 düşüyor — eksik 10 router'ın listesi nereden gelir?]`: ChromaDB-bağımlı 4 (P2) + diary_api / live_session_routes / productive_failure_api / expert_agents_api / vision_api / PWA-offline 2 / stub 2 + diğerleri
- D-Dataset Phase 2+ (YOLO crops, answer matching pipeline) — düşük öncelik (kriz çözüldü, v3.5 production)

**P2**
- ChromaDB → ES migration (4 router için)
- TÜBİTAK BİGG başvuru
- Risk Map sistemi (orchestrator)
- Otonom multi-agent sistem (`KIRO2_Tam_Otonom_Sistem_Rehberi.md`, L4-L5 hedef)

---

## HARD RULES — İHLAL EDİLMEZ

1. `questions` tablosu LEGACY → `question_bank` kullan
2. `emergency_content.sql` DEPRECATED → çalıştırma
3. `KullaniciServisi` DEPRECATED → `core.database.db_manager.get_session()`
4. İki PG ayrımı: 5434 native = backend, `kiro2_postgres` container ≠ `kiro2` DB
5. `ENVIRONMENT=development` (production = crash loop)
6. `users.id` / `user_badges.id` = VARCHAR → FK'ler `sa.String`
7. Türkçe SQL: `psql -f` (inline `-c` bozar)
8. **Onaysız `bash` / `docker exec` / `psql` çalıştırma** (insan döngüsünde pattern; tek istisna: salt-okunur dosya görüntüleme)

---

## v17 DEĞİŞİKLİK NOTU (v16'dan, 28 Nis 2026)

- **Yapı konsolide edildi (B yaklaşımı):** 06 Nis tarihçesi + 21-24 Nis offline_sync 4'lü pilot kronolojisi + v13/v15/v16 değişiklik notları çıkarıldı. Detay arayan: `git log` + `.cursor/plans/`.
- **DSN parolası düzeltildi:** `postgres` → `1470` (kaynak `claude_desktop_config.json` MCP config; backend authority `.env.mvp`)
- **PostgreSQL ayrımı netleştirildi:** 5434 native PG18 = `kiro2` (236 tablo, backend) | `kiro2_postgres` container = `kiro2_db` (49 tablo, kullanılmıyor)
- **question_bank rakamları güncellendi:** 77.401/64.270 → 77.445/57.920 (28 Nis K1_K2_K3 cleanup 6.278 + Esen dedup 1 satır sonrası)
- **Alembic head:** `diary_drift_recovery_20260422` → `prepilot_m2_indexes_20260428` (commit `36549f9`)
- **Alembic autogenerate kuralı tersine döndü:** v16 "kalıcı yasak" → artık **izinli**, CLAUDE.md akışı (önce ORM, sonra autogenerate)
- **Yeni bölüm:** PREPİLOT SCHEMA (`soru_hash`, MRQ, staging tabloları, dedup snapshot)
- **Yeni bölüm:** ORCHESTRATOR (LangGraph v1.0.5, v2.5.0 STABLE, 24 modül)
- **Yeni alt-bölüm:** D-Dataset durum (kriz çözüldü, doğru yol, v3.5 production)
- **Geri eklendi:** Endpoint smoke testi referansı (`scripts\test_endpoints.ps1`)
- **Pist 3 kapanış commit'i eklendi:** `f05e5d6` (kök dizin 49 → 8 path)
- **Pist 4 kapatıldı:** CLAUDE.md v3.6 + docker-compose.yml redis fix commit + push (28 Nis batch)
- **Auth pattern v16'dan korundu:** `access_token` alan adı, `/refresh/secure` endpoint, çift modlu auth
- **Orphan container listesi netleştirildi:** `kiro2-ollama`, `kiro2_postgres`, `turkiye_sinav_*`

**`[DOĞRULA]` satırları (lokal makinede teyit edilmeli):**
- ES doc sayısı (28 Nis cleanup sonrası reindex yapıldı mı?)
- 23-27 Nis arası commit hash listesi (briefing'de yakın commit özeti için)
- Celery beat alt 6 task (`daily_coaching`, `daily_analytics_report`, `weekly_summary`, `weekly_league_reset`, `weekly_error_cluster`, `check_birlikte_streaks`) — v16'dan taşındı, hâlâ aktif olduğu doğrulanmadı
- 23 disabled router sayısı: liste toplamı 13 düşüyor, eksik 10 router'ın listesi nereden gelir?
- 236 tablo sayısı (28 Nis cleanup sonrası post-state teyidi yapılmadı; cleanup yalnız satır pasifleştirme olmalı, tablo sayısı değişmemeli)
- `30_DERSLER.md` / `40_OPEN_DEBTS.md` / `50_KARARLAR.md` ardışık doküman zinciri hâlâ duruyor mu? v17'de referansı isteniyorsa eklenir.
