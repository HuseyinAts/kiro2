# KIRO2 Test Coverage Deep Audit

**Tarih:** 2026-05-21
**Branch:** master
**Coverage tool:** coverage 7.13.1 + pytest-cov 7.0.0
**Test discovery:** 663 test files in `backend/tests/`
**Source codebase:** 614 modules / 245,036 LOC in `api/services/core/algorithms`

## TL;DR (Executive Summary)

| Iddia (CLAUDE.md) | Gerçek | Delta |
|---|---|---|
| Backend ~%53 statement coverage | **16.64%** (curated, fail-free 20-file run) — `coverage_full.json` | -36pp |
| Backend test results "12,607 passed, 7 collection errors" | tests/unit/ alone: **5,612 passed / 430 failed / 70 errors** (8% failure rate in passing-not-skipped subset) | Health much worse than advertised |
| TDD adherence "ZORUNLU" (CLAUDE.md) | **4 / 30** recent `fix` commits include test files (13%) | Process broken |
| `core/csrf_protection.py` (GF99 regression site) | **0 direct unit tests, 46.99% coverage incidental** | Regression risk reborn |
| 5 critical middleware modules | `auth_middleware`, `security_middleware`, `unified_auth_service`, `csrf_protection` middleware path, `turkish_exam_middleware` = **0.00%** coverage | Catastrophic gap |
| `core/osym_exam_engine.py` | 572 stmts, **14.72%** cov. All 39 integration tests `skipif(True, "ExamType not imported...")` | Entire engine untested |
| Mock density | One test file with **240 mocks** (`test_api_coverage_batch13.py`) — 7,559 mock occurrences total | Tests test the mocks, not the code |

**The honest headline:** The reported %53 is not reproducible. The actually-measured coverage on a clean run is %16.64. The remainder appears to come from either (a) tests that fail/error but still execute lines (counted) or (b) instrumented runs that include long-dead test files. Either way, the **effective behavioral coverage is much worse than the percentage suggests** because thousands of tests assert on inline-constructed data, not on production modules.

---

## 1. Per-module coverage matrix (critical paths)

Measured by running 20 representative tests (`test_bkt_service`, `test_p0_algorithms`, `test_curator_api`, `test_irt_*`, `test_ml_regression`, `test_question_bank`, `test_security_hardening`, `test_sinav_motoru_*`, `test_smoke_api_critical`, `test_bkt_zpd_static_methods`, `test_irt_validators`, `test_core_dependencies`, `test_fsrs_system`, `test_turkish_fsrs_system`, `test_turkish_zpd_maarif_system`, `test_zpd_maarif_service`) with `--cov=api --cov=services --cov=core --cov=algorithms --cov-branch`. 445 PASS, 1 FAIL, 107 SKIP, 95s wall.

### Critical modules (user-specified)

