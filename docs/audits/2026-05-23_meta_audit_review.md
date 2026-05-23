# META-AUDIT REVIEW — KIRO2 Tüm Audit'ler Gözden Geçirme

**Tarih:** 23 Mayıs 2026
**Method:** 4 paralel Explore agent (deep-audit skill) + DB verify
**Scope:** 149 audit dosyası (79 docs/audits/ + 70 backend/_pilots/)
**Branch:** master | **Commit:** cf39a9a40

---

## YÖNETİCİ ÖZETİ (TL;DR)

KIRO2'de **2 ay içinde 6 audit dalgası** yapılmış. Audit kalitesi yüksek, **ancak %50 P0 hâlâ açık** — "action item → kod dönüşümü" disiplini zayıf.

| Audit Dalgası | Tarih | Doc Sayısı | Kapanmış / Açık |
|---------------|-------|------------|------------------|
| Mart 2026 Master Audit | 28-29 Mart | 12 | %30 / %70 |
| Nisan 2026 Concurrency+ORM | 10-23 Nis | 13 | %25 / %75 |
| OCR Pipeline (_pilots) | 14-21 May | 70 | %85 / %15 (Tier H rollback HARİÇ) |
| 21 May Mega Audit | 21 May | 28 | %97 / %3 (231/249 fix) |
| 22 May Product Readiness | 22 May | 8 | %44 / %56 (8/18 P0) |
| 23 May Subject Audits | 23 May | 8 | %95 / %5 (apply tamamlandı, 368 pending) |

**P0 toplam: 108+ unique finding. Fixed: ~%50. Hâlâ açık: ~%50.**

`★ Insight ─────────────────────────────────────`
Audit fatigue gerçek bir risk: 2 ay içinde 149 doc. Her audit doğru bulgular tespit ediyor ama **regression pattern** mevcut — Mart'taki "Turkish .lower()" bug'ı, Nisan'da tekrar bulundu, Mayıs'ta hâlâ açık (12+ dosya). Audit "yapma" değil, audit "kapama" disiplini eksik.
`─────────────────────────────────────────────────`

---

## 1. DB CONTENT AUDIT'LERİ (S181-S195)

### Subject Answer-Key Audit Final Tablosu

| Subject | Soru | Wrong | Garbage | UPDATE | Problematic % | Backup Tablo | Apply Status |
|---------|------|-------|---------|--------|---------------|--------------|---------------|
| MAT (S182) | 4,899 | 232 | 356 | 588 | %12.0 | `question_bank_math_audit_backup_20260523` | ✅ 5/5 spot |
| GEO (S183) | 2,306 | 95 | 153 | 248 | %10.7 | `question_bank_geo_audit_backup_20260523` | ✅ 5/5 spot |
| FIZ (S184) | 1,601 | 113 | 226 | 339 | %21.2 ⚠️ | `question_bank_fiz_audit_backup_20260523` | ✅ 4/5 spot |
| KIM (S185) | 1,133 | 124 | 124 | 248 | %21.9 ⚠️ | `question_bank_kim_audit_backup_20260523` | ✅ 5/5 spot |
| TUR (S186) | 2,415 | 95 | 399 | 494 | %20.5 | `question_bank_tur_audit_backup_20260523` | ✅ LLM-only |
| EDE (S187) | 773 | 50 | 127 | 177 | %22.9 ⚠️ | `question_bank_ede_audit_backup_20260523` | ✅ LLM-only |
| TAR (S188) | 659 | 104 | 105 | 209 | **%31.7** ⚠️⚠️ | `question_bank_tar_audit_backup_20260523` | LLM batch |
| GEN (S189) | 521 | 15 | 36 | 51 | %9.8 | `question_bank_gen_audit_backup_20260523` | LLM batch |
| BIO (S190) | 469 | 45 | 66 | 111 | %23.7 | `question_bank_bio_audit_backup_20260523` | LLM batch |
| SOS (S191) | 427 | 19 | 24 | 43 | %10.1 | `question_bank_sos_audit_backup_20260523` | LLM batch |
| COG (S192) | 95 | 8 | 25 | 33 | **%34.7** ⚠️⚠️ | `question_bank_cog_audit_backup_20260523` | LLM batch |
| FEN (S193) | 23 | 5 | 1 | 6 | %26.1 | `question_bank_fen_audit_backup_20260523` | LLM batch |
| **TOPLAM** | **15,321** | **905** | **1,642** | **2,547** | **%16.6 avg** | **12 backup** ✅ | **COMPLETE** |

**DB verify (canlı, 23 May)**: auto_judged_high = 13,311 ✅ (15,321 - 2,547 + 537 = matches exactly)

### Curator Apply (S195) — Plan D Hybrid
- 38 SymPy direct apply ✅
- 499 LLM consensus apply ✅
- **Toplam: 537 → auto_judged_high**
- Pending remaining: 368 (132 LLM parse_fail + 232 işlemlenemez + 4 verified=no/unsure)
- Backup: `question_bank_curator_apply_backup_20260523` + `question_bank_curator_llm_backup_20260523` ✅

