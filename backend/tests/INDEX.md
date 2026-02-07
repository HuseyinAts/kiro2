# KIRO2 Test Suite Index

Complete reference for all test files in the KIRO2 backend test suite.

---

## 📁 Directory Structure

```
backend/tests/
├── INDEX.md (this file)
├── QUICK_START.md
├── TEST_CREATION_SUMMARY.md
├── run_new_tests.py
│
├── unit/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── test_auth_route.py
│   │   ├── test_health_route.py
│   │   ├── test_sinav_route.py
│   │   ├── test_learning_path_route.py
│   │   └── test_gamification_route.py
│   │
│   └── (other unit tests...)
│
├── db/
│   ├── test_seed_data.py
│   ├── test_connection_pool.py
│   └── test_indexes.py
│
├── devops/
│   ├── __init__.py
│   ├── test_docker.py
│   ├── test_health_components.py
│   └── test_graceful_shutdown.py
│
├── functional/
│   ├── test_video_integration.py
│   ├── test_accessibility.py
│   ├── test_gamification.py
│   ├── test_admin_panel.py
│   ├── test_cultural_adaptation.py
│   └── test_question_bank_quality.py
│
└── integration/
    └── scenarios/
        ├── __init__.py
        └── test_e2e_scenarios.py
```

---

## 🎯 Test Categories

### 1. API Route Tests (`unit/api/`)

#### test_auth_route.py (UT-03.1)
**Purpose:** Authentication and authorization endpoints
**Tests:** 8
**Key Coverage:**
- User registration (kayit)
- User login (giris)
- Profile retrieval
- Password change
- Token refresh
- Logout

**Run:**
```bash
pytest tests/unit/api/test_auth_route.py -v
```

#### test_health_route.py (UT-03.2)
**Purpose:** Health check and monitoring endpoints
**Tests:** 8
**Key Coverage:**
- Basic health endpoint
- Kubernetes probes (readiness, liveness, startup)
- Database health
- Detailed health checks
- Version information

**Run:**
```bash
pytest tests/unit/api/test_health_route.py -v
```

#### test_sinav_route.py (UT-03.3)
**Purpose:** Exam (sinav) functionality
**Tests:** 6
**Key Coverage:**
- Exam creation
- Answer submission
- Question flagging
- Navigation
- Session management
- Performance metrics

**Run:**
```bash
pytest tests/unit/api/test_sinav_route.py -v
```

#### test_learning_path_route.py (UT-03.4)
**Purpose:** Learning path generation and management
**Tests:** 5
**Key Coverage:**
- Student profile creation
- Path generation
- Resource retrieval
- Progress tracking
- Completion status

**Run:**
```bash
pytest tests/unit/api/test_learning_path_route.py -v
```

#### test_gamification_route.py (UT-03.8)
**Purpose:** Gamification features
**Tests:** 4
**Key Coverage:**
- XP earning
- Level progression
- Badge system
- Leaderboards

**Run:**
```bash
pytest tests/unit/api/test_gamification_route.py -v
```

---

### 2. Database Tests (`db/`)

#### test_seed_data.py (DB-04)
**Purpose:** Seed data configuration validation
**Tests:** 8
**Key Coverage:**
- Minimum question counts
- TYT/AYT subject distribution
- User role definitions
- IRT parameter ranges
- Bloom's Taxonomy levels
- MEB grade levels
- University data schema

**Run:**
```bash
pytest tests/db/test_seed_data.py -v
```

#### test_connection_pool.py (DB-05)
**Purpose:** Database connection pool configuration
**Tests:** 5
**Key Coverage:**
- Pool size settings
- Max overflow configuration
- Pool recycle settings
- Connection string format
- Async driver (asyncpg)
- Port 5434 verification

**Run:**
```bash
pytest tests/db/test_connection_pool.py -v
```

#### test_indexes.py (DB-06)
**Purpose:** Database index requirements
**Tests:** 4
**Key Coverage:**
- User email index
- Question subject index
- Question difficulty index
- Exam answers composite index

