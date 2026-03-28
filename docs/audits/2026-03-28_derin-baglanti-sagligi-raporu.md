# KIRO2 Derin Baglanti Sagligi Raporu — 28 Mart 2026

## Context

6 paralel Opus agent ile 284 dosya tarandi. Her agent bir kritik baglanti zincirini uctan uca dogruladi:
1. Algorithm Pipeline (BKT->IRT->FSRS->ZPD->Blackboard)
2. Learning Path Dual System (v2 facade + Daily orchestrator)
3. Auth & Session Flow
4. Frontend-Backend API Contract
5. Gamification Event Chain
6. DB Model & Data Integrity

**Son commit:** `be65c75` | **Branch:** master

---

## GENEL BAGLANTI SKORU: 4.3 / 10

| Baglanti | Durum | Skor |
|----------|-------|------|
| Frontend Auth -> Backend Auth | SAGLAM | 9/10 |
| Frontend Exam -> Backend Sinav | KISMEN | 6/10 -- 3 endpoint 404 |
| Frontend LP -> Backend LP v2 | KOPUK | 3/10 -- facade TODO, DB yok |
| Frontend LP -> Backend LP Daily | KISMEN | 7/10 -- calisiyor ama frontend field eksik |
| LP v2 <-> LP Daily | KOPUK | 0/10 -- birbirinden tamamen habersiz |
| Frontend Gamification -> Backend | KIRIK | 2/10 -- 6 hayalet EP, 4 response shape uyumsuz, cift XP |
| Frontend Reports -> Backend | KOPUK | 0/10 -- prefix yanlis, tumu 404 |
| Frontend Recommendations -> Backend | KOPUK | 1/10 -- URL pattern uyumsuz |
| Frontend Admin -> Backend | KISMEN | 4/10 -- 10+ endpoint yok |
| Frontend Parent -> Backend | KISMEN | 5/10 -- 4 endpoint yok |
| record_answer Pipeline | CALISIYOR | 7/10 -- veri akiyor ama FSRS reps/lapses bozuk |
| Blackboard -> Subscribers | KISMEN | 5/10 -- tetikleniyor ama sync DB riski |
| Gamification Event Chain | KOPUK | 2/10 -- badge/leaderboard otomasyon yok |
| Frontend Video -> Backend YouTube | SAGLAM | 9/10 |
| Frontend AI Chat -> Backend | SAGLAM | 8/10 |

---

## BOLUM 1: P0 KRITIK (Hemen Fix — 12 bulgu)

### 1.1 Gamification Cift XP Yazimi
**Dosya:** `frontend/src/pages/ModernLearningPathPage.tsx:321` + `backend/services/learning_event_service.py:80`

Quiz tamamlandiginda frontend `POST /gamification/points/award` cagrisi yapiyor. Ayni anda backend `LearningEventService.on_quiz_completed()` ile de XP veriyor. Sonuc: her quiz'de 2X puan.

**Fix:** Frontend quiz complete'den XP award cagrisini kaldir (backend zaten yapiyor).

### 1.2 Gamification 6 Hayalet Endpoint
**Dosya:** `frontend/src/hooks/useGamification.ts:170,182,239,249,290,355`

Frontend cagrilan ama backend'de OLMAYAN endpoint'ler:
- `GET /level/milestones` -- YOK
- `GET /level/leaderboard` -- YOK
- `GET /badges/progress` -- YOK
- `POST /badges/{badgeId}/award` -- YOK
- `GET /leaderboard/{type}` -- URL format uyumsuz (path param vs query param)
- `GET /stats` -- YOK

**Fix:** Backend'de eksik endpoint'leri olustur veya frontend cagrilarini kaldir.

### 1.3 Badge Otomasyon Zinciri KOPUK
**Dosya:** `backend/core/gamification/badge_manager.py:284`

`check_and_award_badges()` metodu mevcut ama HICBIR YERDEN cagrilmiyor. Ne `on_quiz_completed()` ne de `on_exam_completed()` badge check yapiyor.

**Fix:** `LearningEventService.on_quiz_completed()` sonuna `BadgeManager.check_and_award_badges()` cagrisi ekle.

### 1.4 Leaderboard Redis ZSET Asla Guncellenmiyor
**Dosya:** `backend/core/gamification/leaderboard_manager.py:61`

