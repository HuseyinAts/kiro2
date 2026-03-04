# MVP Beta Launch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Verify KIRO2 frontend-backend-docker stack works end-to-end, fix integration issues, and package for beta.

**Architecture:** Existing FastAPI backend (150+ routers, PostgreSQL 15, Redis 7) + React 18 frontend (80 pages, 23+ services, Zustand). httpOnly cookie auth. Vite dev proxy at port 3001 → 8000.

**Tech Stack:** Python 3.11+, FastAPI, asyncpg, React 18, Vite, Docker Compose, PostgreSQL 15 (port 5434), Redis 7 (port 6379)

---

## Pre-Flight Checks

Before starting, verify these services are running:

```bash
# PostgreSQL 18 on port 5434
pg_isready -h localhost -p 5434
# Expected: localhost:5434 - accepting connections

# Redis on port 6379
redis-cli ping
# Expected: PONG
```

---

## Task 1: Fix Backend Environment Config

**Files:**
- Modify: `backend/.env`

**Known issues from exploration:**
1. `ALLOWED_ORIGINS` missing `http://localhost:3001` (frontend port)
2. `DATABASE_URL` says `kiro2_db` but real DB is `kiro2`

**Step 1: Fix .env**

```bash
# In backend/.env, change:
DATABASE_URL=postgresql+asyncpg://postgres:changeme_strong_password_here@localhost:5434/kiro2
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
```

**Step 2: Verify DB name**

```bash
cd backend
python -c "from core.config import settings; print(settings.database_url)"
# Expected: ...localhost:5434/kiro2
```

**Step 3: Commit**

```bash
git add backend/.env
# NOTE: .env is gitignored, no commit needed - just local fix
```

---

## Task 2: Backend Smoke Test — Start Server

**Files:**
- Read: `backend/main.py`
- Read: `backend/core/application.py`

**Step 1: Start backend**

```bash
cd backend
python main.py
```

**Expected output:**
```
KIRO2 Backend Starting...
  Environment: development
  Database: postgresql+asyncpg://...
Database initialized
Routers loaded successfully
KIRO2 Backend Started Successfully!
Starting KIRO2 Backend Server
  Host: 0.0.0.0
  Port: 8000
```

**Step 2: Test health endpoint**

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"} or similar

curl http://localhost:8000/
# Expected: {"app": "KIRO2 Educational Platform", ...}
```

**Step 3: Test OpenAPI docs**

Open browser: http://localhost:8000/docs
- Expected: Swagger UI with all 150+ endpoints listed
- Verify `/api/v1/auth/login/secure` is visible

**Step 4: Record any startup errors**

If backend fails to start, common fixes:
- Import errors → missing dependency, install with `pip install <package>`
- DB connection error → check PostgreSQL is on port 5434
- Redis error → non-fatal, backend should start without Redis

---

## Task 3: Backend Auth Test — Register + Login

**Step 1: Register a test user**

```bash
curl -X POST http://localhost:8000/api/v1/auth/kayit \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@kiro2.com",
    "sifre": "TestSifre1!",
    "ad": "Test",
    "soyad": "User",
    "rol": "ogrenci"
  }'
```

Expected: `{"success": true, ...}` or `{"detail": "Bu e-posta adresi zaten kayıtlı"}` if already exists.

**Step 2: Login via secure endpoint**

```bash
curl -v -X POST http://localhost:8000/api/v1/auth/login/secure \
  -H "Content-Type: application/json" \
  -d '{"email": "test@kiro2.com", "sifre": "TestSifre1!"}' \
  -c cookies.txt
```

Expected:
- HTTP 200
- Response body: `{"success": true, "message": "Giriş başarılı", "user": {...}}`
- Set-Cookie headers: `access_token=...; HttpOnly; Path=/api` and `refresh_token=...; HttpOnly; Path=/api/v1/auth`

**IMPORTANT:** If `secure=True` blocks cookies over HTTP, this is a known issue. See Task 4.

**Step 3: Test /me with cookie**

```bash
curl http://localhost:8000/api/v1/auth/me \
  -b cookies.txt
