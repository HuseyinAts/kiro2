# KIRO2 Strategic Implementation Plan
**Date:** 2026-03-26 | **Source:** 4-perspective brainstorm on 28-agent architecture analysis
**Perspectives:** Technical Priority | Risk & Dependencies | Resource & Timeline | Quality Gates

---

## Executive Summary

The 4-sprint action plan has the **right tasks** but the **wrong timeline**. Key corrections:

| Dimension | Original Plan | Revised Assessment |
|-----------|--------------|-------------------|
| Timeline | 4 weeks | **10-12 weeks** (3x longer) |
| P0 issues | 8 greenfield tasks | **3 already have code** (2FA, DAG tests, ZPD tests) |
| Score: Sprint 2 target | 7.8 | **7.45** (at week 4) |
| Score: Sprint 4 target | 8.3 | **8.3** (achievable at week 12) |
| MVP beta launch | After Sprint 2 | **Already viable at 7.1**, comfortable at 7.5 (week 3) |
| Backend coverage final | 50% | **35-40%** (realistic ceiling in timeframe) |

---

## Critical Discoveries

### 3 P0s Are Overestimated (Code Already Exists)

1. **P0#2 "No 2FA"** — 1,114 LOC already written (`core/two_factor_auth.py` 678 LOC + `api/two_factor_auth_api.py` 436 LOC + migration `d7a10d07b648`). **Real task: register router + fix login gating** (2 days, not 1 week)

2. **P0#6 "DAG 0% coverage"** — `tests/test_dag.py` exists (390 lines, NOT skipped). Tests `PrerequisiteDAG`, `build_yks_dag`, `compute_mastery_from_theta`. **Real task: verify pass + add to CI coverage config** (0.5 day)

3. **P0#7 "ZPD 0% coverage"** — 4 ZPD test files exist (2,780 LOC total). 2 are module-level skipped. `test_zpd_boundaries.py` contains reward-hacking (literal assertions). **Real task: un-skip + rewrite assertions** (1 day)

### Critical Security Findings

**2FA Login Bypass:** The login endpoint (`/api/v1/auth/login/secure` in `auth.py`) NEVER checks `is_2fa_enabled`. Enabling 2FA currently provides zero protection — it is completely bypassable. Fix: add `is_2fa_enabled` check, return challenge token, require TOTP verification before issuing cookies.

**Hardcoded Redis URLs (4 files):**
- `app/api/cat.py` line 45
- `app/api/placement.py` line 55
- `app/services/placement_service.py` line 253
- `app/core/deps.py` line 40

These must read from `settings.REDIS_URL`. Break Docker deployment.

---

## P0 Dependency Graph

```
INDEPENDENT (start Day 1, no blockers):
  P0#8  Embeddings (1 day, automated)     → Enables ALL search
  P0#6  DAG tests (0.5 day, verify)       → Closes P0
  P0#7  ZPD tests (1 day, un-skip+fix)    → Closes P0
  P1    Redis config (1 hour)             → Prevents OOM
  P1    VITE_SHOW_DEMO (30 min)           → Removes demo in prod

AFTER GROUP 1:
  P0#2  2FA integration (2 days)          → Register router + login gate
  P0#1  Backend coverage (ongoing)        → 18% → 30% → 40%+

AFTER GROUP 2:
  P0#4  Secret management (5 days)        → Before scaling
  P0#3  Docker multi-instance (3 days)    → After secrets

DEFER:
  P0#5  Orchestrator API (5 days)         → Dev tooling, not user-facing
```

### ROI Rankings

| Rank | P0 | Impact | Effort | ROI |
|------|-----|--------|--------|-----|
| 1 | P0#8 Embeddings | Very High | 1 day | 10/10 |
| 2 | P0#6 DAG tests | High | 0.5 day | 9/10 |
| 3 | P0#7 ZPD tests | High | 1 day | 8/10 |
| 4 | P0#2 2FA | Medium | 2 days | 6/10 |
| 5 | P0#1 Coverage | Very High | 20+ days | 5/10 |
| 6 | P0#4 Secrets | Medium | 5 days | 4/10 |
| 7 | P0#3 Docker HA | Low | 2 days | 3/10 |
| 8 | P0#5 Orchestrator | Low | 5 days | 2/10 |

---

## Risk-Adjusted Priority Matrix

### High Impact + Low Risk → DO FIRST
- P0#8 Embeddings (script exists with resume support)
- P0#6 DAG test verification (tests already written)
- Redis maxmemory config (1-line change)
- VITE_SHOW_DEMO conditional (1-line change)
- P0#7 ZPD test un-skip (tests exist, fix parameter mismatches)
- Hardcoded localhost Redis fix (4 files)

