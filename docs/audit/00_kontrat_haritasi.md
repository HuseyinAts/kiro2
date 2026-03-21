# FAZ 0: Kontrat Haritasi (Backend ↔ Frontend)

**Tarih:** 2026-03-21
**Branch:** audit/fullstack-20260321
**Yontem:** Otomatik tarama (grep + agent) + manuel dogrulama

---

## Genel Istatistikler

| Metrik | Deger |
|--------|-------|
| Backend API dosyasi | 96 (aktif) |
| Backend toplam endpoint | 1,108 |
| Backend auth'lu endpoint | 495 (%44.7) |
| Backend auth'suz endpoint | 613 (%55.3) |
| Frontend axios cagrisi | 58 |
| Frontend fetch cagrisi | 268 |
| Frontend `withCredentials: true` | 5 |
| Frontend `credentials: 'include'` | 152 |
| ForeignKey toplam | 303 |
| ForeignKey `index=True` | 37 (%12.2) |
| Tam auth'lu API dosyasi | 38 |

---

## Backend Endpoint Auth Durumu (Open > 0, Oncelik Sirasinda)

| Dosya | Prefix | Toplam | Auth | Acik | Oncelik |
|-------|--------|--------|------|------|---------|
| auth.py | /api/v1/auth | 23 | 0 | 23 | LOW (public auth) |
| university_info_routes.py | /api/v1/university-info | 19 | 0 | 19 | LOW (public) |
| diary_api.py | /api/v1/diary | 48 | 30 | 18 | HIGH (user data) |
| content_management.py | /api/v1/content-management | 19 | 1 | 18 | HIGH (CMS) |
| zpd_maarif.py | /api/v1/zpd-maarif | 17 | 0 | 17 | HIGH (student data) |
| multisensory_learning_api.py | /api/v1/multisensory | 17 | 0 | 17 | MEDIUM |
| visual_supports_api.py | /api/v1/visual-supports | 16 | 0 | 16 | HIGH (user_id IDOR) |
| department_info_routes.py | /api/v1/department-info | 15 | 0 | 15 | LOW (public) |
| content_api.py | /api/v1/content | 15 | 0 | 15 | HIGH (CMS) |
| curriculum_compliance.py | /api/v1/curriculum | 13 | 0 | 13 | MEDIUM |
| university_advisory_routes.py | /api/v1/university-advisory | 15 | 3 | 12 | MEDIUM |
| student_dashboard.py | /api/v1/student-dashboard | 12 | 0 | 12 | CRITICAL (student data) |
| question_bank_v2_routes.py | /api/v2 | 12 | 0 | 12 | HIGH (question data) |
| tracing_example.py | /api/v1/tracing-demo | 11 | 0 | 11 | LOW (demo) |
| teacher_routes.py | /api/v1/teachers | 25 | 14 | 11 | HIGH (teacher data) |
| student_review_routes.py | /api/v1/reviews | 14 | 3 | 11 | MEDIUM |
| sentry_demo.py | /api/v1/sentry-demo | 11 | 0 | 11 | LOW (demo) |
| preference_simulation_routes.py | /api/v1/preference-simulation | 11 | 0 | 11 | MEDIUM |
| monitoring.py | /api/v1/monitoring | 11 | 0 | 11 | LOW (ops) |
| math_solution_steps.py | /api/v1/math-solution-steps | 11 | 0 | 11 | MEDIUM |
| live_session_routes.py | /api/v1/live-sessions | 21 | 10 | 11 | HIGH (session data) |
| youtube_routes.py | /api/v1/youtube | 10 | 0 | 10 | LOW (public) |
| video_analytics_routes.py | /api/v1/video-analytics | 18 | 8 | 10 | MEDIUM |
| sequential_reasoning_api.py | /api/v1/reasoning | 10 | 0 | 10 | HIGH (cache clear) |
| response_validation_api.py | /api/v1/response-validation | 10 | 0 | 10 | LOW (not loaded) |
| ogretmen.py | /api/v1/ogretmen | 10 | 0 | 10 | HIGH (teacher data) |
| veli.py | /api/v1/veli | 9 | 0 | 9 | HIGH (parent data) |
| question_crud_api.py | /api/v1/questions | 17 | 8 | 9 | HIGH (question CRUD) |
| ocr_api.py | /api/v1/ocr | 9 | 0 | 9 | MEDIUM |
| difficulty_classification_api.py | /api/v1/difficulty | 8 | 0 | 8 | MEDIUM |
| vision_api.py | /api/v1/vision | 7 | 0 | 7 | MEDIUM |
| validation.py | /api/v1/validation | 7 | 0 | 7 | LOW (utility) |
| turkish_nlp.py | /api/v1/turkish-nlp | 7 | 0 | 7 | LOW (utility) |
| question_pipeline_api.py | /api/v1/question-pipeline | 7 | 0 | 7 | LOW (not loaded) |
| health.py | /api/v1 | 7 | 0 | 7 | LOW (public health) |
| enhanced_auth_api.py | /api/v1/auth | 13 | 6 | 7 | MEDIUM |
| ebatv.py | /api/v1/eba | 9 | 2 | 7 | MEDIUM |
| eba_routes.py | /api/v1/eba | 15 | 8 | 7 | MEDIUM |
| config_routes.py | /api/v1/config | 9 | 2 | 7 | HIGH (system config) |
| ai_chat_routes.py | /api/v1/chat | 7 | 0 | 7 | HIGH (user data) |
| yolo_detection_api.py | /api/v1/yolo | 6 | 0 | 6 | LOW (utility) |
| pdf_processing_api.py | /api/v1/pdf | 6 | 0 | 6 | MEDIUM |
| ferpa_coppa_compliance_api.py | /api/v1/compliance | 6 | 0 | 6 | LOW (public) |
| wave2b_quality_routes.py | /api/v2/quality | 5 | 0 | 5 | MEDIUM |
| team_challenges_api.py | /api/v1/challenges | 5 | 0 | 5 | MEDIUM |
| soru_bankasi.py | /api/v1/soru-bankasi | 14 | 9 | 5 | MEDIUM |
| osym_questions_api.py | /api/v1/osym | 5 | 0 | 5 | MEDIUM |
| learning_style.py | /api/v1/learning-style | 12 | 7 | 5 | MEDIUM |
| enhanced_chat.py | /api/v1/enhanced-chat | 6 | 1 | 5 | HIGH (user data) |
| alternative_solutions_api.py | /api/v1/alternatives | 8 | 3 | 5 | MEDIUM |

