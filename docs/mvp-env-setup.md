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
   docker compose -f docker-compose.mvp.yml up --build
   ```
