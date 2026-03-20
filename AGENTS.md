# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Scope and critical constraints
- This is a large monorepo with three active engineering surfaces: `backend/`, `frontend/`, and `orchestrator/`.
- Do not run repository-wide text search from the repo root on this project size. Scope searches to specific directories (for example `backend/`, `frontend/`, `orchestrator/`, `docs/`).
- Treat these paths as read-only unless explicitly directed by the repository owner:
  - `d-dataset/ocr_output/**`
  - `d-dataset/answer_keys/**`
  - `d-dataset/eslesmis_sorucevap.jsonl`
  - `backend/alembic/versions/*.py`
  - `backend/core/config.py`
  - `.env*`, `.git/**`, `node_modules/**`, `venv/**`
- Use `orchestrator/` (active). Do not use any deprecated `kiro2-orchestrator/` path.

## Platform notes from project rules
- Primary local environment is Windows + PowerShell. Prefer Windows-safe commands and use `python` (not `python3`).
- Frontend dev server is configured for port `3001` in `frontend/vite.config.ts`.
- Backend default API port is `8000`.
- PostgreSQL default local port in this repo is `5434`.

## Common development commands
All commands below are verified from repository scripts/config.

### Preferred one-command workflow (PowerShell, repo root)
```powershell
.\scripts\dev.ps1 help
.\scripts\dev.ps1 backend
.\scripts\dev.ps1 frontend
.\scripts\dev.ps1 lint
.\scripts\dev.ps1 mypy
.\scripts\dev.ps1 test
.\scripts\dev.ps1 test-fast
.\scripts\dev.ps1 test-cov
.\scripts\dev.ps1 check
```

### Backend (from repo root unless noted)
```powershell
# run API
.\scripts\dev.ps1 backend

# lint / format / type-check
ruff check backend/
ruff format backend/
mypy backend/ --config-file pyproject.toml

# tests
cd backend; pytest -v --tb=short
cd backend; pytest -m "not slow" --tb=short -x
cd backend; pytest --cov=. --cov-report=term-missing --cov-report=html

# run a single backend test
cd backend; pytest tests\path\to\test_file.py::TestClass::test_name -v
```

### Frontend
```powershell
cd frontend; npm install
cd frontend; npm run dev
cd frontend; npm run build
cd frontend; npm run lint
cd frontend; npm run type-check
cd frontend; npm test
cd frontend; npm run test:coverage

# run a single frontend test file / test case
cd frontend; npm test -- src\components\MyComponent.test.tsx
cd frontend; npx vitest run src\components\MyComponent.test.tsx -t "test name"
```

### Orchestrator
```powershell
cd orchestrator; pytest tests\ -v
python orchestrator\test_complete_system.py
```

### Docker stacks (repo root)
```powershell
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml down
```

## Big-picture architecture (what matters first)
### 1) Backend request lifecycle
- Entry point is `backend/main.py`, which creates `app` via `core.application.create_app()`.
- Application assembly lives in `backend/core/application.py`:
  - lifespan startup/shutdown (DB init/close, agent lifecycle)
  - middleware stack (timing, CORS, cache headers, gzip)
  - optional rate limiting (`slowapi`)
  - OpenAPI customization
- Routers are dynamically imported and registered by `backend/routers/loader.py` from `api.*` modules through a central mapping. To understand endpoint availability, inspect router mapping and imported modules rather than assuming static includes.

### 2) Auth and dependency model
- `backend/core/dependencies.py` is the central auth/dependency layer.
- Auth supports both Bearer token and httpOnly cookie flows (`get_current_user` checks header first, then cookie).
- Role checks are dependency-driven (`student/teacher/admin` guards), so API authorization behavior is typically enforced through FastAPI dependency wiring.

### 3) Frontend composition model
- Entry: `frontend/src/main.tsx` → renders `App` from `frontend/src/app.tsx`.
- `app.tsx` is the composition root: Theme, QueryClient, AuthProvider, Router, protected routes, error boundary, and major lazy-loaded route/page modules.
- Route access is role-based through `ProtectedRoute` and role strings used in UI state (`ogrenci`, `ogretmen`, `veli`, `admin`).
- State architecture:
  - Client/server fetch state: React Query.
  - Global client state: Zustand stores in `frontend/src/store/` (`authStore`, `examStore`, `uiStore`, `settingsStore`, `notificationStore`).
  - `authStore` is cookie-session oriented (no localStorage token persistence).

### 4) Orchestrator subsystem
- `orchestrator/core/graph.py` defines a LangGraph state machine: plan → route → implement → quality_check → review/fix loop → report.
- `orchestrator/core/routing.py` contains policy-based task analysis/routing by risk, domain keywords, and task type.
- `orchestrator/core/state.py` enforces run-scoped state, quality-gate tracking, no-progress detection, and diff/iteration limits.
- Treat this as a separate execution/control plane, not just utility scripts.

## Turkish text handling rule (project-critical)
When normalizing Turkish text for matching/comparison, preserve this order:
1. Unicode normalize to NFC
2. Turkish-specific mapping: `İ→i`, `I→ı`
3. Then lowercase

Do not apply naive lowercase first for Turkish-sensitive paths.