**Run:**
```bash
pytest tests/db/test_indexes.py -v
```

---

### 3. DevOps Tests (`devops/`)

#### test_docker.py (DO-01)
**Purpose:** Docker configuration validation
**Tests:** 6
**Key Coverage:**
- Dockerfile existence
- Production Dockerfile
- .dockerignore
- docker-compose.yml
- Non-root user configuration
- HEALTHCHECK instruction

**Run:**
```bash
pytest tests/devops/test_docker.py -v
```

#### test_health_components.py (DO-02)
**Purpose:** Health check component structure
**Tests:** 5
**Key Coverage:**
- Health checker import
- Kubernetes probes
- Health status enumeration
- ComponentHealth structure
- check_all method

**Run:**
```bash
pytest tests/devops/test_health_components.py -v
```

#### test_graceful_shutdown.py (DO-03)
**Purpose:** Graceful shutdown configuration
**Tests:** 3
**Key Coverage:**
- Lifespan handler
- Shutdown events
- Signal handling (SIGTERM, SIGINT)

**Run:**
```bash
pytest tests/devops/test_graceful_shutdown.py -v
```

---

### 4. Functional Tests (`functional/`)

#### test_video_integration.py (F-06)
**Purpose:** Video platform integrations
**Tests:** 6
**Key Coverage:**
- YouTube search
- Khan Academy
- EBA (MEB) integration
- Video analytics
- Transcripts
- Recommendations

**Run:**
```bash
pytest tests/functional/test_video_integration.py -v
```

#### test_accessibility.py (F-07)
**Purpose:** Accessibility and special needs support
**Tests:** 8
**Key Coverage:**
- ADHD Pomodoro timer
- Focus mode
- Task splitting
- Text simplification
- Bionic reading
- Text-to-speech (TTS)
- Virtual manipulatives
- WCAG compliance

**Run:**
```bash
pytest tests/functional/test_accessibility.py -v
```

#### test_gamification.py (F-08)
**Purpose:** Gamification system
**Tests:** 6
**Key Coverage:**
- XP earning
- Level progression
- Badge achievements
- Leaderboards
- Streak tracking
- Team challenges

**Run:**
```bash
pytest tests/functional/test_gamification.py -v
```

#### test_admin_panel.py (F-14)
**Purpose:** Admin panel functionality
**Tests:** 5
**Key Coverage:**
- Admin authentication
- User management
- Content management
- System settings
- Monitoring dashboard

**Run:**
```bash
pytest tests/functional/test_admin_panel.py -v
```

#### test_cultural_adaptation.py (F-15)
**Purpose:** Turkish cultural adaptation
**Tests:** 5
**Key Coverage:**
- Ramadan mode
- Holiday adaptation
- YKS stress management
- Family pressure factors
- Regional customization

**Run:**
```bash
pytest tests/functional/test_cultural_adaptation.py -v
```

#### test_question_bank_quality.py (K-05)
**Purpose:** Question bank quality requirements
**Tests:** 8
**Key Coverage:**
- Minimum question counts
- Subject-specific minimums
- Difficulty distribution (30/50/20)
- OSYM format (5 options)
- Correct answer validation

**Run:**
```bash
pytest tests/functional/test_question_bank_quality.py -v
```

---

### 5. Integration Tests (`integration/scenarios/`)

#### test_e2e_scenarios.py (UT-05)
**Purpose:** End-to-end user workflows
**Tests:** 10
**Key Coverage:**
- Register → Login → Profile
- Exam → Answer → Results
- Question generation → Storage → Query
- Learning path → Progress → Completion
- IRT → ZPD → Adaptive exam
- FSRS card → Review → Interval
- Chat → AI response → Save
- Teacher → Students → Reports
- KVKK consent → Query → Delete
- XP → Badge → Leaderboard

**Run:**
```bash
pytest tests/integration/scenarios/test_e2e_scenarios.py -v
```