### High Impact + High Risk → PLAN CAREFULLY
- P0#1 Backend coverage 18%→50% (190 skipped test files may cascade)
- P0#4 Secret management (.env.mvp → Vault/Docker Secrets)
- P0#2 2FA integration (login flow redesign)
- Frontend page refactor (14 monolithic pages)

### Low Impact + Low Risk → BATCH TOGETHER (Sprint 4)
- Pipeline script consolidation (184→30)
- Migration downgrade tests
- Missing image URLs (18,813 questions)
- BKT-IRT bridge linearity improvement

### Low Impact + High Risk → SKIP/DEFER
- P0#5 Orchestrator API (dev tooling, not user-facing)
- ELK stack (use Loki+Grafana instead, lighter)
- Docker HA (single instance OK for MVP beta)

---

## Cross-Layer Dependency Analysis

### Backend ↔ Algorithms: record_answer() Pipeline
- **Chain:** BKT → IRT (theta=p_L bridge) → FSRS (card state) → ZPD (scaffold)
- **FSRS silent failure is highest risk:** missed DB write has no retry, corrupts spaced repetition schedule over time. Error is logged but invisible to user.
- **Mitigation:** Add retry queue or write-ahead log for FSRS writes

### Backend ↔ pgvector: Embedding Generation
- **27 files** reference semantic/vector search — ALL return empty until embeddings generated
- **Risk:** Partial batch (50% complete) causes biased search results
- **Mitigation:** `WHERE embedding IS NOT NULL` filter on search queries

### 2FA ↔ Login Flow
- **Login endpoint never checks `is_2fa_enabled`** → 2FA is security theater
- **Cascade risk:** Modifying login flow could lock out ALL users if buggy
- **Mitigation:** Feature flag mandatory. Deploy frontend TOTP screen BEFORE backend enforcement.

### Infrastructure → Everything
- Redis no maxmemory → OOM under load (production crash)
- Secrets in .env.mvp → single file compromise = full system access
- Docker single instance → no redundancy for backend crashes

---

## Cascade Failure Scenarios

| Scenario | Trigger | Cascade | Prevention |
|----------|---------|---------|------------|
| Migration downgrade after 2FA | Rollback `d7a10d07b648` | Destroys 2FA secrets, users locked out of authenticator apps | Disable 2FA for all users BEFORE downgrade |
| Secret migration misconfigured | .env.mvp → Vault cutover | Backend boots with None JWT_SECRET, issues invalid JWTs | Startup validation for all required secrets |
| Frontend page refactor | Extract QuizInterface | handleQuizComplete callback breaks → FSRS never updates | Write E2E test BEFORE refactoring |
| Redis maxmemory set | allkeys-lru eviction starts | CAT session state or JWT blacklist evicted | Check current usage first, ensure TTLs exist |
| Script consolidation | Delete match_simple_v4.py | pipeline.py may import as fallback | Move to _archive/, don't delete |

---

## Revised Timeline (Realistic)

### Capacity Baseline
- **Team:** 1 solo developer + Claude Code AI (2-3x acceleration for test writing)
- **Effective hours:** ~30h/week (6h/day × 5 days)
- **Original plan:** 4 weeks compressed. **Reality:** 12 weeks.

### Week-by-Week Milestones

| Week | Focus | Key Deliverables | Score |
|------|-------|-----------------|-------|
| 1 | Quick Wins | Redis, VITE, DAG, ZPD, embeddings, localhost fix | 7.3 |
| 2 | 2FA + Test Start | 2FA router + login gate, begin backend test un-skip | 7.35 |
| 3 | Test Foundation | Backend coverage 18%→22%, pipeline script audit | 7.45 |
| 4 | Coverage Push 1 | Backend 22%→27%, secret management plan | 7.5 |
| 5 | Secrets + Orchestrator | Secret migration, orchestrator basic routes | 7.6 |
| 6 | Algorithm + Docker | Algorithm coverage 42%→55%, Docker HA | 7.8 |
| 7 | Frontend Refactor | Split top 5 monolithic pages | 7.85 |
| 8 | 2FA Hardening | Full 2FA E2E, feature flag rollout | 8.0 |
| 9-10 | Coverage Push 2 | Backend →35%, security audit | 8.15 |
| 11-12 | Polish + Logging | Log aggregation, remaining fixes, documentation | 8.3 |

### Score Progression Forecast

