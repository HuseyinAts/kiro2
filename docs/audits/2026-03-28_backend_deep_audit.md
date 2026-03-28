# Backend Deep Audit Report

**Tarih:** 2026-03-28
**Concern'ler:** Security+Auth, Models+Schemas, Services+Algorithms, NLP+Tests
**Agent sayisi:** 4 (paralel)
**Toplam bulgu:** 19 P0, 27 P1, 30 P2 = **76 bulgu**

---

## P0 — Hemen Fix (19 bulgu)

### Security & Auth (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| S1 | api/celery_tasks_api.py:98-138 | Auth bypass — task cancel/active/stats unauthenticated | `Depends(get_current_user)` + `require_role("ADMIN")` |
| S2 | api/team_challenges_api.py:29,45,63 | Auth bypass + IDOR — user_id plain param, impersonation | `Depends(get_current_user)` ile degistir |
| S3 | api/osym_questions_api.py:1-210 | Auth bypass — 77K soru+cevap unauthenticated | `Depends(get_current_user)` tum endpoint'lere |
| S4 | api/wave2b_quality_routes.py:163,213,279 | Auth bypass — AI evaluate/batch/bertscore unprotected | Auth dependency ekle |
| S5 | api/osym_inspired_routes.py:21 | Auth bypass — AI question generation unprotected (API maliyet riski) | Auth + rate limiting |

### Models & Schemas (3)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| M1 | models/content_db.py:33 | Legacy `Question` model hala tanimli ve `__init__.py:58,212` uzerinden export ediliyor | `__all__`'dan cikar, deprecation docstring |
| M2 | models/exam_db.py:116,152 | `ExamQuestion.question_id` ve `StudentAnswer.question_id` FK constraint YOK — orphan data riski | `ForeignKey("question_bank.id", ondelete="CASCADE")` + migration |
| M3 | models/osym_question.py:162 | `StudentQuestionResponse.exam_session_id` Integer FK ama `exam_sessions.id` String (UUID) — tip uyumsuzlugu | `Column(String, ForeignKey(...))` |

### Services & Algorithms (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| V1 | algorithms/irt_model.py:21-27 | Broken import — `from core.irt_validators` sadece CWD=backend ise calisir | Relative veya fully-qualified import |
| V2 | algorithms/irt_morfoloji_service.py:16 | Broken import — `from core.turkish_nlp_service` ayni sorun | Ayni fix |
| V3 | algorithms/cultural_adaptation_engine.py:21 | `from hijri_converter import Gregorian` try/except YOK — ImportError crash | try/except wrap |
| V4 | services/cat_session.py:631-650 | N+1 INSERT — 20 soruluk CAT icin 20 ayri DB round-trip | `executemany` veya multi-row INSERT |
| V5 | services/dag_service.py:158-168 | Cartesian join — 77K question x sessions = milyonlarca satir | `DISTINCT ON` veya rewrite |

### NLP & Tests (6)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| N1 | core/encoding.py:152 | `normalize_turkish_text()` bare `.lower()` — I→i (YANLIS), I→ı olmali | `normalize_tr()` kullan |
| N2 | tests/test_exam_answer_tracking.py:88 | Legacy `Question` import — bos tablo | `QuestionBankItem` |
| N3 | tests/slow/test_soru_bankasi_service.py:15 | Legacy `Question` import | `QuestionBankItem` |
| N4 | tests/integration/test_end_to_end_platform.py:31 | Legacy `Question` import | `QuestionBankItem` |
| N5 | tests/slow/test_turkish_morphology_irt_comprehensive.py:22 | Legacy `Question` import | `QuestionBankItem` |
| N6 | tests/integration/test_end_to_end_platform.py:42,52 | Mojibake encoding bozulmasi — `"sÄ±nav"` olmasi gereken `"sinav"` | UTF-8 NFC ile yeniden kaydet |

---

## P1 — Sprint Icinde Fix (27 bulgu)

### Security & Auth (5)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| S6 | api/sentry_demo.py:237 | IDOR — user_id Query param | `Depends(get_current_user)` |
| S7 | core/application.py:189-196 | CSRF exempt_paths=["/api/v1/"] — TUM API unprotected | Frontend X-CSRF-Token implement, exempt kaldir |
| S8 | api/enhanced_chat.py:674 | SSRF redirect bypass — `follow_redirects=True` private IP check'i atlar | `follow_redirects=False` veya redirect sonrasi re-validate |
| S9 | api/celery_tasks_api.py:78-80 | Stack trace leakage — full traceback response'ta | Admin-only veya kaldir |
| S10 | api/encryption_management.py:226 | Encryption key API response'ta doner | Key'i response'tan cikar, vault'a yaz |

