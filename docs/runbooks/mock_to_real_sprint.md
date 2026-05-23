# Mock-to-Real Sprint Runbook (S196)

**Sprint:** S196 (2026-05-23 → 2026-05-30, 5 day plan)
**Driver:** S180 audit P0 #3 — 38 mock endpoint canlıda, beta blocker
**Stack:** Lightweight JSON flag (`core/mock_endpoint_flags.py`) + pytest + syrupy
**Methodology:** Per-endpoint flag flip, Day-N implementation incremental

---

## Scope (38 endpoint)

| File | Mock Count | Day target |
|------|-----------:|-----------:|
| `backend/api/advanced_reports.py` | 5 | Day 2 |
| `backend/api/analytics.py` | 24 | Day 3-4 |
| `backend/api/content_management.py` | 9 | Day 5 |

## Day 1 (2026-05-23) ✅ COMPLETE

### Delivered

1. **`backend/core/mock_endpoint_flags.py`** — 60-line lightweight flag reader
   - `is_real_impl(name: str) -> bool` — single public API
   - JSON config at `backend/config/mock_endpoint_flags.json`
   - `MOCK_FLAGS_PATH` env override for tests
   - `lru_cache` — read JSON once per process
   - Corrupt/missing config → log warning + all-mock fallback (never crashes)

2. **`backend/config/mock_endpoint_flags.json`** — 10 initial flag slots, all `false`

3. **`backend/api/advanced_reports.py:343-422`** — pilot wiring for IRT analysis
   - `_get_irt_morfoloji_analizi()` is now a dispatcher
   - `_get_irt_morfoloji_analizi_mock()` — legacy hardcoded math (untouched logic)
   - `_get_irt_morfoloji_analizi_real()` — scaffold, raises `NotImplementedError`
   - Response envelope `computed_by` now reflects actual code path (`mock`/`real`)

4. **`backend/tests/unit/test_mock_endpoint_flags.py`** — 4 unit tests, all pass
   - Default mock path
   - Config flip via env var override
   - Corrupt JSON does not crash
   - **Day-1 guard**: production config all-false invariant

### Karpathy Discipline

- **No real implementation in Day 1**: scaffold + flag wiring + tests only.
  Real path lands when DB query design + integration test ready.
- **Flag default = false**: safe rollback. The frontend continues to receive
  `computed_by: "mock"` until Day 2 flips the flag.
- **Reused `feature_flags.py`?** No — that module is video-discovery enum-heavy.
  Mock-to-real sprint flips 38 endpoint slots; an enum maintenance burden
  outweighs the type safety.

---

## Day 2 (2026-05-24) — Plan

### IRT analysis real implementation

1. **Implement `_get_irt_morfoloji_analizi_real()`** at
   `backend/api/advanced_reports.py:343`
   - Replace `NotImplementedError` with DB query against `question_bank`
   - Filter by `subject_area` from `temel_sonuc.konu_performanslari`
   - Aggregate: `AVG(irt_difficulty)`, `AVG(irt_discrimination)`, `AVG(irt_guessing)`
     WHERE `is_active = TRUE`
   - 100% IRT param coverage already in DB (MEMORY: "IRT params coverage: 100%")
   - Replace hardcoded `morfoloji_faktoru` with Zemberek call (separate prep)

2. **Snapshot test** — `backend/tests/api/test_advanced_reports_irt.py`
   - Capture mock response shape with syrupy `--snapshot-update`
   - Assert real response **schema identical** (no new/missing keys)
   - Numeric values different (real DB vs hardcoded) — assert ranges, not equality

3. **Flag flip** — `backend/config/mock_endpoint_flags.json`:
   `"advanced_reports.irt_analysis": true`

4. **Smoke test** — curl/httpx against running server, assert
   `computed_by == "real"` and `irt_morfoloji_analizi.genel_istatistikler.ortalama_zorluk`
   within plausible bounds `[-3, 3]` (theta scale).

5. **Update Day 1 guard** — `test_production_config_defaults_all_mock` should
   exclude `advanced_reports.irt_analysis` from the all-false invariant.

### Remaining advanced_reports endpoints (4)

- ZPD recommendations — Day 2 afternoon (similar pattern)
- learning-style-analysis — Day 2 evening
- osym-ets-comparison — Day 2 evening
- _get_performance_trend helper — Day 3 morning

---

## Day 3 (2026-05-23) ✅ COMPLETE

### Delivered (4 _real impls in `advanced_reports.py`)

1. `_get_zpd_analizi_real` → `ZPDMaarifService.hesapla_turk_zpd()` per konu
2. `_get_hibrit_ogrenme_stili_analizi_real` → `LearningStyleService.detect_learning_style()`
3. `_get_osym_ets_karsilastirmasi_real` → weighted IRT aggregates via
   `_get_subject_irt_aggregate` + existing `_karsilastir_*` static helpers
   (intentionally skipped `OSYMBenchmarkComparator` — wrong abstraction;
   it scores AI-generated questions, not exam IRT params)
4. `_get_performance_trend_real` → `ExamPerformanceService._analyze_improvement_trends()`
   with TR localization (improving→yukselis) + 0-100→0-1 normalization

### Smoke test (real DB, 5/5 PASS)

- IRT: 184ms cold (slow query — see below)
- ZPD: real Vygotsky + Maarif calculation, optimal_zorluk=9.98 for 75% cohort
- LearningStyle: VARK + Felder profile created in `student_learning_profiles`
- OSYM-ETS: real IRT-driven thresholds
- PerfTrend: empty branch correct shape

### Day 3 follow-up: IRT slow query — Redis cache solution