---

## 🚀 Quick Commands

### Run Everything
```bash
python tests/run_new_tests.py
```

### Run by Category
```bash
pytest tests/unit/api/ -v          # API tests
pytest tests/db/ -v                # Database tests
pytest tests/devops/ -v            # DevOps tests
pytest tests/functional/ -v        # Functional tests
pytest tests/integration/scenarios/ -v  # E2E tests
```

### Run by Pattern
```bash
pytest tests/ -k "auth" -v         # All auth-related tests
pytest tests/ -k "health" -v       # All health-related tests
pytest tests/ -k "gamification" -v # All gamification tests
```

### With Coverage
```bash
pytest tests/unit/api/ --cov=backend/api --cov-report=term-missing
pytest tests/ --cov=backend --cov-report=html
```

---

## 📊 Test Statistics

| Category | Files | Tests | Lines | Coverage Focus |
|----------|-------|-------|-------|----------------|
| API Routes | 5 | 31 | ~1600 | Endpoint validation |
| Database | 3 | 17 | ~800 | Config & schema |
| DevOps | 3 | 14 | ~700 | Docker & health |
| Functional | 6 | 38 | ~2000 | Feature integration |
| Integration | 1 | 10 | ~600 | E2E workflows |
| **TOTAL** | **18** | **110** | **~5700** | **Comprehensive** |

---

## 📋 Quality Standards

All tests follow:

✅ **Boris Cherny Verification Standards**
- Meaningful assertions only
- No `assert True` patterns
- Verification feedback loops

✅ **KIRO2 Standards**
- Port 5434 for PostgreSQL
- Turkish UTF-8 encoding
- IRT parameters: [-4.0, 4.0]
- Async/await patterns
- Pydantic validation

✅ **Test Isolation**
- Independent tests
- Mocked external dependencies
- Database transaction rollback
- No shared state

---

## 🔍 Finding Tests

### By Feature
- **Authentication:** `test_auth_route.py`
- **Health Checks:** `test_health_route.py`, `test_health_components.py`
- **Exams:** `test_sinav_route.py`
- **Learning Paths:** `test_learning_path_route.py`
- **Gamification:** `test_gamification_route.py`, `test_gamification.py`
- **Video:** `test_video_integration.py`
- **Accessibility:** `test_accessibility.py`
- **Admin:** `test_admin_panel.py`
- **Cultural:** `test_cultural_adaptation.py`
- **Database:** `test_seed_data.py`, `test_connection_pool.py`, `test_indexes.py`
- **Docker:** `test_docker.py`
- **E2E:** `test_e2e_scenarios.py`

### By Test ID
Use the test IDs from documentation:
- UT-03.1: `test_auth_route.py`
- UT-03.2: `test_health_route.py`
- UT-03.3: `test_sinav_route.py`
- UT-03.4: `test_learning_path_route.py`
- UT-03.8: `test_gamification_route.py`
- DB-04: `test_seed_data.py`
- DB-05: `test_connection_pool.py`
- DB-06: `test_indexes.py`
- DO-01: `test_docker.py`
- DO-02: `test_health_components.py`
- DO-03: `test_graceful_shutdown.py`
- F-06: `test_video_integration.py`
- F-07: `test_accessibility.py`
- F-08: `test_gamification.py`
- F-14: `test_admin_panel.py`
- F-15: `test_cultural_adaptation.py`
- K-05: `test_question_bank_quality.py`
- UT-05: `test_e2e_scenarios.py`

---

## 📚 Documentation

- **QUICK_START.md** - Getting started guide
- **TEST_CREATION_SUMMARY.md** - Detailed test documentation
- **run_new_tests.py** - Automated test runner
- **.claude/rules/testing.md** - Testing standards
- **.claude/rules/verification.md** - Verification rules

---

**Last Updated:** 2026-01-28
**KIRO2 Version:** 1.0
**Total Tests:** 110
**Coverage Target:** 60%+ global, 80%+ services