### Models & Schemas (7)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| M4 | enums_db.py:16 vs question_bank.py:388 | exam_type case mismatch — enum lowercase, DB UPPERCASE, join 0 row | Tek convention standardize |
| M5 | curriculum.py:30 vs enums_db.py:16 | Duplicate ExamType enum — farkli member set'ler | Birini sil, diger import |
| M6 | learning_path_models.py:130+ (40 yer) | `default=datetime.now` timezone YOK — naive datetime | `server_default=func.now()` standardize |
| M7 | content_db.py:130 | `Question.is_active` maps to column `aktif` — standart disi | Deprecate ile birlikte cikar |
| M8 | gamification.py:239 | `Duel.winner_id` Integer ama `users.id` String (UUID) — tip uyumsuzlugu | `Column(String)` |
| M9 | gamification.py:299 | `StudentAbility.subject_id` Integer PK, FK yok — anlam belirsiz | FK ekle veya dokumante |
| M10 | learning_path_models.py:78 | `LearningPathStudentProfile.user_id` nullable=True — orphan profil riski | `nullable=False` + migration |

### Services & Algorithms (6)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| V6 | services/cat_session.py:170-172 | Redis None check yok — `self.redis.hgetall` AttributeError | `if self.redis:` guard |
| V7 | services/placement_service.py:262-266 | Redis None guard yok — `except Exception: pass` hatayi yutar | Explicit None check |
| V8 | services/fsrs_service.py:234-270 | N+1 batch — 20 review = 40 DB call | Batch SELECT + multi-row UPSERT |
| V9 | services/cat_session.py:579-675 | DB commit fail ama Redis "completed" — inconsistent state | try/except + Redis revert |
| V10 | algorithms/irt_model.py:46-48 | IRT param bounds uyumsuz — `[0.2,4.0]` vs calibrator `[0.3,3.0]` | Tek source of truth |
| V11 | services/dag_service.py:96-103 | `NULL AS subject_id` — tum topic'ler subject_id="None" | Gercek kolonu sec |

### NLP & Tests (9)

| # | Dosya:Satir | Aciklama | Fix |
|---|-------------|----------|-----|
| N7 | core/turkish_nlp_chat_system.py:325+ (5 yer) | Bare `.lower()` — Turkish I/i mapping yok | `normalize_tr()` |
| N8 | core/turkish_exam_middleware.py:137+ (6 yer) | Bare `.lower()` — exam subject/type | `normalize_tr()` |
| N9 | core/turkish_nlp_service.py:297 | Bare `.lower()` — suffix extraction | `normalize_tr()` |
| N10 | core/turkish_nlp_service.py:420 | Bare `.lower()` — common error fix | `normalize_tr()` |
| N11 | core/turkish_exam_event_handlers.py:515 | Bare `.lower()` — subject lookup | `normalize_tr()` |
| N12 | ai_engine/enhanced_turkish_nlp.py:333+ (9 yer) | 9x bare `.lower()`, 0 NFC — ana Turkish NLP motoru! | `unicodedata` import + `normalize_tr()` |
| N13 | services/youtube/nlp.py:127,203,204 | Bare `.lower()` — YouTube Turkish content detect | `normalize_tr()` |
| N14 | 19 dosya, 60 occurrence | Deprecated `AsyncClient(app=app)` — httpx 0.27+ | `ASGITransport(app=app)` batch migration |
| N15 | core/turkish_nlp_chat_system.py + turkish_exam_middleware.py | NFC normalization yok — decomposed vs composed char fail | `unicodedata.normalize("NFC", ...)` |

---

## P2 — Teknik Borc (30 bulgu)

### Security & Auth (8)

| # | Dosya:Satir | Aciklama |
|---|-------------|----------|
| S11 | api/turkish_nlp.py:1-60 | NLP endpoint'ler auth yok — compute abuse |
| S12 | api/text_simplification.py:1-80 | Text simplification auth yok |
| S13 | api/yolo_detection_api.py:1-60 | YOLO detection auth yok, file validation yok |
| S14 | api/vision_api.py:1-80 | Vision/OCR endpoint'ler auth yok — LLM maliyeti |
| S15 | core/application.py:181-184 | CORS allow_methods/headers=["*"] — asiri permissive |
| S16 | api/osym_questions_api.py:8 | Raw asyncpg.connect() — ORM bypass |
| S17 | core/database_optimizer.py:597,600 | `text(f"ANALYZE {table}")` — SQL injection riski |
| S18 | api/question_crud_api.py:951-965 | f-string text() — gelecekte injection riski |

### Models & Schemas (8)

| # | Dosya:Satir | Aciklama |
|---|-------------|----------|
| M11 | models/__init__.py:58 | `Question` legacy `__all__`'da — kazara kullanim |
| M12 | enums.py + enums_db.py | 3x difficulty enum, 3x exam type enum — kaos |
| M13 | content_db.py:82-97 vs question_bank.py | Schema divergence — enum vs string |
| M14 | osym_question.py:92-93 | `datetime.utcnow` deprecated Python 3.12+ |
| M15 | user_badge.py | Sadece re-import dosyasi — gereksiz indirection |
| M16 | learning_path_models.py:94 | JSONB default=list/dict — schema validation yok |
| M17 | question_bank.py:86,299,309,409 | JSONB kolonlar — structure enforcement yok |
| M18 | content_db.py:140 | `EgitimIcerigi = "EducationalContent"` string, class degil |

