# KIRO2 Repository Map

**Generated:** 2026-04-05
**Status:** COMPLETE AUDIT

---

## Repository Structure

```
kiro2/
├── backend/                    # FastAPI Python backend (~1000 files)
├── frontend/                  # React 18 + TypeScript (~500 files)
├── orchestrator/               # LangGraph multi-agent system (v2.5.0)
├── d-dataset/                  # OCR pipeline + question processing
├── monitoring/                  # Prometheus + Grafana
├── kubernetes/                  # K8s manifests
├── .github/workflows/           # CI/CD pipelines
├── init-scripts/               # DB initialization SQL
├── docs/                        # Documentation
├── ssl/                         # TLS certificates
└── redis.conf                  # Redis configuration
```

---

## Section 1: BACKEND

**Path:** `C:\Users\husey\kiro2\backend`

### Entry Points
| File | Purpose |
|------|---------|
| `main.py` | Application entry point, factory pattern |
| `core/application.py` | FastAPI app factory, lifespan events, DB initialization |
| `routers/loader.py` | Dynamic router loading, 249 registered routers |

### Core Infrastructure (`core/`)
- `config.py` - Settings management (.env)
- `database.py` - Async SQLAlchemy + asyncpg (pool_size=200)
- `auth.py` - JWT + bcrypt + RBAC
- `jwt_auth.py` - Refresh tokens + Redis blacklist
- `enhanced_authentication.py` - 50KB advanced auth (2FA, OAuth2, biometric)
- `rbac_system.py` - Hierarchical RBAC
- `exceptions.py` - 30+ exception types with factory pattern
- `security_middleware.py` - 43KB security layer
- `cache.py`, `cache_service.py` - Redis caching
- `rate_limiting.py` - Rate limit system

### API Layer (`api/`)
| File | Size | Purpose |
|------|------|---------|
| `auth.py` | 61KB | Authentication endpoints |
| `sinav.py` | 53KB | Exam management |
| `learning_path_v2.py` | 74KB | Learning paths (ZPD + DAG + IRT + FSRS) |
| `youtube_routes.py` | 41KB | YouTube integration |
| `analytics.py` | 54KB | Analytics |
| `soru_bankasi.py` | 34KB | Question bank |
| `content_management.py` | 28KB | Content CRUD |
| `question_crud_api.py` | 41KB | Question CRUD |

### Services (`services/`)
- 100+ service files
- `question_crud_service.py` (42KB)
- `soru_bankasi_service.py` (58KB)
- `video_solution_service.py` (31KB)
- `irt_service.py` (29KB)
- `fsrs_service.py` - Spaced repetition
- `osym_inspired_generator.py` (30KB)
- `youtube/` - YouTube-related services
- `quality/` - Quality gates
- `psychometrics/` - Psychometric services
- `llm/` - LLM integration

### Models (`models/`)
- `base.py` - SQLAlchemy Base (relative imports only)
- `database.py` - ORM models (User, Exam, Content, FSRS, Learning)
- `user.py` - Pydantic models
- `enums.py` - Enum definitions
- `learning_path_models.py` - Canonical student profile
- `gamification.py` - Gamification models
- `fsrs_models.py` - FSRS spaced repetition

### Agents (`agents/`)
- `coordination/blackboard.py` - Redis-based inter-agent communication
- `domain_experts/` - Subject-specific agents
- `learning_path_agent.py` - ZPD-aware recommendations

### Key Dependencies
```
asyncpg (PostgreSQL driver, 3-5x faster)
Redis (caching, JWT blacklist, sessions)
FastAPI + Uvicorn
Pydantic v2
LangGraph >=0.2.0
```

---

## Section 2: FRONTEND

**Path:** `C:\Users\husey\kiro2\frontend`

### Entry Points
| File | Purpose |
|------|---------|
| `src/main.tsx` | Entry point, PWA registration, axios defaults |
| `src/App.tsx` | Router, 30+ lazy pages, AuthProvider, React Query |

