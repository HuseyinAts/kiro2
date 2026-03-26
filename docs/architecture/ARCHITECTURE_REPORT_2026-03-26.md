# KIRO2 Unified Architecture Report
**Date:** 2026-03-26 | **Analysis:** 28 parallel agents, 5 rounds | **Codebase:** ~550K LOC

---

## Executive Summary

| Layer | LOC | Files/Endpoints | Tests | Score |
|-------|-----|-----------------|-------|-------|
| Backend | 318K | 1,164 endpoints, 312 models | 10K+ pass | 7.5/10 |
| Frontend | 121K | 403 components, 86 test files | 9% coverage | 6.5/10 |
| Infrastructure | - | 8 workflows, 24 alerts, Docker MVP | Enterprise CI/CD | 7.0/10 |
| Data Pipeline | 73.5K | 184 scripts, 77,336 questions | 100% PASS | 7.3/10 |
| Algorithms | ~14K | IRT+FSRS+CAT+BKT+ZPD+DAG | 377+ tests | 8.0/10 |
| Orchestrator | 16.8K | 45 policies, 7 agents, LangGraph | 71 tests | 5.0/10 |
| pgvector/Search | 3.8K | HNSW 21ms, 3-layer cache | Basic | 8.2/10 |
| **TOTAL** | **~550K** | - | - | **7.1/10** |

---

## 1. Backend Architecture (7.5/10)

### 1.1 API Layer
- **41+ FastAPI routers** with `/api/v1/` prefix standard
- **VersionRedirectMiddleware**: 32 rules, 307 redirect (legacy `/api/xxx` -> `/api/v1/xxx`)
- **Dual auth**: Cookie (frontend httpOnly) + Bearer header (API clients)
- **Rate limiting**: 100 req/min general, 5/min login, SSE exempt
- **CORS**: Environment-based (strict prod, permissive dev)

### 1.2 Services Layer
- **30+ dead services** deprecated in Session 110 (~32K LOC removed)
- **Active services**: exam engine, learning path, gamification, AI chat, YouTube search
- **Dual table trap**: `question_bank` = 77,336 prod, `questions` = EMPTY legacy (resolved)
- **record_answer() pipeline**: BKT -> IRT (theta=p_L bridge) -> FSRS (state persistent) -> ZPD

### 1.3 Models Layer
- **312 SQLAlchemy models** across 83 domain-separated files
- **~120+ tables** in Base.metadata
- **Key models**: QuestionBankItem (prod), User, ExamSession, FSRSCard, BKTState
- **Enums**: Turkish (MATEMATIK, COK_KOLAY) not English

### 1.4 Core/Security
- **JWT**: HS256, 15min access, 7d refresh, Redis blacklist
- **Password**: bcrypt, 74-word blocklist, sequential char detection
- **CSRF**: Double-submit cookie pattern
- **Headers**: Full OWASP set (CSP, HSTS, X-Frame-Options, etc.)
- **RBAC**: 5 roles (student, teacher, parent, admin, super_admin)

### 1.5 Weaknesses
- Backend test coverage: **18%** (target 80%)
- No 2FA implementation
- No incident response plan

---

## 2. Frontend Architecture (6.5/10)

### 2.1 Stack
- React 18 + TypeScript + Vite 7 + MUI + Zustand
- **403 components**, 86 test files
- **PWA**: Service Worker + Workbox + IndexedDB (Dexie)
- **Build**: `npm run build` works (tsc 0 errors after Session 110)

### 2.2 Pages
- **14 monolithic pages** (>700 LOC each) need refactoring
- Key pages: ModernStudentDashboard, ModernLearningPathPage, ModernExamStart
- **Admin labs**: `/admin/labs` route with 10+ experimental components

### 2.3 State Management
- **Zustand**: authStore (single source of truth)
- **Auth migration complete**: 30+ files `localStorage.getItem('token')` -> `credentials: 'include'`
- **URL standardization**: All frontend services use `/api/v1/...`

### 2.4 Weaknesses
- Test coverage: **9%** (86 test files but many untested components)
- 14 monolithic pages need splitting
- Accessibility (a11y) gaps

---