### Services & Algorithms (9)

| # | Dosya:Satir | Aciklama |
|---|-------------|----------|
| V12 | services/cat_session.py:220-253 | `ORDER BY RANDOM()` 77K row — full scan |
| V13 | services/placement_service.py:296 | `ORDER BY RANDOM() LIMIT 80` 77K row |
| V14 | services/dag_service.py:300-301 | Mastery cache invalidation yok — 5dk stale |
| V15 | services/learning_path_orchestrator.py:78 | Hardcoded exam date — module load'da evaluate |
| V16 | services/learning_path_orchestrator.py:134 | `datetime.utcnow()` deprecated |
| V17 | services/learning_path_orchestrator.py:169 | `get_user_mastery()` return value kullanilmiyor |
| V18 | algorithms/turkish_optimized_fsrs.py | Duplicate FSRS impl — dead code |
| V19 | algorithms/irt_model.py | Duplicate IRT impl (4PL) — dead code |
| V20 | services/irt_calibrator.py:25 | Docstring "questions tablosuna" — yanlis tablo referansi |

### NLP & Tests (5)

| # | Dosya:Satir | Aciklama |
|---|-------------|----------|
| N16 | core/turkish_nlp_service.py:49 | Hardcoded Zemberek URL `localhost:6789` |
| N17 | tests/core/test_circuit_breaker.py:235+ | 5x `asyncio.sleep(1.1)` — flaky risk |
| N18 | 59 dosya | `skipif(True)` — permanent skip masking |
| N19 | 94 dosya | `pytest.skip(allow_module_level=True)` — 153 dosya skipped toplam |
| N20 | core/encoding.py:152 | `normalize_turkish_text` duplicate — yanlis impl |

---

## Konsensus (2+ agent hemfikir)

| Konu | Agent'lar | Guvenilirlik |
|------|-----------|-------------|
| **Auth bypass yaygin** | Security + NLP/Tests | YUKSEK — 14+ API dosyasi 0 auth |
| **Legacy Question model tehlikesi** | Models + NLP/Tests | YUKSEK — 4 test + export hala aktif |
| **Bare .lower() Turkish bozuklugu** | NLP/Tests + Models | YUKSEK — 20+ yer, ana NLP motoru dahil |
| **N+1 query pattern** | Services + Models | YUKSEK — CAT, FSRS, DAG hepsinde |
| **datetime.utcnow deprecated** | Models + Services | ORTA — 40+ yer, Python 3.12+ warning |
| **Duplicate enum tanimlari** | Models + Services | ORTA — 3x exam type, 3x difficulty |

---

## Oncelikli Aksiyon Plani

### Faz 1 — Acil (Bu hafta)
1. **Auth bypass fix** (S1-S5): 5 API dosyasina `Depends(get_current_user)` ekle
2. **DAG cartesian join** (V5): Milyonlarca satir donebilir — rewrite zorunlu
3. **DAG NULL subject_id** (V11): Tum topic'ler kirik — `th.subject_area AS subject_id`
4. **FK constraint** (M2): ExamQuestion + StudentAnswer orphan data onleme

### Faz 2 — Sprint (Bu ay)
5. **Turkish .lower() batch fix** (N7-N13): 6 dosya, 30+ yer — `normalize_tr()` standardize
6. **CSRF fix** (S7): exempt_paths'ten `/api/v1/` cikar, frontend token implement
7. **SSRF redirect** (S8): `follow_redirects=False`
8. **N+1 batch** (V4, V8): CAT persist + FSRS batch — multi-row INSERT/UPSERT
9. **Redis null guard** (V6, V7): 2 servis

### Faz 3 — Teknik Borc (Sonraki sprint)
10. **httpx migration** (N14): 19 dosya batch script
11. **Enum consolidation** (M5, M12): Tek canonical enum per concept
12. **Dead code archive** (V18, V19): algorithms/ duplicate impl'ler
13. **Question model deprecation** (M1, M11): Export + test migration

---

## Metrikler

| Kategori | P0 | P1 | P2 | Toplam |
|----------|----|----|----|----|
| Security & Auth | 5 | 5 | 8 | 18 |
| Models & Schemas | 3 | 7 | 8 | 18 |
| Services & Algorithms | 5 | 6 | 9 | 20 |
| NLP & Tests | 6 | 9 | 5 | 20 |
| **TOPLAM** | **19** | **27** | **30** | **76** |

---

*Audit by: 4 parallel agents (Claude Opus 4.6)*
*Rapor: docs/audits/2026-03-28_backend_deep_audit.md*
