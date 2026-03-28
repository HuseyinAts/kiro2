# KIRO2 Sistem Baglanti Raporu — Tam Tarama (28 Mart 2026)

## Context

3 paralel Opus agent ile backend (532 dosya), frontend (189 dosya) ve orchestrator (40 modul) tum bilesenleri taranip baglanti haritasi cikarildi.

**Son commit:** `b3ffbaa` | **Branch:** master

---

## BOLUM 1: ANA BILESENLER ENVANTERI

### Backend (532 dosya)

| Katman | Dosya Sayisi | Konum |
|--------|-------------|-------|
| API Router'lar | 126 | `backend/api/` |
| App API (LP/CAT/DAG) | 8 | `backend/app/api/` |
| Servisler | ~111 | `backend/services/` |
| App Servisleri | 11 | `backend/app/services/` |
| Modeller | 79 | `backend/models/` |
| Core | 177 | `backend/core/` |
| Agent'lar | 9 | `backend/agents/` |
| Algoritmalar | 7 | `backend/algorithms/` |

### Frontend (189 dosya)

| Katman | Dosya Sayisi | Konum |
|--------|-------------|-------|
| Sayfa Component'leri | 61 aktif + 44 deprecated | `frontend/src/pages/` |
| Custom Hook'lar | 53 (test dahil) | `frontend/src/hooks/` |
| Servisler | 28 aktif + 4 deprecated | `frontend/src/services/` |
| Store'lar (Zustand) | 5 | `frontend/src/store/` |
| Component Dizinleri | 42+ | `frontend/src/components/` |

### Orchestrator (40 modul)

| Katman | Dosya Sayisi | Konum |
|--------|-------------|-------|
| Core Moduller | 35 | `orchestrator/core/` |
| Kok Dosyalar | 5 | `orchestrator/` |

---

## BOLUM 2: AKTIF BAGLANTI ZINCIRLERI (7 Ana Akis)

### Zincir 1: Sinav Akisi — BAGLI

```
Frontend: examService.ts -> POST /api/v1/osym-exam/create, /start, /save-answer, /complete
    |
Backend:  api/sinav.py -> core/osym_exam_engine.py -> models/database.py (ExamSession, StudentAnswer)
    |                                                -> models/question_bank.py (QuestionBankItem 77K)
    |
          api/sinav.py save_answer -> services/bkt_service.py record_answer() [5-adim pipeline]
```

**Durum:** Tam bagli. Frontend credentials:'include', backend auth, DB read/write hepsi calisiyor.

### Zincir 2: Algoritma Pipeline (record_answer) — BAGLI

```
sinav.py save_answer()
  -> BKTService.record_answer()
      [1] BKT -> models/gamification.py BKTState (DB upsert)
      [2] IRT -> services/irt_service_3pl.py EAP theta (lazy import)
             -> models/gamification.py StudentAbility (DB upsert)
      [3] FSRS -> services/fsrs_v6_service.py (lazy import)
              -> models/fsrs_models.py FSRSCard (DB upsert)
      [4] ZPD -> ZPDManager.zone() (pure)
             -> models/gamification.py ZPDHistory (DB insert)
      [5] Blackboard -> services/blackboard_service.py publish (fire-and-forget)
```

**Durum:** 5 adim zincirlenmis, her biri try/except icinde. errors dict ile partial failure raporlama.

### Zincir 3: Learning Path — CIFT YOLLU, KISMEN BAGLI

**Yol A: LP v2 (ana frontend yolu)**
```
Frontend: useLearningPath.ts + ModernLearningPathPage.tsx
    -> GET /api/v1/learning-path/my-profile, /completion/{id}
    -> PUT /api/v1/learning-path/progress/{sid}/{nodeId}
    -> POST /api/v1/learning-path/quiz/{id}/submit
    |
Backend: api/learning_path_v2.py -> agents/learning_path/facade.py
    -> services/path_generation.py, resource_discovery.py, path_adaptation.py
    -> models/learning_path_models.py (LearningPath, Quiz, PathNode)
```

**Yol B: LP Daily (orchestrator katmani)**
```
Frontend: useStudentProfile.ts + DailyPlanPage.tsx
    -> GET /api/v1/learning-path/status, /today, /weekly
    |
Backend: app/api/learning_path_daily.py -> app/services/learning_path_orchestrator.py
    -> app/services/dag_service.py -> dag_engine.py (prereq grafigi)
    -> DB: StudentAbility theta, FSRSCard due, BKTState mastery
```

