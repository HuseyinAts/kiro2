# Feature Health Audit — 12 User Flow Trace

**Tarih:** 2026-04-10
**Yöntem:** 4 paralel sub-agent, statik analiz (Read + Grep), ROOT dizin taranmadı
**Kapsam:** 12 ana kullanıcı akışı, frontend → API → service → DB zinciri
**Amaç:** "Yarım çalışan" feature'ların kök sorununu belirlemek, root cause kategorisi histogramı üretmek

---

## TL;DR

- **12 flow** trace edildi
- **5 flow OK** (Sınav, Chat, League, Veli, Admin)
- **7 flow kırık veya kırılgan**
- **En belirgin kategori**: `router-loader` (2×) + `orchestrator-prereq/mastery` (2×)
- **Kritik bulgu**: `/api/v1/teacher/classes` endpoint backend'de yok (çoğul/tekil prefix mismatch)
- **Kritik bulgu**: `/api/v1/fsrs/due` sadece `_deprecated` klasöründe — frontend 404 alıyor

---

## Flow Bazlı Özet Tablosu

| # | Flow | Katman | Kategori | Severity | Kanıt |
|---|------|--------|----------|----------|-------|
| 1 | Sınav (başlat→çöz→sonuç) | ✅ OK | none | — | `sinav.py:22,356` + `osym_exam_engine.py:441` (is_active ✓), router kayıtlı |
| 2 | Günlük çalışma planı | Service | orchestrator-mastery-inflation | P1 | `learning_path_v2.py` — `quality = 0.5 + like_ratio * 0.5` (0.5 base offset) |
| 3 | FSRS tekrar | Router | router-loader | **P0** | `/api/v1/fsrs/due` sadece `api/_deprecated/fsrs.py`'da — modern path yok, frontend `FSRSReviewPage.tsx:45` 404 alır |
| 4 | AI sohbet (SSE) | ✅ OK | none | — | SSRF + file chunking + SSE timeout + graceful fallback hepsi var |
| 5 | Lig sıralaması | ✅ OK | none | — | XP aggregation OK, contract match, graceful fallback |
| 6 | 1v1 düello (SSE) | Service | is-active-missing (silent) | P1 | `duel_api.py:444-445` — soru yoksa boş liste döner, matchmaking devam → oyun bozuk |
| 7 | Veli çocuk takibi | ✅ OK | none | — | `parent_service.py:176-180` IDOR check + approved=TRUE, KVKK uyumlu |
| 8 | Öğretmen sınıf yönetimi | Router | router-loader | **P0** | Frontend `/api/v1/teacher/classes` → backend `/api/v1/teachers` (çoğul!). `ModernTeacherClassesPage.tsx:65` vs `teacher_routes.py:30` |
| 9 | Admin kullanıcı yönetimi | ✅ OK | none | — | RBAC + parameterized queries + soft delete |
| 10 | Öğrenci dashboard/stats | Service | async-generator (cache race) | P2 | `student_dashboard.py:67-68` — cache init race on Redis down |
| 11 | Sosyal hub | API | dual-table (N+1) + content-filter (XSS) | P1 | `social_summary_api.py:32-123` — 6 ayrı model query, no batch; `social_content_filter.py:62-88` HTML entity encoding eksik |
| 12 | Dungeon Learning Path | Service | orchestrator-prereq-bypass | **P0** | `learning_path_orchestrator.py:197` — `prereq_blocked=False` default + exception handling. DAGService fail → tüm konular UNBLOCKED |

---

## Root Cause Kategori Histogramı

| Kategori | Count | Flows | Pattern |
|----------|-------|-------|---------|
| **OK (çalışıyor)** | 5 | 1, 4, 5, 7, 9 | — |
| **router-loader** | 2 | 3, 8 | Frontend path ↔ backend prefix/register mismatch |
| **orchestrator-prereq/mastery** | 2 | 2, 12 | DAG exception → unsafe default, mastery hesap hatası |
| **is-active-missing (silent)** | 1 | 6 | Filter var ama fallback sessiz fail |
| **dual-table (N+1)** | 1 | 11 | 6 model query, batch yok |
| **content-filter (XSS)** | 1 | 11 | HTML entity encoding eksik |
| **async-generator (cache)** | 1 | 10 | Cache init race condition |

