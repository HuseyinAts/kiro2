# MVP Environment Setup

## One-Click Launch (Recommended)

```bash
./launch-mvp.sh
```

This automates everything below: env setup, secret generation, migrations, seeding, Docker build, and health verification. See `./launch-mvp.sh --help` for flags.

## Manual Setup

```bash
cp .env.mvp.example .env.mvp
# Edit .env.mvp with real values (generate secrets, set DB password)
```

## Environment Variables

Create `.env.mvp` in the project root with these variables:

```env
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_DB_PASSWORD@host.docker.internal:5434/kiro2
REDIS_URL=redis://host.docker.internal:6379/0
ENVIRONMENT=development
DEBUG=false
JWT_SECRET_KEY=GENERATE_WITH: openssl rand -base64 64
JWT_ALGORITHM=HS256
SECRET_KEY=GENERATE_WITH: openssl rand -base64 32
ENCRYPTION_KEY=GENERATE_WITH: openssl rand -base64 32
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001,http://localhost:5173
PYTHONUNBUFFERED=1
```

> **PRODUCTION WARNING:** `ALLOWED_ORIGINS` MUST be set to your actual domain(s) in production (e.g., `https://kiro2.com`). Leaving localhost origins in production is a security risk. The backend logs a warning at startup if localhost origins are detected in non-development environments.

## Pre-launch Steps

1. Run database migrations (from host, not Docker):
   ```bash
   cd backend
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5434/kiro2 alembic upgrade head
   ```

2. Seed test users:
   ```bash
   cd backend
   DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5434/kiro2 python scripts/seed_mvp_data.py
   ```

3. Start services:
   ```bash
   docker compose up --build
   ```

## Security Notes

### Docker-compose Passwords

Never use default passwords in production. All docker-compose files should reference environment variables:

```yaml
# CORRECT — password from env var (fails if missing)
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Required}

# WRONG — hardcoded password
POSTGRES_PASSWORD: changeme
```

### Database Timestamps

All timestamps should use UTC (`TIMESTAMPTZ` in PostgreSQL). The backend expects UTC-normalized timestamps. Do not store local time.

### Redis TTL Policy

- Session data: 15 min TTL (JWT access token lifetime)
- Cache data: 5 min default TTL (configurable via `LEARNING_PATH_CACHE_TTL`)
- Blackboard messages: 1 hour TTL
- Shared context: 10 min TTL

Always set explicit TTLs on Redis keys to prevent unbounded memory growth.
