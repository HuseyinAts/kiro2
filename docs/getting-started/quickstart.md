# Quick Start Guide

Get started with Kiro2 in minutes!

---

## Prerequisites

Before you begin, ensure you have the following installed:

### Required

- **Python 3.11+**: [Download Python](https://python.org/downloads/)
- **PostgreSQL 15+**: [Download PostgreSQL](https://postgresql.org/download/)
- **Redis 7+**: [Download Redis](https://redis.io/download/)

### Optional (but recommended)

- **Docker & Docker Compose**: [Download Docker](https://docker.com/get-started)
- **Git**: [Download Git](https://git-scm.com/downloads)

---

## Installation Methods

Choose your preferred installation method:

=== "Method 1: Docker (Recommended)"

    ### 1. Clone Repository

    ```bash
    git clone https://github.com/yourusername/kiro2.git
    cd kiro2
    ```

    ### 2. Configure Environment

    ```bash
    # Copy example environment file
    cp backend/.env.example backend/.env

    # Edit .env file with your settings
    nano backend/.env  # or use your preferred editor
    ```

    ### 3. Start Services

    ```bash
    # Start all services (PostgreSQL, Redis, Backend)
    docker-compose up -d

    # Check logs
    docker-compose logs -f backend

    # Check health
    curl http://localhost:8000/health
    ```

    ### 4. Run Migrations

    ```bash
    # Access backend container
    docker-compose exec backend bash

    # Run migrations
    alembic upgrade head

    # Exit container
    exit
    ```

    ### 5. Access API

    - **API**: http://localhost:8000
    - **Swagger UI**: http://localhost:8000/docs
    - **ReDoc**: http://localhost:8000/redoc
    - **Health Check**: http://localhost:8000/health

=== "Method 2: Local Development"

    ### 1. Clone Repository

    ```bash
    git clone https://github.com/yourusername/kiro2.git
    cd kiro2/backend
    ```

    ### 2. Create Virtual Environment

    === "Linux/Mac"

        ```bash
        python3.11 -m venv venv
        source venv/bin/activate
        ```

    === "Windows"

        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```

    ### 3. Install Dependencies

    ```bash
    # Upgrade pip
    pip install --upgrade pip

    # Install dependencies
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    ```

    ### 4. Configure Environment

    ```bash
    # Copy example environment file
    cp .env.example .env

    # Edit .env file
    # Required variables:
    # - DATABASE_URL
    # - REDIS_URL
    # - SECRET_KEY
    # - OPENAI_API_KEY (for AI features)
    ```

    ### 5. Setup Database

    ```bash
    # Create database
    createdb kiro2

    # Run migrations
    alembic upgrade head

    # (Optional) Seed data
    python scripts/seed_database.py
    ```

    ### 6. Start Redis

    === "Linux/Mac"

        ```bash
        redis-server
        ```

    === "Windows"

        ```bash
        # Download and run Redis for Windows
        # Or use Docker: docker run -p 6379:6379 redis:7-alpine
        ```

    ### 7. Start Backend

    ```bash
    # Development mode with auto-reload
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

    # Production mode
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
    ```

    ### 8. Access API

    - **API**: http://localhost:8000
    - **Swagger UI**: http://localhost:8000/docs
    - **ReDoc**: http://localhost:8000/redoc

---

## First API Calls

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T10:00:00",
  "version": "1.0.0"
}
```

### 2. Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!",
    "name": "Test Student",
    "role": "student"
  }'
```

Expected response:
```json
{
  "id": "uuid-here",
  "email": "student@example.com",
  "name": "Test Student",
  "role": "student",
  "created_at": "2025-11-12T10:00:00"
}
```

### 3. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 4. Get Profile (Authenticated)

```bash
# Save token from login response
TOKEN="your_access_token_here"

curl -X GET http://localhost:8000/api/v1/user/profile \
  -H "Authorization: Bearer $TOKEN"
```

Expected response:
```json
{
  "id": "uuid-here",
  "email": "student@example.com",
  "name": "Test Student",
  "role": "student",
  "is_premium": false,
  "created_at": "2025-11-12T10:00:00"
}
```

---

## Testing the Installation

### Run Tests

```bash
# Run all tests
make test

# Run fast tests only
make test-fast

# Run with coverage
make test-coverage
```

### Check Code Quality

```bash
# Run all quality checks
make quality

# Format code
make format

# Lint code
make lint

# Type check
make type-check

# Security scan
make security
```

### Access Documentation

1. **Swagger UI**: http://localhost:8000/docs
   - Interactive API documentation
   - Try API calls directly from browser

2. **ReDoc**: http://localhost:8000/redoc
   - Beautiful, responsive API documentation

3. **This Documentation**: http://localhost:8001 (MkDocs)
   ```bash
   # Serve documentation locally
   mkdocs serve
   ```

---

## Common Issues & Solutions

### Issue 1: Database Connection Error

```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solution**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

### Issue 2: Redis Connection Error

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution**:
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
redis-server

# Or use Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Issue 3: Module Import Error

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 4: Port Already in Use

```
OSError: [Errno 98] Address already in use
```

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows

# Or use different port
uvicorn main:app --reload --port 8001
```

---

## Next Steps

Now that you have Kiro2 running, explore these resources:

1. **[API Reference](../api/overview.md)**: Detailed API documentation
2. **[Architecture](../architecture/overview.md)**: System design and patterns
3. **[Development Guide](../development/setup.md)**: Development best practices
4. **[Contributing](../development/contributing.md)**: How to contribute

---

## Interactive Tutorial

Try this interactive tutorial to learn the basics:

### Step 1: Create a Student

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@example.com",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

echo "Token: $TOKEN"
```

### Step 2: Get Learning Path

```bash
curl -X GET http://localhost:8000/api/v1/learning-path \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Step 3: Start Exam

```bash
curl -X POST http://localhost:8000/api/v1/exam/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "exam_type": "TYT",
    "duration": 135,
    "question_count": 40
  }' | jq
```

### Step 4: View Analytics

```bash
curl -X GET http://localhost:8000/api/v1/analytics/performance \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## Development Workflow

Typical development workflow:

```bash
# 1. Start services
docker-compose up -d  # or start PostgreSQL/Redis manually

# 2. Activate virtual environment
source venv/bin/activate

# 3. Start development server
uvicorn main:app --reload

# 4. Make changes to code

# 5. Run tests
make test

# 6. Check code quality
make quality

# 7. Commit changes
git add .
git commit -m "feat: Add new feature"
git push
```

---

## Getting Help

If you encounter issues:

1. Check [FAQ](../reference/faq.md)
2. Search [GitHub Issues](https://github.com/yourusername/kiro2/issues)
3. Join our [Discord Community](https://discord.gg/kiro2)
4. Email [support@kiro2.com](mailto:support@kiro2.com)

---

**Ready to dive deeper?** Continue to [Configuration](configuration.md) for detailed setup options.
