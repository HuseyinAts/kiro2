# KIRO2 Kapsamli Baglanti Sagligi Raporu — 29 Mart 2026

## Context

6 paralel Opus agent ile tum codebase tarandi. Her agent bir kritik baglanti zincirini uctan uca dogruladi:

1. **Gamification Event Chain** — XP, badge, leaderboard, event service
2. **Learning Path Dual System** — v2 facade + Daily orchestrator + frontend
3. **Auth & Session Security** — endpoint auth, CSRF, DB pattern
4. **Algorithm Pipeline** — BKT -> IRT -> FSRS -> ZPD -> Blackboard
5. **Frontend-Backend API Contract** — parent, admin, chat, recommendation, LP mutations
6. **Dead Code & Orphan Router** — kayitsiz API, orchestrator stubs, main.py imports

**Son commit:** `5c50d35` | **Branch:** master | **Tarih:** 29 Mart 2026

---

## GENEL BAGLANTI SKORU: 3.8 / 10

> 28 Mart raporunda 47 bulgu ile 4.3/10 hesaplanmisti. Bu raporda 75 bulguya
> cikti (+60%), P0 guvenlik bulgusu artti (live_session 14 IDOR, main.py crash).
> Ozellikle gamification event chain'in tamamen kopuk olmasi ve 17 orphan
> router'in frontend'den hic cagrilmamasi skoru dusurdu.

| Baglanti Zinciri | Durum | Skor | Kritik Sorun |
|-------------------|-------|------|-------------|
| Frontend Auth -> Backend Auth | SAGLAM | 9/10 | — |
| Frontend Exam -> Backend Sinav | CALISIYOR | 7/10 | examService 1 yanlis path |
| Frontend LP -> Backend LP v2 (facade) | KOPUK | 3/10 | facade TODO, DB yok |
| Frontend LP -> Backend LP Daily | KISMEN | 6/10 | v2 field'lar frontend'de eksik |
| LP v2 <-> LP Daily | KOPUK | 0/10 | birbirinden tamamen habersiz |
| Frontend Gamification -> Backend + Event Chain | KIRIK | 2/10 | cift XP, badge/leaderboard otomasyon yok, 4 manager baglantisi kopuk |
| Frontend Reports -> Backend | KOPUK | 0/10 | prefix yanlis, tumu 404 |
| Frontend Recommendations -> Backend | KOPUK | 1/10 | mock fallback, gercek backend belirsiz |
| Frontend Admin -> Backend | KISMEN | 5/10 | bulk-upload yok, param uyumsuzluk |
| Frontend Parent -> Backend | KISMEN | 5/10 | 4 endpoint yok (PDF, bulk, approval) |
| Frontend Chat -> Backend | KISMEN | 6/10 | bionic-reading yok, import path belirsiz |
| record_answer Pipeline | CALISIYOR | 7/10 | FSRS reps/lapses bozuk |
| Blackboard -> Subscribers | KISMEN | 5/10 | tetikleniyor ama sync DB riski |
| Frontend Video -> Backend YouTube | SAGLAM | 9/10 | — |
| Frontend AI Chat -> Backend | SAGLAM | 8/10 | — |
| Backend -> Orchestrator | SADECE ROUTING | 1/10 | %94 dormant, graph TODO stub |
| main.py -> app/api/ | KIRIK | 2/10 | 5 orphan import (crash riski) |

**Skor hesaplama:** 17 baglanti zincirinin agirlikli ortalamasi. Auth (9) ve Video (9) yuksek;
LP v2<->Daily (0), Reports (0), Recommendations (1), Orchestrator (1) en dusuk.
Ortalama: (9+7+3+6+0+2+0+1+5+5+6+7+5+9+8+1+2) / 17 = **4.5 ham**, guvenlik cezasi (-0.7) ile **3.8/10**.

---

## BOLUM 1: BILESEN ENVANTERI

### Backend (532 dosya)

| Katman | Dosya Sayisi | Konum |
|--------|-------------|-------|
| API Router'lar | 133 | `backend/api/` |
| App API (LP/CAT/DAG) | 8 | `backend/app/api/` |
| Servisler | ~111 | `backend/services/` |
| App Servisleri | 11 | `backend/app/services/` |
| Modeller | 79 | `backend/models/` |
| Core | 177 | `backend/core/` |
| Agent'lar | 9 | `backend/agents/` |
| Algoritmalar | 7 | `backend/algorithms/` |
| Router Loader mapping | 197 | `backend/routers/loader.py` |

### Frontend (189 dosya)

| Katman | Dosya Sayisi | Konum |
|--------|-------------|-------|
| Sayfa Component'leri | 61 aktif + 44 deprecated | `frontend/src/pages/` |
| Custom Hook'lar | 53 (test dahil) | `frontend/src/hooks/` |
| Servisler | 28 aktif + 4 deprecated | `frontend/src/services/` |
| Store'lar (Zustand) | 5 | `frontend/src/store/` |
| Component Dizinleri | 42+ | `frontend/src/components/` |

### Orchestrator (40 modul)