| Module | Stmts | Cov% | Branch% | Miss | Verdict |
|---|---:|---:|---:|---:|---|
| `algorithms/irt_model.py` | 114 | **95.4%** | 81.3% | 3 | Excellent. IRT 4PL covered. Lines 159, 165, 176 — boundary conditions worth filling. |
| `services/bkt_service.py` | 170 | 44.7% (90.3% with batch1b/zpd_static) | 66.7% | 102 | BKT core OK on dedicated tests. Combined-run regression: lines 264-268, 398-406, 432-434 (slug fallback paths, record_answer error branches). |
| `algorithms/turkish_optimized_fsrs.py` | 276 | **87.7%** | 82.7% | 29 | Good. Holes: 317-326 (state-dirty branch), 389-397 (Turkish optimization path), 562-576 (Turkish-specific scheduler). |
| `algorithms/turkish_zpd_maarif_system.py` | 265 | **97.6%** | 90.6% | 2 | Excellent. Only 440-441 (defensive raise). |
| `services/zpd_maarif_service.py` | 338 | **72.6%** | 72.8% | 93 | OK. Big holes: 814-844, 860-891, 904-930, 939-955, 964-980, 989-1033 (analytics/reporting block — likely orchestrator path). |
| `core/dependencies.py` | 148 | **83.0%** | 82.5% | 25 | Good. Holes: 197-200 (token verification fallback), 264-276 (`require_role` admin path), 301-348 (a cluster of guard helpers). |
| `core/csrf_protection.py` | 61 (subset) / 202 total | **46.99%** | 27.3% | 28 | **CRITICAL GAP.** Module imported only incidentally. ZERO test file imports it. GF99 regression class has no test. |
| `api/curator.py` | 148 | **78.7%** | 50.0% | 24 | Good unit-level. Holes: 136-147 (verdict status mapping), 316-325 (queue filter combos), 421-424 (stats edge cases). |
| `core/osym_exam_engine.py` | **572** | **14.7%** | 0.0% | 461 | **CATASTROPHIC.** 39 tests in `test_osym_exam_engine.py` all `skipif(True, reason="ExamType not imported (models.database mocked at module level, NameError: ExamType not defined)")`. Module loaded only via import side-effects. |
| `api/learning_path_v2.py` | **698** | **19.3%** (39.3% from `test_api_coverage_batch*`) | 2.0% | 537 | **CRITICAL.** The supposed unit tests at `tests/unit/api/test_learning_path_route.py` are FAKE — they assert on dict literals, never import the module. See section 5. |
| `services/irt_service.py` | 250 | 11.8% | 0.0% | 210 | **High risk.** Only 1 integration test referencing it, mostly skipped. 771 LOC service unit-tested by none. |
| `services/irt_service_3pl.py` | 58 | **94.4%** | 85.7% | 2 | Excellent. |
| `core/unified_auth_service.py` | **397** | **0.0%** | 0.0% | 397 | **CATASTROPHIC.** JWT issuance, refresh-token rotation, blacklist Redis logic — completely untested. |
| `core/auth_middleware.py` | **405** | **0.0%** | 0.0% | 405 | **CATASTROPHIC.** Entire middleware path untested. |
| `core/security_middleware.py` | **455** | **0.0%** | 0.0% | 455 | **CATASTROPHIC.** |
| `core/turkish_exam_middleware.py` | **462** | **0.0%** | 0.0% | 462 | **CATASTROPHIC.** |
| `api/auth.py` | 496 | 25.3% | 5.7% | 350 | Sparse. Holes: 154-218 (`mevcut_kullanici_getir` JWT decode + cookie fallback), 229-311 (`database_authenticate`), 650-714 (secure_login / secure_logout), 732-771 (secure_refresh), 1538-1671 (refresh_token / logout_all_devices / revoke_device). |

### Top 30 by absolute uncovered LOC (>=100 stmts)

| Module | Stmts | Cov% | Missing |
|---|---:|---:|---:|
| services/alternative_solutions_service.py | 699 | 5.2% | 647 |
| api/learning_path_v2.py | 698 | 19.3% | 537 |
| core/message_queue_system.py | 518 | 0.0% | 518 |
| services/soru_bankasi_service.py | 560 | 6.9% | 511 |
| core/realtime_notification_system.py | 463 | 0.0% | 463 |
| core/turkish_exam_middleware.py | 462 | 0.0% | 462 |
| core/osym_exam_engine.py | 572 | 14.7% | 461 |
| core/kvkk_compliance.py | 459 | 0.0% | 459 |
| core/security_middleware.py | 455 | 0.0% | 455 |
| core/auth_security_utils.py | 454 | 0.0% | 454 |
| core/security_event_monitoring.py | 425 | 0.0% | 425 |
| services/visual_content_generator.py | 407 | 0.0% | 407 |
| core/auth_middleware.py | 405 | 0.0% | 405 |
| core/unified_api_gateway.py | 405 | 0.0% | 405 |
| core/unified_auth_service.py | 397 | 0.0% | 397 |
| core/unified_event_bus.py | 390 | 0.0% | 390 |
| core/middleware_pipeline.py | 386 | 0.0% | 386 |
| api/analytics.py | 466 | 15.7% | 383 |
| core/account_security.py | 381 | 0.0% | 381 |
| core/enhanced_authentication.py | 596 | 30.5% | 372 |
| core/rag_service.py | 410 | 8.5% | 365 |
| core/curriculum_compliance_system.py | 396 | 7.6% | 357 |
| core/learning_analytics.py | 355 | 0.0% | 355 |
| core/sso_saml_service.py | 355 | 0.0% | 355 |
| core/background_job_processor.py | 351 | 0.0% | 351 |
| api/auth.py | 496 | 25.3% | 350 |
| core/query_builder.py | 472 | 20.3% | 350 |
| services/question_crud_service.py | 378 | 6.3% | 347 |
| core/unified/session_system.py | 343 | 0.0% | 343 |
| services/geometry_generator.py | 339 | 0.0% | 339 |

### Per-category weighted coverage (curated 20-file run)

| Category | Files | Stmts | Weighted Cov |
|---|---:|---:|---:|
| api/ | 146 | 23,938 | **32.9%** |
| services/ | 188 | 29,217 | **11.8%** |
| core/ | 231 | 42,466 | **11.6%** |
| algorithms/ | 13 | 2,710 | **30.7%** |
| **TOTAL** | 578 | 98,331 | **16.6%** |