`update_score()` mevcut ama hicbir yerden cagrilmiyor. XP verildikten sonra Redis ZSET guncellenmez. Leaderboard hep bos.

**Fix:** `GamificationDBService.award_xp()` sonuna `LeaderboardManager.update_score()` ekle.

### 1.5 LP v2 Facade get_student_path() DAIMA None Doner
**Dosya:** `backend/agents/learning_path/facade.py:249-264`

`# TODO: Load from database` yorumu var, DB sorgusu YOK. Sadece in-memory `_paths_cache` dict'ine bakiyor. Sunucu restart edilince tum path'ler kaybolur.

**Fix:** LearningPath DB tablosundan student_id ile sorgu ekle.

### 1.6 LP v2 Facade _get_or_create_profile() DAIMA Default Profil
**Dosya:** `backend/agents/learning_path/facade.py:543-568`

`# TODO: Load from database` yorumu var. LearningPathStudentProfile DB tablosu mevcut ama facade OKUMAZ. Her zaman `knowledge_level=INTERMEDIATE`, `name=""`, `grade="12"` ile calisir.

**Fix:** LearningPathStudentProfile DB sorgusu ekle.

### 1.7 advancedReportsService 7 Endpoint Prefix Eksik
**Dosya:** `frontend/src/services/advancedReportsService.ts:182-260`

Tum 7 URL `/reports/...` formatinda. Backend prefix `/api/v1/reports`. VersionRedirectMiddleware'da `/reports` kurali YOK. Tumu 404.

**Fix:** Tum URL'lere `/api/v1/` prefix ekle.

### 1.8 examService 3 Endpoint Yanlis Path
**Dosya:** `frontend/src/services/examService.ts:590,614,636`

- `/api/v1/sinav/history` -- Backend'de `/api/v1/osym-exam/my-exams`
- `/api/v1/sinav/results` -- Backend'de yok
- `/api/v1/students/stats` -- Backend'de `/api/v1/student-dashboard`

**Fix:** Dogru endpoint path'lerine yonlendir.

### 1.9 osym_questions_api 5 Endpoint Tamamen Auth'suz
**Dosya:** `backend/api/osym_questions_api.py:37-341`

`/statistics`, `/subjects`, `/random-questions`, `/practice-exam`, `/questions` -- hepsi kimlik dogrulamasi olmadan soru bankasina erisim sagliyor. Ayrica `asyncpg.connect()` ile kendi DB baglantisini aciyor (connection leak riski).

**Fix:** 5 endpoint'e `Depends(get_current_user)` ekle. asyncpg yerine SQLAlchemy session kullan.

### 1.10 litellm_chat Auth Fallback _noop_auth
**Dosya:** `backend/api/litellm_chat.py:96-104`

`core.dependencies` import basarisiz olursa LLM chat endpoint'leri tamamen auth'suz calisiyor. Genel `Exception` yakalanip noop'a dusuyor.

**Fix:** `_noop_auth` fallback'i kaldir, import hatasinda endpoint'i devre disi birak.

### 1.11 _on_mastery_event Sync DB Async Context Icinde
**Dosya:** `backend/services/blackboard_service.py:144-156`

`get_db()` (sync generator) + `ExperienceManager` (sync Session) async event loop icinde kullaniliyor. Event loop bloke olur, `greenlet_spawn` hatalari olusabilir.

**Fix:** `get_db_session_context()` (async context manager) kullan veya `run_in_executor()` ile sar.

### 1.12 populate_question_bank.py Yanlis Tablo
**Dosya:** `backend/scripts/populate_question_bank.py:17`

`from models.database import ... Question` -- legacy `questions` (BOS) tablosunu import ediyor. Script ile veri yuklenirse yanlis tabloya yazilir.

**Fix:** `from models.question_bank import QuestionBankItem as Question` kullan.

---

## BOLUM 2: P1 ONEMLI (Sprint Icinde — 30 bulgu)