## 3. Infrastructure (7.0/10)

### 3.1 Docker
- **MVP stack**: 2 services (backend + frontend), host PostgreSQL/Redis
- **Production blueprint**: 17 services (archived, ready for scale)
- **Multi-stage builds**: uv builder (10x pip), uvloop+httptools
- **Turkish locale**: tr_TR.UTF-8 in all images
- **Health checks**: `/health/ready` (backend), `/healthz` (nginx-local frontend)

### 3.2 CI/CD (9/10 - Enterprise Grade)
- **8 active workflows**: ci, claude-ci, claude-review, deploy, health-checks, quality-gates, security, release
- **60+ parallel jobs** across workflows
- **Blue-green deployment** (zero-downtime production)
- **11 security scanning tools**: CodeQL, Trivy, Bandit, Semgrep, TruffleHog, Gitleaks, ZAP, etc.
- **5-layer quality gates**: Code Quality, Coverage, Security, Architecture, Documentation

### 3.3 Database Migrations
- **34 active migrations** + 4 disabled (historical conflicts)
- **4 merge nodes** (consolidation points)
- **pgvector HNSW**: m=16, ef_construction=200, vector_cosine_ops
- **Pool config**: 50 base + 100 overflow, asyncpg driver

### 3.4 Security (OWASP 7/10)
- Auth: 8/10 | Authorization: 8/10 | Input Validation: 9/10
- Encryption: 6/10 | Infrastructure: 5/10 | Incident Response: 0/10
- **Missing**: 2FA, WAF, secret rotation policy, audit logging

### 3.5 Cache/Redis (8/10)
- **3-tier**: L1 memory (1ms) + L2 Redis (5ms) + L3 DB (50ms)
- **Key patterns**: `cat:{session_id}`, `jwt:blacklist:{token}`, `fsrs:{user_id}:*`
- **Estimated memory**: <51MB for 100K concurrent users
- **Missing**: maxmemory config, eviction policy

### 3.6 Monitoring (Level 4/5)
- **Prometheus**: 8 scrape jobs, 15s interval, 30d retention
- **Grafana**: 12-panel dashboard, auto-refresh 30s
- **Alertmanager**: 24 rules (14 critical, 12 warning), Slack/email notifications
- **Sentry**: Error tracking + APM
- **OpenTelemetry**: Jaeger tracing configured

---

## 4. Data Pipeline (7.3/10)

### 4.1 Production Data
- **77,336 questions** in `eslesmis_sorucevap.jsonl` (112 MB, v3.5+)
- **405 books** processed (19 unviable)
- **43 fields** per question entry
- **100% validation PASS** (0 critical, 0 warning)

### 4.2 Pipeline Stages
```
[405 PDF Books] -> [YOLO26s Detection] -> [Multi-Provider OCR]
  -> [Answer Key Extraction] -> [Matching Engine (Tier A-D)]
  -> [Bayesian Cross-Validation (7 AI sources)]
  -> [13-Check Validator] -> [PostgreSQL Import (idempotent)]
```

### 4.3 Quality Metrics
| Metric | Value |
|--------|-------|
| OCR extracted | 75,745 |
| Answer keys | 88,711 |
| Final matched (v3.5+) | 77,336 |
| Book answer source | 76.2% |
| AI crossval/Bayes | 22.7% |
| AI crop solve | 1.0% |
| Deactivated garbage | 13,055 (is_active=FALSE) |
| Image coverage | 58,523/77,336 (75.7%) |

### 4.4 Version History
```
v1.0: 36,967 -> v2.4: 86,249 -> v3.0-v3.4: 76,527 -> v3.5+: 77,336
```

### 4.5 Weaknesses
- **184 scripts** (85 root + 99 in scripts/) - consolidation needed
- GitHub 100MB limit for JSONL (need Git-LFS)
- 991 Tier5 AI solve backlog
- 18,813 questions missing image URL (24.3%)

---

## 5. Algorithms (8.0/10)