**KOPUKLUK:** Yol A ve Yol B birbirinden HABERSIZ. Yol A'nin facade'i Yol B'nin orchestrator'unu cagirmiyor. Iki farkli LP profil yonetimi var.

### Zincir 4: Auth — BAGLI

```
Frontend: authService.ts -> POST /api/v1/auth/login/secure (credentials: 'include')
    | httpOnly cookie set
Backend: api/auth.py -> core/dependencies.py (JWT decode) -> models/database.py (User)
    | 401 -> apiClient.ts interceptor -> POST /refresh/secure -> retry
```

**Durum:** Tam bagli. 0 localStorage kalintisi, 57 dosya credentials:'include'.

### Zincir 5: Gamification — BAGLI

```
Frontend: useGamification.ts (axios, withCredentials)
    -> GET/POST /api/v1/gamification/points, /level, /badges, /leaderboard
    |
Backend: api/gamification_api.py -> core/gamification/*.py (4 manager)
    -> services/learning_event_service.py -> models (UserAchievement, XPTransaction, etc.)
```

**Durum:** Tam bagli. Auth IDOR fix tamamlandi (Session 84).

### Zincir 6: YouTube/Video — BAGLI

```
Frontend: VideoLoadingManager.ts -> POST /api/v1/learning-path/search-resources
    |
Backend: api/youtube_routes.py -> services/youtube/* (12 modul)
    -> services/advanced_youtube_search.py -> core/youtube_channels.py (17 kanal)
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

---

## BOLUM 3: KOPUK / DORMANT BAGLANTILAR

### 3A. Orchestrator — %97 DORMANT

| Bilesen | Durum | Detay |
|---------|-------|-------|
| `orchestrator/core/routing.py` RoutingEngine | AKTIF | `orchestrator_api.py /dispatch` cagrisi |
| `orchestrator/__init__._GRAPH_AVAILABLE` | AKTIF | Status check |
| `orchestrator/core/graph.py` LangGraph | COMPILE ediyor ama node'lar TODO stub | Plan/implement/review hepsi sabit string doner |
| `orchestrator/core/policy_engine.py` (45 politika) | DORMANT | Hicbir endpoint cagirmiyor |
| `orchestrator/core/agents.py` (7 agent) | DORMANT | graph.py icinden bile cagirilmiyor |
| `orchestrator/core/llm_gateway.py` | DORMANT | |
| `orchestrator/core/memory.py` | DORMANT | |
| Diger 28 core modul | DORMANT | Backend'den 0 import |
| `orchestrator/algorithms.py` | TEKRAR | Backend'in kendi servisleriyle overlap |
| `orchestrator/master_orchestrator.py` | LEGACY | Tamamen kullanilmiyor |

**Sonuc:** 35 core modulden sadece 2'si (routing.py + __init__.py flag) backend'le iletisimde. Geri kalan %94'u dormant.

### 3B. Blackboard — AKTIF AMA ETKISIZ

```
record_answer() -> BlackboardService.publish() -> DomainBlackboard -> _notify_subscribers()
    -> _on_mastery_event() -> SADECE LOG YAZIYOR (aksiyon yok)