```

Expected: User info JSON, OR 401 if cookie not accepted (secure=True issue).

**Step 4: Test logout**

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout/secure \
  -b cookies.txt -c cookies.txt
```

Expected: `{"success": true, "message": "Çıkış başarılı"}`

---

## Task 4: Fix Cookie secure=True for Local Development

**Files:**
- Modify: `backend/api/auth.py:443-462`

**Problem:** `secure=True` on cookies means they only work over HTTPS. Local dev uses HTTP, so cookies won't be set.

**Step 1: Add environment-aware cookie security**

In `backend/api/auth.py`, find the `secure_login` function (~line 443) and change:

```python
# BEFORE (line 447):
secure=True,  # Only HTTPS in production

# AFTER:
secure=settings.environment != "development",  # HTTP in dev, HTTPS in prod
```

Apply same fix to refresh_token cookie (~line 458):

```python
# BEFORE:
secure=True,

# AFTER:
secure=settings.environment != "development",
```

Also need to add import at top of file if not present:
```python
from core.config import settings
```

**Step 2: Verify the fix**

```bash
# Restart backend, then:
curl -v -X POST http://localhost:8000/api/v1/auth/login/secure \
  -H "Content-Type: application/json" \
  -d '{"email": "test@kiro2.com", "sifre": "TestSifre1!"}' \
  -c cookies.txt
```

Now cookies should be set even over HTTP.

**Step 3: Test full auth cycle**

```bash
# Login
curl -v -X POST http://localhost:8000/api/v1/auth/login/secure \
  -H "Content-Type: application/json" \
  -d '{"email": "test@kiro2.com", "sifre": "TestSifre1!"}' \
  -c cookies.txt

# Access protected endpoint
curl http://localhost:8000/api/v1/auth/me -b cookies.txt
# Expected: 200 with user data

# Refresh
curl -X POST http://localhost:8000/api/v1/auth/refresh/secure -b cookies.txt -c cookies.txt
# Expected: 200 with new cookie

# Logout
curl -X POST http://localhost:8000/api/v1/auth/logout/secure -b cookies.txt -c cookies.txt
# Expected: 200

# Access after logout
curl http://localhost:8000/api/v1/auth/me -b cookies.txt
# Expected: 401
```

**Step 4: Commit**

```bash
git add backend/api/auth.py
git commit -m "fix(auth): use secure=False for cookies in development mode"
```

---

## Task 5: Test Semantic Search Endpoint

**Step 1: Test search**

```bash
curl -X POST http://localhost:8000/api/v1/questions/semantic-search \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"query": "integral hesaplama", "top_k": 5}'
```

Expected: JSON with question results and similarity scores.

If 401: endpoint may require auth. Login first (Task 3 Step 2).
If 404: check router is loaded in /docs.
If 500: check Ollama running for embeddings.

**Step 2: Test with filters**

```bash
curl -X POST http://localhost:8000/api/v1/questions/semantic-search \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"query": "fizik kuvvet", "top_k": 3, "exam_type": "TYT"}'
```

---

## Task 6: Frontend Build Test

**Step 1: Install dependencies**

```bash
cd frontend
npm install
```

**Step 2: Type check**

```bash
npx tsc --noEmit 2>&1 | tail -5
```