### Gamification (4)
| # | Sorun | Dosya |
|---|-------|-------|
| 13 | 4 response shape uyumsuzlugu: usePoints, useLevel, useBadges, useLeaderboard -- `response.data` yerine `response.data.data.X` olmali | `useGamification.ts:88,159,217,294` |
| 14 | Level formulu tutarsiz -- API: `lv*100*1.5^lv`, ExperienceManager: `100*1.5^(lv-1)` | `gamification_api.py:619` vs `experience_manager.py:38` |
| 15 | `GamificationDBService.award_xp()` User.level field'ini GUNCELLEMEZ | `learning_event_service.py:255` |
| 16 | `/points/award` self-service XP istismar -- herkes kendi puanini artirabilir | `gamification_api.py:160` |

### Learning Path (6)
| # | Sorun | Dosya |
|---|-------|-------|
| 17 | Iki LP sistemi ayni prefix, birbirinden habersiz, farkli veri kaynaklari | `learning_path_v2.py` + `learning_path_daily.py` |
| 18 | `user_theta` tablosu ORM modeli YOK -- raw SQL | `learning_path_orchestrator.py:503` |
| 19 | `yks_exam_goals` tablosu ORM modeli YOK | `learning_path_daily.py:106` |
| 20 | `topic_prerequisites` tablosu ORM modeli YOK | `dag_service.py:109` |
| 21 | DailyPlanPage frontend v2 field'lari (theta_se, prereq_blocked) tanimsiz | `DailyPlanPage.tsx:34` |
| 22 | Quiz submit body format uyumsuz -- mutation vs backend schema | `useLearningPathMutations.ts:104` |

### Auth (3)
| # | Sorun | Dosya |
|---|-------|-------|
| 23 | live_session_routes 7 endpoint auth'suz | `live_session_routes.py:133-430` |
| 24 | department/university/preference 3 router tumuyle auth'suz (create dahil) | `department_info_routes.py` + 2 diger |
| 25 | CSRF Phase 1: `/api/v1/` tamamen muaf -- tum API bypass | `application.py:210` |

### API Contract (4)
| # | Sorun | Dosya |
|---|-------|-------|
| 26 | parentService 4 endpoint backend'de YOK (PDF, bulk notify, approval) | `parentService.ts:203-269` |
| 27 | adminService 10+ endpoint backend'de YOK (trends, system, reports) | `adminService.ts:208-415` |
| 28 | chatService bionic-reading yanlis path | `chatService.ts:395` |
| 29 | recommendationService URL pattern uyumsuz (path param vs body) | `recommendationService.ts:35-71` |

### Algorithm Pipeline (5)
| # | Sorun | Dosya |
|---|-------|-------|
| 30 | BKT baslangic p_L=0.05-0.10 cok dusuk (standart: 0.3-0.5) | `bkt_service.py:231` |
| 31 | FSRS lapses daima 0 -- takip edilmiyor | `fsrs_v6_service.py:133` |
| 32 | FSRS reps = card.step (0 veya 1) -- gercek tekrar sayisi degil | `fsrs_v6_service.py:132` |
| 33 | ZPD zone p_L'den hesaplaniyor, theta yok sayiliyor | `bkt_service.py:412` |
| 34 | Subject ID map tutarsizligi: bkt_service vs learning_event_service | `bkt_service.py:309` |

### DB Integrity (5)
| # | Sorun | Dosya |
|---|-------|-------|
| 35 | `_analyze_performance()` is_active filtresi YOK | `osym_exam_engine.py:1041` |
| 36 | `soru_bankasi_service` NULL OR kosulu -- is_active=NULL aktif sayiliyor | `soru_bankasi_service.py:349,441` |
| 37-39 | 3 test dosyasi legacy Question import kullaniyor | Cesitli test dosyalari |
| 40 | chatService, socialService vb. raw fetch 401 retry YOK | 5+ servis dosyasi |
| 41 | `apiHelpers.ts` apiRequest 401'de refresh denemiyor | `apiHelpers.ts:449` |

---

## BOLUM 3: P2 TEKNIK BORC (22 bulgu)

### Orphan Backend Endpoint'ler (16 router, ~80+ endpoint)
Frontend'den hic cagrilmayan backend router'lar:

| Router Prefix | Dosya |
|---------------|-------|
| `/api/v1/adhd-support/*` (3 router) | adhd_support_api.py, adhd_focus_mode_api.py, adhd_task_management_api.py |
| `/api/v1/coaching` | coaching_api.py |
| `/api/v1/dina` | dina_api.py |
| `/api/v1/diary` | diary_api.py |
| `/api/v1/error-clusters` | error_cluster_api.py |
| `/api/v1/kvkk/*` (2 router) | kvkk_consent_api.py, kvkk_privacy_api.py |
| `/api/v1/mnemonics` | mnemonic_api.py |
| `/api/v1/productive-failure` | productive_failure_api.py |
| `/api/v1/study-plan` | study_planner_api.py |
| `/api/v1/mastery-confidence` | mastery_confidence_api.py |
| `/api/v1/knowledge-map` | knowledge_graph_api.py |
| `/api/v1/leagues` | league_api.py |
| `/api/v1/daily-quests` | daily_quest_api.py |
| `/api/v1/oba-seferleri` | oba_seferleri_api.py |

### Diger P2 Bulgular (6)
| # | Sorun | Dosya |
|---|-------|-------|
| 42 | Facade in-memory cache multi-worker'da tutarsiz | `facade.py:141` |
| 43 | FSRSReview audit trail olusmuyor (tablo bos) | `bkt_service.py:339-409` |
| 44 | Leaderboard period filtresi calismaz (hep all-time) | `gamification_api.py:470` |
| 45 | FK constraint eksiklikleri (BKTState, ZPDHistory, StudentAbility type mismatch) | `gamification.py:44,301,318` |
| 46 | Global mutable `_ALGO_ERRORS` counter thread-safe degil | `bkt_service.py:20` |
| 47 | `get_user_mastery()` sonucu kullanilmiyor | `learning_path_orchestrator.py:170` |

---

## BOLUM 4: KONSENSUS (2+ Agent Ayni Sorunu Isaret Etti)

| Sorun | Agent'lar | Guvenilirlik |
|-------|-----------|-------------|
| Gamification cift XP | Gamification + API Contract | YUKSEK |
| _on_mastery_event sync DB | Algorithm Pipeline + Gamification | YUKSEK |
| LP facade TODO'lar (DB yok) | LP + API Contract | YUKSEK |
| Gamification response shape uyumsuzlugu | Gamification + API Contract | YUKSEK |
| osym_questions_api auth'suz | Auth + DB Integrity | YUKSEK |
| is_active filtresi eksik | DB Integrity + Algorithm Pipeline | YUKSEK |
| FSRS reps/lapses bozuk | Algorithm Pipeline | ORTA |
| 16 orphan router | API Contract | ORTA |

---

## BOLUM 5: ONERILEN AKSIYON PLANI

### Faz A: Acil Fix (P0 — ayni gun)
1. Frontend quiz XP cagrisini kaldir (cift XP fix)
2. Gamification 4 response shape fix (`response.data.data`)
3. advancedReportsService 7 URL prefix fix
4. examService 3 endpoint path fix
5. _on_mastery_event async DB migration

### Faz B: Gamification Wiring (P0 — 1-2 gun)
6. Badge check otomasyonu: `on_quiz_completed()` sonuna ekle
7. Leaderboard update otomasyonu: `award_xp()` sonuna ekle
8. Level formulu tekillestir
9. 6 hayalet endpoint: ya backend'de olustur ya frontend'den kaldir

### Faz C: Auth Enforcement (P0-P1 — 1-2 gun)
10. osym_questions_api 5 endpoint auth ekle
11. litellm_chat _noop_auth kaldir
12. live_session_routes 7 endpoint auth ekle
13. CSRF Phase 2 planla

### Faz D: LP Facade DB Baglantisi (P0-P1 — 2-3 gun)
14. facade get_student_path() DB sorgusu
15. facade _get_or_create_profile() DB sorgusu
16. LP v2 ve Daily arasinda veri paylasimi (en azindan theta okuma)

### Faz E: Algorithm Pipeline Iyilestirme (P1 — 3-5 gun)
17. FSRS reps/lapses duzeltme
18. BKT baslangic p_L yukseltme (0.3)
19. ZPD zone hesaplamasina theta ekleme
20. Subject ID map tutarliligi

---

## Metodoloji

- 6 Opus agent paralel calistirildi
- Her agent 1 baglanti zincirini uctan uca dogruladi
- Toplam 284 dosya taranarak Read/Grep ile kod okundu
- Severity: P0=runtime hata/veri kaybi, P1=yanlis davranis, P2=teknik borc
- Konsensus: 2+ agent'in ayni sorunu isaret etmesi yuksek guvenilirlik gostergesi