```

**Sorun:** Subscriber kayitli ve tetikleniyor ama:
- Cache invalidation YOK
- LP node complete isaretleme YOK
- Notification gonderme YOK
- Sadece `logger.info()` cikisi var

### 3C. LP Cift Yol Kopuklugu

| | Yol A (LP v2) | Yol B (LP Daily) |
|--|--------------|-----------------|
| API prefix | `/api/v1/learning-path/` | `/api/v1/learning-path/` (ayni!) |
| Backend | `api/learning_path_v2.py` | `app/api/learning_path_daily.py` |
| Servis | `agents/learning_path/facade.py` | `app/services/learning_path_orchestrator.py` |
| Theta kaynagi | Yok (facade'de theta hesaplanmiyor) | `StudentAbility` tablosu |
| ZPD kaynagi | Yok | mastery_pct threshold |
| DAG | Yok | `dag_service.py` onkosul grafigi |
| Birbirine bagli mi? | **HAYIR** | **HAYIR** |

**Risk:** Iki yol ayni prefix'i paylasiyor ama farkli veri kaynaklari kullaniyor. Frontend hangisini cagirdigina gore farkli sonuc alir.

### 3D. Router'da Kayitsiz API Dosyalari (3 adet)

| Dosya | Durum |
|-------|-------|
| `backend/api/question_pipeline_api.py` | Kayitli DEGIL |
| `backend/api/response_validation_api.py` | Kayitli DEGIL |
| `backend/api/websocket_connection_manager.py` | Kayitli DEGIL |

### 3E. Kullanilmayan Servisler (17 dead code)

`adaptive_test_engine`, `bloom_taxonomy_classifier`, `enhanced_bloom_classifier`, `enhanced_question_templates`, `geometry_generator`, `graph_generator`, `irt_analysis_service`, `irt_calibration_service`, `irt_psychometric_analysis`, `map_diagram_generator`, `osym_benchmark_comparator`, `question_generation_engine`, `question_reranker`, `subject_relevance_scorer`, `subject_specific_prompts`, `visual_content_generator`, `zemberep_morfoloji_service`

### 3F. Kullanilmayan Modeller (23 dead model)

`analytics_db`, `content_db`, `eba_models`, `exam_models`, `gamification_db`, `leaderboard_entry`, `learning_models`, `main`, `manipulatives`, `notification`, `profile_migration`, `quality_gates_db`, `question_parser`, `reports_models`, `revolutionary_models`, `student_goal`, `student_learning_profile`, `system_models`, `user_models`, `video_cache_model`, `yks_generation`, `youtube_playlist`, `claude_md_improvement_models`

### 3G. Kullanilmayan Frontend Hook'lar (15 adet)

`useAPI`, `useAccessibilityAnnouncer`, `useApiIntegration`, `useExamKeyboard`, `useExamMetrics`, `useFocusManagement`, `useLocalStorage`, `useOfflineMode`, `useQueryKeys`, `useRevolutionaryFeatures`, `useStudentProfile`, `useTurkishLanguageCorrection`, `useVideoPlayer`, `useWebSocket`, `useAsync`

### 3H. Fiilen Erisilemez Frontend Servisler (2 adet)

`monitoringService.ts` ve `ragService.ts` — tek import eden hook (`useApiIntegration`) hicbir yerde kullanilmiyor.

---

## BOLUM 4: BAGLANTI MATRISI OZET

| Baglanti | Durum | Notlar |
|----------|-------|--------|
| Frontend Auth -> Backend Auth | BAGLI | 57 dosya credentials:'include', 0 localStorage |
| Frontend Exam -> Backend Sinav | BAGLI | Full flow calisiyor |
| Frontend LP -> Backend LP v2 | BAGLI | Facade pattern |
| Frontend LP -> Backend LP Daily | BAGLI | Orchestrator katmani |
| LP v2 <-> LP Daily | KOPUK | Birbirinden habersiz |
| Frontend Gamification -> Backend | BAGLI | Auth + IDOR fix |
| Frontend Video -> Backend YouTube | BAGLI | 12 modul pipeline |
| Frontend Chat -> Backend AI | BAGLI | SSE stream |
| Backend record_answer Pipeline | BAGLI | BKT->IRT->FSRS->ZPD->Blackboard |
| Blackboard -> Subscriber | TETIKLENIYOR AMA AKSIYONSUZ | Sadece log |
| Backend -> Orchestrator | SADECE ROUTING | %94 dormant |
| Orchestrator Graph -> LLM | DORMANT | TODO stub node'lar |
| Redis Pub/Sub | SADECE DUEL | Blackboard LPUSH kullanir |

---

## BOLUM 5: ONERILEN AKSIYONLAR (Oncelik Sirasi)

### P0: Kritik Baglantilar

1. **LP Cift Yol Birlestirmesi**: LP v2 facade'inin LP Daily orchestrator'dan theta/zpd/dag verisi almasi gerekiyor. Simdi iki paralel sistem birbirinden habersiz calisiyor.

2. **Blackboard Subscriber'a Aksiyon Ekle**: `_on_mastery_event` sadece log yaziyor. LP cache invalidation + gamification XP award eklenmeli.

### P1: Dead Code Temizligi

3. **17 kullanilmayan backend servis** -> `_archive/` tasi veya sil
4. **23 kullanilmayan model** -> `_archive/` tasi (Alembic migration icin metadata'da kalabilir)
5. **15 kullanilmayan frontend hook** -> `_deprecated/` tasi
6. **3 kayitsiz API dosyasi** -> router'a kaydet veya sil

### P2: Orchestrator Aktivasyonu

7. **graph.py TODO stub'lari** -> LLM gateway entegrasyonu (maliyet/benefit analizi gerekli)
8. **policy_engine.py stub validator'lar** -> gercek validation implementasyonu
9. **Version uyumsuzlugu**: root=2.0.0, core=3.2.1, CLAUDE.md=v2.5.0 -> tekillestir