If errors: note them but continue (TypeScript errors don't block runtime).

**Step 3: Start dev server**

```bash
npm run dev
# Expected: VITE v5.x.x ready in X ms
#   Local: http://localhost:3001/
```

**Step 4: Verify proxy works**

```bash
# From a separate terminal:
curl http://localhost:3001/api/v1/auth/me
# Expected: 401 (proxied to backend, which returns 401 for unauthenticated)
# NOT 404 (would mean proxy isn't working)
```

---

## Task 7: Frontend-Backend Integration — Login Flow

**Step 1: Open browser**

Navigate to: http://localhost:3001/login

**Step 2: Inspect login page**

- Login form should appear
- Check browser console for errors (F12 → Console)
- Common errors: CORS, 404, network errors

**Step 3: Submit login**

- Email: `test@kiro2.com`
- Password: `TestSifre1!`
- Click login button

Expected:
- Network tab shows POST to `/api/v1/auth/login/secure`
- Response: 200 with user data
- Set-Cookie in response headers
- Redirect to `/student/dashboard` or similar

**Step 4: Check dashboard loads data**

After login:
- Dashboard should load
- Network tab shows API calls (stats, recommendations)
- Some may 404 if endpoints return no data — that's OK for MVP

**Step 5: Record all errors**

Document every console error, network failure, and UI issue. These become fix tasks.

---

## Task 8: Fix CORS for Cookie Auth

**Files:**
- Modify: `backend/core/application.py` or `backend/.env`

**Problem:** Cookie auth requires `withCredentials: true` which means CORS cannot use `allow_origins=["*"]`. Must use exact origins.

**Step 1: Verify CORS config**

Check `backend/core/application.py` for CORSMiddleware setup. Ensure:

```python
CORSMiddleware(
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,  # MUST be True for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 2: If CORS reads from settings**

Ensure `backend/.env` has:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
```

**Step 3: Test CORS**

```bash
curl -v -X OPTIONS http://localhost:8000/api/v1/auth/login/secure \
  -H "Origin: http://localhost:3001" \
  -H "Access-Control-Request-Method: POST"
```

Expected headers:
- `Access-Control-Allow-Origin: http://localhost:3001`
- `Access-Control-Allow-Credentials: true`

**Step 4: Commit if changed**

```bash
git add backend/core/application.py
git commit -m "fix(cors): add localhost:3001 to allowed origins for cookie auth"
```

---

## Task 9: Docker Compose Verification

**Files:**
- Read: `docker-compose.minimal.yml`
- May modify: `docker-compose.minimal.yml`

**Step 1: Check current docker-compose.minimal.yml**

Current config has backend + frontend but NO PostgreSQL/Redis services. The minimal compose expects external DB.

For MVP, we use the existing native PostgreSQL (port 5434) and Redis (port 6379) running on the host.

**Step 2: Test backend Docker build**

```bash
cd backend
docker build -f Dockerfile.minimal -t kiro2-backend:mvp .
```

**Step 3: Test frontend Docker build**

```bash
cd frontend
docker build -t kiro2-frontend:mvp .
```

**Step 4: Run with host networking**

```bash
# Backend connecting to host DB
docker run --rm -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -e DATABASE_URL=postgresql+asyncpg://postgres:changeme_strong_password_here@host.docker.internal:5434/kiro2 \
  -e REDIS_URL=redis://host.docker.internal:6379/0 \
  -e ENVIRONMENT=development \
  -e JWT_SECRET_KEY=dev-jwt-secret \
  -e ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173 \
  kiro2-backend:mvp
```

**Step 5: Test**

```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

---

## Task 10: Create MVP Docker Compose

**Files:**
- Create: `docker-compose.mvp.yml`

**Step 1: Write MVP compose file**

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.minimal
    container_name: kiro2-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:changeme_strong_password_here@host.docker.internal:5434/kiro2
      - REDIS_URL=redis://host.docker.internal:6379/0
      - ENVIRONMENT=development
      - DEBUG=true
      - JWT_SECRET_KEY=dev-jwt-secret
      - JWT_ALGORITHM=HS256
      - ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
      - PYTHONUNBUFFERED=1
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: kiro2-frontend
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

**Step 2: Test**

```bash
docker-compose -f docker-compose.mvp.yml up --build
```

**Step 3: Verify all services**

```bash
curl http://localhost:8000/health  # Backend
curl http://localhost:3000         # Frontend
```

**Step 4: Commit**

```bash
git add docker-compose.mvp.yml
git commit -m "feat(docker): add MVP docker-compose for beta launch"
```

---

## Task 11: Create Seed Data Script

**Files:**
- Create: `backend/scripts/seed_mvp_data.py`

**Purpose:** Create test users for each role so MVP can be demonstrated.

**Step 1: Write seed script**

```python
"""Seed MVP test data: users for each role."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from core.database import db_manager
from models.database import User as DBUser
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SEED_USERS = [
    {"email": "ogrenci@kiro2.com", "first_name": "Ali", "last_name": "Yilmaz",
     "role": "STUDENT", "password": "OgrenciTest1!"},
    {"email": "ogretmen@kiro2.com", "first_name": "Ayse", "last_name": "Demir",
     "role": "TEACHER", "password": "OgretmenTest1!"},
    {"email": "admin@kiro2.com", "first_name": "Admin", "last_name": "Kiro2",
     "role": "ADMIN", "password": "AdminTest1!"},
]

async def seed():
    await db_manager.initialize()
    async with db_manager.async_session_maker() as session:
        for u in SEED_USERS:
            exists = await session.execute(
                select(DBUser).where(DBUser.email == u["email"])
            )
            if exists.scalar_one_or_none():
                print(f"  SKIP: {u['email']} (already exists)")
                continue
            user = DBUser(
                email=u["email"],
                first_name=u["first_name"],
                last_name=u["last_name"],
                role=u["role"],
                password_hash=pwd_context.hash(u["password"]),
                is_active=True,
            )
            session.add(user)
            print(f"  ADD: {u['email']} ({u['role']})")
        await session.commit()
    print("Seed complete.")

if __name__ == "__main__":
    asyncio.run(seed())
```

**Step 2: Run seed**

```bash
cd backend
python scripts/seed_mvp_data.py
```

**Step 3: Verify login with seeded users**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/secure \
  -H "Content-Type: application/json" \
  -d '{"email": "ogrenci@kiro2.com", "sifre": "OgrenciTest1!"}'
```

**Step 4: Commit**

```bash
git add backend/scripts/seed_mvp_data.py
git commit -m "feat(seed): add MVP seed data script with test users"
```

---

## Task 12: End-to-End Verification Checklist

Run through this checklist to confirm MVP readiness:

- [ ] Backend starts without fatal errors
- [ ] `GET /health` returns 200
- [ ] `GET /docs` shows Swagger UI
- [ ] Register user works
- [ ] Login/secure sets httpOnly cookies
- [ ] `/me` returns user data with cookie
- [ ] Refresh/secure issues new cookie
- [ ] Logout/secure clears cookies
- [ ] Semantic search returns results
- [ ] Frontend dev server starts (port 3001)
- [ ] Vite proxy forwards `/api/*` to backend
- [ ] Login page renders
- [ ] Login form submits successfully
- [ ] Dashboard loads after login
- [ ] Docker backend image builds
- [ ] Docker frontend image builds
- [ ] `docker-compose.mvp.yml up` starts both services

---

## Summary

| Task | Effort | Dependency |
|------|--------|-----------|
| 1. Fix .env | 2 min | None |
| 2. Backend smoke test | 5 min | Task 1 |
| 3. Auth register+login | 5 min | Task 2 |
| 4. Fix cookie secure | 5 min | Task 3 |
| 5. Semantic search test | 3 min | Task 2 |
| 6. Frontend build test | 5 min | None |
| 7. Login flow E2E | 10 min | Task 4 + 6 |
| 8. Fix CORS | 5 min | Task 7 |
| 9. Docker verify | 10 min | Task 4 |
| 10. MVP docker-compose | 10 min | Task 9 |
| 11. Seed data | 5 min | Task 2 |
| 12. E2E checklist | 10 min | All |

**Total estimated: ~75 minutes**