```
Week 0:  ██████████████░░░░░░  7.1  (current)
Week 2:  ██████████████▓░░░░░  7.35 (quick wins + 2FA)
Week 4:  ███████████████░░░░░  7.5  (test foundation)  ← MVP beta comfortable
Week 6:  ████████████████░░░░  7.8  (algorithm + Docker)
Week 8:  ████████████████▓░░░  8.0  (2FA hardened)     ← production-ready beta
Week 12: █████████████████▓░░  8.3  (quality push)     ← enterprise-ready
```

**Minimum viable score for MVP beta launch: 7.5 (Week 4)**

---

## Sprint Quality Gates (MUST-PASS)

### Sprint 1 Gate: "Foundation Integrity"
- [ ] Algorithm coverage ≥ 45% (ZPD + DAG > 0%)
- [ ] 77,336 embeddings in pgvector, search returns results
- [ ] Redis maxmemory 256MB + allkeys-lru configured
- [ ] VITE_SHOW_DEMO not hardcoded as "true"
- [ ] Zero reward-hacking patterns in ZPD tests
- [ ] Existing 10K+ backend tests still pass

### Sprint 2 Gate: "Stabilization"
- [ ] Backend coverage ≥ 30% (exam engine ≥ 40%, auth ≥ 50%)
- [ ] Zero hardcoded secrets in `app/` directory
- [ ] Auth E2E flow: login → cookie → /me → refresh → logout → 401
- [ ] 2FA: TOTP working for admin/teacher, login gating enforced
- [ ] Coverage floor CI gate: `--cov-fail-under=28`

### Sprint 3 Gate: "Hardening"
- [ ] Docker 3 backend replicas + nginx load balancing
- [ ] Structured logs shipping to aggregation
- [ ] Login works with AND without 2FA (feature flag)
- [ ] Top 5 frontend pages < 500 LOC each

### Sprint 4 Gate: "Quality Push"
- [ ] Backend coverage ≥ 50% (or realistic: ≥ 40%)
- [ ] Algorithm coverage ≥ 60% (or realistic: ≥ 55%)
- [ ] record_answer() pipeline integration test (BKT→IRT→FSRS→ZPD)
- [ ] Migration downgrade tested (head~3 → head round-trip)
- [ ] Incident response plan documented
- [ ] OWASP ZAP scan: 0 HIGH/CRITICAL findings

---

## Definition of "Done" Per Task Type

### Test Writing
- Coverage delta > 0% for target module
- All tests pass (`pytest -x`)
- No `assert True` / literal-only assertions
- Tests exercise real code paths (not mocks returning mocks)
- Turkish text tests include İ/ı characters

### Security Fix
- Root Cause Analysis table filled (per debugging-first.md)
- Fail-first test written before fix
- Bandit scan clean
- No new hardcoded secrets
- Existing auth E2E unbroken

### Infrastructure Change
- Docker health checks pass (all containers healthy)
- Rollback tested (can revert in < 5 min)
- Monitoring alert configured for the change
- No port conflicts with existing services

### Code Refactoring
- Test count unchanged or increased
- Coverage % does not decrease
- `ruff check .` exits 0
- Deprecation guard protocol followed (if moving files)

---

## Automated Metrics Dashboard

### Test Metrics
| Metric | Current | Sprint 2 | Sprint 4 |
|--------|---------|----------|----------|
| `backend_test_coverage_%` | 18% | 30% | 40%+ |
| `algorithm_test_coverage_%` | 31% | 45% | 55%+ |
| `frontend_test_coverage_%` | 9% | 15% | 25% |
| `test_pass_rate` | ~99.99% | >99.9% | >99.9% |
| `tests_skipped_count` | 4,065 | <3,500 | <2,500 |
| `reward_hacking_count` | >0 | 0 | 0 |

### Performance Metrics
| Metric | Current | Target |
|--------|---------|--------|
| `api_p95_latency_ms` | <4ms | <100ms |
| `vector_search_latency_ms` | 21ms | <50ms |
| `cat_submit_answer_ms` | ~22ms | <50ms |
| `record_answer_pipeline_ms` | 30-40ms | <100ms |

### Security Metrics
| Metric | Current | Target |
|--------|---------|--------|
| `owasp_compliance` | 7/10 | 9/10 |
| `hardcoded_secrets` | 4 | 0 |
| `open_p0_issues` | 8 | 0 |

### Infrastructure Metrics
| Metric | Current | Target |
|--------|---------|--------|
| `redis_memory_mb` | <51MB | <256MB |
| `postgres_pool_usage_%` | Unknown | <80% |
| `embedding_coverage_%` | 0% | 100% |

