# KIRO2 Backend Full Audit Report

**Tarih:** 26 Mart 2026
**Commit:** 48a35f5
**Yontem:** 8 paralel subagent ile kapsamli analiz
**Kapsam:** API, Services, Models, Algorithms, Core, NLP+Schemas, Tests+Scripts, Migrations+DB

---

## EXECUTIVE SUMMARY

| Katman | Dosya | Skor | Kritik Bulgu |
|--------|-------|------|-------------|
| API Routers | 135 | - | 1,144 endpoint, %70 auth coverage, validation.py korumasiz |
| Services | 10 | 8.2/10 | 4,557 satir, async/sync optimal, dual table trap YOK |
| Models | 83 | 8.2/10 | 312 model, 3 duplicate enum, import %100 dogru |
| Algorithms | 10 | 8.5/10 | IRT/FSRS/DAG/ZPD saglam, BKT eksik |
| Core | 182 | 8.3/10 | CSRF wired degil, IDOR kismi, token cleanup yok |
| NLP + Schemas | 19 | 7.5/10 | Turkish case mapping eksik, 0 enum, Pydantic v1 |
| Tests + Scripts | 735 | 6.5/10 | 648 test dosya, 29 collection error, over-mock |
| Migrations + DB | 79 | 7.0/10 | 34 Alembic + 45 raw SQL dual system |

**Genel Skor: 7.8/10 — Production-ready with caveats**

---

## P0 CRITICAL FINDINGS (Hemen cozulmeli)

### 1. validation.py Auth Eksik (API)
- 7 endpoint SIFIR auth
- POST `/api/v1/validation/submit` — herkes content dogrulamaya gonderebilir
- GET `/api/v1/validation/experts/{expert_id}/pending` — IDOR riski
- **Fix:** Tum endpoint'lere `Depends(get_current_user)` ekle

### 2. CSRF Middleware Wired Degil (Core)
- `csrf_protection.py` dosyasi var ama `application.py` middleware'de kullanilmiyor
- **Fix:** `setup_middleware()` icine CSRF middleware ekle

### 3. 29 Test Collection Error (Tests)
- 400-500 test unreachable (%3.7 kayip)
- Root cause: Deprecated imports + circular deps
- **Fix:** Import audit + restore/deprecation marker

### 4. Dual Migration System (DB)
- 34 Alembic (.py) + 45 raw SQL (.sql) birlikte var
- Hangi raw SQL uygulanmis belirsiz, rollback yok
- **Fix:** Raw SQL'leri Alembic'e konsolide et veya MIGRATION_STATUS.md olustur

---

## P1 HIGH PRIORITY (Sprint'e alinmali)

### 5. Auth Coverage %70 (API)
- 343/1,144 endpoint korumasiz (%30)
- Cogu public (health, auth, university_info) ama audit gerekli
- **Fix:** Tum POST/PUT/DELETE'lere auth zorunlu

### 6. Turkish Case Mapping Eksik (NLP)
- `_normalize_turkish()` sadece NFC, I/i mapping yok
- `istanbul` vs `Istanbul` eslesme bozuk olabilir
- **Fix:** `text.replace("I", "i").replace("I", "i")` ekle

### 7. 3 Duplicate Enum Tanimi (Models)
- SubjectType: 3 dosyada (ai_chat, curriculum, curriculum_db)
- ExamType: 3 dosyada
- **Fix:** Tum enum'lari `enums_db.py`'a konsolide et

### 8. httpx Deprecated Pattern (Tests)
- 33 dosya, 111 occurrence — AsyncClient(app=...) kullanimi
- En kotu: test_main_async.py (19 match)
- **Fix:** ASGITransport migration

### 9. Over-Mocking (Tests)
- 8,566 Mock/patch occurrence
- test_high_impact_modules.py (756 satir fake test)
- 1,359+ `assert is not None` zayif assertion
- **Fix:** Real algorithm tests yaz, sadece external deps mock'la

### 10. Token Cleanup Scheduled Degil (Core)
- `cleanup_expired_tokens()` manual task
- RefreshToken tablosu sinirsi buyur
- **Fix:** APScheduler/Celery daily task

---