### Directory Structure
```
frontend/src/
├── api.ts                    # Legacy API (4.4MB - NEEDS SPLIT)
├── main.tsx                  # Entry point
├── App.tsx                   # Main router
├── config/                   # Configuration
├── context/                  # AuthProvider
├── db/                       # IndexedDB (Dexie PWA offline)
├── hooks/                    # 30+ custom hooks
├── pages/                    # 70+ pages
│   └── _deprecated/          # Deprecated pages
├── components/               # 150+ components
│   ├── ui/                   # Base UI primitives
│   ├── Auth/                 # Auth components
│   ├── Exam/                 # Exam components
│   ├── LearningPath/         # Learning path
│   ├── Gamification/         # Gamification
│   ├── Revolutionary/        # Revolutionary features
│   └── ...
├── services/                 # API service layer
│   ├── apiClient.ts          # Axios with interceptors
│   └── authService.ts        # Authentication
├── store/                    # Zustand stores (5)
│   ├── authStore.ts          # Auth state
│   ├── examStore.ts          # Exam session
│   ├── settingsStore.ts      # User preferences
│   └── uiStore.ts            # UI state
├── theme/                    # MUI themes
├── types/                    # TypeScript types
└── utils/                    # Utilities
```

### State Management (Zustand)
| Store | Purpose |
|-------|---------|
| `authStore` | Authentication, user session, role permissions |
| `examStore` | Exam sessions, questions, answers, timer |
| `settingsStore` | User preferences, accessibility |
| `uiStore` | Modals, toasts, sidebar |
| `notificationStore` | Notifications |

### Key Pages
| Page | File | Role |
|------|------|------|
| Login | `ModernLoginPage.tsx` | Public |
| Student Dashboard | `ModernStudentDashboard.tsx` | ogrenci |
| Teacher Dashboard | `ModernTeacherDashboard.tsx` | ogretmen |
| Parent Dashboard | `ModernParentDashboard.tsx` | veli |
| Admin Dashboard | `ModernAdminDashboard.tsx` | admin |
| Exam Start/Page/Results | `ModernExam*.tsx` | ogrenci |
| Learning Path | `ModernLearningPathPage.tsx` | ogrenci |
| Social Features | `SocialHubPage.tsx`, `SoruMeydaniPage.tsx` | ogrenci |
| FSRS Review | `FSRSReviewPage.tsx` | ogrenci |

### API Service Patterns
1. **Axios-based** (`apiClient.ts`): 30s timeout, credentials: include
2. **Fetch-based** (`apiHelpers.ts`): Legacy utilities
3. **Service Classes**: Domain-specific wrappers

---

## Section 3: ORCHESTRATOR / AGENT FLOWS

**Path:** `C:\Users\husey\kiro2\orchestrator`

### Entry Points
| File | Purpose |
|------|---------|
| `master_orchestrator.py` | Main orchestrator class |
| `core/graph.py` | LangGraph StateGraph orchestration |
| `backend/api/orchestrator_api.py` | FastAPI endpoints |
| `backend/app/services/learning_path_orchestrator.py` | Learning path orchestration |

### Core Modules (`orchestrator/core/`)
| Module | Purpose |
|--------|---------|
| `agents.py` | 7 specialized agents: Planner, Implementer, Reviewer, Fixer, Tester, SecurityAuditor, DocumentWriter |
| `graph.py` | LangGraph StateGraph (plan, route, implement, quality_check, review, fix, report) |
| `state.py` | RunState management with Redis backing |
| `routing.py` | Policy-driven routing (20 task types, model selection) |
| `llm_gateway.py` | Multi-provider LLM gateway (Claude, OpenAI, Codex) |
| `quality_gates.py` | Quality pipeline: Lint, TypeCheck, UnitTest, Security |
| `memory.py` | PostgreSQL-based persistent memory |
| `self_improvement.py` | Self-improvement engine |
| `policy_engine.py` | 45 policies (P1-P45) across 6 categories |
| `loop_guardrail.py` | Infinite loop protection |
| `tool_executor.py` | Sandbox tool executor |
| `metrics_collector.py` | Centralized metrics |