---

## Top 5 Risks (by severity)

| # | Risk | Score | Mitigation |
|---|------|-------|-----------|
| 1 | 2FA login bypass (security theater) | 80 | Fix login endpoint BEFORE advertising 2FA |
| 2 | 0 embeddings = 0 search results | 54 | Priority #1 operational task in Week 1 |
| 3 | Orchestrator sandbox RCE if exposed | 45 | Admin-only routes, delay public access |
| 4 | FSRS silent failure corrupts schedules | 32 | Retry queue + monitoring alert |
| 5 | Secret migration locks out production | 30 | Blue-green + instant .env.mvp rollback |

---

## Week 1 Detailed Execution Plan

```
Monday:
  09:00  [30min] VITE_SHOW_DEMO → conditional env var
  09:30  [1h]    Redis maxmemory 256MB + allkeys-lru
  10:30  [2h]    Run test_dag.py → verify PASS → add to CI coverage
  13:00  [4h]    ZPD test un-skip + rewrite literal assertions
  17:00  [10min] Start embedding batch (overnight, ~64 min)

Tuesday:
  09:00  [3h]    Complete ZPD test fixes, verify all pass
  12:00  [2h]    Verify embeddings complete + test search API
  14:00  [2h]    Fix 4 hardcoded localhost Redis URLs
  16:00  [1h]    Commit all quick wins

Wednesday:
  09:00  [4h]    2FA: register router in FastAPI application
  13:00  [4h]    2FA: add is_2fa_enabled check to login endpoint

Thursday:
  09:00  [4h]    2FA: frontend TOTP input screen
  13:00  [4h]    2FA: E2E testing (setup → verify → login → backup codes)

Friday:
  09:00  [4h]    Backend test un-skip audit (categorize 190 files)
  13:00  [4h]    Un-skip Category A (fixed imports) → free coverage gains
```

**Expected P0 status after Week 1:**
- P0#6 DAG tests: **CLOSED**
- P0#7 ZPD tests: **CLOSED**
- P0#8 Embeddings: **CLOSED**
- P0#2 2FA: **CLOSED** (integrated + login gate)
- P0#1 Coverage: **IN PROGRESS** (18% → ~22%)
- P0#3, P0#4, P0#5: **DEFERRED** to Week 4+

---

## Success Milestones

### Milestone 1: MVP Beta Launch Ready (Score ≥ 7.5)
- 0 P0 issues blocking user experience
- Semantic search working
- Algorithm tests passing
- Backend coverage ≥ 25%
- **Target: Week 4**

### Milestone 2: Production-Ready Beta (Score ≥ 8.0)
- 2FA enforced for admin/teacher
- Docker HA with replicas
- Secrets properly managed
- Backend coverage ≥ 35%
- **Target: Week 8**

### Milestone 3: Enterprise Ready (Score ≥ 8.5)
- All P0 + P1 closed
- OWASP 9/10
- Log aggregation + monitoring complete
- Backend coverage ≥ 50%
- Incident response plan documented
- **Target: Week 14+**

---

## Key Files for Implementation

| File | Sprint | Action |
|------|--------|--------|
| `docker-compose.yml` | S1 | Redis maxmemory, VITE_SHOW_DEMO |
| `backend/scripts/generate_embeddings.py` | S1 | Run batch |
| `backend/tests/test_dag.py` | S1 | Verify + CI |
| `backend/tests/unit/algorithms/test_zpd_boundaries.py` | S1 | Rewrite assertions |
| `backend/api/auth.py` | S1 | Add 2FA login gating |
| `backend/api/two_factor_auth_api.py` | S1 | Register router |
| `backend/core/feature_flags.py` | S1 | Add TWO_FACTOR_AUTH flag |
| `backend/app/api/cat.py` | S1 | Fix hardcoded Redis URL |
| `backend/app/api/placement.py` | S1 | Fix hardcoded Redis URL |
| `backend/app/services/placement_service.py` | S1 | Fix hardcoded Redis URL |
| `backend/app/core/deps.py` | S1 | Fix hardcoded Redis URL |
| `.github/workflows/ci.yml` | S2 | Lower --cov-fail-under to baseline |
| `.github/workflows/quality-gates.yml` | S2 | Add reward-hacking detection |
| `backend/services/bkt_service.py` | S2 | FSRS retry queue |

---

*Generated by 4 parallel brainstorm agents analyzing 28-agent architecture findings*
*Analysis date: 2026-03-26 | Plan owner: Huseyin | Review date: Weekly Friday*