EXPLAIN ANALYZE on `_get_subject_irt_aggregate` showed **184ms Parallel Seq
Scan** on 187K rows. Investigation:

- Pre-existing `idx_qb_cat_subject_active` uses `LOWER(subject_area::text)` —
  unusable for plain equality (case-convention requires UPPERCASE).
- Created `idx_qbank_subject_active_irt` (partial INCLUDE) — **planner refused**
  to use it. Root cause: 30% selectivity (MATEMATIK = 57K of 187K active rows)
  makes Bitmap Index Scan + heap fetch more expensive than Parallel Seq Scan
  in the cost model. Even forced index plan: 201ms (no improvement).
- **Dropped the index** (9MB waste with no benefit).
- **Added Redis cache @ 1h TTL** in `_get_subject_irt_aggregate`.
  - Cold: 458ms → Cache warm: **0.25–0.39ms** (1500-1800x speedup)
  - Cache footprint: ~3KB (12 subjects)
  - Invalidation risk: ~zero (IRT params change only on Curator UPDATE, rare)

This pattern (`cache_manager.get/set` with subject-scoped key) is the
template for any future IRT/aggregate hot-path.

---

## Day 4 (2026-05-24) — analytics.py (24 endpoints)

### Pre-work delivered (sprint start)

- **9 analytics.* flag entries** added to `mock_endpoint_flags.json` (8 false
  + `analytics.d7_retention: true`)
- **`get_d7_retention` tagged with `computed_by`** — it was already
  DB-backed (not a hardcoded mock); flag flip just signals provenance.

### Tier-1 pilot targets (Day 4 morning, easy complexity)

| Function | Lines | Real candidate | Flag |
|---|---|---|---|
| `_get_exam_statistics` | 1035-1049 | `exam_session` COUNT/AVG grouped by exam_type | `analytics.exam_statistics` |
| `_get_class_students` | 833-846 | `student_profiles` JOIN `class_membership` | `analytics.class_students` |

### Tier-2 (Day 4 afternoon, medium complexity)

| Function | Lines | Real candidate |
|---|---|---|
| `_calculate_student_performance_metrics` | 678-697 | `exam_session.score` AVG + `student_answer` COUNT WHERE correct |
| `_get_exam_performance_analysis` | 730-754 | `exam_session` JOIN `question_bank` grouped by exam_type |
| `_get_subject_performance_analysis` | 757-793 | `student_answer` JOIN `question_bank` grouped by subject |
| `_calculate_class_metrics` | 849-869 | Aggregate Tier-1 student metrics over class |
| `_get_user_statistics` | 1011-1032 | `users` COUNT by role + registration/last_login filters |
| `_get_content_usage_statistics` | 1052-1081 | `video_analytics`, `content` tables |

### Tier-3 — DEFERRED (hard / blocked by missing tables)

- `_get_learning_style_analysis` — requires ML model or pre-computed profile
- `_get_detailed_student_analysis` — time-of-day bucketing + feature tables
- `_get_class_learning_style_distribution` — aggregate profiles over class
- `_calculate_system_metrics`, `_get_system_performance_metrics` — APM tools
- `_get_revolutionary_features_usage` — feature-flag event log table missing

### Code duplication finding

`_get_system_performance_metrics`, `_get_revolutionary_features_usage`,
export helpers, and PDF/Excel/CSV generators appear **twice** in
`analytics.py` (lines 1084-1163 & 1371-1450, then 1401-1672). Dedupe
before flag integration to avoid double-dispatcher confusion.

---

## Day 5 (2026-05-27) — content_management.py (9 endpoints)

CRUD endpoints with hardcoded mock responses. Pattern:
- `POST /questions` → real `QuestionService.create()`
- `GET /questions/{id}` → real `QuestionRepo.get_by_id()`
- `GET /search` → existing `elasticsearch_service.search_questions()`

Easier than analytics — CRUD already has service-layer scaffolding.

---

## Final Day Checklist

- [ ] All 38 flags flipped to `true` in `mock_endpoint_flags.json`
- [ ] No `computed_by: mock` markers in production responses (grep guard in CI)
- [ ] 100+ snapshot tests passing (`pytest backend/tests/api/`)
- [ ] Schemathesis contract test gate in CI (`.github/workflows/contract.yml`)
- [ ] Sprint retrospective at `docs/sprints/S196_retrospective.md`

---

## Rollback Procedure

Any endpoint exhibiting prod issue:

1. Edit `backend/config/mock_endpoint_flags.json` → flip the flag to `false`
2. Service restart (config loaded via `lru_cache`, reload required)
3. Endpoint reverts to mock path within seconds — frontend sees
   `computed_by: "mock"` immediately and suppresses display per S180 contract

No DB rollback needed — flag only routes code paths, no schema changes.

---

## Why this design (Karpathy "önce sadelik")

| Alternative | Why rejected |
|---|---|
| LaunchDarkly | $72K/yr, external dependency, 38 flags don't justify SaaS |
| GrowthBook self-hosted | Mongo + Node app to manage 10 boolean flags, overkill |
| `fastapi-featureflags` pip lib | Decorator-based, requires endpoint annotation rewrite |
| Existing `core/feature_flags.py` (enum) | Video-discovery scoped, 19 enum slots + dataclasses; 38 new enum entries adds maintenance burden |
| **`mock_endpoint_flags.py` (60 lines, JSON file)** | Single function, single config file, zero deps, hot-swappable for tests |

If/when KIRO2 graduates to A/B testing or gradual rollout
(>50 concurrent flags), revisit. For "mock-to-real over 5 days", this is the
pareto-optimal point.
