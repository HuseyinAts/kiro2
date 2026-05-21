# Test Coverage Audit — Product Readiness (2026-05-22)

**Verdict**: Real coverage **16.64%** (curated fail-free, MEMORY correct). 5 critical middleware modules (1,579 LOC) at **0%**. Golden Flow suite green but happy-path only.

## Real Coverage

| Metric | Value |
|---|---|
| Statement | **16.64%** (curated 20-file fail-free run) |
| Branch | Significantly lower |
| Method | 445 PASS, 1 FAIL, 107 SKIP (95s wall) |
| Source | docs/audits/2026-05-21_full_audit/test_coverage_DEEP.md |

The previous "53%" claim was line-execution from failing tests; not reproducible.

## Auth Module Critical 0% Spots

| Module | LOC | Cov | Tests |
|---|---|---|---|
| `core/unified_auth_service.py` | 397 | **0%** | 0 — JWT issuance, refresh rotation untested |
| `core/auth_middleware.py` | 405 | **0%** | 0 — Middleware path untested |
| `core/security_middleware.py` | 455 | **0%** | 0 — CORS/security headers untested |
| `core/turkish_exam_middleware.py` | 462 | **0%** | 0 — Exam-layer auth untested |
| `core/csrf_protection.py` | 202 | 46.99% (incidental) | 2 smoke S179 (May 22) |

**Risk**: 5 modules / 1,921 LOC at near-zero coverage. Auth surface = highest production risk.

## Golden Flow Suite

- File: `backend/tests/e2e/test_golden_flows.py` (5,008 LOC)
- Tests: **174** functions (`@pytest.mark.golden_flow` + `@pytest.mark.e2e`)
- Status per May 22: **164 PASS / 0 FAIL / 2 SKIP**
- Coverage: GF1-GF8 read-path + GF1w-GF149 write-path
- Verified last: 2026-05-21

## Test Isolation (May 22 ✅ CLEANED)

Cleanup commit `fb9d280eb` deleted 117 coverage-hack tests:
- ✅ `test_api_coverage_final.py` — slowapi stub pollution
- ✅ `test_core_partial_batch1.py` + `batch2.py` — error_context stubs
- 0 further stub pollution sites found
- Post-cleanup: 184 unit tests PASS

## Frontend Test Status

| Item | Value |
|---|---|
| Setup | Vitest 3.2.4 + Jest DOM + @testing-library/react |
| Test files | **470** `.test.*` / `.spec.*` |
| Coverage tool | @vitest/coverage-v8 configured |
| Last run | **Unknown** — no git trace |
| CI integration | Status unknown |

## Integration Tests

| Item | Value |
|---|---|
| Files | 120 in `backend/tests/integration/` |
| Subdirs | 8 (auth, core, learning_style, exam_engine, irt, zpd, ai_agents, external) |
| Postgres toggle | `USE_POSTGRES_TESTS=true` env (CI status unknown) |

## Smoke Test Status

⚠️ **Anomali**: Agent reports `test_smoke_api_critical.py` has **0 test functions** (file exists, no `def test_*`). Contradicts MEMORY claim of "15 test, 8 PASS / 7 SKIPPED". Needs verification — may be parse error.

## Top 10 High-Value Untested (P0)

| Module | LOC | Cov | Risk |
|---|---|---|---|
| services/alternative_solutions_service.py | 699 | 5.2% | Daily UX |
| api/learning_path_v2.py | 698 | 19.3% | 5/8 GF touch this |
| core/message_queue_system.py | 518 | **0%** | Background jobs |
| services/soru_bankasi_service.py | 560 | 6.9% | Question filtering, IRT |
| core/realtime_notification_system.py | 463 | **0%** | WebSocket/SSE |
| core/kvkk_compliance.py | 459 | **0%** | Legal/privacy |
| core/security_middleware.py | 455 | **0%** | Auth bypass risk |
| core/auth_security_utils.py | 454 | **0%** | JWT validation |
| core/security_event_monitoring.py | 425 | **0%** | Audit trail |
| services/visual_content_generator.py | 407 | **0%** | Rich media |

## Top 10 P0 Coverage Gaps

1. **core/osym_exam_engine.py:281-1699** — 461 uncovered, 14.7%. 39 integration tests `skipif(True, reason="ExamType not imported")` — never resumed.
2. **core/unified_auth_service.py** — 0% JWT/refresh/blacklist
3. **core/{auth,security}_middleware.py** — 860 LOC, 0%. 8 tests skip on `AsyncClient deprecated httpx 0.27+` (partial migration)
4. **core/csrf_protection.py** — 47% incidental, 0 unit tests
5. **api/learning_path_v2.py:304-2163** — 537 uncovered; tests mock deeply
6. **services/irt_service.py** — 250 LOC, 11.8%, 0% branch
7. **core/message_queue_system.py** — 518 LOC, 0%
8. **services/soru_bankasi_service.py** — 560 LOC, 6.9%
9. **core/realtime_notification_system.py** — 463 LOC, 0%
10. **core/kvkk_compliance.py** — 459 LOC, 0% (legal risk!)

## Methodology

- Source: docs/audits/2026-05-21_full_audit/test_coverage_DEEP.md (663 test files, 614 modules, 245K LOC)
- Git commit fb9d280eb verified — 117 coverage-hack deletions
- Test files: 183 unit, 120 integration, 1 e2e (Golden Flows)
- Tools: coverage 7.13.1 + pytest-cov 7.0.0
- READ-ONLY, no test runs that write to DB.