### Policy Engine (45 Policies)
| Category | Count | Examples |
|----------|-------|----------|
| CORE | P1-P10 | Task Routing, Agent Capability |
| SAFETY | P11-P20 | High Risk Files, Secret Exposure |
| QUALITY | P21-P30 | Code Style, Test Coverage |
| RESOURCE | P31-P37 | CPU/Memory Limits, API Rate Limits |
| LEARNING | P38-P42 | Strategy Evolution |
| SUSTAINABILITY | P43-P45 | Carbon Footprint, Cost Efficiency |

### Backend Agent Systems
- `DomainBlackboard` (`/backend/agents/coordination/blackboard.py`) - Redis-based communication
- `LearningPathAgent` (`/backend/agents/learning_path_agent.py`) - ZPD-aware recommendations
- YKS Plugin (`/.claude/plugins/installed/kiro2-yks/`) - IRT/ZPD/FSRS calculators

---

## Section 4: OCR / DATASET PIPELINE

**Path:** `C:\Users\husey\kiro2\d-dataset`

### Directory Structure
```
d-dataset/
├── config.yaml                    # Main configuration
├── requirements.txt               # Python dependencies
├── scripts/                       # Main processing scripts (NOT git-tracked)
│   ├── pipeline.py               # Main YOLO + Multi-Provider OCR
│   ├── script_common.py          # Shared utilities (1,824 lines)
│   ├── ai_solve_pipeline.py      # AI self-solving
│   ├── cevap_crop_ocr.py         # Answer key extraction
│   └── ...
├── output/                        # Processing outputs
│   ├── detections/               # YOLO detection JSON
│   ├── crops/                     # Cropped question regions
│   ├── ocr_v3/                    # OCR results
│   ├── answer_keys_v8/            # SQLite answer keys
│   └── final/                     # Final processed data
├── processed/                     # Processed data (NOT git-tracked)
│   ├── eslesmis_sorucevap*.jsonl # Matched Q&A datasets
│   └── quality_improvement/
├── backups/                       # Backup versions
└── CLAUDE.md                      # Project metadata
```

### Production Data (v3.5+)
| Metric | Value |
|--------|-------|
| Total Questions | **77,336** |
| Books Processed | 405 |
| Validation Pass Rate | 100% |
| Critical Errors | 0 |
| Match Rate | ~85% book, ~15% AI |

### Pipeline Stages
1. **Book Screenshot Processing** - PNG screenshots from 400+ YKS books
2. **YOLO Object Detection** - YOLO26 model (7 classes: soru, konu, cevaplar, etc.)
3. **Region Cropping** - Question regions, answer options, topics
4. **OCR Processing** - Multi-provider (Gemini, GPT-4o-mini, Qwen2.5-VL-2B, PaddleOCR)
5. **Answer Key Extraction** - Three-phase (scan OCR, book-end pages, crop OCR)
6. **Question-Answer Matching** - Page-based (95%), YOLO test_no (90%), smart estimation (65-85%)
7. **AI Self-Solving** - Gemini Flash with 3x CoT + majority voting
8. **Quality Validation** - Hallucination detection, minimum thresholds

### Key Scripts
| Script | Purpose |
|--------|---------|
| `pipeline.py` | Main orchestrator - YOLO + OCR |
| `script_common.py` | Shared utilities: Turkish normalization, image preprocessing |
| `ai_solve_pipeline.py` | Self-solving MCQs |
| `match_questions_v5.py` | Q&A matching with ultra-quality filtering |
| `ab_validate_ocr.py` | A/B testing for OCR |
| `validate_3tier.py` | 3-tier validation |
| `import_to_kiro2.py` | Import to PostgreSQL |

---

## Section 5: INFRA / DOCKER / CONFIG / TEST

### Docker Configuration
| File | Purpose |
|------|---------|
| `Dockerfile` | Main backend Dockerfile |
| `Dockerfile.production` | Multi-stage production (Node.js + Python) |
| `Dockerfile.dev` | Development with hot reload |
| `Dockerfile.minimal` | Minimal backend |
| `backend/Dockerfile` | Backend with uv optimization |