### 5.1 IRT 3PL Model (8.5/10)
- **Formula**: P(theta) = c + (1-c) / (1 + exp(-a(theta-b)))
- **Parameters**: a=[0.3,3.0], b=[-4,4], c=[0.05,0.40]
- **Theta estimation**: EAP (Gauss-Hermite 21 nodes)
- **Calibration**: EM-3PL (200+ responses) + CTT fallback (50+)
- **LOC**: 711 (irt_engine + irt_calibrator)

### 5.2 CAT Engine (8.5/10)
- **Item selection**: Epsilon-greedy MFI (epsilon=0.20)
- **ZPD filter**: 0.40 <= P(correct) <= 0.85
- **Exposure control**: max_rate = 0.30
- **Termination**: SE < 0.35 or n_items >= 20
- **Latency**: ~22ms per submit_answer
- **State**: Redis hash (1h TTL, ~2KB/session)

### 5.3 FSRS v6 (9/10)
- **17 W parameters** (Ye et al. 2024 - Anki v22)
- **State machine**: New -> Learning -> Review -> Relearning
- **Retention target**: 0.90
- **Turkish cultural factors**: YKS period, summer break, exam season
- **DB tables**: 7 (fsrs_cards, fsrs_reviews, fsrs_schedules, etc.)

### 5.4 BKT (8.5/10)
- **STEM params**: p_T=0.10, p_G=0.20, p_S=0.10, mastery=0.80
- **Verbal params**: p_T=0.05, p_G=0.20, p_S=0.15, mastery=0.85
- **Subject mapping**: tarih->sosyal, edebiyat->turkce, geometri->matematik
- **19 tests PASS**

### 5.5 ZPD (7.5/10)
- **Vygotsky + MEB Maarif** integration
- **8 cultural factors** (group_learning, teacher_respect, family_involvement, etc.)
- **ZPD expansion**: up to 2x with all factors active
- **0 unit tests** (CRITICAL GAP)

### 5.6 DAG Prerequisites (9/10)
- **Kahn's algorithm** (topological sort, O(V+E))
- **42 topics**, ~50 edges (TYT+AYT)
- **HARD**: 70% mastery required, **SOFT**: 40% warning
- **Mastery**: P(theta > cutoff) via normal CDF

### 5.7 IRT Bootstrap
| Level | Questions | Range |
|-------|-----------|-------|
| VERY_EASY | 9,293 | theta < -1.5 |
| EASY | 18,631 | -1.5 <= theta < -0.5 |
| MEDIUM | 15,624 | -0.5 <= theta < 0.5 |
| HARD | 12,947 | 0.5 <= theta < 1.5 |
| VERY_HARD | 7,710 | theta >= 1.5 |
| **TOTAL** | **64,205** | |

### 5.8 Algorithm Pipeline (record_answer)
```
BKT (p_L update) -> IRT (theta via EAP) -> FSRS (card state) -> ZPD (scaffold)
Latency: 30-40ms total
Error handling: Silent fallback with counter logging
```

### 5.9 Test Coverage
- **377+ tests PASS** across all algorithm modules
- **Code coverage: 31.46%** (target 60%)
- fsrs_engine: 92.57% | irt_engine: 88.30% | irt_calibrator: 88.02%
- dag_engine: 0% | fsrs_service: 0% | cat_session: 24.5%

---

## 6. Semantic Search / pgvector (8.2/10)

### 6.1 Architecture
- **pgvector HNSW**: m=16, ef_construction=200, 768-dim
- **Model**: nomic-embed-text (Ollama), prefix `search_document:`/`search_query:`
- **3-layer cache**: Memory LRU (1000) + Redis async + In-memory index
- **Quantization**: float32 -> int8 (75% memory reduction)

### 6.2 Performance
| Operation | Latency |
|-----------|---------|
| Vector search | 21ms avg |
| Cache hit | <1ms |
| Question search API | ~50ms |
| Video semantic search | 300-500ms |

### 6.3 Search Types
- Semantic (cosine similarity)
- Keyword (GIN full-text, pg_trgm trigram)
- Hybrid (0.6*semantic + 0.2*recency + 0.2*popularity)
- MMR diversity (lambda=0.5)

---

## 7. Orchestrator / LangGraph (5.0/10)