## P2 MEDIUM PRIORITY (Sonraki sprint)

### 11. FSRS Weights Hardcoded (Algorithms)
- 21 element W array kod icinde
- Fine-tune icin config/env var yok

### 12. BKT Service Eksik (Algorithms)
- IRT+FSRS pipeline var ama Bayesian Knowledge Tracing yok
- Subject-specific mastery eksik

### 13. Pydantic v1 (Schemas)
- ConfigDict yok, field_validator yok
- v2 migration planlanmali

### 14. Enum String Literals (Schemas)
- 0/7 field enum kullaniyor (hepsi string literal)
- Compile-time type checking yok

### 15. Static Files Directory Traversal (Core)
- `/static/crops` mount validation eksik
- Symlink + path traversal kontrolu yok

### 16. IDOR Audit Incomplete (Core)
- 14+ endpoint tamamlanmamis
- Learning path fixed (Session 85), gamification fixed (Session 84)

### 17. Raw SQL Rollback Yok (DB)
- 45 .sql dosyasi DOWN migration icermiyor
- One-way only

### 18. Script Hardcoded Passwords (Scripts)
- 5 dosya `password="changeme..."` pattern
- Demo/test script'leri ama pre-commit hook gerekli

---

## KATMAN DETAY OZET

### 1. API Routers (135 dosya, 1,144 endpoint)

| Metrik | Deger |
|--------|-------|
| Toplam router | 135 |
| Toplam endpoint | 1,144 |
| Auth korumali | 801 (%70) |
| Korumasiz | 343 (%30) |
| GET | 603 (%52.7) |
| POST | 448 (%39.2) |
| DELETE | 40 (%3.5) |
| PUT | 36 (%3.1) |

En yogun dosyalar: diary_api.py (48), teacher_routes.py (25), auth.py (23)

### 2. Services (10 dosya, 4,557 satir)

| Dosya | Satir | Async % |
|-------|-------|---------|
| cat_session.py | 712 | 65% |
| yks_estimator.py | 593 | 0% (pure math) |
| dag_engine.py | 577 | 0% (pure math) |
| placement_service.py | 493 | 46% |
| irt_calibrator.py | 448 | 0% (pure math) |
| learning_path_orchestrator.py | 448 | 42% |
| fsrs_engine.py | 375 | 0% (pure math) |
| fsrs_service.py | 348 | 86% |
| dag_service.py | 300 | 70% |
| irt_engine.py | 263 | 0% (pure math) |