### Docker Compose
| File | Purpose |
|------|---------|
| `docker-compose.yml` | Production stack |
| `docker-compose.dev.yml` | Development stack |
| `monitoring/docker-compose.monitoring.yml` | Monitoring (Prometheus, Grafana) |

### Environment Files
- `.env.example`, `.env.production`, `.env.development`, `.env.local`
- `.env.docker`, `.env.mvp`, `.env.test`, `.env.mcp.example`
- `backend/.env`, `backend/.env.production`

### Test Infrastructure
```
backend/tests/
├── conftest.py              # Main pytest config
├── conftest_postgres.py     # PostgreSQL fixtures
├── conftest_security.py      # Security fixtures
├── unit/                    # Unit tests
├── integration/             # Integration tests
├── e2e_fullstack/          # E2E tests (Playwright)
├── services/               # Service tests
├── core/                   # Core module tests
└── ...
```

**Pytest Configuration:**
- Framework: pytest 7.4.3 + pytest-asyncio
- Coverage: 80% threshold
- Markers: 30+ (unit, integration, e2e, slow, fast, ai, db, redis, ml, fsrs, irt, zpd, load)

### CI/CD (`.github/workflows/`)
| File | Purpose |
|------|---------|
| `ci.yml` | Quality, tests, build |
| `deploy.yml` | Multi-environment deployment |
| `security.yml` | Security scanning |
| `quality-gates.yml` | Quality gates |
| `health-checks.yml` | Health monitoring |
| `release.yml` | Release management |

### Monitoring Stack
- **Prometheus** - Metrics collection (30-day retention)
- **Grafana** - Visualization (port 3100)
- **Alertmanager** - Alert routing
- **Node/Redis/Postgres Exporters** - Target metrics

### Kubernetes (`kubernetes/`)
- `deployment.yaml`, `service.yaml`, `secrets.yaml`
- `statefulset.yaml`, `hpa.yaml`, `pvc.yaml`, `rbac.yaml`
- `filebeat/`, `logstash/`, `kibana/` - Log processing
- `postgres-replication/` - PostgreSQL HA

### Security Config
- `.secrets.baseline` - detect-secrets
- `ssl/` - TLS certificates
- Non-root containers
- Pre-commit hooks (ruff, mypy, bandit, detect-secrets)

---

## Critical File Paths Summary

| Section | Key File |
|---------|----------|
| Backend Entry | `backend/main.py`, `backend/core/application.py` |
| Backend Auth | `backend/core/auth.py` (16+ auth modules!) |
| Backend API | `backend/api/auth.py` (61KB), `backend/api/learning_path_v2.py` (74KB) |
| Backend DB | `backend/core/database.py` (asyncpg, pool_size=200) |
| Frontend Entry | `frontend/src/main.tsx`, `frontend/src/App.tsx` |
| Frontend State | `frontend/src/store/authStore.ts` |
| Frontend API | `frontend/src/services/apiClient.ts` |
| Orchestrator | `orchestrator/master_orchestrator.py`, `orchestrator/core/graph.py` |
| Pipeline | `d-dataset/scripts/pipeline.py` |
| Production Data | `d-dataset/processed/eslesmis_sorucevap.jsonl` (77,336 questions) |
| Docker | `docker-compose.yml`, `Dockerfile` |
| Monitoring | `monitoring/docker-compose.monitoring.yml` |

---

## Known Issues (Quick Reference)

| Issue | Section | Severity |
|-------|---------|----------|
| 16+ auth modules fragmentation | Backend | HIGH |
| 43 disabled routers | Backend | HIGH |
| 4.4MB api.ts needs split | Frontend | MEDIUM |
| 783 console.log statements | Frontend | MEDIUM |
| In-memory rate limiting | Backend | MEDIUM |
| TODO markers in orchestrator | Orchestrator | MEDIUM |
| Policy engine validators are stubs | Orchestrator | MEDIUM |
| Self-improvement not active | Orchestrator | LOW |

---

*Last Updated: 2026-04-05*