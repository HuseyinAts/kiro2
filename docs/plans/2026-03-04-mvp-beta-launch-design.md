# MVP Beta Launch Design

## Date: 2026-03-04
## Status: APPROVED

## Problem Statement

KIRO2 has 77,336 questions, a full backend (150+ routers), a full frontend (80 pages, 337 components, 23+ services), Docker/K8s infrastructure, and 8 CI/CD workflows. But none of it has been tested end-to-end. We need to verify it actually works as a system.

## Key Finding

**Auth endpoint alignment confirmed:** Frontend and backend auth endpoints match perfectly (login/secure, logout/secure, refresh/secure, register, me). The httpOnly cookie flow is implemented on both sides. No code changes needed for auth routing.

## Architecture (Existing)

```
Frontend (React 18, Vite, port 3001)
  → Axios client (withCredentials: true)
  → Vite proxy: /api/* → localhost:8000
  → httpOnly cookie auth

Backend (FastAPI, Uvicorn, port 8000)
  → 150+ routers (dynamic loader)
  → PostgreSQL 15 (port 5434, 77K questions)
  → Redis 7 (port 6379, session cache)
  → pgvector (semantic search, 21ms avg)

Docker (docker-compose.minimal.yml)
  → backend + postgres + redis
  → frontend Dockerfile + nginx
```

## Implementation Plan (4 Phases)

### Phase 1: Backend Smoke Test
**Goal:** Verify backend starts, connects to DB, loads routers

1. Start backend with `python main.py`
2. Test health endpoint: `GET /health`
3. Test router loading: `GET /docs` (OpenAPI)
4. Test DB connection: Check question_bank table
5. Test auth: `POST /api/v1/auth/kayit` + `POST /api/v1/auth/login/secure`
6. Test semantic search: `POST /api/v1/questions/semantic-search`

**Success:** Backend returns 200 on all endpoints

### Phase 2: Auth E2E Flow
**Goal:** Complete login → access → refresh → logout cycle

1. Register test user via `/api/v1/auth/register`
2. Login via `/api/v1/auth/login/secure` → verify httpOnly cookies set
3. Access protected endpoint with cookie → verify 200
4. Refresh via `/api/v1/auth/refresh/secure` → verify new cookie
5. Logout via `/api/v1/auth/logout/secure` → verify cookies cleared
6. Access protected endpoint → verify 401

**Potential Issues:**
- `secure=True` on cookies blocks HTTP (non-HTTPS) in dev → may need `secure=False` for local
- CORS withCredentials needs exact origin match (not wildcard)
- Cookie `path=/api` may not match Vite proxy paths

### Phase 3: Frontend-Backend Integration
**Goal:** Frontend pages load data from backend

1. Start both backend (8000) and frontend (3001)
2. Open login page → submit credentials → verify redirect to dashboard
3. Student dashboard → verify API calls succeed (stats, recommendations)
4. Exam flow → create session → answer questions → submit
5. Semantic search → query → verify results
6. Logout → verify redirect to login

**Potential Issues:**
- Vite proxy config must match backend routes
- CORS origin must include `http://localhost:3001`
- Missing data (no exam sessions, no student profiles) → need seed data

### Phase 4: Docker Compose Packaging
**Goal:** Single `docker-compose up` starts everything

1. Verify `docker-compose.minimal.yml` config
2. Build backend image: `docker build -f backend/Dockerfile .`
3. Build frontend image: `docker build -f frontend/Dockerfile .`
4. Start stack: `docker-compose -f docker-compose.minimal.yml up`
5. Test all Phase 1-3 scenarios through Docker
6. Fix any container networking issues

**Potential Issues:**
- `localhost:5434` won't work inside container (use service name)
- Env vars need Docker-specific values
- Frontend nginx config must proxy to backend service name

## Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| DB not running | Check PostgreSQL 18 service on port 5434 first |
| Cookie secure=True blocks HTTP | Add dev override: secure=False when ENVIRONMENT=development |
| CORS blocks frontend | Ensure localhost:3001 in allowed_origins |
| Missing seed data | Create seed script for test user + exam session |
| Router import failures | Backend has graceful fallback mode |

## Out of Scope (Post-MVP)

- SSL/TLS certificates (use HTTP for local beta)
- Kubernetes deployment (Docker Compose sufficient for beta)
- Performance optimization (already 21ms search)
- Monitoring stack (Prometheus/Grafana)
- CI/CD pipeline fixes
