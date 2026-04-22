# KIRO2 SESSION BRIEFING - 22 Nisan 2026 (v16)

## YENİ SOHBET BAŞLATMAK İÇİN
```
KIRO2 projesine devam et. C:\Users\husey\kiro2\KIRO2_SESSION_BRIEFING.md dosyasini oku.
```

---

## PROJE
YKS hazirlik platformu. 100K+ kullanici. TUBITAK BIGG planli.
Konum: C:\Users\husey\kiro2
Stack: FastAPI+PostgreSQL(5434, native Windows)+Redis(6379)+React18+Docker+ES(9200)+Ollama(11434)
Backend DSN: postgresql+asyncpg://postgres:postgres@host.docker.internal:5434/kiro2
(DİKKAT: backend native Windows PostgreSQL'e bağlanır. `kiro2_postgres` Docker
konteyneri — varsa — AYRI instance'dır, `kiro2` DB'si orada YOK. Bu ayrım
22.04 Round 2 smoke'da doğrulandı.)

---

## ERİŞİM
Admin:  admin@kiro2.com / Kiro2Beta2026@x
DB:     localhost:5434 / user=postgres / pw=postgres / db=kiro2

Token al (DİKKAT: alan adı `access_token`, eski briefing'lerdeki `.token` YANLIŞ):
  $body='{"email":"admin@kiro2.com","password":"Kiro2Beta2026@x"}'
  $t=((Invoke-WebRequest http://localhost:8000/api/v1/auth/giris -Method POST -ContentType "application/json" -Body $body -UseBasicParsing).Content | ConvertFrom-Json).access_token

psql:
  $env:PGPASSWORD='postgres'
  & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5434 -U postgres -d kiro2

---

## ÇALIŞAN SERVİSLER (20 Nisan 2026)
kiro2-backend     :8000  healthy (tüm 141 router ROUTER_MAPPING'de, DISABLED_ROUTERS boş)
kiro2-celery-worker     healthy (concurrency=8, 31 task)
kiro2-celery-beat       running (8 scheduled task)
kiro2-frontend    :3000  healthy
kiro2-ollama      :11434 healthy (qwen3:8b)
kiro2_postgres    :5434  native host (~162 tablo)
kiro2_redis       :6379  native host
ES                :9200  yellow/normal (64.270 doc — ES yellow beklenen durum)

---

## VERİTABANI DURUMU (24.04.2026)
question_bank: 77.401 toplam / 64.270 aktif
  is_calibrated=TRUE : 360  (IRT 3PL gerçek kalibrasyon)
  is_calib_pool=TRUE : 1909 (her ders x zorluk 30 soru)
users: 65
Alembic head: diary_drift_recovery_20260422 (tek head, çift head yok — 22.04 Round 2 teyit)
Son Alembic zinciri (Nisan): 20260406_uni_dept → 20260410_* (4) → 20260412_* (2) → student_review_drift_001 → offline_sync_pkg_20260420 → diary_drift_recovery_20260422 (22 Nisan Round 2)
ALTIN KURAL: alembic revision --autogenerate YASAK (IRT kolonlarini DROP eder)
ALTIN KURAL: alembic revision ID'si `alembic_version` kolonunda **32 char sınırı**. Uzun ID'ler truncate olup zincir kırılır (Lesson 10).

### ⚠️ ALEMBIC DRIFT (20.04.2026 diary pilotunda tespit)
Bazı tablolar (örn. 8 diary tablosu) DB'de FİZİKSEL olarak mevcut ama Alembic revision grafiğinde kayıtlı değil. Anlamı:
- Mevcut DB'de endpointler çalışır ✅
- Taze DB kurulumunda `alembic upgrade head` → diary tabloları OLUŞMAZ ❌
- Staging/production deploy → 500 riski
Çözüm kararı bekliyor (A: yok say + doküman / B: idempotent recovery migration / C: resmi migration + alembic stamp)

---

## KRİTİK KOLON ADLARI (YANLIŞ VARSAYIMDAN KAÇIN)
ExamSession : student_id (NOT user_id), raw_score (NOT score)
users.role  : BUYUK HARF (STUDENT/TEACHER/PARENT/ADMIN) — runtime teyit 22.04 Round 2 (DISTINCT: STUDENT, TEACHER, ADMIN, PARENT). require_role kodu içindeki `.lower()` normalize sadece input hoşgörüsü, DB enum BÜYÜK HARF saklar.
users.id    : VARCHAR (NOT UUID!) — FK'ler sa.String olmali, UUID degil
user_badges.id : VARCHAR (NOT UUID!)
video_watch_sessions.id : UUID
sub_problems.id : UUID (reasoning domain, productive_failure_api ile İLGİSİZ)
IRT kolonlar: irt_discrimination(a), irt_difficulty(b), irt_guessing(c)
YKS field   : "puan" (NOT "puan_tahmini")
CAT tablo   : kiro2_cat_sessions (NOT cat_sessions)
Refresh EP  : /api/v1/auth/refresh/secure (NOT /refresh, cookie gerekli)
Auth yanıt  : TokenYaniti.access_token (NOT .token)

### offline_sync_packages (24.04.2026 yeni)
Tablo şeması (borç #2 ile oluştu):
```
package_id    VARCHAR PRIMARY KEY
student_id    VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE
created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
consumed_at   TIMESTAMPTZ NULL
question_ids  JSONB NULL
```
Endpoint davranışları:
- `POST /api/v1/offline-sync/sync-results` → `answered_at` alanı **ISO-8601 zorunlu** (Round 2'de keşfedildi). Eksikse 422.
- `GET /api/v1/offline-sync/sync-package?limit=N` → sıra dışı davranış: `remaining_slots<1` iken deterministik değil (K-2 açık karar).
- 3 katman guard: `already_consumed` / `unknown_package` / `ownership_mismatch` (log pattern'leri aynen).

---

## ROUTER DURUMU (20.04.2026 — batch ADIM 0 sonrası)

**Briefing v12'deki "13 disabled router" iddiası GÜNCEL DEĞİL.** Gerçek durum (20.04.2026 itibariyle, 5434 dev DB):

- `backend/routers/loader.py` → `DISABLED_ROUTERS = {}` (boş)
- Briefing'in v12'de disabled diye listelediği 13 router hepsi `ROUTER_MAPPING`'de kayıtlı
- Hepsi log'da "Registered" satırı veriyor

Ama runtime'da hepsinin "çalıştığı" anlamına gelmez. Batch ADIM 0 (`backend/_pilots/20260420_batch_router_state.md`) şu sınıflandırmayı üretti:

### Aşama B — Tablolar var, Alembic drift olası (pilot için uygun)
- `api.diary_api` ✅ **20.04 pilot aktivasyonu tamamlandı** (smoke test geçti)
- `api.productive_failure_api` — gerçek bağımlılık: `question_bank` + `topic_progress` (VARCHAR uyumlu). v12 briefing'deki `sub_problems`/`solution_steps` notu YANLIŞ (farklı domain, UUID, reasoning_api'ye ait)
- `api.offline_sync_api` — `question_bank` + FSRS akışı mevcut
- `api.pwa_sync_api` — `exam_sessions`, `student_answers` mevcut. ⚠️ prefix `/api/pwa-sync-api` (tutarsız, `/api/v1/...` değil)

### Aşama D — Dış bağımlılık (altyapı kararı gerekli, önce ADIM 0 değil)
- `api.v1.semantic_search` — ChromaDB yok, "WARNING chromadb not available"
- `api.clustering_api` — ChromaDB
- `api.v1.content_recommendation` — ChromaDB
- `api.v1.duplicate_detection` — ChromaDB
- `api.v1.expert_agents_api` — Expert agent framework deploy edilmedi
- `api.vision_api` — YOLO + Gemini pipeline entegre değil

### Aşama E — Belirsiz / manuel inceleme (pilot öncesi kod review)
- `api.live_session_routes` — **🔥 GERÇEK BOZUK ROUTER**: kodda ham SQL `live_session_participants`, DB'de tablo adı `session_participants`. Runtime'da 500 üretme riski yüksek.
- `api.revolutionary_features` — hesaplama ağırlıklı, hangi endpoint'ler DB yazıyor belirsiz
- `api.team_challenges_api` — `services/_deprecated/team_challenges` kullanıyor, kalıcı tablo yok

### Bilinen kategori bug'ı (fonksiyonel değil, log/doküman)
`router_registry.ROUTER_CATEGORIES` içinde `"search"` YOK. `ROUTER_MAPPING` ise 4 ChromaDB router'ını `"search"` kategorisinde tanımlıyor. Sonuç: `backend/routers/__init__.py` bilinmeyen kategoriyi `misc/`'e düşürüyor → loglar `misc/semantic_search` vb. gösteriyor. Çözüm: registry'ye `search` ekle veya mapping'i düzelt.

---

## 06 NİSAN 2026 — OTURUMLAR (tarihçe)

### Oturum 1:
1. Auth ölü kod temizliği: jwt_auth_docker.py + consolidated_auth_dependencies.py silindi (48KB) [ede451a]
2. Disabled router analizi: gerçek sayı 23 (önceki audit 43 demişti — yanlış)
3. KVKK 5 tablo oluşturuldu (migration: 20260406_kvkk_recreate) [3b5e688]
4. KVKK 2 router aktif edildi (kvkk_consent_api, kvkk_privacy_api)

### Oturum 2:
5. KVKK router commit + deploy tamamlandı [8190c65]
6. FERPA/COPPA 5 tablo oluşturuldu (migration: 20260406_ferpa_coppa) [c0aa533]
   Tablolar: ferpa_consents, coppa_parental_consents, educational_record_access_logs,
   data_retention_policies, data_processing_agreements
   NOT: sa.Enum create_type=False çalışmadı, sa.String(20) kullanıldı
7. FERPA/COPPA router aktif edildi (ferpa_coppa_compliance_api)
8. ChromaDB bağımlı 4 router → P2 roadmap (disabled kalacak, ES alternatifi)
9. Frontend api.ts 4.4MB iddiası → yanlış, gerçek: 42KB/1263 satır, sağlıklı yapı
10. 99 console.log temizlendi (production koddan) [83a092c]. Kalan 14 meşru runtime log.
11. Video analytics 4 tablo oluşturuldu (migration: 20260406_video_analytics) [fc6d0ff]
    Tablolar: video_completion_milestones, video_notes, video_bookmarks, video_analytics_summary
    NOT: users.id VARCHAR → user_id kolonları sa.String olmalı; user_badges.id de VARCHAR
    video_analytics_routes aktif edildi
12. Sequential reasoning 4 tablo oluşturuldu (migration: 20260406_reasoning) [88dc01f]
    Tablolar: reasoning_sessions, reasoning_steps, sub_problems, reasoning_cache
    Enum'lar DO $$ BEGIN..EXCEPTION ile oluşturuldu ama sa.String kullanıldı
    sequential_reasoning_api aktif edildi
13. Üniversite/Bölüm/Review 21 tablo oluşturuldu (migration: 20260406_uni_dept) [a51626f]
    21 tablo; 5 router aktif: university_advisory, preference_simulation,
    department_info, university_info, student_review_routes

### Toplam Nisan 6: 34 yeni tablo, 10 router aktifleştirildi. Disabled 23→13.

---

## 20 NİSAN 2026 — OTURUMLAR

### Keşif turu (3 tur gözden geçirme)
- Audit raporları okundu (5 tur: REPO_MAP, AUDIT_PLAN, BACKEND_AUDIT, FRONTEND_AUDIT, AI_PIPELINE_AUDIT, INFRA_TEST_AUDIT)
- Composer 2 güçlü alanları × KIRO2 P1/P2 listesi eşleştirildi
- 3 tur yanlış derinleşmeden sonra plan sadeleştirildi: tek pilot (`diary_api`) ile başla

### diary_api pilot aktivasyonu
Plan: `.cursor/plans/20260420_diary_api_activation.md`
ADIM 0 (durum tespiti): `backend/_pilots/20260420_diary_api_state.md`
RESULT: `.cursor/plans/20260420_diary_api_RESULT.md`

Bulgular:
- **Aşama B** ortaya çıktı — 8 diary tablosu DB'de mevcut, VARCHAR uyumlu, router canlı
- Eski `20260119_add_diary_tables.py.disabled` ve `c937128ce051_merge_diary_and_quality_gates.py.disabled` migrations `backend/alembic/versions/_archive/` dizinine taşındı (UUID yazılmış — mevcut VARCHAR şemayla uyumsuz, arşivde tutulacak)
- Alembic drift tespit edildi (bkz. yukarıdaki DB durumu bölümü)
- Smoke test sonuçları:
  - `POST /api/v1/auth/giris` → 200, yanıt alanı `access_token`
  - `GET /api/v1/diary/goals` (Bearer) → 200
  - `POST /api/v1/diary/summary` + `DiaryEntryCreate` → 200, kayıt DB'ye yazıldı

### Batch ADIM 0 — kalan 12 router durum tespiti
Plan: `.cursor/plans/20260420_batch_router_adim0.md`
RESULT: `backend/_pilots/20260420_batch_router_state.md`

Bulgular yukarıdaki "ROUTER DURUMU" bölümüne yansıtıldı. Önerilen sonraki pilot: `api.offline_sync_api` veya `api.pwa_sync_api` (ikisi de Aşama B, dış bağımlılık yok).

### Git (20 Nisan)
- `d5c803c` chore(diary): archive old UUID migration + add pilot RESULT
- `ab6c8b8` chore(pilots): create backend/_pilots/ for router activation state reports (amend, hook'suz)
- `83421cc` chore(pilots): add batch ADIM 0 router state matrix (12 routers)

---

## 21-24 NİSAN 2026 — offline_sync DÖRTLÜ PİLOT

### 21 Nisan — offline_sync_api aktivasyon (Pilot 2)
Plan: `.cursor/plans/20260421_offline_sync_activation.md`
RESULT: `.cursor/plans/20260421_offline_sync_RESULT.md`

Bulgular: Aşama B olarak yürütüldü. 4 kod borcu tespit edildi:
- #1 student_answers persist yok (ürün kararı)
- #2 package_id persist yok
- #3 FSRS eşleme `front_text.contains` kırılgan
- #4 `q.options` ORM uyumsuz

### 22 Nisan — Borç #4 kapandı (Pilot 3)
Plan: `.cursor/plans/20260422_offline_sync_code_fix.md`
RESULT: `.cursor/plans/20260422_offline_sync_code_fix_RESULT.md`
Commit: `ff06119` fix(offline_sync): build_sync_package compose options from option_a..e (debt #4)

### 23 Nisan — Borç #2 plan + Round 1 deploy drift (Pilot 4)
Plan: `.cursor/plans/20260423_offline_sync_debt_2_package_persist.md`
RESULT: `.cursor/plans/20260420_offline_sync_debt_2_RESULT.md` (Round 1 FAIL bu turda append)

Composer 2 migration + guard yazdı ama smoke **FAIL** — deploy drift (D-12):
kod lokal değişti, container'a `docker cp` yapılmadı. Claude bu durumu
repo'yu bizzat okumadan fark edemedi (§1.9 dersi).

### 24 Nisan — Round 2 PASS + hijyen bekliyor
Commit: `5008ab6` (footer'lı, amend bekliyor)

Round 2 Composer 2 tarafından (`docker cp + pyc temizle + restart`) ardından
gerçek smoke S1-S6 hepsi PASS:
- S1 /sync-status 200 | S2 /sync-package?limit=5 PASS | S3 happy /sync-results PASS
- S4 replay (already_consumed) PASS | S5 unknown UUID PASS | S6 ownership_mismatch PASS
Mock kullanılmadı, log pattern'leri `docker logs` ile doğrulanıyor.

### Composer 2 Sapma Matrisi (Borç #2 pilot zinciri)
- D-8 KABUL: raw SQL (sqlalchemy.text) ORM yerine — fonksiyonel eşdeğer
- D-9 KABUL: 6 unit test eklendi (AsyncMock) — zararsız
- D-10 KABUL: ADIM 0 state.md hiç üretilmedi (22+23 Nisan) — K-1 kararı ayrı
- D-11 FIX: `down_revision` yanlış yazıldı — `5008ab6`'da düzeltildi
- D-12 FIX: container deploy drift — Round 2 ile tamamlandı

### Git (21-24 Nisan)
Push yapılmadı. `origin/master` fb18866, HEAD `5008ab6`. 10-11 commit ileri
(hijyen 4'lü + autogenerate commit'i ile push bekleniyor).

### Açık Kararlar (Hüseyin'e ait)
- **K-1** state.md dosya yolu (3 seçenek, Claude önerisi A: mevcut yolu koru, ADIM 0 sertleştir)
- **K-2** `sync-package?limit=N` davranışı bug mu kasıtlı mı? Bug ise borç #5 açılır
- **K-3** kiro2-celery-worker/beat + kiro2-frontend container'ları kapalı — kasıtlı mı?

---

## 24 NİSAN 2026 — CLAUDE (DESKTOP) §1.9 DERSİ

Claude Desktop, Files 7 dosyasını yeniden yazarken **transkript özetine**
dayandı. Compaction özeti "Round 2 bekliyor" diyordu, gerçekte RESULT
dosyasına Round 2 PASS zaten append edilmişti. Claude repo'daki RESULT
dosyasını bizzat okumadan Files'ı yanlış zemine yazdı. Hüseyin "gözdengeçir" dedi, hata yakalandı.

İroni: Aynı turda `30_DERSLER §6`'ya "Tuzak 9: Files Dosyaları Güncel Varsayımı" eklenmişti. Claude kendi yazdığı dersi ihlal etti.

Ders (30_DERSLER.md §1.9'a giriyor): Files yazmadan önce `40_OPEN_DEBTS`'in bahsettiği RESULT dosyasını **aç oku**, Round N sayısını gör, status matrisini taramadan yazma.

---

## GIT DURUMU (24.04.2026)
Branch: master
HEAD: `5008ab6` fix(offline_sync): persist package_id in offline_sync_packages with guard (debt #2)
  — footer'lı, hijyen amend bekliyor
Origin/master: `fb18866` (10 commit ileri, amend sonrası 11 olacak).

Uncommitted (M):
  KIRO2_SESSION_BRIEFING.md        ← v15 update (bu dosya, pending)

Untracked (??):
  .cursor/plans/20260423_offline_sync_debt_2_package_persist.md   (docs commit)
  .cursor/plans/20260420_offline_sync_debt_2_RESULT.md            (Round 1+2)
  backend/tests/unit/services/test_offline_sync_service.py        (D-9 mock)
  AGENTS.md, DERSLER.md, NEXT_SESSION_HANDOFF.md, backups/
  CHAT_SUMMARY_20260422.md, CHAT_SUMMARY_20260423.md
  tmp_db_tables.txt, tmp_existing_tables.txt, tmp_token.txt

Son commitler (push yapılmadı):
  5008ab6 fix(offline_sync): persist package_id (debt #2) [footer, amend bekliyor]
  ff06119 fix(offline_sync): build_sync_package compose options (debt #4, 22 Nisan)
  83421cc chore(pilots): batch ADIM 0 router state matrix
  ab6c8b8 chore(pilots): create backend/_pilots/ for router activation state
  d5c803c chore(diary): archive old UUID migration + add pilot RESULT
  a51626f fix(university): 21 university/department/review tables + 5 routers
  88dc01f fix(reasoning): reasoning tables + router
  fc6d0ff fix(video): video analytics tables + router
  83a092c chore(frontend): 99 console.log temizliği
  c0aa533 fix(ferpa): FERPA/COPPA tables + router
  8190c65 fix(kvkk): enable kvkk_consent_api and kvkk_privacy_api
  3b5e688 fix(kvkk): create missing KVKK tables + routers
  ede451a chore(auth): remove jwt_auth_docker.py + consolidated_auth_dependencies.py

---

## MİGRASYON YAZARKEN ÖĞRENİLEN DERSLER
1. users.id VARCHAR — tüm user_id FK'lerinde sa.String kullan, UUID değil
2. user_badges.id VARCHAR — badge FK'lerinde de sa.String
3. video_watch_sessions.id UUID — bu FK'de UUID kullanılabilir
4. sub_problems.id UUID — ama bu tablo reasoning_api'ye ait, productive_failure_api'ye DEĞİL
5. sa.Enum(create_type=False) SQLAlchemy'de çalışmıyor — enum kolonları için sa.String kullan
6. DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL; END $$; enum oluşturmak için güvenli
7. Container'da /app/alembic/versions/ yazma izni yok — migration dosyalarını lokalde yaz, docker cp ile kopyala
8. PowerShell here-string (@'...'@) ile dosya oluştur veya Desktop Commander write_file kullan
9. **Alembic drift pattern'i**: tablolar fiziksel var ama revision graph'ta yok — diary pilotunda görüldü, taze DB için ayrı migration stratejisi gerekli
10. **`alembic_version` kolonu 32 char sınırlı** — `revision = "..."` ID'si 32 karakteri geçmemeli, aksi halde truncate olur ve zincir kırılır
11. **Migration ≠ Deploy** (D-12): migration dosyasını repo'ya eklemek yeterli değil. Container'a `docker cp`, `.pyc` temizleme, `restart`, `grep` ile doğrulama zinciri **zorunlu**. Smoke test deploy olmadan asla "PASS" demez

---

## AÇIK KALAN KONULAR

### P0 — Ürün kritik
- D-Dataset match rate %0.11 → hedef %66 (725 YOLO crop işlenmemiş)
  Yol: C:\Users\husey\d-dataset\
  Strateji: CEVAP_ANAHTARI_STRATEJI_RAPORU.md (4 faz)
  GEMINI_API_KEY hem backend/.env hem .env.mvp'ye eklenecek

### P1 — Teknik borç
- Auth audit: ~50 mutating endpoint review (IDOR + role check + rate limit + audit log)
- Router aktivasyonu — 12 router kaldı, sınıflandırma yukarıda. Önerilen sıra:
  1. `api.offline_sync_api` veya `api.pwa_sync_api` (Aşama B, düşük risk)
  2. `api.productive_failure_api` (Aşama B, `topic_progress` önkoşulu ile)
  3. `api.live_session_routes` (Aşama E — SQL tablo adı drift'i önce düzeltilmeli)
  4. ChromaDB dörtlüsü (Aşama D — ES migrasyon altyapı kararı)
  5. Expert agents + vision (Aşama D — deploy altyapısı)
  6. Revolutionary features + team challenges (Aşama E — endpoint haritalama)
- **Alembic drift stratejisi** (A/B/C): diary için pilot ertelendi, genel karar bekliyor
- **Kategori bug'ı**: `ROUTER_CATEGORIES`'e `"search"` eklemek veya mapping'i düzeltmek
- Frontend 14 kalan console.log (meşru, temizlik gerekmez)

### P2 — Planlama
- TÜBİTAK BİGG başvuru hazırlığı
- ChromaDB → ES migration (4 router, Aşama D'deki)
- Risk Map sistemi (orchestrator)
- Gamification, adventure mode, DAG visualization, PWA

### Bakım
- IRT gerçek kalibrasyon: 236 yanıt/64K soru (50 eşiği gerekli, Celery Pazar 03:00)
- Educational materials tablosu (admin /content/educational 501 stub)
- Admin CRUD mock'lar (POST/PUT/DELETE hala mock)
- Git push yapılmadı — origin'den ~11 commit ileride

---

## BACKEND MİMARİSİ
main.py → core/application.py → routers/loader.py (141 router ROUTER_MAPPING'de, DISABLED_ROUTERS boş)

AUTH CIFT MODLU:
  Bearer header VEYA httpOnly cookie
  /api/v1/auth/giris       → Bearer token (alan adı: access_token)
  /api/v1/auth/login/secure → httpOnly cookie set eder
  /api/v1/auth/refresh/secure → cookie ile yeniler

Celery Beat (8 task):
  02:00 daily → refresh_daily_plans  |  03:00 Pazar → irt_calibration
  06:00 daily → daily_coaching       |  08:00 daily → daily_analytics_report
  09:00 Pzt  → weekly_summary       |  00:00 Pzt  → weekly_league_reset
  23:00 Pazar → weekly_error_cluster |  00:05 daily → check_birlikte_streaks

---

## PİLOT ARTIFACT SİSTEMİ (20 Nisan'da kuruldu)

KIRO2'de router/feature aktivasyon işleri artık "pilot" olarak yürütülüyor. Her pilot 3 dosya üretir:

```
.cursor/plans/YYYYMMDD_<name>.md          ← Plan (pilot öncesi)
backend/_pilots/YYYYMMDD_<name>_state.md  ← ADIM 0 durum tespiti çıktısı
.cursor/plans/YYYYMMDD_<name>_RESULT.md   ← Pilot sonrası rapor
```

Pilot pattern'i (tüm router aktivasyonları için):
1. **ADIM 0** — Gerçek durum tespiti (psql + docker logs + loader kontrolü). Kod dokunma.
2. **Aşama kararı** — A/B/C/D/E sınıflandırması, insan onayı.
3. **Arşivle** — Eski `.disabled` migration'ları varsa `_archive/`'a taşı.
4. **Migration yaz** (varsa gerekli) — Pattern: `20260406_uni_dept.py`. Lokalde yaz, sonra `docker cp`.
5. **Staging deploy** — dry-run SQL preview, sonra gerçek upgrade. İnsan elle.
6. **Loader güncelle** — Sadece gerekirse (DISABLED_ROUTERS'a dokunma, boş tut).
7. **Runtime smoke** — Auth + endpoint testleri.
8. **Commit + rapor** — Kapsam dar tut, hook'suz amend ile `Made-with: Cursor` footer atla.

### Composer 2 × Pilot İş Bölümü
- ✅ Composer 2'ye: terminal sorguları, dosya taşıma, migration yazımı (pattern'den), smoke testler, rapor üretimi
- ❌ İnsan: backup alma, `alembic upgrade`, `git push`, aşama kararı, kapsam genişletme

### Prior Knowledge Pattern
Yeni pilot açarken Composer 2'ye verilecek prompt:
```
@.cursor/plans/<yeni_plan>.md — uygula
Prior: backend/_pilots/ dizinindeki önceki _state.md dosyalarını oku.
Aynı ortamdaki tespitleri tekrar sorma (users.id VARCHAR, DISABLED_ROUTERS boş vs).
```

---

## ENV UYARILARI
ENVIRONMENT=production → CRASH (postgres sifresi + localhost CORS reddedilir)
Simdilik development modda kal. .env.mvp tek kaynak.

---

## DOSYA GUNCELLEME (image rebuild gerektirmez)
docker cp C:\Users\husey\kiro2\backend\api\DOSYA.py kiro2-backend:/app/api/DOSYA.py
docker exec kiro2-backend bash -c "find /app -name '*.pyc' -delete"
docker restart kiro2-backend

## FULL IMAGE REBUILD (env degisikligi icin)
cd C:\Users\husey\kiro2
docker compose up -d --no-deps backend

---

## ROUTER AKTİVASYON PATTERNİ (eski v12 pattern'i, güncellendi)

**Artık doğrudan bu pattern'i uygulama.** 20 Nisan itibariyle pilot-based yürütüm standardı (yukarıdaki "PİLOT ARTIFACT SİSTEMİ" bölümü). Ama hızlı referans için adımlar:

1. Model dosyasını oku: docker exec kiro2-backend bash -c "grep '__tablename__' /app/models/MODEL.py"
2. Eksik tabloları bul (önce DB'de var mı bak):
   psql -c "SELECT table_name FROM information_schema.tables WHERE table_name IN (...);"
3. FK tiplerini kontrol et: users.id=VARCHAR, diğer tablolar karışık
4. Migration yaz (lokalde, gerekirse): backend\alembic\versions\YYYYMMDD_isim.py
   - Enum'lar için sa.String kullan
   - user_id FK'leri için sa.String kullan
5. Deploy: docker cp → alembic upgrade head (İNSAN yapar, Composer 2'ye verme)
6. **DISABLED_ROUTERS'a dokunma** — set boş, dokunursa accidental re-disable riski
7. docker cp (değiştiyse) → pyc temizle → restart → log kontrol

---

## TEST SCRİPTİ
C:\Users\husey\kiro2\scripts\test_endpoints.ps1
Calistir: powershell -ExecutionPolicy Bypass -File scripts\test_endpoints.ps1

---

## v16 DEĞİŞİKLİK NOTU (v15'ten, 22 Nisan — Borç #6 Round 2 sonrası)
- Tarih: gerçek = 22.04.2026 (önceki v15 header'ı "24 Nisan" senaryo bağlamı içindi)
- Alembic head güncellendi: `offline_sync_pkg_20260420` → `diary_drift_recovery_20260422` (22 Nisan Round 2 teyit, state.md §A2)
- Stack özetine netlik: backend DSN = `host.docker.internal:5434/kiro2` (native Windows PostgreSQL). `kiro2_postgres` Docker konteyneri AYRI instance, backend ona bağlanmıyor. Round 1'deki `docker exec kiro2_postgres -d kiro2` sorgusu yanlış hedef bir D-12 varyantıydı.
- users.role BÜYÜK HARF iddiası runtime doğrulandı (DISTINCT: STUDENT/TEACHER/ADMIN/PARENT). require_role `.lower()` normalize input hoşgörüsü, DB enum değişmez.
- Borç #6 Round 2 PASS: A1.a deploy fix + A2 alembic teşhis + A3 DB/seed + A4 auth pattern → pilot kısmi başarı ile KAPANDI. TEACHER/PARENT seed hunt + 3 rol runtime smoke ayrı mini-pilota bırakıldı.
- 40_OPEN_DEBTS §Borç #6 kapsam revizyonu pending (A4 karma pattern: A4.i baskın + PARENT için A4.iii, hiyerarşik required_roles listesi).
- A5 (20610e9 cherry-pick) ayrı pilot bekliyor.
- 30_DERSLER §1.12 eklendi: Plan yazımı Pre-Flight (literal envanteri + sorgu failure-mode + sınıflandırma boyutluluğu).

## v15 DEĞİŞİKLİK NOTU (v13'ten, 24 Nisan)
- Tarih 20.04 → 24.04, versiyon v13 → v15 (v14 sessiz: gün içi tutulan ara taşlak)
- Alembic head `student_review_drift_001` → `offline_sync_pkg_20260420`
- `offline_sync_packages` tablo şeması + endpoint davranışları Kritik Kolon Adları'na eklendi
- `answered_at` ISO-8601 zorunluluğu (Round 2'de keşfedildi, plan'da yoktu)
- `sync-package?limit=N` deterministik olmayan davranış (K-2 açık karar)
- Alembic revision ID 32 char sınırı (Lesson 10)
- Migration ≠ Deploy dersi (D-12, Lesson 11)
- 21-24 Nisan offline_sync dörtlü pilot kronolojisi
- 24 Nisan Claude Desktop §1.9 dersi
- Açık kararlar bloku (K-1 state.md yol, K-2 limit bug, K-3 container durumu)
- Git durumu 5008ab6 HEAD, origin fb18866 (10 ileri, hijyen 11 yapacak)

## v13 DEĞİŞİKLİK NOTU (v12'den, referans)
- Tarih 06.04 → 20.04, versiyon v12 → v13
- Token alanı `.token` → `.access_token` (diary pilotunda tespit)
- Alembic head `20260406_uni_dept` → `student_review_drift_001`
- "13 disabled router" bloğu kaldırıldı, yerine Aşama A/B/C/D/E sınıflandırması (batch ADIM 0 sonucu)
- `productive_failure_api` bağımlılık notu düzeltildi (question_bank+topic_progress, sub_problems DEĞİL)
- `live_session_routes` SQL tablo adı drift'i (session_participants vs live_session_participants) eklendi
- `search` kategori bug'ı eklendi
- Alembic drift konsepti eklendi (diary pilot dersi)
- `pwa_sync_api` prefix tutarsızlığı notu (/api/pwa-sync-api)
- 20 Nisan oturumları bölümü eklendi
- "PİLOT ARTIFACT SİSTEMİ" yeni bölüm (Composer 2 × KIRO2 iş bölümü)
- Git durumu + açık konular güncellendi
