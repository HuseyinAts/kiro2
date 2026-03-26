# KIRO2 Action Plan — Post-Architecture Analysis
**Date:** 2026-03-26 | **Based on:** 28-agent unified analysis

---

## Sprint 1: Critical Fixes (This Week)

### S1.1 Algorithm Test Gaps [2 days]
- [ ] Write 15+ ZPD unit tests (scaffold_level, bilge_mode, maarif_alignment, cultural_factors)
- [ ] Write 10+ DAG engine integration tests (topo sort, mastery check, learning path)
- [ ] Target: Algorithm coverage 31% -> 45%

### S1.2 Embedding Generation [1 day]
- [ ] Run batch embedding for 77,336 questions via Ollama/nomic-embed-text
- [ ] Verify pgvector HNSW index creation
- [ ] Test semantic search endpoint returns results

### S1.3 Redis Config [1 hour]
- [ ] Set maxmemory 256MB in docker-compose
- [ ] Set maxmemory-policy allkeys-lru
- [ ] Document TTL strategy

### S1.4 VITE_SHOW_DEMO Fix [30 min]
- [ ] Change build arg to conditional: `VITE_SHOW_DEMO=${BUILD_ENVIRONMENT}`

---

## Sprint 2: Stabilization (Next Week)

### S2.1 Backend Test Coverage [3 days]
- [ ] Focus on: api/, core/, services/ critical paths
- [ ] Target: 18% -> 30%
- [ ] Priority files: exam engine, learning path, auth endpoints

### S2.2 Secret Management [2 days]
- [ ] Evaluate: Docker Secrets vs HashiCorp Vault vs AWS Secrets Manager
- [ ] Migrate .env.mvp secrets to chosen solution
- [ ] Remove hardcoded dev credentials

### S2.3 Orchestrator API Routes [2 days]
- [ ] Add `/api/v1/orchestrator/run` endpoint
- [ ] Add `/api/v1/orchestrator/status/{run_id}` endpoint
- [ ] Integration test: orchestrator -> backend -> database flow

### S2.4 Pipeline Script Consolidation [2 days]
- [ ] Remove extract_answers_v1-v6 (keep v7)
- [ ] Remove match_questions_v1-v3 (keep v5)
- [ ] Consolidate phase4_v1-v8 to single version
- [ ] Target: 184 scripts -> ~30 core scripts

---

## Sprint 3: Hardening (Week 3)

### S3.1 2FA Implementation [3 days]
- [ ] TOTP (Time-based One-Time Password) for admin/teacher accounts
- [ ] QR code setup flow
- [ ] Backup codes generation
- [ ] Optional for students

### S3.2 Docker Multi-Instance [2 days]
- [ ] nginx upstream config with 3x backend replicas
- [ ] Health-check-based load balancing
- [ ] Session affinity for WebSocket/SSE

### S3.3 Log Aggregation [2 days]
- [ ] ELK stack setup (Elasticsearch, Logstash, Kibana)
- [ ] Structured log shipping from backend
- [ ] Dashboard for error trends

### S3.4 Frontend Page Refactor [3 days]
- [ ] Split top 5 monolithic pages (>700 LOC each)
- [ ] Extract reusable components
- [ ] Add lazy loading for heavy components

---

## Sprint 4: Quality Push (Week 4)

### S4.1 Backend Coverage Push [5 days]
- [ ] Target: 30% -> 50%
- [ ] Focus: Services layer (exam, learning_path, gamification)
- [ ] Add integration tests for record_answer() pipeline

### S4.2 Algorithm Coverage Push [3 days]
- [ ] CAT session lifecycle tests (Redis disconnect recovery)
- [ ] FSRS service integration tests
- [ ] Placement bounds parametrize tests
- [ ] Target: 31% -> 60%

### S4.3 Migration Downgrade Tests [1 day]
- [ ] Add pytest suite for `alembic downgrade head~N`
- [ ] Test safe rollback to merge nodes
- [ ] Document downgrade limitations

### S4.4 Security Audit [2 days]
- [ ] Tool executor sandbox penetration test
- [ ] SSRF validation review
- [ ] Rate limit bypass testing
- [ ] Incident response plan draft

---

## Monthly Goals

| Month | Focus | Target Score |
|-------|-------|-------------|
| April 2026 | Sprint 1-2 (Critical + Stabilize) | 7.1 -> 7.8 |
| May 2026 | Sprint 3-4 (Harden + Quality) | 7.8 -> 8.3 |
| June 2026 | Enterprise features (HA, monitoring, perf) | 8.3 -> 8.7 |

---

## Success Metrics

| Metric | Current | Sprint 2 | Sprint 4 | Target |
|--------|---------|----------|----------|--------|
| Backend test coverage | 18% | 30% | 50% | 80% |
| Algorithm test coverage | 31% | 45% | 60% | 80% |
| Frontend test coverage | 9% | 15% | 25% | 70% |
| OWASP compliance | 7/10 | 7/10 | 8/10 | 9/10 |
| Overall readiness | 7.1/10 | 7.8/10 | 8.3/10 | 9.0/10 |
| P0 issues open | 8 | 3 | 0 | 0 |
| P1 issues open | 12 | 8 | 4 | 0 |

---

## Dependencies & Risks

| Risk | Probability | Impact | Mitigation |
|------|-----------|--------|-----------|
| Embedding generation slow (77K * 50ms) | Medium | Low | Batch overnight, resume support |
| 2FA breaks existing login flow | Low | High | Feature flag, gradual rollout |
| Script consolidation breaks pipeline | Medium | Medium | Dry-run + sample validation first |
| Secret migration downtime | Low | Critical | Blue-green migration, test in staging |
| Orchestrator integration complexity | High | Medium | Incremental: routes first, then full flow |

---

*Plan owner: Huseyin | Review date: Weekly Friday*
*Based on 28-agent architecture analysis (2026-03-26)*