> **Caveat:** This is the coverage from a 20-file fail-free curated run. The 53% claim in CLAUDE.md likely comes from running the *entire* `tests/` directory including the 430 failing and 70 erroring tests in `tests/unit/` — line execution is still counted under coverage even when the test fails. That number is technically valid but operationally misleading.

---

## 2. Critical paths uncovered (regression risk catalog)

### 2.1 `core/osym_exam_engine.py:281-1699` — 461 lines, 14.72% cov, 0% branch
**Risk:** Exam scheduling, answer key resolution, scoring weights — the engine that decides what a student sees and how it's graded.
**Why uncovered:** `tests/integration/test_osym_exam_engine.py:55` carries `@pytest.mark.skipif(True, reason="ExamType not imported (models.database mocked at module level, NameError: ExamType not defined)")`. The skip note has not been resolved. All 39 tests defined under it never run.
**Concrete regression scenario:** Question-skip-permitted exams without preferred subject (Turkish AYT) — line range 685-754 (`_select_questions_with_preferences`) — could silently swap subject buckets, causing students to see wrong question groups. Production-visible, no test catches it.

### 2.2 `core/unified_auth_service.py` — 397 lines, 0.0%
**Risk:** JWT issuance, refresh token rotation, Redis blacklist, session management.
**Why uncovered:** No test file imports it. The `core/auth_security_utils.py` (454 LOC, also 0%) sits alongside.
**Concrete regression scenario:** A refresh-token rotation bug could allow indefinite session extension (no blacklist on rotation). Or a Redis outage could downgrade auth to "always succeed" instead of "always fail". Neither tested.

### 2.3 `core/auth_middleware.py` (405) + `core/security_middleware.py` (455) — 0.0% each
**Risk:** Auth check ordering, CORS preflight bypass paths, security header injection.
**Why uncovered:** No test exercises the middleware as a unit. Integration tests that *would* exercise them are mostly `skipif(True, ...)` due to httpx ASGITransport migration.
**Concrete regression scenario:** Same class as GF99 (raise vs return). 8 separate test files carry `pytestmark = pytest.mark.skipif(True, reason="AsyncClient(app=...) deprecated in httpx 0.27+ (needs ASGITransport)")`. The httpx migration was *partial* — these files never came back.

### 2.4 `core/csrf_protection.py` — 0 direct unit tests
**Risk:** Same GF99 class. Re-introduction of `raise HTTPException(403)` inside middleware dispatch would surface as 500 again.
**Why uncovered:** `tests/integration/test_critical_security.py:168-189` *redefines* `generate_csrf_token` and `validate_csrf_token` inline (using `secrets.token_urlsafe(32)` and `==` comparison) and asserts on the **inline implementation**, not on `core/csrf_protection.py`. This is a textbook fake test.
**Concrete regression scenario:** Any developer reintroducing the GF99 `raise HTTPException` pattern in middleware. Current safeguard: the rule in `.claude/rules/middleware.md`. No CI gate. No unit test.

### 2.5 `api/learning_path_v2.py:304-2163` — 537 lines uncovered
**Risk:** The core daily learning path endpoint set. 5 of the 8 read-path Golden Flows touch this.
**Why uncovered:** The 6 files named `test_learning_path_*` in `tests/unit/` test (a) JWT helpers, (b) cold-start fallback logic in isolation, (c) auth role string handling, or (d) **inline dict literals** (`tests/unit/api/test_learning_path_route.py` — see section 5 for a verbatim excerpt). They do NOT import `api.learning_path_v2`. The functions in `tests/fast/test_api_coverage_batch6/7/9/13/14.py` do exercise it (39.3% in isolation), but those tests have 4 failures.
**Concrete regression scenario:** `_recommend_next_topic_v2` (range 869-875) or `_generate_daily_schedule` (range 1320-1433) silently returning empty list on edge case (no theta_se, no DAG, cold-start fallback fails). User sees empty path, no error.

### 2.6 `services/alternative_solutions_service.py` — 699 stmts, 5.2% cov
**Risk:** "Alternative solution generation" — student-facing feature.
**Why uncovered:** Test exists at `tests/test_alternative_solutions.py` (not in subset), but coverage on it would need to be measured.

### 2.7 `services/soru_bankasi_service.py` — 560 stmts, 6.9% cov
**Risk:** The main question-bank service. Question filtering, IRT-weighted selection, exam composition.
**Why uncovered:** Has `tests/unit/test_soru_bankasi_service.py` (mentions "NO assert True / assert False patterns" in its preamble — good intent), but apparently mocked deeply enough that real lines aren't hit.

---

## 3. Test smell detection (concrete counts)

### 3.1 Mock density per file (top 20)

