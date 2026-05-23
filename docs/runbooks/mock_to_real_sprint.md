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

## Day 3-4 (2026-05-25/26) — analytics.py (24 endpoints)

Pattern: snapshot existing mock response → implement real path → flip flag.

Endpoint groups (process by group, single PR per group):

- **Group A — Student analytics (5 endpoints)**: per-student dashboard data
- **Group B — Class analytics (4 endpoints)**: teacher dashboard
- **Group C — Admin dashboard (3 endpoints)**: system-wide metrics
- **Group D — Export endpoints (3 endpoints)**: PDF/Excel/CSV
- **Group E — Retention/web-vitals (2 endpoints)**: leave as-is (already real)
- **Group F — Helper functions (7 functions)**: refactor into shared module

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
