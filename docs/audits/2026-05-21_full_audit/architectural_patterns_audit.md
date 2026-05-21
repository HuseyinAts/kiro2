# KIRO2 Architectural Patterns + Design Approach Audit

## Executive Summary

**Detected style:** Pragmatic Layered Architecture with service-heavy bias (5 de-facto layers).

**Major architectural debt:**
- 8 confirmed wrong-direction imports (services → api schemas)
- BaseService ABC defined but inherited by 0 of 93 services
- In-memory OgretmenServisi still loaded in production router registry
- Two competing cache layers + two transaction conventions
- BKTService.record_answer = 250+ line god method (4 algorithm pipeline)
- 0 ADRs (substitute = CLAUDE.md hard rules)

## 1. Architecture Style (5 layers)

```
HTTP Layer    backend/api/         — FastAPI routers, schemas
Service Layer backend/services/    — Business operations
Domain Layer  backend/algorithms/  — Pure algos (IRT, FSRS, BKT)
Data Layer    backend/models/      — SQLAlchemy ORM, enums
Infrastructure backend/core/       — DB, cache, auth, middleware
```

## 2. Dependency Direction — VIOLATIONS

### Wrong-direction imports (services → api)

- `backend/services/diary_service.py:16` — `from api.schemas.diary`
- `backend/services/emotional_service.py:27` — `from api.schemas.diary`
- `backend/services/export_service.py:49` — `from api.schemas.diary`
- `backend/services/goal_service.py:15` — `from api.schemas.diary`
- `backend/services/insight_service.py:24` — `from api.schemas.diary`
- `backend/services/learning_journal_service.py:16` — `from api.schemas.diary`
- `backend/services/reflection_service.py:15` — `from api.schemas.diary`
- **`backend/services/learning_event_service.py:291` — `from api.gamification_api import calculate_level` (WORSE: imports function from router!)**

## 3. SOLID Compliance

| Principle | Compliance | Examples |
|---|---|---|
| **SRP** | MEDIUM | TeacherService god class; BKTService.record_answer 250+ lines |
| **OCP** | MEDIUM | OK: ResourceSearchStrategy ABC. BAD: soru_bankasi_service `_enum_donusturucu` |
| **LSP** | OK | YouTubeSearchStrategy/KhanSearchStrategy consistent |
| **ISP** | WEAK | BaseService ABC = 5 mixed concerns, **0 of 93 services inherit** |
| **DIP** | WEAK | Concrete AsyncSession via Depends, no Port/Adapter |

## 4. Anti-Patterns

| Pattern | Severity | Evidence |
|---|---|---|
| Service → api schema (wrong dir) | **HIGH** | 8 files |
| God method (4-algo pipeline) | MEDIUM | BKTService.record_answer 300+ lines |
| In-memory service in prod registry | **HIGH** | OgretmenServisi (deprecated=True still loaded) |
| Stringly-typed Turkish→UPPERCASE | **HIGH** | 30-entry _KONU_MAP + _SUBJECT_AREA_MAP + _SUBJECT_ID_MAP (3 duplicates) |
| Deprecated cache imported | MEDIUM | `core/redis_cache.py` DEPRECATED but imported by `api/health.py:16` |
| TR/EN dual routes | MEDIUM | /ogretmen/* + /teacher/* coexist |

## 5. Async Correctness

**Sync-in-async violations:** 12 files. Pattern A bug:
- `services/exam_answer_tracking_service.py`
- `services/soru_bankasi_service.py`

**Missing await (CRITICAL):** 3 sites in `api/encryption_management.py` — `session.commit()` without await = silent no-op (**NEVER COMMITS**).

**Two transaction conventions:**
- `Depends(get_db_session)` → DatabaseManager lifecycle
- `async with db_manager.get_session()` → 284 explicit `session.commit()` calls

## 6. Caching Strategy

3-layer cache exists but partial:
- `core/redis_cache.py` — sync, DEPRECATED (still imported)
- `core/cache/cache_manager.py` — async aioredis (CANONICAL)
- `core/multi_layer_cache.py` — L1 LRU(100) + L2 Redis

**Cache stampede protection:** NONE. Risk under 100K+ load.
**Event-driven invalidation:** unified_event_bus exists but NOT wired.

## 7. Frontend Architecture (OK)

5 Zustand stores + React Query for server state + useState local. httpOnly cookie auth migration complete.

## 8. Error Handling (mature)

`core/exceptions.py`: ServiceError → 14 subclasses, EnhancedServiceError with correlation_id, ErrorFactory.

BKT pipeline fault-tolerance: per-step errors dict accumulator → graceful degradation.

CI gate `audit_httpexception_guard.py` blocks rule-of-eight pattern.

## 9. CI/CD (unusually mature)

10 active + 18 archived workflows. 7 AST linters run before tests:
- dual-table, missing-auth, missing-is_active, missing-rate-limit, user_id type, HTTPException guard, db-dependency

## 10. ADR Status — MISSING

0 ADR files. Substitute = CLAUDE.md hard rules + .claude/rules/*.md + MEMORY.md sessions.

## P0 / P1 Findings

### P0 (architecture-level breaks)

- **AP-P0-1:** Service → API schema dependency cycle (7 services + 1 router function). Fix: move shared types to `schemas/` or `domain/` package outside api/.
- **AP-P0-2:** In-memory OgretmenServisi in router registry. Fix: DISABLED_ROUTERS.

### P1 (technical debt)

- BaseService unused by 93 services
- Two cache layers + deprecated still imported
- 3 duplicate Turkish→UPPERCASE maps
- 3 sites missing `await db.commit()` (silent no-op!)
- 12 files sync-in-async violation
- 0 formal ADRs
- BKTService.record_answer 300-LOC god method

## Essential Files

- `backend/core/application.py` — app factory
- `backend/routers/loader.py` — 150+ dynamic registry
- `backend/services/bkt_service.py` — 4-algo pipeline (god method)
- `backend/services/learning_event_service.py:291` (imports calculate_level from router)
- `backend/services/diary_service.py:16` (schema dependency)
- `backend/services/llm/base_llm_provider.py:55` — BEST practice example