| File | Mock count (`MagicMock`/`AsyncMock`/`@patch`) |
|---|---:|
| tests/fast/test_api_coverage_batch13.py | **240** |
| tests/unit/test_coverage_final_push2.py | 209 |
| tests/unit/test_auth_coverage.py | 200 |
| tests/unit/test_zero_cov_batch4.py | 198 |
| tests/unit/test_api_batch2.py | 197 |
| tests/fast/test_api_coverage_batch14.py | 192 |
| tests/unit/test_coverage_final_push.py | 164 |
| tests/unit/health/test_database_health.py | 120 |
| tests/unit/test_sinav_api.py | 113 |
| tests/unit/test_core_database_coverage.py | 112 |

**Interpretation:** A test file with 240 mocks is no longer testing behavior — it's testing that the mocked-out collaborators are called with the expected arguments. The file names (`coverage_final_push*`, `zero_cov_batch4`, `api_coverage_batch*`) reveal these were written to *raise the coverage number*, not to catch regressions. **These are coverage-hacking tests.** When the underlying API changes, they fail (which is why we see 430 unit-test failures in section 1).

**Action:** Audit and quarantine the 10 files above (1,945 mocks combined). Replace coverage they're "claiming" with thinner integration tests against real collaborators where possible (curator pattern works well — see `tests/test_curator_api.py`).

### 3.2 Vacuous assertions (`assert len(x) >= 0`)

19 instances. Files:
- `tests/db/test_pre_migration.py:205`
- `tests/fast/test_api_coverage_batch7.py:42`
- `tests/fast/test_core_assessment_system.py:114`
- `tests/fast/test_enum_instantiation.py:90`
- `tests/functional/test_learning_path_full.py:50`
- `tests/integration/test_algorithms.py:135`
- `tests/integration/test_claude_md_improvement_e2e.py:593`
- `tests/integration/test_database_operations.py:47`
- `tests/integration/test_phase2_api_optimizer.py:768`
- `tests/integration/test_real_database_operations.py:52`
- (+ 9 more)

These are equivalent to `pass`. Action: either replace with meaningful assertion or delete the test.

### 3.3 Blanket `skipif(True, ...)` patterns

| Count | Reason snippet |
|---:|---|
| **111** | `pytest.skip(...allow_module_level=True)` module-level skips |
| **65** | `@pytest.mark.skipif(True, reason="...")` decorator skips |

Top reasons (module-level):
| Count | Reason |
|---:|---|
| 30 | Deprecated module — see _deprecated/ (LEGITIMATE) |
| 18 | Heavy imports (from main import app) cause 10+ second timeout |
| 16 | Module has import errors or API changes - skip to prevent collection failure |
| 13 | Test requires running server or has heavy imports that timeout |

Top reasons (decorator):
| Count | Reason |
|---:|---|
| 8 | AsyncClient(app=...) deprecated in httpx 0.27+ (needs ASGITransport) |
| 4 | Password validator rejects sequential characters - fixture password fails validation |
| 2 | LogEntry model API changed |
| 2 | Requires running Redis |

**Interpretation:** The 8 httpx-skip files are a partial migration. They're not deprecated, just blocked on a single technical change. The 16 "API changes" files indicate test rot — source moved, tests didn't.

### 3.4 Skip distribution by tier

| Tier | skipif/skip count |
|---:|---|
| tests/unit/ | 39 |
| tests/integration/ | 413 |
| tests/slow/ | 153 |

The integration tier carries most of the rot. Most of the auth/middleware critical paths can only be exercised at integration tier — and that tier is the most-skipped.

### 3.5 `assert True` / `assert 1 == 1`