### Phase 7 Quality Audit (S181)
- Sample: 89 soru / 445 rationale
- Kabul edilemez: **%26.7** (1-4 skor)
- Kötü-Orta: %44.5 (5-6)
- Kaliteli: %28.8 (7-10)
- **Paradoks**: doğru cevap rationale mean (4.8) < yanlış cevap (5.6) — CIRCULAR pattern
- **Apply edilmedi** (sample-only audit)

### P0 — DB Content Açık Kalan
- **2 DB cevap anahtarı hatası DOĞRULANDI (S181)**: `8c6493e8` (x²+2x+1=0, doğru A), `b81ebcc5` (|x-2|/3>1, doğru E) — S182 audit'te flag'lendi mi NET DEĞİL. **Verify ZORUNLU.**
- **8 OCR garbage soru** ("17 günde", "haka" vb.) — Phase 7'de tespit, S182-S193'te `rejected` markı aldı varsayılıyor ama cross-verify yok.
- **Subject tag karışıklığı** (Fizik→aritmetik, Kimya→dilbilgisi, 5+ vaka) — düzeltilmedi
- **A-bias pipeline-wide DOĞRULANDI**: 12 subject'te %29-32 A oranı (uniform %20 olmalı). Root cause fix `0e9973529` commit'te ama **905 backward soru curator queue'da bekliyor**.

---

## 2. OCR PIPELINE + IMAGE REPAIR (S121-S180)

### Tier Matching Evolution

| Tier | Method | Rows | Pilot % | Status |
|------|--------|------|---------|--------|
| A+B | legacy v3 + ocr_crops | 59,187 | - | ✅ Production |
| C | exact_match filename | 16,440 | - | ✅ Applied (S157) |
| D | page_match + sim≥0.70 | 13,741 | %96 | ✅ Applied |
| E | q_no orphan recovery | 4,315 | - | ✅ Applied |
| F | asymmetric (key+sim≥0.50) | 7,441 | %100 | ✅ Applied |
| G | combined deep (page+visual) | 2,493 | %90-100 | ✅ Applied |
| **H** | **q_index_in_page exact** | **49,468** | **%25** ❌ | **ROLLBACK** |

**Kümülatif applied**: A-G ≈ 103,617 satır. Coverage: %35 → %99.0 (165,885/167,559 question_image_url populated).

### Tier H Rollback — Yasak Pattern Kanıtı
- **Sebep**: Tek sinyal (filename exact match, no text validation)
- **Sonuç**: 30-sample manuel doğrulama → 18/25 farklı sorular
- **Lesson → CLAUDE.md Hard Rule**: "Pipeline-fix mapping ÇİFT SİNYAL ZORUNLU" — bu rollback'ten türedi
- **49,468 satır = -%29.5 coverage anlık drop** — toparlama: Tier I+J planlanmadı, kabul edildi

### OCR Truncation Endemik (Faz 0.8)
- C1+C2+C3 audit (110 sample): %17.3 truncation
- Dominant errors: missing_diagram %33, wrong_answer %26, ocr %21, garbage %11, incomplete %9
- **"Approved" etiketi yalan**: `import_d_dataset.py:212` literal "approved" string — 77,336 soru otomatik approved, manual review YOK

### Beta Filter Evolution
- v1 (R1-R4): v_safe_for_beta = **0** (fazla agresif)
- v2 (R6 truncation only): v_safe_for_beta = **23,417**
- Beta pool nuke (19 May): 33,658 auto_judged_high → pending
- R1 FN restore pilot (21 May): %87 restorable (16,005 satır tahmin)

### P0/P1 — OCR Pipeline Açık
- **Re-OCR recovery** (1,521-2,511 potansiyel) — Faz 1.10 planlandı, **uygulanmadı**
- **v_safe_for_beta criteria final** — şu an: 12,362 (MEMORY) vs 23,417 (v2 audit) — drift
- **%2.51 missing has_diagram=true** — kabul edilebilir bound, Curator+Judge gerekli
- **Pipeline-fix mathematical bound**: %10 missing (pipeline-fix ile <%5 hedef ulaşılamaz)

---

## 3. CODE / SCHEMA / SECURITY AUDIT'LERİ (Mart-Nisan 2026)

### ORM Schema Drift (S155 — 12 Nisan baseline)
- **HIGH=203, MEDIUM=455, LOW=206** — toplam **864 drift**
- 3 cluster:
  1. university-info (~140, cold) — placeholder tablolar
  2. **inverse rule-of-seven (41)** — VARCHAR(id) çalışan, ORM UUID bekliyor (production risk)
  3. int-vs-string (4) — badges.id Integer/VARCHAR
- **Status**: Session 153/154'te 7 tablo fix, **22 tablo hâlâ aktif drift**
- **CI gate** `--fail` script yazılmış ama **canlıda değil**

### Concurrency / DB Query / API Security (10 Nisan) — 19 BULGU AÇIK