**Pattern tespiti:** En büyük 2 kategori (**router-loader + orchestrator**) 4 flow'u vuruyor — %33. Pilot fix Learning Path olduğundan, orchestrator pattern'i doğrudan pilot'un kapsamında.

---

## P0 Öncelikli (Hemen Fix)

### P0-1: `/api/v1/fsrs/due` 404 (Flow 3)
- **Dosya**: `backend/api/_deprecated/fsrs.py` (taşınmış), `frontend/src/pages/FSRSReviewPage.tsx:45`
- **Sebep**: Modern FSRS router `backend/routers/loader.py`'de `app.api.fsrs` olarak kayıtlı ama dosya `_deprecated/`'e taşınmış
- **Fix**: Modern router'ı restore et veya `diary_api.py:85` altındaki due endpoint'e yönlendir

### P0-2: Teacher router prefix mismatch (Flow 8)
- **Dosya**: `backend/api/teacher_routes.py:30` prefix=`/api/v1/teachers` vs `frontend/src/pages/ModernTeacherClassesPage.tsx:65` fetch=`/api/v1/teacher/classes`
- **Sebep**: Çoğul/tekil inconsistency + `/classes` endpoint backend'de yok
- **Fix**: Prefix `/api/v1/teacher` olarak düzelt VE `/classes`, `/students`, `/exams` endpoint'lerini ekle (ya da frontend'i backend'e uyarla)