Direct false positives are minimal. Almost all occurrences are inside `tests/hooks/reward_hacking/` (the detector's own test fixtures — *they need to contain the pattern they detect*). The codebase actively guards against this anti-pattern. Good.

---

## 4. Mutation testing assessment

`mutmut 3.5.0` is installed locally. `cosmic-ray` is not.

### Recommended mutation testing candidates (high coverage + complex logic)

| Module | Cov% | Why it's a good mutation target |
|---|---:|---|
| `algorithms/irt_model.py` | 95.4% | Logistic 4PL formula, validators. Mutating `1 - c` → `c` in the 4PL response equation should be caught. |
| `algorithms/turkish_zpd_maarif_system.py` | 97.6% | ZPD thresholds, retention curves. Sign-flip mutations on `lower_bound` checks. |
| `algorithms/turkish_optimized_fsrs.py` | 87.7% | FSRS interval/ease updates. Mutating `factor * delta` → `factor / delta` would alter scheduling, must be caught. |
| `services/irt_service_3pl.py` | 94.4% | 3PL discrimination/difficulty calc — short, dense math. |
| `core/dependencies.py` | 83.0% | Auth dependency tree — mutate `role == required` → `role != required`. |

**Sample mutations to seed the suite:**
1. `services/bkt_service.py:107` — `posterior = p_L_given_correct` → `posterior = 1 - p_L_given_correct` (sign-flip mastery update)
2. `algorithms/irt_model.py:73` — `return c + (1 - c) / (1 + np.exp(...))` → `return c + c / (1 + np.exp(...))` (drop `(1-c)` factor — should fail test)
3. `services/zpd_maarif_service.py:343-347` — currently uncovered; mutation here would not be caught (zero-coverage mutation flag)

**Cost estimate:** Running mutmut on `algorithms/` + `services/bkt_service.py` + `services/irt_service_3pl.py` (≈900 LOC combined, ~95% coverage) — about 400 mutants, ~2 hours wall on a 4-core machine using the existing test suite.

**Do not mutmut yet:** Modules at <50% coverage will spawn thousands of survived mutants and tell you nothing new. Mutation testing is only informative on >80%-cov targets.

---

## 5. Concrete fake-test evidence

### 5.1 `tests/unit/api/test_learning_path_route.py` — entire file is fake

The file lives at the exact path you'd expect to test `api.learning_path_v2`. It has 4 PASSED test functions. It imports nothing from the production module.

```python
"""
Unit tests for learning path routes (UT-03.4).

Tests learning path endpoint data structures and validation.
NO REWARD HACKING - All assertions must be meaningful.
"""
from __future__ import annotations
import pytest

@pytest.mark.asyncio
async def test_create_profile_request():
    """Create profile request must have student data."""
    request = {
        "name": "Ahmet Yilmaz",
        "grade": 11,
        "subjects": ["matematik", "fizik"],
        "learning_style": "visual",
    }
    assert request["grade"] in range(9, 13)
    assert len(request["subjects"]) >= 1
    assert request["learning_style"] in ("visual", "auditory", "kinesthetic", "mixed")
```

The test asserts on a dict the test itself just constructed. The production endpoint, the Pydantic schema, the route handler — none of them are involved.

**Smell:** the docstring says "NO REWARD HACKING - All assertions must be meaningful". This is anti-reward-hacking theater. **Delete this file entirely.** Replace with a thin TestClient request against the real router.

### 5.2 `tests/integration/test_critical_security.py:168-189` — CSRF self-test

```python
def test_csrf_token_generation(self):
    """Test CSRF token generation and validation"""
    def generate_csrf_token() -> str:
        return secrets.token_urlsafe(32)
    def validate_csrf_token(provided_token: str, stored_token: str) -> bool:
        return hmac.compare_digest(provided_token, stored_token)
    token1 = generate_csrf_token()
    token2 = generate_csrf_token()
    # ...
```

This is a test of Python's `secrets` and `hmac` modules. It does not import `core.csrf_protection` and would not catch any of the GF99 class of bugs.

---

## 6. Test infrastructure audit

### 6.1 Fixture scope

| Scope | Count |
|---|---:|
| function (default) | ~1058 |
| module | 17 |
| session | 11 |

Healthy distribution. `tests/conftest.py:241` has a `session, autouse=True` `worker_id` fixture supporting pytest-xdist parallel runs. Good.

### 6.2 Conftest count

10 `conftest.py` files (root + tests/ + 8 subdirectories). Some specialized:
- `tests/conftest.py` — main fixtures
- `tests/conftest_postgres.py` — Postgres-specific (NOT auto-loaded — requires explicit `pytest -p tests.conftest_postgres`)
- `tests/conftest_security.py`, `tests/conftest_testcontainers.py` — same caveat

**Risk:** Three conftest files starting with `conftest_` rather than overriding `conftest.py` means most test runs won't pick them up. If those fixtures contain critical setup (e.g., truncate-between-tests DB isolation), tests are running without it. Verify whether their fixtures are imported elsewhere or quietly orphaned.

### 6.3 pytest-xdist readiness

- `pytest-xdist` installed.
- `worker_id` fixture exists.
- Test database URL is parametrized per-worker (`./test_{db_name}.db`).
- **Risk:** SQLite file per worker — fine for unit tests, but no PostgreSQL parallel setup. Integration tests cannot parallelize on real DB without per-worker schemas.

### 6.4 Environment hardening (`tests/conftest.py:7-26`)

Good practice: HF_HUB_OFFLINE, TRANSFORMERS_OFFLINE, JWT_SECRET, REDIS_URL all set at module level *before* any imports. Windows SelectorEventLoopPolicy set early. This is correct.

### 6.5 Mock cleanup

The 240-mock files use `@patch` decorators (auto-cleanup). No explicit `patch.stop()` violations found. However, `monkeypatch` is used in many places and is auto-undone. Infrastructure is correct, but the *quantity* of mocking is the concern (section 3.1).

### 6.6 Test isolation

- SQLite in-memory by default (`sqlite+aiosqlite:///:memory:`) — strong isolation.
- No truncate-between-tests fixture observed in root conftest — relies on in-memory rebuild per session.
- 70 collection-time ERRORS in `tests/unit/` (from broad run) suggest some tests have side-effect imports that interfere with each other.

---

## 7. TDD adherence (commit pair analysis)

Sampled 30 most recent `fix` commits (since 2026-04-01):

| Commit pattern | Count |
|---|---:|
| `fix(...)` commit with **0 test files** changed | **26** (87%) |
| `fix(...)` commit with `tests/` files changed | 4 (13%) |

Sample of fix-without-test commits:
- `d376b22ee fix(image-match): final residual cleanup — strict NEAR + 0 residual` — 0 tests
- `23bfcf99a fix(image-match): iterative cleanup — 64,451 wrong rollback + re-match` — 0 tests
- `655d08bea fix(image-match): root cause + deterministic exhaustion (v5/v6/v7)` — 0 tests
- `baaf984de fix(image-match): audit + rollback — v4 full rollback, v1 conditional 37,869 rollback` — 0 tests

CLAUDE.md / `.claude/rules/debugging-first.md` and `.claude/rules/verification.md` mandate **TDD bug fix (ZORUNLU)**: fail-test-first, fix, re-test, commit. **The discipline is not being followed.** Either the rule should be enforced (pre-commit hook checking `fix(*)` commits for paired `tests/` changes) or relaxed in writing.

> **Caveat:** A few of these commits are data-pipeline operations (image-match, beta-cleanup) where test pairing is genuinely unusual. But even setting those aside, the rate is low.

---

## 8. Tests with no real production code (dead tests)

Beyond section 5's fake tests, the following pattern repeats: tests of functions that don't exist or were moved.

### 8.1 Examples

- `tests/integration/test_background_job_processor.py` — `skipif(True, reason="Mock API mismatches real module: QueueType values differ, BackgroundJobProcessor/JobScheduler/JobMonitor not exported")`
- `tests/integration/test_content_models.py` — `skipif(True, reason="Content model schema changed")`
- `tests/integration/test_core_cache.py` — `skipif(True, reason="CacheManager API changed")`
- `tests/integration/test_core_config.py` — `skipif(True, reason="Settings API changed")`
- `tests/integration/test_core_database.py` — `skipif(True, reason="DatabaseManager API changed")`
- `tests/integration/test_core_dependencies.py` — `skipif(True, reason="Dependencies API changed")` (29 tests dormant)
- `tests/integration/test_core_services.py` — `skipif(True, reason="LLMService API changed")`

These are not deprecated *features* — they're deprecated *tests*. The features still exist. The tests just don't compile against the current API. They take up directory space, inflate the test-file count (663), and create the illusion of coverage.

**Action:** For each `skipif(True, "API changed")` block: either fix the test (preferred, since the feature still ships) or delete the file. Don't leave them as cargo-cult skeletons.

---

## 9. Concrete sprint plan — top 10 modules for next coverage sprint

Ranked by `(missing_lines × production_criticality)`, with concrete entry points.

### Tier P0 (security/auth — must be tested before MVP launch)

1. **`core/csrf_protection.py`** (202 LOC, ~47% incidental cov, 0 direct tests)
   - Add `tests/unit/core/test_csrf_protection.py`.
   - Tests: middleware `dispatch()` returns 403 (not 500) on missing token; Bearer-auth requests early-return; cookie/header token mismatch returns 403.
   - GF99 regression test: middleware never propagates raised HTTPException as 500.
   - **Cost: ~20 LOC test code, ~1 hour.**

2. **`core/dependencies.py:264-348` (auth guard cluster)** (current 83%, push to 95%)
   - `require_role`, `require_admin`, refresh-token edge cases.
   - **Cost: ~30 LOC, ~1.5 hours.**

3. **`core/auth_middleware.py`** (405 LOC, 0%) + **`core/unified_auth_service.py`** (397 LOC, 0%)
   - Pair these. Test issuance + verification round-trip. Test Redis blacklist insert/check. Test refresh rotation invalidates old refresh.
   - **Cost: ~200 LOC test code, ~6 hours.**

### Tier P1 (production-critical exam path)

4. **`core/osym_exam_engine.py`** (572 LOC, 14.7%)
   - Unskip `tests/integration/test_osym_exam_engine.py` (resolve the `ExamType` import issue — likely 30-min fix at top of file).
   - **Cost: ~2 hours to unskip, then existing test suite kicks in (39 tests dormant).**

5. **`api/learning_path_v2.py:854-1433` (recommendation + scheduling)** (39.3% → target 70%)
   - Delete `tests/unit/api/test_learning_path_route.py` (fake).
   - Add real route tests via TestClient + DB mock (curator pattern).
   - **Cost: ~120 LOC, ~4 hours.**

6. **`services/soru_bankasi_service.py`** (560 LOC, 6.9%)
   - The main question-bank service. Test `get_questions_by_filter` with realistic filters (subject_area, exam_type, is_active=True, difficulty range).
   - **Cost: ~80 LOC, ~3 hours.**

### Tier P2 (high-volume code paths)

7. **`api/auth.py:154-771`** (496 LOC, 25.3%) — login, refresh, secure_logout
   - `tests/unit/test_auth_coverage.py` has 200 mocks. Replace with thinner real-router tests.
   - **Cost: refactor, ~6 hours.**

8. **`services/alternative_solutions_service.py`** (699 LOC, 5.2%)
   - Service exists; tests don't. Add a thin happy-path + 2 edge-cases.
   - **Cost: ~60 LOC, ~2.5 hours.**

9. **`api/sinav.py`** (435 LOC, 0% in the curated run)
   - Exam UI/endpoint. Cross-reference with `core/osym_exam_engine.py` work.
   - **Cost: ~60 LOC, ~2 hours.**

10. **`services/irt_service.py`** (771 LOC, 11.8%)
    - 4 mentions in `tests/`. Likely orphaned. If still used, build out from `tests/test_irt_service_3pl.py` pattern (94.4% cov, 13 dense tests).
    - **Cost: ~50 LOC, ~2 hours.**

### Sprint summary

| Tier | Modules | Estimated LOC test code | Estimated wall time |
|---|---:|---:|---:|
| P0 | 4 | ~250 | ~10 hours |
| P1 | 3 | ~200 | ~9 hours |
| P2 | 4 | ~250 | ~12.5 hours |
| **Total** | **11** | **~700** | **~32 hours** |

Realistic 1-developer sprint: **2 weeks** assuming P0/P1 fixed, P2 partial. Coverage uplift estimate: from ~17% (curated) to ~28% (curated) on the critical risk surface. Far more important than the percentage: the GF99 class of regressions, the 0% auth middleware, and the 39 dormant exam-engine tests get permanently closed.

---

## 10. Recommendations beyond coverage %

1. **Quarantine coverage-hacking tests.** Files matching `*coverage*push*.py`, `*zero_cov_batch*.py`, `*api_coverage_batch*.py` should be reviewed file-by-file. Many are pure mock theater. Coverage measured *after* deleting them is more honest.

2. **Add a CI gate on TDD adherence.** Pre-commit hook: if commit subject starts with `fix(...):`, require at least one file changed under `backend/tests/`. Skip allowed via `[skip-test-pair]` in commit body (used judiciously).

3. **Resolve the 8 httpx ASGITransport skips.** All carry the same skip reason; one PR fixes them all and restores ~150+ integration tests.

4. **Stop counting failed tests in coverage.** When `tests/unit/` has 430 failures, those tests still execute lines and the coverage tool counts them. Configure CI to fail-fast on test failures *before* generating the coverage report, so the percentage reflects only passing tests.

5. **Mutation-test the algorithms tier.** `algorithms/` has 4 modules at >87% coverage. Run `mutmut` against this tier as a baseline, then re-run after each subsequent sprint. This will catch the "tests don't actually assert the right invariant" class of bug.

6. **Audit conftest_*.py files.** Confirm `conftest_postgres.py`, `conftest_security.py`, `conftest_testcontainers.py` are actually loaded by some test run path. If orphaned, either rename them to `conftest.py` in a subdirectory or delete.

7. **Decide and document the source-of-truth coverage number.** CLAUDE.md says ~53%. Our measurement says 17% on a clean fail-free run. Pick the methodology, publish the exact command in CLAUDE.md, and stop reporting different numbers.

---

## Appendix A — Reproducibility

The curated coverage measurement that produced section 1 numbers:

```bash
cd backend
rm -f .coverage coverage_full.json
python -m pytest \
  tests/test_bkt_service.py \
  tests/test_p0_algorithms.py \
  tests/test_curator_api.py \
  tests/test_irt_service_3pl.py \
  tests/test_ml_regression.py \
  tests/test_question_bank.py \
  tests/test_security_hardening.py \
  tests/test_sinav_motoru_part2.py \
  tests/test_sinav_motoru_part3.py \
  tests/test_sinav_motoru_service.py \
  tests/test_smoke_api_critical.py \
  tests/unit/test_bkt_zpd_static_methods.py \
  tests/unit/test_irt_validators.py \
  tests/unit/algorithms/test_irt_boundaries.py \
  tests/unit/services/test_irt_service.py \
  tests/unit/test_core_dependencies.py \
  tests/integration/test_fsrs_system.py \
  tests/integration/test_turkish_fsrs_system.py \
  tests/integration/test_turkish_zpd_maarif_system.py \
  tests/integration/test_zpd_maarif_service.py \
  --cov=api --cov=services --cov=core --cov=algorithms \
  --cov-branch \
  --cov-report=json:coverage_full.json \
  --cov-report=term:skip-covered \
  --maxfail=500
```

Result: 445 pass / 1 fail / 107 skip in 95.94s wall. Total cov 16.64%, branch 2.23%.

The broader tests/unit/ run that produced section 1's failure counts:

```bash
python -m pytest tests/unit/ --maxfail=500 -q --tb=no -p no:warnings \
  --ignore=tests/unit/test_coverage_50pct_final.py \
  --ignore=tests/unit/test_enhanced_chat_student_guard.py \
  --ignore=tests/unit/test_enhanced_user_management_auth.py \
  --ignore=tests/unit/test_quality_ab_testing.py \
  --ignore=tests/unit/test_quality_expert_review.py \
  --ignore=tests/unit/test_quality_nlp_metrics.py \
  --ignore=tests/unit/test_quality_question_scorer.py \
  --ignore=tests/unit/test_response_models.py
```

Result: **430 failed, 5612 passed, 154 skipped, 70 errors in 166.10s.**

## Appendix B — Coverage artifact files left in repo

These were generated during this audit and can be deleted or committed:

- `backend/coverage_full.json` (the curated-run JSON used in section 1)
- `backend/coverage_critical.json` (BKT/FSRS/ZPD-specific run)
- `backend/coverage_irt.json` (IRT-specific run)
- `backend/coverage_auth.json` (auth-specific run)
- `backend/coverage_broad.json` (does not exist — broad run hit maxfail)
- `backend/.coverage` (latest SQLite, stale after these runs)

Repo files referenced (all absolute):

- `C:\Users\husey\kiro2\backend\coverage_full.json`
- `C:\Users\husey\kiro2\backend\coverage_critical.json`
- `C:\Users\husey\kiro2\backend\coverage_irt.json`
- `C:\Users\husey\kiro2\backend\coverage_auth.json`
- `C:\Users\husey\kiro2\backend\algorithms\irt_model.py`
- `C:\Users\husey\kiro2\backend\services\bkt_service.py`
- `C:\Users\husey\kiro2\backend\algorithms\turkish_optimized_fsrs.py`
- `C:\Users\husey\kiro2\backend\algorithms\turkish_zpd_maarif_system.py`
- `C:\Users\husey\kiro2\backend\services\zpd_maarif_service.py`
- `C:\Users\husey\kiro2\backend\core\dependencies.py`
- `C:\Users\husey\kiro2\backend\core\csrf_protection.py`
- `C:\Users\husey\kiro2\backend\api\curator.py`
- `C:\Users\husey\kiro2\backend\core\osym_exam_engine.py`
- `C:\Users\husey\kiro2\backend\api\learning_path_v2.py`
- `C:\Users\husey\kiro2\backend\services\irt_service.py`
- `C:\Users\husey\kiro2\backend\core\unified_auth_service.py`
- `C:\Users\husey\kiro2\backend\core\auth_middleware.py`
- `C:\Users\husey\kiro2\backend\core\security_middleware.py`
- `C:\Users\husey\kiro2\backend\api\auth.py`
- `C:\Users\husey\kiro2\backend\tests\unit\api\test_learning_path_route.py` (FAKE — recommend delete)
- `C:\Users\husey\kiro2\backend\tests\integration\test_critical_security.py` (CSRF self-test at lines 168-189 — recommend rewrite)
- `C:\Users\husey\kiro2\backend\tests\integration\test_osym_exam_engine.py` (39 tests `skipif(True)` at line 55 — unskip to recover)
- `C:\Users\husey\kiro2\backend\tests\fast\test_api_coverage_batch13.py` (240 mocks — recommend audit)
- `C:\Users\husey\kiro2\backend\tests\unit\test_coverage_final_push2.py` (209 mocks)
- `C:\Users\husey\kiro2\backend\tests\unit\test_auth_coverage.py` (200 mocks)
- `C:\Users\husey\kiro2\backend\tests\conftest.py` (root fixtures)
- `C:\Users\husey\kiro2\backend\tests\conftest_postgres.py` (verify if loaded)

---

*Audit duration: ~85 minutes. Methodology: read-only — no tests written, no source modified.*