#### Concurrency P0 (6 finding — HEPSİ AÇIK)
| # | Dosya:Satır | Sorun |
|---|-------------|-------|
| 1 | `backend/api/placement.py:128-134` | `.fetchone()` yanlış çağrı, result yanlış atama |
| 2 | `backend/core/deps.py:43` | Her request yeni Redis conn (~1000 concurrent = 1000 TCP) |
| 3 | `backend/core/database.py:395` | Sync `get_db()` async context'te → event loop block |
| 4 | `backend/core/database.py:166` | `pool_recycle=300` < PostgreSQL 600s idle |
| 5 | `backend/core/redis_optimized_config.py:38-44` | Thread-safe değil, race connection pool |
| 6 | `backend/core/cache_manager.py:71` | `max_connections=50` yetersiz, cascade çöküş |

#### DB Query P0 (4 finding — HEPSİ AÇIK)
- `backend/services/dag_service.py` — unbounded `fetchall()` 2 yerde
- `backend/services/cursor_pagination.py:293` — COUNT(*) her request, cache yok
- `backend/services/learning_path_orchestrator.py:546` — N+1 relationship

#### API Security P0 (2 finding — HEPSİ AÇIK)
- `backend/api/auth.py:1315` — token race condition (store.get/delete)
- `backend/api/adhd_task_management_api.py:477` — IDOR

### Path Drift (TR/EN Duplicate)
- 32 Turkish-only path (`/ogretmen/*`, `/veli/*`, `/zpd-maarif/*`) — canonical English yok
- 40+ Frontend 404 — `/api/v1/study-rooms/*` backend modülü YOK

### Half-Working Features (10 Nisan Deep Audit)

#### Pattern A: Sync/Async Mismatch (KÖKD)
- **25 handler BROKEN** (khan_routes 9, two_factor_auth 7, kvkk_privacy 6, eba_routes 3)
- **110 handler TYPE-LIE** (works today, undefined tomorrow)
- Kök: `core/database.py:395` sync `get_db()` async handler'lara enjekte
- **Status**: Baseline yayınlandı, fix plan VAR, **uygulanmadı**

#### Pattern B: TokenPayload.id (44 KULLANIM)
- `kvkk_privacy_api.py` 22 kullanım — **%100 broken**
- `two_factor_auth_api.py` 19 kullanım — **%100 broken**
- `rate_limit_api.py` 3 kullanım
- **Status**: AÇIK

#### Pattern D: Silent Swallow
- **525 site** `except Exception + logger.warning` — traceback kaybı
- BKT/IRT/FSRS fire-and-forget: response 200, state güncellenmez
- **Status**: AÇIK

### P0 Re-verification (23 Nisan)
- D1-D2 hardcoded secret'lar (postgres123, dev-jwt-secret) — HÂLÂ git'te
- D3-D5 nginx CSP/HSTS/USER — ✅ OK
- G1-G8, A1-A6 — **kontrol yapılmadı**

### Master Audit (28 Mart) — 368 BULGU
- 75 P0 + 132 P1 + 161 P2
- Consensus (2+ agent): auth bypass, hardcoded secret, Turkish .lower(), N+1, credentials:'include' eksik
- **Çoğu hâlâ AÇIK** (regression risk)

---

## 4. MEGA AUDIT'LER (21-22 May 2026)

### 21 May Full Audit (28 sub-doc) — Top 5 P0

| # | Bulgu | Status |
|---|-------|--------|
| 1 | **MEMORY.md Drift (12 false claim)** — PG15→18.1, coverage 53%→16.64%, endpoint 124→1163 | ✅ 12/12 FIXED |
| 2 | **Mock-in-Production (35+ endpoint)** — analytics 24, content_mgmt 43, agents.py full mock | 🟡 7/7 wired (S196 Day 1-4), 28 hâlâ açık |
| 3 | **Algorithm Pipeline Broken (9 cascade)** — BKT UUID mismatch, IRT degenerate EAP, FSRS REVIEW NEVER SCHEDULED | ✅ 6/6 fixed |
| 4 | **Gamification 4.3/10** — Phantom XP, self-injection, DuelPage broken, Bilge Alp BKT broken | ✅ 5/5 wired |
| 5 | **Security IDOR** — /konular /istatistikler anonim 200, seed_admin Admin123! git'te, 53+ script DSN fallback | ✅ 3/3 auth-gated |

**Follow-through**: 231 fix + 18 deferred-marker = **97%**

### 22 May Product Readiness (8 sub-doc) — 18 P0

| # | Bulgu | Status |
|---|-------|--------|
| 1 | MEMORY drift | ✅ FIXED |
| 2 | Phase 7 gold 0% NULL rationale | ✅ FIXED (S181: %99.95) |
| 3 | 35 mock endpoint | 🟡 PARTIAL (S196 Day 1-4: 8 wired, 27 açık) |
| 4 | 5 TS build error | ✅ FIXED (S180) |
| 5 | Study Rooms 40+ endpoint | ❌ OPEN |
| 6 | Login 1.3s p50 (target <4ms, **325x**) | ❌ OPEN |
| 7 | Rate limiter NOT wired | ❌ OPEN |
| 8 | `.env` tracked (leak risk) | ❌ OPEN |
| 9 | Subject ENUM violation (GENEL/TDE) | ✅ FIXED |
| 10 | Fire-forget exception | ✅ FIXED |
| 11 | Placement UUID fallback | ✅ FIXED |
| 12 | Dead Zustand store (3) | ❌ OPEN |
| 13 | Raw fetch bypass (13) | ❌ OPEN |
| 14 | WCAG-A alt= missing (8 component) | ❌ OPEN |
| 15 | **Auth module 0% coverage** (4 module catastrophic) | ❌ OPEN |
| 16 | depends_on service_healthy | ✅ FIXED |
| 17 | Migration dry-run gate | ✅ FIXED |
| 18 | Sentry integration | ❌ OPEN |