| Katman | Dosya Sayisi | Konum | Aktif |
|--------|-------------|-------|-------|
| Core Moduller | 35 | `orchestrator/core/` | 2 aktif (%6) |
| Kok Dosyalar | 5 | `orchestrator/` | — |

---

## BOLUM 2: AKTIF BAGLANTI ZINCIRLERI (7 Ana Akis)

### Zincir 1: Sinav Akisi — BAGLI

```
Frontend: examService.ts -> POST /api/v1/osym-exam/create, /start, /save-answer, /complete
    |
Backend:  api/sinav.py -> core/osym_exam_engine.py -> models/question_bank.py (77,336 soru)
    |
          sinav.py save_answer -> services/bkt_service.py record_answer() [5-adim pipeline]
```

**Durum:** Tam bagli. Frontend credentials:'include', backend auth, DB read/write calisiyor.
**Sorun:** `examService.ts:590` `/api/v1/students/stats` — backend'de `/api/v1/student-dashboard` olmali.

### Zincir 2: Algoritma Pipeline (record_answer) — BAGLI

```
sinav.py save_answer()
  -> BKTService.record_answer() [bkt_service.py:176-468]
      [1] BKT Guncelleme (satir 211-268)
          -> BKTState DB upsert
          -> Baslangic p_T: STEM=0.10, Sozel=0.05
          -> Mastery threshold: p_L >= 0.80
      [2] IRT Theta Gecisi (satir 270-291)
          -> IRTService3PL.eap_theta() (varsa)
          -> Fallback: p_L -> theta linear bridge: (p_L - 0.5) * 8.0
          -> SE: max(0.3, 1 - p_L)
      [3] IRT Theta Persist (satir 293-337)
          -> _SUBJECT_ID_MAP (1-12, hardcoded)
          -> StudentAbility tablosu PostgreSQL UPSERT (idempotent)
      [4] FSRS State Persist (satir 339-409)
          -> FSRSCard DB read -> review_card() -> DB upsert
          -> SORUN: reps = card.step (0/1 proxy, gercek tekrar sayisi degil)
          -> SORUN: lapses = 0 (hardcoded, takip edilmiyor)
      [5] ZPD History (satir 411-433)
          -> ZPDHistory row insert: zone, p_learn, theta, scaffold_level
          -> Zone hesaplama: p_L bazli (theta degil)
      [6] Blackboard Publish (satir 435-451)
          -> Fire-and-forget event
          -> Event: new_p_L, theta, theta_se, zpd_zone, correct
```

**Durum:** 5 adim zincirlenmis, her biri try/except icinde. errors dict ile partial failure raporlama.

### Zincir 3: Learning Path — CIFT YOLLU, KISMEN BAGLI

**Yol A: LP v2 (facade pattern)**
```
Frontend: useLearningPath.ts + ModernLearningPathPage.tsx
    -> GET /api/v1/learning-path/my-profile, /completion/{id}
    -> PUT /api/v1/learning-path/progress/{sid}/{nodeId}
    -> POST /api/v1/learning-path/quiz/{id}/submit
    |
Backend: api/learning_path_v2.py -> agents/learning_path/facade.py
    -> SORUN: get_student_path() -> TODO: Load from database (satir 263)
    -> SORUN: _get_or_create_profile() -> TODO: Load from database (satir 552)
    -> Sonuc: Sadece in-memory cache, sunucu restart = veri kaybi
```

**Yol B: LP Daily (orchestrator katmani)**
```
Frontend: useStudentProfile.ts + DailyPlanPage.tsx
    -> GET /api/v1/learning-path/status, /today, /weekly
    |
Backend: app/api/learning_path_daily.py -> app/services/learning_path_orchestrator.py
    -> app/services/dag_service.py -> dag_engine.py (prereq grafigi)
    -> DB: StudentAbility theta + theta_se, FSRSCard due, BKTState mastery
    -> v2 field'lar: theta_se, prereq_blocked, prereq_topic, prereq_topic_name
```

**KOPUKLUK DETAYI:**