**Ozet:** 613 acik endpoint'in ~250'si kullanici/ogrenci verisi isliyor (CRITICAL/HIGH).

---

## Frontend Credential Durumu

### Toplam
| Tip | Mevcut | Eksik (tahmini) |
|-----|--------|-----------------|
| axios `withCredentials: true` | 5 | ~53 |
| fetch `credentials: 'include'` | 152 | ~116 |

### Bilinen Eksik Dosyalar (onceki session'dan)
- `useGamification.ts` — 13 axios cagrisi eksik
- `api.ts` RAG bolumu — 12+ fetch cagrisi eksik
- `revolutionaryFeaturesService.ts` — 18 fetch eksik
- `fsrsService.ts` — 8 fetch eksik
- `StudyRooms/` — 7 axios eksik
- `Manipulatives/` — 9 fetch eksik

---

## Hardcoded URL'ler

| Dosya | URL | Tip |
|-------|-----|-----|
| YOLODetectionPage.tsx | `localhost:8000/api/yolo/detect` | HARDCODED (env var eksik) |
| SystemSettings.tsx:31 | `localhost:3000` | HARDCODED (default config) |
| AIChatAssistant.tsx:11 | `localhost:8000` | FALLBACK (env var ile) |
| DepartmentInfo.tsx:11 | `localhost:8000` | FALLBACK (env var ile) |
| StudentReviews.tsx:11 | `localhost:8000` | FALLBACK (env var ile) |
| TeacherPool.tsx:11 | `localhost:8000` | FALLBACK (env var ile) |
| UniversityInfo.tsx:11 | `localhost:8000` | FALLBACK (env var ile) |
| config/index.ts:14-17 | `localhost:8000/3000` | EXPECTED (dev config) |

---

## Veri Katmani Ozet

| Sorun | Sayi | Ciddiyet |
|-------|------|----------|
| Yanlis tablo import (legacy `questions`) | 3 (test dosyalari) | LOW |
| ForeignKey index eksik | 266/303 (%87.8) | MEDIUM |
| get_async_session yanlis kullanim | 0 (tumu `_context` kullanir) | OK |

---

## Router Loader Durumu

**Yuklenen:** 96 router (ROUTER_MAPPING'deki)
**Yuklenmeyen API dosyalari:** `response_validation_api.py`, `question_pipeline_api.py` (ROUTER_MAPPING'de ama module not found olabilir)

---

## STATUS: TAMAM