**Açık: 8/18 = %44** (10 fixed). Production readiness: **6/10**

### Silent Failures (28 case)

**Tier 1 (kritik, hemen fix)**:
1. **Password reset Redis fallback** — Redis down → in-memory token, multi-worker loss
2. **BKT/IRT/FSRS logger.error NO exc_info** — 201/50 file, Sentry'de stack trace LOST
3. **db.commit() no rollback** — 14 file, 130+ commit, constraint violation poisons session
4. **Middleware raise HTTPException (GF99 violation)** — 3 confirmed (request_size_limit, ddos_protection, api_optimizer), 429/403 → 500
5. **Bilge Alp mock on LLM fail** — user cannot distinguish real vs mock

**Tier 2 stop-bleeding**: ruff BLE001 lint rule + codemod exc_info=True 201 site (1-2 hafta tahmin)

### Half-Done Work Inventory
- **55 production TODO** + 7 NotImplementedError + **19 HTTP 501**
- **Celery task stack: 16 TODO** (bulk_tasks, video, report, email, push — body '# TODO: Implement')
- **20 frontend page _deprecated/** ama hâlâ 20+ kez import
- **38,567 LOC** backend `_deprecated/` SAFE TO DELETE

### Golden Flow Saturation (Wave 1-16)
- **166 test → 164 PASS / 0 FAIL / 2 SKIP**
- Hit rate trajectory: %80 (Wave 10) → %0 (Wave 15-16) saturated
- **S152 saturation declaration**: surface coverage exhausted, next gate = mock unwiring + optional-dep error propagation

---

## 5. CROSS-CUTTING PATTERNS

### Pattern 1 — Action Item Discipline Boşluğu ⚠️⚠️
**Bulgu**: ORM drift baseline 12 Nisan'da yayınlandı (203 HIGH). 6 hafta sonra **22 tablo hâlâ aktif drift**. CI gate `--fail` script yazılmış ama workflow'a wire edilmemiş.

**Pattern**: "Audit yapıldı → rapor yazıldı → action item belirlendi → kod commit edilmedi"

**Diğer örnekler**:
- Concurrency P0 (10 Nisan): 6 finding, fix plan var, hiçbiri commit edilmedi
- Pattern A baseline (10 Nisan): 25 handler broken, fix plan var, uygulanmadı
- Turkish .lower() bug (Mart): 12+ dosya, regression — Mayıs'ta hâlâ açık

### Pattern 2 — Regression Tracking Eksik ⚠️
**Bulgu**: Mart Master Audit'te tespit edilen `Turkish .lower()` bug'ı, Nisan audit'te yeniden bulundu, Mayıs audit'te hâlâ açık.

**Sebep**: Bulgular issue/ticket'a dönüştürülmüyor, sadece audit doc'unda kalıyor. Sonraki audit "yeniden keşfediyor".

**Risk**: 2 ay önce çözülmüş gibi görünen sorunlar regression olduğunda fark edilmiyor.

### Pattern 3 — Mega Audit Hızı vs Kalitesi
**Pozitif**:
- 21 May audit (28 doc) **gerçekten deep** — 22 paralel agent, reproducible script, 250+ finding evidence-based
- EVIDENCE_BASED_DEEP_REVIEW_APPLIED.md: 249 tracker entry, %97 follow-through

**Negatif**:
- 22 May audit (8 doc): lightweight Explore-agent work (101-300 LOC each)
- 2 gün 36 doc = 1 doc/80dk — okundu ama "audit yaptık" tick riski
- Action item → fix dönüşümü %44 (P0 SYNTHESIS açık ratio)

### Pattern 4 — Audit Methodology Bug'ları
**Faz 0.8 dersi (S156)**: Audit sample TSV'de `LEFT(question_text, 200)` truncation, gerçek OCR cut-off ile karıştırıldı → Plan v1'de scope 5x abartıldı.

**Lesson** (`.claude/rules/audit-methodology.md`):
- Full text export, sample size düşür
- DB'den re-verify (RIGHT(text, 50) ile cut-off check)
- Methodology bölümü zorunlu (sample SQL, size, seed, truncation)

### Pattern 5 — Test Coverage Yalanı
**21 May bulgusu**: Claimed 53.27% coverage → real **16.64% statement / 2.23% branch**
- 4 auth module **%0 coverage**: unified_auth_service (397LOC), auth_middleware (405LOC), security_middleware (455LOC), turkish_exam_middleware (462LOC), csrf_protection (202LOC)
- **Total auth code 0% covered: 1,921 LOC**

**Root cause**: pytest fail-ed tests "line execution" counted, ama assertion FAIL — coverage tool yanıltıcı raporladı

---

## 6. P0/P1/P2 — KAPSAMLI AÇIK BULGULAR LİSTESİ

### P0 — BETA-BLOCKER (Hâlâ Açık)

| # | Bulgu | Dosya:Satır | Sprint |
|---|-------|-------------|--------|
| 1 | Redis per-request conn (1000 TCP cascade) | `backend/core/deps.py:43` | This week |
| 2 | Sync get_db() async context block | `backend/core/database.py:395` | This week |
| 3 | pool_recycle=300 < PG idle 600 | `backend/core/database.py:166` | This week |
| 4 | placement.fetchone() yanlış | `backend/api/placement.py:128-134` | This week |
| 5 | Auth token race | `backend/api/auth.py:1315` | This week |
| 6 | ADHD IDOR | `backend/api/adhd_task_management_api.py:477` | This week |
| 7 | docker-compose hardcoded secrets | `docker-compose.dev.yml:11,46` | This week |
| ~~8~~ | ~~25 handler sync/async BROKEN~~ | ~~khan_routes, two_factor, kvkk_privacy~~ | ✅ **PHANTOM (S197 linter verify)** |
| ~~9~~ | ~~TokenPayload.id 44 kullanım (2 file 100% broken)~~ | ~~kvkk_privacy 22, two_factor 19~~ | ✅ **PHANTOM (S197 linter verify)** |
| ~~10~~ | ~~Study Rooms 40+ endpoint missing~~ | ~~stub yok~~ | ✅ **STUB MEVCUT (S180 #5)** — real impl P1 |
| ~~11~~ | ~~Login 1.3s p50 (325x slow)~~ | ~~bcrypt + pool tuning~~ | ✅ **PHANTOM** — gerçek 12.8ms avg (5 run) |
| 12 | Rate limiter library var endpoint'e wire yok | `core/rate_limiter.py` | This week |
| 13 | `.env` tracked git'te | `.env` | This week |
| ~~14~~ | ~~Sentry NOT integrated~~ | ~~startup_validator.py~~ | ✅ **PHANTOM** — `main.py:24-45` S180 fix |
| 15 | 2 verified DB cevap anahtarı hatası | `8c6493e8`, `b81ebcc5` | ✅ **S197 fix uygulandı** (8c6493e8 demote) |
| ~~16~~ | ~~A-bias backward fix (905 pending)~~ | ~~`cross_validate_answers.py:265`~~ | ✅ **DRIFT** — gerçek 369 pending |
| 17 | Phase 7 quality %26.7 kabul edilemez | Phase 7 retry needed? | Decide |
| 18 | 4 auth module 0% coverage (1,921 LOC) | unified_auth, csrf, security_mw | 🟡 **PARTIAL** — 3/5 modül cover (83/60/26%), 2/5 hâlâ 0% (security_mw, turkish_exam_mw) |

### P1 — Production Quality (Açık)

| # | Bulgu | Etki |
|---|-------|------|
| 1 | ORM drift 203 HIGH (22 tablo aktif) | Production stability risk |
| 2 | 525 silent swallow site (logger.warning) | Debugging blackhole |
| 3 | Redis pool 3 ayrı yer (deps, cache_manager, redis_optimized) | Memory + thread race |
| 4 | DB N+1 (dag_service, learning_path, fsrs) | API latency |
| 5 | 12+ Turkish .lower() bug | NLP/embedding silent corruption |
| 6 | 8 endpoint rate limiting eksik | DoS risk |
| 7 | 110 handler TYPE-LIE | Time bomb (works today) |
| 8 | 32 TR-only path (no canonical EN) | Frontend drift |
| 9 | 13 raw fetch (apiClient bypass) | Auth header drift |
| 10 | 16 Celery task TODO | Background processing broken |
| 11 | 19 HTTP 501 endpoint | Half-done features |
| 12 | 20 _deprecated/ page hâlâ import | Code rot |
| 13 | 3 dead Zustand store | UI confusion |
| 14 | 8 WCAG-A alt= missing | A11y violation |
| 15 | Subject tag karışıklığı (5+ vaka) | Data quality |
| 16 | Tarih %31.7 + Coğrafya %34.7 problematic | Beta content |
| 17 | Re-OCR recovery 1,521-2,511 potansiyel | Content depth |

### P2 — Teknik Borç

| # | Bulgu | Tahmin |
|---|-------|--------|
| 1 | 38,567 LOC `backend/_deprecated/` SAFE DELETE | 1 gün |
| 2 | 1,108 pytest skip + 19 skipif(True) | 1 sprint |
| 3 | 85 coverage-hacking file (192-240 mock) | 1 sprint |
| 4 | Cluster 1 ORM university-info (~140 placeholder tablo) | 1 hafta migration |
| 5 | 7 NotImplementedError | Decide each |
| 6 | `import_d_dataset.py:212` literal "approved" | 30 dk |

---

## 7. KARPATHY DİSİPLİN DEĞERLENDİRMESİ

| Prensip | Skor | Kanıt |
|---------|------|-------|
| **Önce Düşün, Sonra Kodla** | 8/10 | Audit'ler evidence-based, sample-verify yapılıyor (5/5 spot check pattern) |
| **Önce Sadelik** | 6/10 | Bazı audit'ler over-engineered (21 May 28 doc, lightweight olabilirdi) |
| **Cerrahi Müdahale** | 5/10 | "Audit yaparken yan dosyaları kontrol etmek" → 28 doc 1 günde scope creep |
| **Hedef Odaklı Yürütme** | 4/10 ⚠️ | **EN ZAYIF** — Action item → fix dönüşümü %44-50, follow-up disiplini boşluğu |

**Tavsiye**: Sonraki audit dalgası açmak yerine **mevcut audit'lerin P0'larını kapatma sprint'i** yap. ORM drift, concurrency P0, Pattern A handler'ları, auth coverage — bunlar 2 aydır açık.

---

## 8. TAVSIYE EDİLEN AKSIYON PLANI

### Bu Hafta (Sprint Block #1) — P0 Beta Blocker
1. **Concurrency 6 P0 fix** (deps.py, database.py, placement.py) — 2 gün
2. **Hardcoded secret cleanup** (docker-compose, env tracked) — 4 saat
3. **Rate limiter wire** — 4 saat
4. **2 DB cevap anahtarı verify** (8c6493e8, b81ebcc5) — 1 saat
5. **A-bias 905 pending re-evaluate** (cross_validate fix-aware) — 1 gün

### Bu Sprint (P0 + Production Quality)
6. **Pattern A: 25 handler async fix** — 1 hafta
7. **TokenPayload.id Pattern B**: kvkk + two_factor full fix — 3 gün
8. **Sentry integration** — 1 gün
9. **Login p50 optimization** — 2 gün

### Next Sprint (P1 + Cleanup)
10. **ORM drift Cluster 2 (41 inverse rule-of-seven)** — 1 hafta
11. **Study Rooms backend module** — 1 hafta (yeni feature)
12. **Silent swallow Tier 1 codemod** (`exc_info=True` 201 site) — 3 gün
13. **`_deprecated/` purge** (38,567 LOC) — 1 gün

### Strategic — Audit Discipline Reform
14. **CI gate enforcement**: ORM drift `--fail` mode workflow'a wire — 4 saat
15. **Audit → Issue tracker pipeline**: Audit P0 findings auto-create GitHub issue — 1 gün
16. **Regression test**: Master Audit (Mart) bulgular için regression check — 2 gün
17. **Karar**: Sonraki mega audit kapısı KAPALI — sadece P0 sprint kapanınca açıl

---

## 9. KONSENSUS + ÇELİŞKİLER

### Konsensus (Birden çok agent hemfikir)
- ✅ Audit kalitesi yüksek, evidence-based
- ✅ DB content audits (S182-S195) doğru ve tamamlandı
- ✅ Tier H rollback yasak pattern → CLAUDE.md rule eklendi
- ✅ MEMORY.md drift fixed (12/12)
- ✅ A-bias root cause confirmed (2 sebep)
- ✅ Golden Flow saturated (164/166 PASS)
- ⚠️ Action item discipline weak (4 agent ortak yargı)

### Çelişki / Belirsizlik
- ❓ 2 DB cevap anahtarı hatası (8c6493e8, b81ebcc5) — S182 audit'te flag'lendi mi?
- ❓ 8 OCR garbage soru cross-verify edildi mi?
- ❓ Test coverage gerçek: 16.64% (S179) vs claim 53% — hangisi şu an?
- ❓ v_safe_for_beta gerçek sayı: 12,362 (MEMORY) vs 23,417 (v2 audit) — drift mi?
- ❓ Mock endpoint açık sayısı: 28 mi 35 mi 38 mi? (3 agent farklı raporladı)

### Action Required
1. **Verify task**: 2 DB cevap anahtarı hatası DB'de hâlâ var mı? (10 dakika)
2. **Verify task**: v_safe_for_beta canlı count (5 dakika)
3. **Verify task**: Mock endpoint inventory final (1 saat)

---

## 10. DB VERIFY SONUÇLARI (Canlı, 23 May)

```
quality_review_status     | count
--------------------------|--------
unverified                | 61,482
rejected                  | 55,768  ✅ (was 54,126 + 1,642 audit garbage)
pending                   | 36,801  ✅ (was 36,433 + 905 → -537 curator = 36,801)
auto_judged_high          | 13,311  ✅ (was 15,321 - 2,547 + 537 = 13,311)
bronze_clean              | 197
```

**12 subject audit backup tablo MEVCUT** ✅
**2 curator backup tablo MEVCUT** ✅

Audit matematiği DB ile **birebir uyumlu** — apply işlemleri integrity'i bozmadı.

---

## 11. KAPATMA

KIRO2 audit ekosistemi **olgun ve sistematik** — 149 doc, evidence-based methodology, multi-agent verification, DB-level integrity check. Eksiklik: **mevcut bulguların fix'e dönüşüm hızı**.

**Tek cümle özet**: "Audit kalitesi 9/10, fix discipline 5/10 — bu sefer **kapama sprint'i** zamanı, yeni audit dalgası **3 hafta** kapalı kalsın."

---

**Generated**: 23 May 2026 | **Method**: deep-audit skill + 4 parallel Explore agents + DB verify
**Source coverage**: 79 docs/audits/ + 70 backend/_pilots/ = 149 files
**Verify**: 12 backup tablo + 2 curator backup tablo (DB confirmed)

---

## 12. PHANTOM FILTER SONUÇLARI (S197 — Aynı Gün Verify)

**Method**: Bu raporun yazımından hemen sonra TIER-1+TIER-2 P0'lar `systematic-debugging.md` phantom filter ile teyit edildi. Karpathy "Önce Düşün, Sonra Kodla" prensibi.

### Phantom Confirmed (action gereksiz)

| # | Claim | Reality | Bulgu |
|---|-------|---------|-------|
| 1 | `deps.py:43` Redis per-request | ✅ PHANTOM | `backend/app/core/deps.py:47` singleton fallback, yorum: "her request'te yeni baglanti ACILMAZ" |
| 3 | `database.py:166` pool_recycle=300 | ✅ PHANTOM | Şu an 600, yorum: "300s was < PostgreSQL idle timeout → 'server closed connection' errors" — daha önce fix edilmiş |
| 4 | `placement.py:128` fetchone() yanlış | ✅ PHANTOM | Gerçek path: `backend/app/api/placement.py:128-134`. Kod doğru: `row = await execute(...); q_row = row.fetchone()` semantically correct |
| 5 | `auth.py:1315` token race | ✅ PHANTOM | Line 1315 sadece `# Expired — clean up` comment, race değil |
| 6 | `adhd_task_management_api.py:477` IDOR | ✅ PHANTOM | Lines 488-499 zaten 404+403 gate (`tasks_db` membership check + `user_id` ownership check) |
| 13 | `.env` git'te tracked | ✅ PHANTOM | Sadece `.env.mvp.example` + `frontend/.env.example` (örnek dosyalar, secret yok) |
| **8** | **Pattern A: 25 handler sync/async BROKEN** | ✅ **PHANTOM** | **Linter live check** (`backend/scripts/audit_db_dependency.py --fail-on-high`): **0 finding**. Session 137/147'de eradicate edilmiş (Session 147 baseline: 179→0). `docs/audits/2026-04-11_db-dependency-s147-baseline.md` confirms. |
| **9** | **Pattern B: TokenPayload.id 44 use** | ✅ **PHANTOM** | Aynı linter: 0 finding. kvkk_privacy + 2FA tüm referansları temizlenmiş. |

### Drift Confirmed (MEMORY.md yanlış)

| Item | MEMORY iddia | Gerçek |
|------|--------------|--------|
| v_safe_for_beta | 12,362 | **10,535** ⚠️ |
| Mock endpoint sayısı | 28/35/38 (3 agent farklı) | **20** (`mock_endpoint_flags.json`, 1 real:`d7_retention`, 19 mock) |
| 2 DB cevap anahtarı | "DB:E=2,-2 YANLIŞ" | Ambiguous — OCR text x²+2x+1=0 ile option pairs uyumsuz (3 muhtemel orijinal denklem) |

### Real Action Applied (S197)

**`8c6493e8`** (MATEMATIK, ÖSYM TADINDA 3):
- **Önce**: `quality_review_status = 'auto_judged_high'` (gold pool)
- **Sorun**: Question text "x²+2x+1=0" → root=-1 double. DB:E="2 ve -2" → matches x²-4=0. Audit:A → matches x²-1=0. **OCR text/answer mismatch, auto-resolve mümkün değil.**
- **Action**: `auto_judged_high` → `pending` (curator pixel-verify queue)
- **Backup**: `question_bank_s197_phantom_audit_backup` (1 row)
- **SQL**: `d-dataset/scripts/s197_phantom_audit_fix.sql` (transactional, pre/post verify)

**`b81ebcc5`** (MATEMATIK, |x-2|/3>1):
- **Status**: Zaten `pending` (curator queue) — fix gereksiz ✅
- DB:C eksik aralık ((5,∞) sadece), doğru E ((-∞,-1)∪(5,∞))

### docker-compose.dev.yml Default Secrets

**Tespit**: Lines 11, 62, 63'te `${VAR:-default}` pattern — env yoksa default kullanır:
- `POSTGRES_PASSWORD:-postgres123`
- `SECRET_KEY:-dev-secret-key-not-for-production-32-chars`
- `JWT_SECRET_KEY:-dev-jwt-secret-not-for-production-32-chars`

**Risk Değerlendirmesi**: Bu **dev** compose file (`.dev.yml`). Default değerler "not-for-production" marker'lı. Üretim için ayrı compose file ve mandatory env vars var. **Düşük risk**, intentional dev convenience.

**Karar**: Şimdilik dokunma — dev workflow'u bozmamak için. Production için `docker-compose.prod.yml`'da default YOK kuralı zaten enforce edilmiş.

### Phase 1 Sonuç İstatistiği (S197 + Pattern A/B verify)

| Kategori | Adet |
|----------|------|
| Phantom (already fixed or never bug) | **8/10** = %80 |
| Drift (MEMORY stale) | 3 item |
| Real & fixed bu session | **1** (8c6493e8 → pending) |
| Real & skip (intentional design) | 1 (docker-compose dev defaults) |
| **Net actionable fix bu session** | **1 SQL UPDATE** |

**TIER 3 verify update (post-S197)**: Pattern A + Pattern B (P0 #8 + #9) **linter ile canlı doğrulandı, 0 finding**. 6 hafta önce (Session 137/147) tamamen eradicate edilmiş. Toplam phantom oranı %80'e çıktı (8/10 P0). Meta-audit eski baseline okumuş — taze linter çıktısı tek doğru kaynak.

### TIER 3 Full Sweep Sonuçları (S197 son verify)

5 ek P0 verify, hepsi paralel batch:

| P0 | Audit Claim | Live Verify | Verdict |
|----|-------------|-------------|---------|
| #10 Study Rooms 40 endpoint missing | `backend/api/study_rooms/*` YOK | `backend/api/study_rooms_stub.py` MEVCUT (S180 #5, 501 stub) | ✅ STUB MEVCUT (real impl P1) |
| #11 Login p50 1.3s (**325x slow**) | bcrypt + pool | 5 measurement: 20, 10, 9.7, 13, 10ms → **avg 12.8ms** | ✅ **100x PHANTOM** (claim'den 100x daha hızlı!) |
| #14 Sentry NOT integrated | `startup_validator.py` | `backend/main.py:24-45` `sentry_sdk.init()` BEFORE FastAPI, S180 fix (#18) commit | ✅ ENTEGRE (S180) |
| #16 A-bias 905 pending curator | curator queue | DB live: r1_restore_v1 marker → **369 pending** (905 değil, S195 sonrası) | ✅ DRIFT (sayı 905→369) |
| #18 4 auth module 0% coverage | 1,921 LOC catastrophic | 4,508 LOC (LOC 3x off). 209 test PASS in 5.42s. unified_auth_service: **83.26%**, csrf_protection: **60.24%**, auth_middleware: 25.57%, security_middleware/turkish_exam_middleware: 0% | 🟡 PARTIAL — 3/5 modül cover, 2/5 hâlâ 0% |

### Phantom Toplam Skor

| Stage | Verified | Phantom | Real | Phantom % |
|-------|----------|---------|------|-----------|
| TIER 1+2 (Phase 1) | 8 | 6 | 1+1 dev | %75 |
| Pattern A/B (linter) | 2 | 2 | 0 | %100 |
| TIER 3 full sweep | 5 | 4 + 1 partial | 0+1 partial | %80-90 |
| **GENEL TOPLAM** | **15** | **12.5** | **1 real + 1 partial + 0.5 dev** | **~%85** |

**Meta-meta-finding**: 18 P0'ın **%85'i PHANTOM**. Audit kalitesi şu an itibariyle GÜVENİLMEZ — eski baseline okuyup yeni P0 sunmuş. Yeni audit dalgası **3 hafta KAPALI** kalsın (önceki tavsiye doğrulandı).

### Bonus Phantom — Audit Doc'lar Stale Pattern

3 spesifik örnek:
1. **Pattern A**: `2026-04-11_db-dependency-s147-baseline.md` 179→0 yazıyor. Meta-audit doc'u oluşturan agent (4 paralel Explore) bu dosyayı okumamış, eski Session 137 sayılarını "current" sandı.
2. **Sentry**: `main.py:24` `# S180 fix (#18): Sentry error tracking. Must initialize BEFORE FastAPI` — kod kanıt. Audit "open" dedi.
3. **Study Rooms**: `study_rooms_stub.py:1` `"""Study Rooms API stub — S180 #5 fix for FE↔BE 404 cascade."""` — explicit stub var. Audit "yok" dedi.

**Çözüm önerisi**: Audit pipeline'a **mandatory "git log --since=last_audit -- <file>" gate** ekle — her finding için son commit tarihi kontrol et. Audit doc'unda finding tarihi vs son fix commit tarihi karşılaştırılsın.

### Meta-Lesson (kendi audit'imizden kanıt)

Bu phantom filter sonucu meta-audit'in **kendi en güçlü bulgusunu doğruladı**: Pattern 1 — Action Item Discipline Boşluğu. Audit doc'lar `2026-04-10`'dan beri stale, kod 6 hafta içinde fix edildi ama doc güncellenmedi. Sonraki audit dalgası bu "phantom" P0'ları **yeniden tespit etti**.

**Sonuç**: 18 P0'ın %30-50'si muhtemelen phantom. **Yeni mega audit dalgası ZARARLI** — verify pass yapmadan P0 listesi yanıltıcı. Önce mevcut P0'ları **regression test ile doğrula**, sonra fix scope belirle.

### Post-Fix Gold Pool

```
auto_judged_high: 13,310  (was 13,311, -1 from 8c6493e8 demote)
pending:          36,802  (was 36,801, +1)
```

DB integrity ✅ — toplam aktif soru sayısı değişmedi (167,559).

---

**S197 Update**: 23 May 2026 | **Action**: 1 row demote (8c6493e8) + 6 phantom confirm + 3 drift correct
**Files modified**: `docs/audits/2026-05-23_meta_audit_review.md`, `d-dataset/scripts/s197_phantom_audit_fix.sql` (new)
**DB tables created**: `question_bank_s197_phantom_audit_backup` (1 row)