| Ozellik | Yol A (LP v2 facade) | Yol B (LP Daily) |
|---------|---------------------|-----------------|
| API prefix | `/api/v1/learning-path/` | `/api/v1/learning-path/` (ayni!) |
| Backend dosya | `api/learning_path_v2.py` | `app/api/learning_path_daily.py` |
| Servis | `agents/learning_path/facade.py` | `app/services/learning_path_orchestrator.py` |
| Theta kaynagi | YOK (facade'de hesaplanmiyor) | `StudentAbility` tablosu (DB) |
| ZPD kaynagi | YOK | mastery_pct threshold |
| DAG | YOK | `dag_service.py` onkosul grafigi |
| DB persist | YOK (TODO comment) | EVET (PostgreSQL) |
| Birbirine bagli mi? | **HAYIR** | **HAYIR** |

**Frontend Eksiklikleri (DailyPlanPage.tsx):**
- SubjectStatus interface'inde EKSIK: `theta_se`, `prereq_blocked`, `prereq_topic`, `prereq_topic_name`
- StudyBlock interface'inde EKSIK: `prereq_blocked`
- Backend bu field'lari donduruyor ama frontend kullanmiyor

### Zincir 4: Auth — BAGLI

```
Frontend: authService.ts -> POST /api/v1/auth/login/secure (credentials: 'include')
    | httpOnly cookie set
Backend: api/auth.py -> core/dependencies.py (JWT decode) -> models/database.py (User)
    | 401 -> apiClient.ts interceptor -> POST /refresh/secure -> retry
```

**Durum:** Tam bagli. 0 localStorage kalintisi, 57 dosya credentials:'include'.
**401 Retry:** apiClient.ts:64-80 — refresh token ile retry implementasyonu mevcut.

### Zincir 5: Gamification — KIRIK

```
Frontend: useGamification.ts (axios, withCredentials)
    -> GET/POST /api/v1/gamification/points, /level, /badges, /leaderboard
    |
Backend: api/gamification_api.py -> core/gamification/*.py (4 manager)
    -> services/learning_event_service.py -> models (UserAchievement, XPTransaction)
    |
    SORUNLAR:
    1. Quiz complete -> frontend XP award + backend XP award = CIFT XP
    2. on_quiz_completed() badge check YAPMIYOR
    3. on_quiz_completed() leaderboard update YAPMIYOR
    4. /points/award self-service (query param'dan points)
```

### Zincir 6: YouTube/Video — BAGLI

```
Frontend: VideoLoadingManager.ts -> POST /api/v1/learning-path/search-resources
    |
Backend: api/youtube_routes.py -> services/youtube/* (12 modul)
    -> core/youtube_channels.py (17 kanal, 27 alias)
```

**Durum:** Bagli. YouTube API key aktif, difficulty-aware cache.

### Zincir 7: AI Chat — BAGLI

```
Frontend: chatService.ts -> POST /api/v1/enhanced-chat/stream (SSE)
    |
Backend: api/ai_chat_routes.py -> services/ai_chat_service.py -> core/llm_service.py
    -> models/ai_chat.py (ChatSession, ChatMessage)
```

**Durum:** Bagli. Konu-bazli prompt, Sokratik mod, dosya eki destegi.
**Sorun:** `applyBionicReading()` endpoint `/api/v1/enhanced-chat/bionic-reading` backend'de BULUNAMADI.

---

## BOLUM 3: P0 KRITIK BULGULAR (14 bulgu)

### 3.1 Gamification Cift XP Yazimi
**Dosya:** `frontend/src/pages/ModernLearningPathPage.tsx:321` + `backend/services/learning_event_service.py:80`

Quiz tamamlandiginda:
- Frontend `fetchWithRetry('/api/v1/gamification/points/award?points=...')` cagrisi yapiyor (satir 321)
- Ayni anda backend `LearningEventService.on_quiz_completed()` ile de `GamificationDBService.award_xp()` cagriliyor (satir 80)
- **Sonuc:** Her quiz'de 2X puan yaziliyor

**Fix:** Frontend quiz complete'den XP award cagrisini kaldir (backend zaten yapiyor).

### 3.2 Badge Otomasyon Zinciri KOPUK
**Dosya:** `backend/core/gamification/badge_manager.py:284`

`check_and_award_badges()` metodu mevcut ama HICBIR YERDEN otomatik cagrilmiyor. `on_quiz_completed()` (satir 25-103) sadece BKT + XP + Streak yapiyor; badge check YOK.

**Fix:** `LearningEventService.on_quiz_completed()` sonuna `BadgeManager.check_and_award_badges()` cagrisi ekle.

### 3.3 Leaderboard Redis ZSET Asla Guncellenmiyor
**Dosya:** `backend/core/gamification/leaderboard_manager.py:61`

`update_score()` mevcut ama `on_quiz_completed()`'den cagrilmiyor. XP verildikten sonra Redis ZSET guncellenmez. Leaderboard hep bos veya eski.

**Fix:** `GamificationDBService.award_xp()` sonuna `LeaderboardManager.update_score()` ekle.

### 3.4 Self-Service XP Istismar
**Dosya:** `backend/api/gamification_api.py:160-166`

`/points/award` endpoint'i kullanicidan `points` Query parameter alip direkt XP veriyor. Auth var ama miktar siniri YOK. Kullanici `?points=999999` gonderebilir.

**Fix:** Backend'de max XP limiti + event-based XP verme (query param degil).

### 3.5 LP v2 Facade get_student_path() DAIMA None Doner
**Dosya:** `backend/agents/learning_path/facade.py:263`

`# TODO: Load from database` yorumu var, DB sorgusu YOK. Sadece in-memory `_paths_cache` dict'ine bakiyor. Sunucu restart edilince tum path'ler kaybolur.

**Fix:** LearningPath DB tablosundan student_id ile sorgu ekle.

### 3.6 LP v2 Facade _get_or_create_profile() DAIMA Default Profil
**Dosya:** `backend/agents/learning_path/facade.py:552`

`# TODO: Load from database` yorumu var. LearningPathStudentProfile DB tablosu mevcut ama facade OKUMAZ. Her zaman `knowledge_level=INTERMEDIATE`, `name=""`, `grade="12"` ile calisir.

**Fix:** LearningPathStudentProfile DB sorgusu ekle.

### 3.7 advancedReportsService 7 Endpoint Prefix Eksik
**Dosya:** `frontend/src/services/advancedReportsService.ts:182-260`

Tum 7 URL `/reports/...` formatinda:
- `/reports/exam/{sinavId}/advanced` (satir 182)
- `/reports/exam/{sinavId}/irt-analysis` (satir 195)
- `/reports/exam/{sinavId}/zpd-recommendations` (satir 208)
- `/reports/exam/{sinavId}/learning-style-analysis` (satir 221)
- `/reports/exam/{sinavId}/osym-ets-comparison` (satir 234)
- `/reports/exam/{sinavId}/generate-pdf` (satir 247)
- `/reports/exam/{sinavId}/comparative` (satir 260)

Backend prefix `/api/v1/reports`. VersionRedirectMiddleware'da `/reports` kurali YOK. **Tumu 404.**

**Fix:** Tum URL'lere `/api/v1/` prefix ekle.

### 3.8 main.py 5 Orphan Import — Startup Crash Riski
**Dosya:** `backend/main.py:85-109`

5 router import'u basarisiz olacak (dosyalar mevcut degil):
```
from app.api.calibration_api import router  # YOK
from app.api.cat import router              # YOK
from app.api.dag import router              # YOK
from app.api.estimator import router        # YOK
from app.api.placement import router        # YOK
```

Sadece `app/api/fsrs.py` mevcut.

**Impact:** main.py uzerinden baslatilirsa ModuleNotFoundError ile crash.
**Not:** Production'da `core/application.py` + `routers/loader.py` kullanildigi icin simdilik calisir ama main.py tehlikeli.

**Fix:** main.py'deki olmayan import'lari temizle veya dosyayi deprecate et.

### 3.9 osym_questions_api 5 Endpoint Tamamen Auth'suz
**Dosya:** `backend/api/osym_questions_api.py:38-342`

| Endpoint | Satir | Auth |
|----------|-------|------|
| GET `/statistics` | 38 | YOK |
| GET `/subjects` | 97 | YOK |
| GET `/random-questions` | 142 | YOK |
| GET `/practice-exam` | 241 | YOK |
| GET `/questions` | 342 | YOK |

Ayrica `asyncpg.connect()` ile kendi DB baglantisini aciyor (satir 22-32) — SQLAlchemy ORM parametrize sorgu korumasi yok, connection leak riski.

**Fix:** 5 endpoint'e `Depends(get_current_user)` ekle. asyncpg yerine SQLAlchemy session kullan.

### 3.10 litellm_chat Auth Fallback _noop_auth
**Dosya:** `backend/api/litellm_chat.py:89-104`

`core.dependencies` import basarisiz olursa `_noop_auth` fallback'e duser — LLM chat endpoint'leri tamamen auth'suz calisiyor.

**Fix:** `_noop_auth` fallback'i kaldir, import hatasinda endpoint'i devre disi birak.

### 3.11 live_session_routes 14 Endpoint Auth'suz + IDOR
**Dosya:** `backend/api/live_session_routes.py`

21 endpoint'ten sadece 7'si auth gerektiriyor (create, start, end, join, leave, screen-share/start, my-sessions). 14 endpoint IDOR riski tasiyor:

| Endpoint | Satir | Auth |
|----------|-------|------|
| GET `/{session_id}` | 133 | YOK |
| POST `/screen-share/{id}/stop` | 245 | YOK |
| POST `/{session_id}/whiteboard` | 265 | YOK |
| GET `/whiteboard/{id}` | 285 | YOK |
| POST `/whiteboard/{id}/stroke` | 304 | YOK |
| POST `/whiteboard/{id}/equation` | 334 | YOK |
| GET `/whiteboard/{id}/page/{page}` | 363 | YOK |
| POST `/whiteboard/{id}/page` | 374 | YOK |
| DELETE `/whiteboard/stroke/{id}` | 389 | YOK |
| POST `/{session_id}/recording/start` | 406 | YOK |
| POST `/recording/{id}/stop` | 418 | YOK |
| GET `/{session_id}/recordings` | 430 | YOK |
| POST `/{session_id}/chat` | 457 | YOK |
| GET `/{session_id}/chat` | 478 | YOK |

**Fix:** Tum whiteboard/recording/chat endpoint'lere `Depends(get_current_user)` + ownership check ekle.

### 3.12 _on_mastery_event Sync DB Async Context Icinde
**Dosya:** `backend/services/blackboard_service.py:141-154`

```python
from core.database import get_db       # sync generator (satir 141)
db_gen = get_db()                       # (satir 144)
db_session = next(db_gen)               # blocking call async icinde! (satir 145)
```

Async event loop icinde sync blocking DB call = deadlock riski.

**Fix:** `get_db_session_context()` (async context manager) kullan.

### 3.13 populate_question_bank.py Yanlis Tablo
**Dosya:** `backend/scripts/populate_question_bank.py:17`

`from models.database import ... Question` — legacy `questions` (BOS) tablosunu import ediyor.
Satir 150'de `question = Question(...)` — yanlis tabloya INSERT.

**Fix:** `from models.question_bank import QuestionBankItem as Question` kullan.

### 3.14 soru_bankasi_service is_active Filtresi YOK
**Dosya:** `backend/services/soru_bankasi_service.py:289-299`

`soru_getir()` fonksiyonunda `is_active` filtresi yok. Devre disi birakilmis (is_active=FALSE) soru dondurebilir.

**Fix:** `Question.is_active == True` filtresi ekle.

---

## BOLUM 4: P1 ONEMLI BULGULAR (31 bulgu)

### P0'dan Tasindi (3)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 15 | CSRF `/api/v1/` tamamen muaf (Phase 1 tasarim karari) | `application.py:204-212` | Frontend X-CSRF-Token gonderdikten sonra muafiyeti kaldir |
| 16 | Parent service 4 endpoint backend'de YOK (PDF, bulk, approval) | `parentService.ts:200-263` | Frontend 404 alir ama runtime crash degil |
| 17 | Chat bionic-reading endpoint YOK | `chatService.ts:393` | Backend'de olustur veya frontend'den kaldir |

### Gamification (4)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 18 | Level formulu tutarsiz | `gamification_api.py:619` vs `experience_manager.py:38` | API: `lv*100*1.5^lv`, Manager: `100*1.5^(lv-1)` |
| 19 | `GamificationDBService.award_xp()` User.level GUNCELLEMEZ | `learning_event_service.py:255` | XP verilir ama level artmaz |
| 20 | Response shape: `response.data.total_points` vs nesting | `useGamification.ts:88` | Frontend/backend response format dogrulandi ama diger hook'lar farkli format bekleyebilir |
| 21 | Leaderboard period filtresi calismaz (hep all-time) | `gamification_api.py:470` | Period param islenmez |

### Learning Path (6)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 22 | Iki LP sistemi ayni prefix, birbirinden habersiz | `learning_path_v2.py` + `learning_path_daily.py` | Ayni `/api/v1/learning-path/` prefix |
| 23 | `user_theta` tablosu ORM modeli YOK — raw SQL | `learning_path_orchestrator.py:503` | — |
| 24 | `yks_exam_goals` tablosu ORM modeli YOK | `learning_path_daily.py:106` | — |
| 25 | `topic_prerequisites` tablosu ORM modeli YOK | `dag_service.py:109` | — |
| 26 | DailyPlanPage v2 field'lari (theta_se, prereq_blocked) eksik | `DailyPlanPage.tsx:34-43` | Backend donduruyor ama interface'de tanimli degil |
| 27 | Quiz submit body format uyumsuz | `useLearningPathMutations.ts:116` | Frontend body vs backend schema dogrulanmali |

### Auth & Security (3)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 28 | department/university/preference 3 router tumuyle auth'suz | `department_info_routes.py` + 2 diger | Create dahil auth yok |
| 29 | CSRF Phase 2 henuz uygulanmadi | `application.py:212` | Frontend X-CSRF-Token bekliyor |
| 30 | JWT secret env var zorunlu degil (default fallback var) | Onceki audit bulgusu | — |

### API Contract (5)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 31 | adminService bulk-upload endpoint YOK | `adminService.ts:281` | Multipart form handling eksik |
| 32 | adminService toggleUserStatus param mismatch | `adminService.ts:208` | PATCH body vs query param |
| 33 | examService `/students/stats` yanlis path | `examService.ts:590` | Backend'de `/student-dashboard` |
| 34 | chatService import path belirsiz | `chatService.ts:1-5` | `from '../api'` -> tanimli degil |
| 35 | recommendationService tum endpoint'ler mock fallback | `recommendationService.ts:33-44` | Backend basarisiz olursa mock data |

### Algorithm Pipeline (5)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 36 | FSRS reps = card.step proxy (0 veya 1) | `fsrs_v6_service.py:132` | Gercek tekrar sayisi takip edilmiyor |
| 37 | FSRS lapses = 0 hardcoded | `fsrs_v6_service.py:133` | Hatali tekrar sayisi takip edilmiyor |
| 38 | ZPD zone p_L'den hesaplaniyor, theta yok sayiliyor | `bkt_service.py:412` | theta daha guvenilir olabilir |
| 39 | Subject ID map hardcoded (1-12) — FK yok | `bkt_service.py:297-310` | StudentAbility.subject_id orphan riski |
| 40 | _analyze_performance() is_active filtresi YOK | `osym_exam_engine.py:1340` | Devre disi soru matching hatalari |

### DB Integrity (5)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 41 | soru_bankasi_service NULL OR kosulu | `soru_bankasi_service.py:349,441` | is_active=NULL aktif sayiliyor |
| 42 | 3 test dosyasi legacy Question import kullaniyor | Cesitli test dosyalari | question_bank olmali |
| 43 | chatService, socialService raw fetch 401 retry YOK | 5+ frontend servis dosyasi | apiClient interceptor kullanilmali |
| 44 | StudentAbility FK eksik | `gamification.py:295-308` | subject_id FK yok, subjects tablosu yok |
| 45 | ZPDHistory zone string, enum olmali | `gamification.py:311-326` | Validation yok |

**P1 Toplam:** 3 (P0'dan tasindi) + 4 + 6 + 3 + 5 + 5 + 5 = **31 bulgu** (#15-45)

---

## BOLUM 5: P2 TEKNIK BORC (30 bulgu)

### Orphan Backend Router'lar (17 router dosyasi / 14 prefix, ~80+ endpoint)

Frontend'den hic cagrilmayan ama backend'de KAYITLI router'lar:

| Router Prefix | Dosya | Loader Kaydi |
|---------------|-------|-------------|
| `/api/v1/adhd-support/*` (3 router) | adhd_support_api, adhd_focus_mode_api, adhd_task_management_api | loader.py:117 |
| `/api/v1/coaching` | coaching_api.py | loader.py:176 |
| `/api/v1/dina` | dina_api.py | loader.py:186 |
| `/api/v1/diary` | diary_api.py | loader.py:172 |
| `/api/v1/error-clusters` | error_cluster_api.py | loader.py:188 |
| `/api/v1/kvkk/*` (2 router) | kvkk_consent_api, kvkk_privacy_api | loader.py:27-28 |
| `/api/v1/mnemonics` | mnemonic_api.py | loader.py:189 |
| `/api/v1/productive-failure` | productive_failure_api.py | loader.py:187 |
| `/api/v1/study-plan` | study_planner_api.py | loader.py:174 |
| `/api/v1/mastery-confidence` | mastery_confidence_api.py | loader.py:184 |
| `/api/v1/knowledge-map` | knowledge_graph_api.py | loader.py:182 |
| `/api/v1/leagues` | league_api.py | loader.py:175 |
| `/api/v1/daily-quests` | daily_quest_api.py | loader.py:85 |
| `/api/v1/oba-seferleri` | oba_seferleri_api.py | loader.py:153 |

**Not:** Tumu loader.py'de kayitli ve calisir durumda. Sorun: Frontend'den HICBIRI cagrilmiyor.
**Bulgu numaralari:** #46 (toplu — 17 dosya, 14 prefix)

### Orchestrator Dormant Modulleri (#47-52)

| # | Bilesen | Durum | Detay |
|---|---------|-------|-------|
| 47 | `graph.py` 4 node TODO stub | DORMANT | _plan_node, _implement_node, _review_node, _fix_node LLM entegrasyonu yok |
| 48 | `policy_engine.py` (45 politika) | AKTIF | Tum validator'lar gercek implementasyon (bilgi amacli) |
| 49 | `agents.py` (7 agent) | DORMANT | graph.py icinden bile cagirilmiyor |
| 50 | `llm_gateway.py` | DORMANT | — |
| 51 | `memory.py` | DORMANT | — |
| 52 | 28 diger core modul | DORMANT | Backend'den 0 import |

### Diger P2 Bulgular (#53-59)

| # | Sorun | Dosya | Detay |
|---|-------|-------|-------|
| 53 | Facade in-memory cache multi-worker'da tutarsiz | `facade.py:141` | Gunicorn workers arasi paylasim yok |
| 54 | FSRSReview audit trail olusmuyor (tablo bos) | `bkt_service.py:339-409` | Review kaydi yazilmiyor |
| 55 | FK constraint eksiklikleri (BKTState, ZPDHistory topic_id) | `gamification.py:44,311` | String FK, TopicHierarchy ref yok |
| 56 | Global mutable `_ALGO_ERRORS` counter thread-safe degil | `bkt_service.py:20` | — |
| 57 | `get_user_mastery()` sonucu kullanilmiyor | `learning_path_orchestrator.py:170` | Dead code |
| 58 | questions_api "REMOVED" ama loader mapping'de | `loader.py:49` | Deprecated isareti var ama kayit duruyor |
| 59 | 3 kayitsiz API dosyasi artik mevcut degil | question_pipeline_api, response_validation_api, websocket_connection_manager | Onceki rapordan silinmis |

---

## BOLUM 6: KOPUK / DORMANT BAGLANTILAR

### 6A. Orchestrator — %94 DORMANT

35 core modulden sadece 2'si backend'le iletisimde:
- `routing.py` RoutingEngine: `orchestrator_api.py /dispatch` cagrisi — AKTIF
- `__init__._GRAPH_AVAILABLE` flag: Status check — AKTIF
- Geri kalan 33 modul: Backend'den 0 import

### 6B. Blackboard — AKTIF AMA MINIMAL

```
record_answer() -> BlackboardService.publish() -> DomainBlackboard -> _notify_subscribers()
    -> _on_mastery_event():
        - Mastery trigger: zpd_zone == "MASTERED" AND theta_se < 0.5
        - LP facade cache clear
        - XP award: 50 XP per mastery
        - SORUN: sync get_db() async context'te (deadlock riski)
```

### 6C. LP Cift Yol Kopuklugu

Detay Bolum 2 Zincir 3'te.

### 6D. Router'da Deprecated Kayit

`questions_api` "REMOVED - deprecated" olarak isaretlenmis ama ROUTER_MAPPING'de hala var (loader.py:49).

---

## BOLUM 7: KONSENSUS (2+ Agent Ayni Sorunu Isaret Etti)

| Sorun | Agent'lar | Guvenilirlik |
|-------|-----------|-------------|
| Gamification cift XP | Gamification + Frontend-Backend Contract | YUKSEK |
| _on_mastery_event sync DB | Algorithm Pipeline + Auth Security | YUKSEK |
| LP facade TODO'lar (DB yok) | LP Dual System + Frontend-Backend Contract | YUKSEK |
| osym_questions_api auth'suz | Auth Security + Dead Code | YUKSEK |
| is_active filtresi eksik (soru_bankasi + exam engine) | Algorithm Pipeline + Auth Security | YUKSEK |
| advancedReportsService URL prefix | LP Dual System + Frontend-Backend Contract | YUKSEK |
| FSRS reps/lapses bozuk | Algorithm Pipeline | ORTA |
| 16 orphan router | Dead Code + Frontend-Backend Contract | ORTA |
| main.py 5 orphan import | Dead Code | ORTA |
| DailyPlanPage v2 field eksik | LP Dual System | ORTA |

---

## BOLUM 8: ONERILEN AKSIYON PLANI

### Faz A: Acil Fix (P0 — ayni gun, ~4 saat)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| A1 | Frontend quiz XP cagrisini kaldir (cift XP fix) | ModernLearningPathPage.tsx:321 | 15dk |
| A2 | advancedReportsService 7 URL `/api/v1/` prefix ekle | advancedReportsService.ts:182-260 | 15dk |
| A3 | main.py 5 orphan import temizle | main.py:85-109 | 10dk |
| A4 | _on_mastery_event async DB migration | blackboard_service.py:141-154 | 30dk |
| A5 | populate_question_bank.py QuestionBankItem import | populate_question_bank.py:17 | 10dk |
| A6 | soru_bankasi_service.soru_getir() is_active filtresi | soru_bankasi_service.py:289 | 15dk |
| A7 | _analyze_performance() is_active filtresi | osym_exam_engine.py:1340 | 15dk |

### Faz B: Gamification Wiring (P0 — 1-2 gun)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| B1 | Badge check otomasyonu: on_quiz_completed() sonuna ekle | learning_event_service.py | 1s |
| B2 | Leaderboard update: award_xp() sonuna ekle | learning_event_service.py | 1s |
| B3 | Level formulu tekillestir | gamification_api.py + experience_manager.py | 30dk |
| B4 | Self-service XP istismar fix (max limit + event-based) | gamification_api.py:160 | 1s |

### Faz C: Auth Enforcement (P0-P1 — 1-2 gun)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| C1 | osym_questions_api 5 endpoint auth + asyncpg->SQLAlchemy | osym_questions_api.py | 2s |
| C2 | litellm_chat _noop_auth kaldir | litellm_chat.py:89-104 | 30dk |
| C3 | live_session_routes 14 endpoint auth + IDOR fix | live_session_routes.py | 2s |
| C4 | CSRF Phase 2 planla (frontend X-CSRF-Token) | application.py + frontend | 2s |

### Faz D: LP Facade DB Baglantisi (P0-P1 — 2-3 gun)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| D1 | facade get_student_path() DB sorgusu | facade.py:263 | 2s |
| D2 | facade _get_or_create_profile() DB sorgusu | facade.py:552 | 2s |
| D3 | DailyPlanPage v2 field'lari interface + render | DailyPlanPage.tsx:34-43 | 1s |
| D4 | LP v2 ve Daily arasinda theta paylasimi | facade.py + orchestrator.py | 3s |

### Faz E: Algorithm Pipeline Iyilestirme (P1 — 3-5 gun)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| E1 | FSRS reps proper tracking (step proxy kaldir) | fsrs_v6_service.py:132 | 2s |
| E2 | FSRS lapses tracking (hardcoded 0 kaldir) | fsrs_v6_service.py:133 | 1s |
| E3 | StudentAbility FK + subjects table olustur | gamification.py:295-308 | 2s |
| E4 | ZPD zone hesaplamasina theta ekleme | bkt_service.py:412 | 1s |

### Faz F: API Contract Temizligi (P1-P2 — 2-3 gun)

| # | Aksiyon | Dosya | Tahmini |
|---|---------|-------|---------|
| F1 | Parent 4 eksik endpoint olustur veya frontend kaldir | parentService.ts + parent.py | 2s |
| F2 | Chat bionic-reading endpoint | chatService.ts:393 + ai_chat_routes.py | 1s |
| F3 | Admin bulk-upload multipart endpoint | adminService.ts:281 + admin.py | 2s |
| F4 | examService yanlis path duzeltme | examService.ts:590 | 15dk |

---

## BOLUM 9: BAGLANTI MATRISI OZET

| Baglanti | Durum | Notlar |
|----------|-------|--------|
| Frontend Auth -> Backend Auth | BAGLI | 57 dosya credentials:'include', 401 retry var |
| Frontend Exam -> Backend Sinav | BAGLI | 1 path uyumsuzlugu |
| Frontend LP -> Backend LP v2 | KISMEN BAGLI | Facade TODO, DB yok |
| Frontend LP -> Backend LP Daily | KISMEN BAGLI | v2 field render eksik |
| LP v2 <-> LP Daily | KOPUK | Birbirinden habersiz |
| Frontend Gamification -> Backend | KIRIK | Cift XP, otomasyon kopuk |
| Frontend Reports -> Backend | KOPUK | Tum URL'ler 404 |
| Frontend Recommendations -> Backend | KOPUK | Mock fallback |
| Frontend Admin -> Backend | KISMEN | bulk-upload eksik |
| Frontend Parent -> Backend | KISMEN | 4 endpoint eksik |
| Frontend Chat -> Backend | KISMEN | bionic-reading eksik |
| Frontend Video -> Backend YouTube | BAGLI | 12 modul pipeline |
| Frontend AI Chat -> Backend | BAGLI | SSE stream |
| Backend record_answer Pipeline | BAGLI | FSRS reps/lapses bozuk |
| Blackboard -> Subscriber | AKTIF AMA RISKLI | Sync DB async icinde |
| Backend -> Orchestrator | SADECE ROUTING | %94 dormant |
| Orchestrator Graph -> LLM | DORMANT | 4 TODO stub node |
| Redis Pub/Sub | MINIMAL | Sadece leaderboard ZSET (guncellenmiyor) |
| main.py Startup | KIRIK | 5 import crash riski |

---

## BOLUM 10: METODOLOJI

- **6 Opus agent** paralel calistirildi (toplam ~1200s agent suresi)
- Her agent 1 baglanti zincirini uctan uca dogruladi:
  1. Gamification Event Chain — XP, badge, leaderboard akisi
  2. Learning Path Dual System — v2 facade + Daily orchestrator + frontend
  3. Auth & Session Security — endpoint auth, CSRF, DB pattern
  4. Algorithm Pipeline — BKT -> IRT -> FSRS -> ZPD -> Blackboard
  5. Frontend-Backend API Contract — parent, admin, chat, recommendation
  6. Dead Code & Orphan Router — kayitsiz API, orchestrator stubs
- Toplam ~400+ dosya taranarak Read/Grep ile kod okundu
- Severity: P0=runtime hata/veri kaybi/guvenlik, P1=yanlis davranis, P2=teknik borc
- Konsensus: 2+ agent'in ayni sorunu isaret etmesi yuksek guvenilirlik gostergesi
- Toplam bulgu: **75** (14 P0 + 31 P1 + 30 P2)
- Numaralandirma: #1-14 (P0), #15-45 (P1), #46-59 (P2, orphan router'lar #46 altinda gruplanmis)

---

## BOLUM 11: ONCEKI RAPORLARLA KARSILASTIRMA

| Metrik | 28 Mart Rapor 1 (Envanter) | 28 Mart Rapor 2 (Derin Audit) | 29 Mart (Bu Rapor) |
|--------|---------------------------|------------------------------|-------------------|
| Agent sayisi | 3 | 6 | 6 |
| Taranan dosya | ~761 | 284 | ~400+ |
| Toplam bulgu | Envanter odakli | 47 | 75 |
| P0 bulgu | — | 12 | 14 |
| P1 bulgu | — | 30 | 31 |
| P2 bulgu | — | 22 | 30 |
| Yeni bulgular | — | — | main.py crash, parent 4 EP, admin bulk, live_session 14 IDOR, FSRS detay, DailyPlanPage v2 |
| Genel skor | — | 4.3/10 | 3.8/10 (daha fazla bulgu + guvenlik sorunlari) |

### Yeni Bulgular (Bu Raporda Ilk Kez)

1. **main.py 5 orphan import** — startup crash riski (3.8)
2. **live_session_routes 14 endpoint IDOR** — onceki raporda 7 endpoint denilmisti, aslinda 14 (3.11)
3. **Parent service 4 eksik endpoint** — PDF, bulk notify, approval status (3.15)
4. **Chat bionic-reading endpoint YOK** — chatService.ts:393 (3.16)
5. **DailyPlanPage v2 field eksikligi** — theta_se, prereq_blocked, prereq_topic (Bolum 4 #26)
6. **FSRS reps/lapses detayli analiz** — step proxy + hardcoded 0 (Bolum 4 #36-37)
7. **Admin bulk-upload endpoint YOK** — multipart form handling (Bolum 4 #31)

---

*Rapor Sonu — 29 Mart 2026*
*Yazar: Claude Opus 4.6 (6 paralel agent ile)*
*Toplam: 75 bulgu (14 P0 + 31 P1 + 30 P2) | Skor: 3.8/10*
*Son commit: `5c50d35` | Branch: master*
