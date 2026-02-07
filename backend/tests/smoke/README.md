# KIRO2 Backend Smoke Tests

## Overview

Smoke tests verify critical functionality without deep integration testing. These tests ensure the application can start and respond to basic requests.

## Test Suites

### ST-01: Startup Tests (`test_smoke_startup.py`)
**5 tests** - Verifies backend initialization and configuration

- `test_backend_import_no_error`: Backend module imports successfully
- `test_app_is_fastapi_instance`: App is a valid FastAPI instance
- `test_utf8_encoding`: UTF-8 encoding for Turkish characters
- `test_middleware_loaded`: Middleware stack initialization
- `test_routers_loaded`: API routers loaded (50+ routes expected)

### ST-02: Health Check Tests (`test_smoke_health.py`)
**10 tests** - Verifies health check endpoints

- `test_health_returns_200`: Basic health endpoint responds
- `test_health_status_field`: Response contains health_status field
- `test_health_ready_200`: Kubernetes readiness probe
- `test_health_live_200`: Kubernetes liveness probe
- `test_health_startup_200`: Kubernetes startup probe
- `test_health_database_available`: Database health check
- `test_health_detailed_returns_components`: Detailed health report
- `test_health_response_time_field`: Response time tracking
- `test_health_ready_returns_json`: JSON response format
- `test_health_cache_header`: Consistent health status

### ST-03: Documentation Tests (`test_smoke_docs.py`)
**3 tests** - Verifies API documentation

- `test_docs_returns_html`: Swagger UI accessibility
- `test_openapi_json_valid`: Valid OpenAPI 3.x specification
- `test_openapi_has_endpoints`: 50+ endpoints documented

### ST-04: Database Tests (`test_smoke_database.py`)
**4 tests** - Verifies database configuration

- `test_database_url_configured`: DATABASE_URL is set
- `test_pool_size_configured`: Connection pool size ≥ 5
- `test_async_driver_in_url`: Uses async driver (asyncpg/aiosqlite)
- `test_sqlite_rejected_in_production`: SQLite blocked in production

### ST-05: Redis Tests (`test_smoke_redis.py`)
**3 tests** - Verifies Redis cache configuration

- `test_redis_url_configured`: REDIS_URL is set (port 6379)
- `test_app_starts_without_redis`: Graceful degradation
- `test_cache_module_importable`: Cache module imports successfully

### ST-06: Auth Chain Tests (`test_smoke_auth_chain.py`)
**5 tests** - Verifies authentication endpoints

- `test_root_endpoint`: Root endpoint accessible
- `test_register_endpoint_exists`: `/api/v1/auth/kayit` exists
- `test_login_endpoint_exists`: `/api/v1/auth/giris` exists
- `test_profile_requires_auth`: Protected endpoint security
- `test_invalid_token_rejected`: Invalid JWT rejection

## Running Tests

### All smoke tests
```bash
cd backend
pytest tests/smoke/ -v
```

### Specific test suite
```bash
pytest tests/smoke/test_smoke_health.py -v
```

### Collect tests without running
```bash
pytest tests/smoke/ --collect-only
```

### With coverage
```bash
pytest tests/smoke/ --cov=. --cov-report=term-missing
```

## Test Statistics

- **Total tests**: 30
- **Async tests**: 18 (using httpx.AsyncClient)
- **Sync tests**: 12
- **Coverage target**: Critical paths only (startup, health, auth)

## Design Principles

### No Reward Hacking
- **NEVER** use `assert True` or similar fake assertions
- All assertions must be meaningful and test real behavior
- Exit codes properly checked (200, 401, 403, 404, etc.)

### Graceful Degradation
- Tests accept reasonable error states (e.g., 503 for unhealthy services)
- Database/Redis unavailability doesn't crash tests
- Focus on "does it respond" vs "is it perfect"

### Turkish Character Support
- UTF-8 encoding verified
- Turkish uppercase conversion tested (İ, Ş, Ğ, Ü, Ö, Ç)

### FastAPI Testing Best Practices
- Uses `httpx.AsyncClient` with `ASGITransport`
- No external HTTP calls (ASGI transport)
- Proper async/await usage with `@pytest.mark.asyncio`

## Expected Behaviors

### Health Endpoints
```json
{
  "status": "success",
  "health_status": "healthy",
  "response_time_ms": 1.23
}
```

### Auth Endpoints
- `POST /api/v1/auth/kayit` - Registration (returns 201/400/422)
- `POST /api/v1/auth/giris` - Login (returns 200/401)
- `GET /api/v1/auth/profil` - Profile (requires Bearer token)

### Database
- PostgreSQL on port **5434** (not 5432!)
- Async driver: `postgresql+asyncpg://`
- Pool size: 5-20 connections

### Redis
- Default port: **6379**
- URL format: `redis://localhost:6379`

## KIRO2-Specific Rules

### Port Configuration
- PostgreSQL: **5434** (NOT 5432)
- Redis: **6379**
- Backend: **8000**

### Auth Store Path
- ✅ CORRECT: `frontend/src/store/authStore.ts`
- ❌ WRONG: `frontend/src/stores/authStore.ts`

### Turkish Text Handling
```python
# CORRECT
def turkish_upper(text: str) -> str:
    return text.replace('i', 'İ').replace('ı', 'I').upper()

# WRONG - 'i' becomes 'I' instead of 'İ'
def upper(text: str) -> str:
    return text.upper()
```

## Verification Checklist

Before marking smoke tests complete:

- [ ] All 30 tests collected successfully
- [ ] Ruff linting passes
- [ ] No `assert True` or fake assertions
- [ ] Async tests use proper `@pytest.mark.asyncio`
- [ ] Turkish character handling verified
- [ ] Database port 5434 verified
- [ ] Auth endpoints return proper status codes

## Integration with CI/CD

These smoke tests are designed to run:
1. **Pre-commit**: Fast startup checks
2. **CI Pipeline**: Full suite on every PR
3. **Production Deployment**: Health checks before traffic routing

## Troubleshooting

### Tests fail with import errors
Ensure you're running from `backend/` directory:
```bash
cd backend && pytest tests/smoke/
```

### AsyncClient errors
Verify httpx and ASGITransport are installed:
```bash
pip install httpx
```

### Database connection errors
Tests should tolerate missing database in smoke test phase.
Check `test_health_database_available` accepts 503 status.

### UTF-8 encoding errors on Windows
Verify `io.TextIOWrapper` fix in `main.py`:
```python
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

## Next Steps

After smoke tests pass:
1. Run integration tests: `pytest tests/integration/`
2. Run full test suite: `pytest -v`
3. Check coverage: `pytest --cov=. --cov-report=html`
4. Review coverage report: `open htmlcov/index.html`

---

**Created**: 2026-01-28
**Total Tests**: 30
**Framework**: pytest + httpx
**Python**: 3.11+
**Async Support**: ✅