### 7.1 Architecture
- **LangGraph v1.0.5** (v2.5.0 internal versioning)
- **7 specialized agents**: Planner, Implementer, Reviewer, Fixer, Tester, SecurityAuditor, DocumentWriter
- **45 policies** in 6 categories: Core, Safety, Quality, Resource, Learning, Sustainability
- **Quality gates**: Lint -> TypeCheck -> Test -> Security

### 7.2 Learning Loop
- **Thompson Sampling** (Multi-Armed Bandit)
- **5 strategy types**: matching, routing, resource, retry, timeout
- **Beta posterior**: Alpha/Beta update per trial

### 7.3 Weaknesses (Critical)
- **Backend API integration: 0%** (no routes exist)
- **PostgreSQL persistence: mock only**
- **Tool executor: untested sandbox security**
- **Performance benchmarks: none**

---

## 8. Critical Issues (P0)

| # | Issue | Layer | Impact | Effort |
|---|-------|-------|--------|--------|
| 1 | Backend test coverage 18% | Backend | Regression risk | 2-4 weeks |
| 2 | No 2FA | Security | Account takeover | 1 week |
| 3 | Docker MVP single-instance | Infra | SPOF | 2 days |
| 4 | Secret management via .env | Infra | Credential exposure | 1 week |
| 5 | Orchestrator no backend integration | Orchestrator | 50% unusable | 1 week |
| 6 | DAG engine 0% test coverage | Algorithms | Path failure risk | 2 days |
| 7 | ZPD 0% test coverage | Algorithms | Scaffold errors | 2 days |
| 8 | 77K embeddings not generated | pgvector | 0 search results | 1 day |

## 9. Important Issues (P1)

| # | Issue | Layer |
|---|-------|-------|
| 1 | Frontend 14 monolithic pages (>700 LOC) | Frontend |
| 2 | Redis maxmemory config missing | Cache |
| 3 | 184 pipeline scripts need consolidation | Data |
| 4 | Algorithm code coverage 31% (target 60%) | Algorithms |
| 5 | No incident response plan | Security |
| 6 | No log aggregation (ELK/Splunk) | Monitoring |
| 7 | Migration downgrade paths untested | DB |
| 8 | VITE_SHOW_DEMO=true in production | Docker |
| 9 | BKT-IRT bridge is linear (non-linear better) | Algorithms |
| 10 | Tier5 AI solve backlog (991 questions) | Data |
| 11 | 18,813 questions missing image URL (24%) | Data |
| 12 | Orchestrator PostgreSQL persistence mock | Orchestrator |

---

## 10. Production Readiness Scorecard

```
Backend API/Services      7.5/10  ||||||||-
Frontend UI/UX            6.5/10  ||||||---
CI/CD Pipeline            9.0/10  |||||||||-
Docker/Deploy             6.2/10  ||||||---
Security/Auth             7.5/10  ||||||||-
Algorithm Engine          8.0/10  ||||||||--
Data Pipeline             7.3/10  |||||||--
Semantic Search           8.2/10  ||||||||--
Orchestrator              5.0/10  |||||-----
Monitoring/Observability  8.0/10  ||||||||--
-----------------------------------------------
OVERALL                   7.1/10  |||||||--
```

**Verdict:** MVP beta launch ready. Enterprise HA requires hardening (target 8.5/10).

---

## 11. Technology Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend | FastAPI + Uvicorn | Latest |
| Frontend | React 18 + TypeScript + Vite 7 | 18.x |
| Database | PostgreSQL 15 (port 5434) | 15.x |
| Cache | Redis 7 | 7.x |
| Vector Search | pgvector HNSW | Latest |
| Embedding | nomic-embed-text (768d) | Latest |
| AI/NLP | Qwen3-8B (Turkish fine-tuned) | Custom |
| Orchestrator | LangGraph | v1.0.5 |
| CI/CD | GitHub Actions | 8 workflows |
| Monitoring | Prometheus + Grafana + Alertmanager | Latest |
| Error Tracking | Sentry + OpenTelemetry | Latest |

---

*Generated by 28 parallel analysis agents across 5 rounds*
*Analysis date: 2026-03-26 | Report version: 1.0*