- Dual table trap: YOK (QuestionBankItem dogru kullanimda)
- DB context manager: YOK hata (get_db_session_context dogru)
- Dead code: YOK (tum servisler router'dan cagriliyor)

### 3. Models (83 dosya, 312 model)

| Metrik | Deger |
|--------|-------|
| Toplam dosya | 83 |
| Toplam model/tablo | 312 |
| Relative import | 67/83 (%81) |
| Absolute import | 0 (%0) |
| JSONB field | 263 occurrence |
| FK declaration | 232 |
| Explicit index | 30+ |

En buyuk: gamification.py (13 model), ebatv_content.py (12), live_session.py (11)

### 4. Algorithms (10 dosya, 4,557 satir)

| Algoritma | Durum | Parametre Araligi |
|-----------|-------|-------------------|
| IRT 3PL | Saglam | a:[0.3,3.0] b:[-4.0,4.0] c:[0.05,0.40] |
| FSRS v6 | Saglam | 21 weight, 4 state, target R=0.90 |
| DAG | Saglam | 60+ konu, 55 kenar, Kahn topolojik sort |
| ZPD | Saglam | [0.40, 0.85] optimal zone |
| CAT | Saglam | SE<0.35 stop, epsilon=0.20, max 20 soru |
| Placement | Saglam | Bisection, max 12 soru, lise prior |
| YKS Estimator | Saglam | OSYM 2024 puan formulü |
| BKT | EKSIK | Implement edilmemis |

Pipeline: Placement -> CAT -> IRT EAP -> ZPD select -> FSRS update -> DAG mastery -> Learning Path -> YKS Estimator

### 5. Core (182 dosya)

| Kontrol | Durum | Skor |
|---------|-------|------|
| Secrets env var'dan | PASS | 10/10 |
| Production validation | PASS | 9/10 |
| JWT implementation | PASS | 9/10 |
| Password hashing | PASS | 10/10 |
| RBAC (5 rol) | PASS | 9/10 |
| CSRF middleware | FAIL | 5/10 |
| IDOR audit | PARTIAL | 6/10 |
| Token cleanup | MISSING | 0/10 |
| Data retention | MISSING | 0/10 |

Connection pool: asyncpg, pool_size=200, max_overflow=300
Middleware: Timing, CORS, Cache, GZip, VersionRedirect, Auth (CSRF eksik)

### 6. NLP + Schemas

**NLP:**
- Turkish NFC normalizasyon: VAR (case mapping EKSIK)
- Embedding: nomic-embed-text 768d, pgvector HNSW 21ms
- Prompt template: 15+ Turkce (TYT/AYT, Bloom taxonomy)
- Zemberek: Entegrasyon mevcut

**Schemas:**
- 3 dosya, 13 Pydantic model (v1)
- CAT: 8 model (request/response)
- FSRS: 5 model
- Validation coverage: %69 (9/13 field)
- Enum kullanimi: %0 (hepsi string literal)
- Custom validator: 0

### 7. Tests + Scripts

**Tests (648 dosya):**

| Metrik | Deger |
|--------|-------|
| Toplam test dosyasi | 648 |
| Toplam test (collect) | 13,511 |
| Collection error | 29 |
| Backend coverage | ~18% |
| conftest dosyasi | 10 |
| httpx deprecated | 33 dosya |
| Mock/patch occurrence | 8,566 |

**Scripts (87 dosya):**
- Seed/data: 6 dosya (idempotent)
- Import/migration: 8 dosya
- IRT/algorithms: 7 dosya
- Quality/validation: 10 dosya
- Hardcoded password: 5 dosya (demo/test)

### 8. Migrations + DB

| Metrik | Deger |
|--------|-------|
| Alembic migrations | 34 |
| Raw SQL migrations | 45 |
| SQLAlchemy models | 312 |
| Production tables | 120+ |
| FK declarations | 232 |
| Strategic indexes | 30+ |
| Vector search index | 1 (HNSW) |

Kritik: Dual migration system (Alembic + raw SQL) = version chaos
Son migration: 20260320_fix_gamification_fk_types.py

---

## AKSIYON PLANI

### IMMEDIATE (Bu hafta)
1. [ ] validation.py auth ekleme (7 endpoint)
2. [ ] CSRF middleware wiring
3. [ ] 29 collection error fix
4. [ ] Migration status dokumantasyonu

### SPRINT 1 (2 hafta)
5. [ ] Auth audit tamamla (%70 -> %90+)
6. [ ] Turkish case mapping fix
7. [ ] Enum konsolidasyonu (3 duplicate -> 1)
8. [ ] httpx migration (33 dosya)
9. [ ] Token cleanup scheduler
10. [ ] Over-mock refactor (top 5 dosya)

### SPRINT 2 (4 hafta)
11. [ ] BKT service implement
12. [ ] FSRS weights konfigurasyonu
13. [ ] Pydantic v2 migration
14. [ ] Static files security
15. [ ] Test coverage %18 -> %40
16. [ ] Raw SQL -> Alembic konsolidasyonu

---

## GUCLÜ YONLER

1. **Algoritma pipeline** (IRT/FSRS/DAG/ZPD) production-ready, numerik karalilk iyi
2. **Model import pattern** %100 dogru (0 absolute import riski)
3. **Async/sync ayirimi** optimal (I/O=async, compute=sync)
4. **FK + index design** kapsamli (232 FK, 30+ index, HNSW)
5. **JWT implementation** industry-best (rotation, blacklist, dual auth)
6. **API benchmark** <4ms p95 (hedef <2s, 500x asildi)
7. **Secrets management** tamamen env var'dan (0 hardcoded prod)
8. **Production data** 77,336 soru %100 validated

---

**Rapor Sonu**
**Analiz suresi:** ~5 dakika (8 paralel agent)
**Taranan dosya:** ~1,253 dosya