### P0-3: DAG prereq bypass on error (Flow 12)
- **Dosya**: `backend/app/services/learning_path_orchestrator.py:197,227-230`
- **Sebep**: `prereq_blocked = False` default + `try/except` bloğu hatayı yutmuyor ama default False kalıyor (exception'dan önceki path)
- **Fix**: Default `True`, success path'te `False`'a çek. Fail-safe inversi.

---

## P1 Öncelikli (Sprint İçi)

### P1-1: Mastery inflation — quality base offset (Flow 2)
- **Dosya**: `backend/api/learning_path_v2.py`
- **Sebep**: `quality = 0.5 + like_ratio * 0.5` — base 0.5 tüm öğrencileri şişiriyor
- **Fix**: `quality = like_ratio` (bu arada `.claude` tarafındaki `orchestrator.py:641` +1.0 offset de burada mı? — Faz C'de doğrula)

### P1-2: Duel silent fallback (Flow 6)
- **Dosya**: `backend/api/duel_api.py:119-121,444-445`
- **Sebep**: `_select_duel_questions` 5 soru bulamazsa boş liste döner, matchmaking iptal edilmez
- **Fix**: `raise HTTPException(503, "Yeterli soru yok")` — matchmaking öncesi soru sayısı kontrolü

### P1-3: Social XSS encoding eksik (Flow 11)
- **Dosya**: `backend/services/social_content_filter.py:62-88`
- **Sebep**: `_strip_evasion()` + `_normalize_tr()` HTML entity encoding yapmıyor
- **Fix**: `html.escape()` ya da bleach ekle

---

## P2 Teknik Borç

- **Flow 10 cache race**: `backend/api/student_dashboard.py:67-68` — cache init lock ekle
- **Flow 11 N+1**: `social_summary_api.py` — 6 query batch'e çevir veya cache koy

---

## Pilot (Learning Path) Kapsamı — Faz C İçin

Faz A bulguları pilot'un kapsamını **daralttı**:

- **P0-3** (Flow 12 DAG bypass) → `learning_path_orchestrator.py:197,227-230`
- **P1-1** (Flow 2 mastery inflation) → `learning_path_v2.py` quality formula
- **Flow 12 contract**: Frontend `/weekly`, `/status`, `/goal` endpoint'leri backend'de var mı? → Faz C başında doğrula
- **Flow 2 path birleştirme**: 3 route (`/learning-path`, `/learning-path-map`, `/daily-plan`) hangi hook'lardan hangi endpoint'e gidiyor?

**Pilot root cause hipotezi:** Tüm Learning Path sorunlarının ortak kökü `orchestrator-prereq/mastery` kategorisi — hatalı **default değer** + **exception yutma** kombinasyonu. Fix pattern'i: fail-safe defaults + explicit error propagation.

---

## Faz B (Playwright Runtime Smoke) Sonuçları

**Tarih:** 2026-04-10 (Faz A ile aynı gün)
**Dosya:** `frontend/src/test/e2e/feature-health-smoke.spec.ts` (8 flow) + mevcut `mvp-smoke.spec.ts` (4 flow)
**Altyapı:** Docker stack healthy (backend 8000, frontend 3000, postgres 5434, redis 6379)
**Seed:** `ogrenci@kiro2.com / Kiro2Beta2026@x` (+ veli/ogretmen/admin)

### Runtime Matris — 12 Flow

| # | Flow | Faz A Hipotez | Faz B Runtime | Kesişim | Yeni Kanıt |
|---|------|---------------|---------------|---------|-----------|
| 1 | Sınav | ✅ OK | OK | OK | mvp-smoke.spec.ts PASS |
| 2 | Daily Plan | mastery inflation P1 | OK (crash yok) | Semantic only | mvp-smoke.spec.ts PASS — bug runtime'da görünmez (öğrenci şişmiş mastery ile çalışıyor) |
| 3 | **FSRS Review** | `/fsrs/due` 404 **P0** | OK — **0 API fail** | **PHANTOM** | `curl /api/v1/fsrs/due` → **401** (endpoint VAR, auth gerek). OpenAPI: `/api/v1/fsrs/due,due-count,review,stats` hepsi kayıtlı |
| 4 | Chat (SSE) | ✅ OK | OK | OK | mvp-smoke.spec.ts PASS |
| 5 | **League** | ✅ OK | **Content text eksik** (0 5xx) | **YENİ BULGU** | Sayfa açılıyor ama beklenen "lig/tier/rank/xp" metni yok — UI render veya data eksik. 5xx yok, sessiz kırık |
| 6 | Duel (SSE) | silent fail P1 | OK (matchmake crash yok) | Semantic only | Boş soru listesi runtime'da görünmez — oyun başlayamaz ama UI crash etmez |
| 7 | Parent | ✅ OK | OK | OK | 0 5xx, content visible |
| 8 | **Teacher** | `/teacher/classes` 404 **P0** (prefix typo) | **404 DOĞRULANDI** | **DAHA DERİN** | **OpenAPI kanıt**: `/api/v1/teachers/*` var ama sadece profil/randevu (`/teachers/appointments`, `/teachers/register`, `/teachers/profile/{id}`). **`/classes`, `/students`, `/exams` HİÇ YOK**. Prefix typo değil — **sınıf yönetimi backend'i tamamen eksik** |
| 9 | Admin | ✅ OK | OK | OK | 0 5xx |
| 10 | Dashboard | cache race P2 | OK | Race condition runtime'da tetiklenmedi | mvp-smoke.spec.ts PASS |
| 11 | Social | N+1 + XSS P1 | OK (0 5xx) | Semantic + perf only | Runtime crash yok — perf/XSS test etmedi |
| 12 | Dungeon LP | DAG prereq bypass **P0** | OK — SVG+Canvas render | Semantic only | Render çalışıyor, semantic bug (öğrenci yanlış konuya erişebilir) runtime'da görünmez |

### Ek Runtime Bulgusu: mvp-smoke 1.2 (login → dashboard)

```
Expected: /dashboard/
Received: /learning-path
```

Login sonrası student `/dashboard`'a değil **`/learning-path`**'e yönlendiriliyor. Bu bir redirect değişikliği veya auth flow regresyonu. `ProtectedRoute` veya `LoginPage` default target değişmiş olabilir. **Yeni bulgu — Faz A'da yoktu.**

---

## Revize Root Cause Histogramı (Faz A + B Kesişim)

| Kategori | Orijinal | Gerçek | Değişim |
|----------|---------|--------|---------|
| OK (çalışıyor) | 5 | 5 (aynı) | — |
| **router-loader** | 2 (Flow 3, 8) | **1** (sadece Flow 8, Flow 3 phantom) | **-1** |
| **missing-backend** (yeni) | — | **1** (Flow 8 — sınıf yönetimi API yok) | **+1** |
| **orchestrator-prereq/mastery** (semantic) | 2 | 2 (runtime'da görünmez, semantic) | — |
| **is-active-missing** (silent) | 1 | 1 (runtime'da görünmez) | — |
| **dual-table (N+1)** | 1 | 1 (runtime'da görünmez) | — |
| **content-filter (XSS)** | 1 | 1 (runtime test etmedi) | — |
| **async-generator (cache)** | 1 | 1 (runtime'da tetiklenmedi) | — |
| **ui-content-drift** (yeni) | — | **1** (Flow 5 — sayfa açılıyor ama text yok) | **+1** |
| **auth-redirect** (yeni) | — | **1** (Flow 1 — login default `/learning-path`) | **+1** |

**Önemli insight:** Faz A'daki 3 P0'dan **2'si Faz B'de revize edildi**:
- **P0-1 FSRS** → **PHANTOM** (endpoint var, `_deprecated` dosyası yanıltıcıydı)
- **P0-2 Teacher** → **DAHA DERİN** (prefix typo değil, backend yok)
- **P0-3 DAG** → Runtime'da görünmez (semantic, pilot kapsamında kalır)

**Gerçek P0 listesi (post-Faz B):**
1. **Teacher sınıf yönetimi backend'i yok** (Flow 8) — sprint scope
2. **DAG prereq bypass** (Flow 12) — orchestrator pilot
3. Mastery inflation (Flow 2) — orchestrator pilot

**P0'dan düşenler:**
- FSRS route — endpoint var, 401 döndürüyor (auth header eksik runtime'da normal davranış)

**Yeni P1'ler (Faz B):**
- Flow 5 League text yok (data veya UI bug, sessiz kırık)
- Flow 1 login default target değişmiş (regresyon veya kasıtlı UX)

---

## Sentez: Pilot Seçimi Doğrulandı mı?

**Evet — Learning Path pilot seçimi GEÇERLİ, hatta güçlendi.**

Faz A'da pilot'a 2 bulgu (Flow 2 mastery + Flow 12 DAG) işaret ediyordu. Faz B sonrası:
- Bu ikisi **hâlâ geçerli** (semantic bug, runtime'da invisible)
- Runtime'da tespit edilemedikleri için **pilot protokolünün** (Root Cause Analysis tablosu + fail eden test yazma) mecburiyeti arttı
- Pilot fix pattern'i (`fail-safe defaults + explicit error propagation`) tüm "semantic invisible" bug'lara uygulanabilir

**Yeni karar:** Pilot kapsamı değişmiyor. Faz B bulguları (Flow 5, Flow 8 backend, login redirect) **ayrı backlog** — pilot sonrasında Faz D'nin genelleme turunda veya ayrı sprint'te ele alınır.

---

## Sonraki Adım (Faz C — Learning Path Pilot)

Pilot kapsamı:
1. **Flow 12 (P0):** `backend/app/services/learning_path_orchestrator.py:197,227-230` — DAG prereq bypass
2. **Flow 2 (P1):** `backend/api/learning_path_v2.py` — mastery quality formula (`0.5 + like_ratio * 0.5`)

Protokol (`.claude/rules/debugging-first.md` + `systematic-debugging.md`):
1. Root Cause Analysis tablosu (ZORUNLU gate)
2. Fail eden pytest yaz (TDD red)
3. Fix max 3 dosya
4. pytest PASS (TDD green)
5. `pytest backend/tests/app/services/test_learning_path*` + runtime doğrulama

**Backlog (pilot sonrası):**
- [ ] Teacher classroom backend — spec + implement (~5 endpoint yeni)
- [ ] Flow 5 League UI/data drift araştır
- [ ] Login default target regresyon kontrolü

---

## Faz B+ Derin Dalış (4 paralel sub-agent, 2026-04-10)

Faz B sonrası 4 kritik konuda kod+runtime düzeyinde kanıt toplandı. Sonuçlar Faz A/B bulgularını **önemli ölçüde revize etti**.

### Derin dalış 1: FSRS (Flow 3) — **PHANTOM KESİN ONAYLANDI**

**Kanıt zinciri:**
- `frontend/src/pages/FSRSReviewPage.tsx:45` → `apiRequest('/api/v1/fsrs/due?limit=20')` + satır 55 `/review`
- `backend/app/api/fsrs.py:33-50` → `@router.get("/due")` modern, `Depends(get_current_user)` (satır 41), `question_bank` JOIN `user_item_fsrs` WHERE `q.is_active=TRUE` (satır 68)
- `backend/routers/loader.py:54` → `"app.api.fsrs": ("learning", "app.api.fsrs")` **AKTİF**
- `backend/api/_deprecated/fsrs.py` — VAR ama **registry'de kayıtlı değil**, farklı path (`/flashcards/due` — modern `/due` ile çakışmıyor), farklı servis import ediyor

**Ek keşif:** `backend/openapi.json` **stale** — sadece deprecated routes içeriyor, modern routes schema'da yok. Ama runtime Python import üzerinden çalışıyor, curl 401 doğru davranış.

**Faz A neden yanıldı:** `_deprecated/fsrs.py` dosya mevcudiyetini "bozuk" ile karıştırdı. Router registry'yi kontrol etmedi.

**Sonuç:** Faz A P0-1 **SİLİNDİ**. Pilot scope'tan çıkartıldı.

---

### Derin dalış 2: Teacher Classroom (Flow 8) — **%100 yeni feature**

**Frontend envanteri — 6 sayfa, 9 eksik endpoint:**

| Frontend sayfa | Beklenen endpoint | Backend var mı? |
|----------------|-------------------|-----------------|
| ModernTeacherClassesPage.tsx:65,100 | GET/POST `/api/v1/teacher/classes` | **YOK** |
| ModernTeacherStudentsPage.tsx:59 | GET `/api/v1/teacher/students` | **YOK** |
| ModernTeacherExamsPage.tsx:83,134,167 | GET/POST `/api/v1/teacher/exams[/{id}]` | **YOK** |
| ModernTeacherAssignmentsPage.tsx:81,156,183 | GET/POST/DELETE `/api/v1/teacher/assignments` | **YOK** |
| ModernTeacherContentPage.tsx:91,198,231 | GET/POST/DELETE `/api/v1/teacher/contents` | **YOK** |
| ModernTeacherReportsPage.tsx:65 | GET `/api/v1/teacher/reports` | **YOK** |

**Backend mevcut:**
- `backend/api/teacher_routes.py:30` — prefix `/api/v1/teachers` (plural) — **profil + randevu marketplace**
- Endpointler: register, profile, expertise, certifications, availability, appointments, reviews
- Models: `TeacherPoolProfile`, `Appointment`, `TeacherAvailability`, `TeacherExpertise`, `TeacherCertification`
- **Sınıf/Öğrenci/Sınav/Ödev/Rapor modeli YOK**

**Scope gerçekliği:** "Prefix typo" değil — **5+ model, 6+ service, 9+ endpoint yeni yazılacak**. Frontend sayfalar mock fallback yapıyor ki kullanıcıya "yarım çalışıyor" gibi geliyor.

**Sonuç:** Pilot dışı — ayrı sprint. Tek başına minimum 2-3 gün iş.

---

### Derin dalış 3: Learning Path Pilot — **2/2 Faz A hipotezi REVİZE**

#### Bug 1 revizyon: DAG prereq bypass

**Gerçek kanıt (`backend/app/services/learning_path_orchestrator.py`):**
- Satır 197 `prereq_blocked = False` — DOĞRU default (audit notu yanlıştı)
- Satır 203-226 exception handler — zaten `prereq_blocked = True` yapıyor (güvenli default)

**Gerçek bug:** DAGService **fallback built-in DAG** dönüyor (`dag_service.py`). `build_yks_dag()` düz/flat graph — **hiç konu-konu prereq yok**. DB boşsa veya query fail ederse:
1. Exception YAKALANMIYOR (çünkü fallback return ediyor)
2. Flat DAG → tüm konular UNBLOCKED
3. Orchestrator hata GÖRMÜYOR, güvenli default TETİKLENMİYOR

**Kök sebep orchestrator'da değil, `dag_service.py` fallback'inde.** Fix scope:
- `backend/app/services/dag_service.py` — fallback built-in DAG'ı kaldır veya "empty prereq" warning ile işaretle
- DB boşsa 503 veya `prereq_blocked=True` zorla

#### Bug 2 revizyon: Mastery inflation

**Gerçek kanıt (`backend/api/learning_path_v2.py:353`):**
```python
quality = 0.5 + like_ratio * 0.5
```
Bu değer `_compute_final_score()` içinde **video resource ranking** için kullanılıyor:
```python
score = relevance * 0.35 + quality * 0.25 + popularity * 0.15 + turkish * 0.25
```

**Kritik:** Bu score **mastery'ye feed OLMUYOR**. Mastery truth = `StudentAbility.theta` (IRT 3PL, quiz submission'da `submit_quiz` endpoint 1361-1398 güncelliyor). Video quality score sadece frontend ranking için.

**Sonuç:** **Bug 2 yanlış pozitif.** Kullanıcı için etkisi: kötü videolar iyi görünür (UI deception), ama mastery yanlış hesaplanmıyor. P2 teknik borç olarak düşer.

#### Frontend 3-route gerçek durumu

| Route | Component | Hook | Endpoint |
|-------|-----------|------|----------|
| `/learning-path` | LearningPathPage | `useLearningPath()` | `/learning-path/completion/{sid}` |
| `/daily-plan` | DailyPlanPage | **yok** (direct fetch) | `/learning-path/today` + `/status` |
| `/learning-path-map` | LearningPathMapPage | **yok** (direct fetch) | `/learning-path/weekly` + `/status` |

**Drift:** 3 farklı endpoint, 2 sayfada hook kullanılmıyor (cache miss, race condition). `/status` iki sayfadan paralel çağrılıyor. Refactor önerilir ama pilot kapsamı değil (MEDIUM effort, LOW risk).

---

### Derin dalış 4: League + Login Redirect

#### Flow 5 — League sessiz kırık

**Kök sebep:** Backend fallback + frontend guard eksikliği kombinasyonu.
- `backend/services/league_service.py:144-165` — exception yakaladığında **mock standings** dönüyor (boş tier, "Sen" hardcoded isim). Gerçek DB tablosu (`league_memberships`) muhtemelen boş veya `week_start` mismatch.
- `frontend/src/pages/LeaguePage.tsx:60-64` — `if (error || !data)` check var ama `data.standings.length === 0` kontrolü YOK. Boş standings → map() hiç render etmiyor → "Haftalık Sıralama" başlığı (satır 107) görünmüyor.

**Fix:**
1. Backend: fallback'te boş standings dönme, 503 fırlat
2. Frontend: `data.standings.length === 0` → "Henüz sıralama yok" empty state

#### Login redirect = KASITLI

**Kanıt:** Commit `3be081f` (16 Mar 2026) — "fix: learning path quiz topic filter, video fallback, **demo login routing**"
- `frontend/src/pages/ModernLoginPage.tsx:56` → `ogrenci: '/learning-path'` (eskiden `/dashboard`)
- **Ama:** `frontend/src/components/Auth/ProtectedRoute.tsx:94` hâlâ `/dashboard` diyor → **tutarsızlık**

**Fix:**
1. `mvp-smoke.spec.ts:44` test'i `/learning-path` beklemeye güncelle
2. `ProtectedRoute.tsx:94` → `/learning-path` (consistency)

---

## Revize Pilot Scope (Post-Derin Dalış)

| Dosya | Değişim | Bug | Risk | Effort |
|-------|---------|-----|------|--------|
| `backend/app/services/dag_service.py` | Fallback built-in DAG kaldır, DB boşsa 503 | **Bug 1 (CRITICAL)** | CRITICAL | 1.5h |
| `backend/app/services/learning_path_orchestrator.py` | DAG empty check → explicit logging | Bug 1 safety net | MEDIUM | 1h |
| `backend/tests/app/services/test_dag_service.py` | `test_dag_empty_blocks_all_topics()` fail-first test | TDD red gate | — | 1h |

**Pilot kapsam dışı (backlog):**
- ❌ Mastery inflation (Bug 2) — yanlış pozitif, P2 UI tweak
- ❌ 3-route refactor — optional
- ❌ Teacher classroom backend — yeni sprint
- ❌ League empty state — ayrı P1 fix
- ❌ ProtectedRoute consistency — P2
- ❌ OpenAPI schema regenerate — P2

**Pilot artık tek bir root cause'a odaklanıyor:** fail-safe default inversi — fallback silent recovery YERİNE explicit error propagation.

**Protokol (Faz C):**
1. RCA tablosu (debugging-first.md gate)
2. `pytest backend/tests/app/services/test_dag_service.py::test_dag_empty_blocks_all_topics` — fail ettiğini doğrula
3. Fix: `dag_service.py` fallback kaldır + `orchestrator.py` empty check
4. Fail→PASS
5. `feature-health-smoke.spec.ts Flow 12` re-run → hâlâ PASS (semantic bug runtime'da invisible olduğu için)
6. Manuel doğrulama: DB `topic_hierarchy` tablosu boşken endpoint 503 mü dönüyor?

---

## Faz C Sonuç (Pilot Fix — GERÇEK Root Cause)

**Pilot pivot:** Faz B+ derin dalış hipotezi (fallback DAG sorunu) runtime'da **yanlış** çıktı.
Native postgres `kiro2` DB'de 125 topic + 106 prereq mevcuttu → fallback hiç tetiklenmiyordu.
Gerçek bug çok daha sinsi ve case convention kaynaklı.

### Root Cause Analysis

| Soru | Cevap |
|------|-------|
| Hata ne? | `curl /api/v1/learning-path/status` → 9 subject'te `prereq_blocked=false`. DAG prereq enforcement sessizce devre dışı. |
| Root cause? | `learning_path_orchestrator.py:206, 463` — `subject_id=subject.lower()`. DB `topic_hierarchy.subject_area` UPPERCASE (MATEMATIK=40, TURKCE=8...). `dag_engine.py:338` `get_subject_topics` exact case-sensitive match: `n.subject_id == subject_id`. lowercase → 0 eşleşme → `get_next_recommended_topic()` None → `prereq_blocked` **asla** True olmuyor. |
| Doğru tablo mu? | ✓ `topic_hierarchy` (125 row, 12 UPPERCASE subject_area) |
| Altyapı OK? | ✓ postgres 5434, redis, backend /health 200 |
| Fix scope? | 1+1 dosya. Orchestrator: 2 satır `.lower()` kaldır. DAGService: defansif `upper()` (Faz D genelleme) |
| Pattern ref | `.claude/rules/testing.md` Lesson 26 (Case Convention Tutarlılığı) |

### TDD Red → Green

- **Test:** `backend/tests/unit/test_learning_path_subject_case.py` (2 regression)
- **Red:** `AssertionError: DAG'a lowercase subject_id geçildi: ['biyoloji','cografya','edebiyat','fizik','kimya','matematik','sosyal','tarih','turkce']`
- **Fix:** `learning_path_orchestrator.py:206, 463` → `subject.lower()` → `subject`
- **Green:** 2/2 yeni + 6/6 cold-start + 47/47 dag = **55/55 PASS**

### Runtime Doğrulama

```bash
# Öncesi: UPPERCASE DB'de 40 topic ama orchestrator lowercase gönderiyordu → 0 eşleşme
# Sonrası: Her iki case de 40 topic (defansif upper)
GET /api/v1/dag/subjects/MATEMATIK/next → {"next_topic_id":"a6e8a0b8-..."}
GET /api/v1/dag/subjects/matematik/next → {"next_topic_id":"a6e8a0b8-..."}  # ← eskiden None
GET /api/v1/dag/topics?subject_id=MATEMATIK → 40 topics
```

**Öğrenci deneyim farkı:**
- **Öncesi:** Cold-start öğrencisi bile bir sonraki konuyu göremezdi (None). DAG prereq enforcement tamamen devre dışı — öğrenci herhangi bir konuya önkoşulsuz erişebilirdi.
- **Sonrası:** DAG topolojik sırayla uygun konuyu öneriyor. İleri konular (ör. `Üçgenler`) gerçek prereq kontrolüne tabi.

---

## Faz D Sonuç (Pattern Genellemesi)

**Grep tarama:**
```
grep -rn "subject.*\.lower\(\)" backend/app/
```

| Dosya | Satır | Context | Aksiyon |
|-------|-------|---------|---------|
| `learning_path_orchestrator.py` | 206, 463 | DAG lookup | ✅ Fix (kaldır) |
| `app/api/dag.py` | 76, 91 | URL path → DAG | ⚠️ DAGService seviyesinde defansif normalize kapsar |
| `cat_session.py` | 526, 761 | `_SUBJ_MAP` enum dict | ✓ Doğru (farklı context) |

**Batch fix stratejisi — kaynakta defansif normalize:**
- `dag_service.py:get_next_recommended_topic` → `subject_id.upper() if subject_id else subject_id`
- Rasyonel: Caller hatası ne olursa olsun DAG katmanı UPPERCASE'e normalize eder → bu bug sınıfı kapalı.
- Yan fayda: `dag.py` API endpoint'leri otomatik korunuyor.

**Root cause kategorisi:** `case-convention` (Lesson 26; Session 78 ile aynı kategori).

---

## Özet: Flow 12 (Learning Path) — Pilot Sonuç

| Metrik | Değer |
|--------|-------|
| Dosya değişim | 2 dosya |
| Satır değişim | ~8 satır (3 fix + 5 yorum) |
| Test eklenen | 2 regression |
| Test durumu | 55/55 PASS |
| Runtime | ✅ DAG 40 topic her case'de |
| Root cause kategorisi | `case-convention` (Lesson 26) |
| Faz A hipotez doğruluğu | ❌ 3/3 P0 phantom |
| Faz B+ derin dalış | ❌ Fallback DAG yoktu |
| Gerçek cause | DAG inspection scripti (30 sn) |

**Öğrenilenler:**
1. Statik analiz hipotezleri runtime doğrulaması olmadan güvenilir değil (3 hipotez yanlış).
2. DAG inspection scripti (`docker exec python` + DB bağlanarak) bug'ı 30 sn'de kesinleştirdi.
3. `testing.md` Lesson 26 bu session'da tekrar doğrulandı — memory pattern aktif fayda sağladı.
