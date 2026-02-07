# Quick Start Guide - KIRO2 Test Suite

## Prerequisites

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio httpx
```

## Run All Tests

```bash
# Run verification script
python tests/run_new_tests.py

# Or manually
pytest tests/unit/api/ -v
pytest tests/db/ -v
pytest tests/devops/ -v
pytest tests/functional/ -v
pytest tests/integration/scenarios/ -v
```

## Run Specific Test Files

```bash
# API Tests
pytest tests/unit/api/test_auth_route.py -v
pytest tests/unit/api/test_health_route.py -v
pytest tests/unit/api/test_sinav_route.py -v

# Database Tests
pytest tests/db/test_seed_data.py -v
pytest tests/db/test_connection_pool.py -v
pytest tests/db/test_indexes.py -v

# DevOps Tests
pytest tests/devops/test_docker.py -v
pytest tests/devops/test_health_components.py -v

# Functional Tests
pytest tests/functional/test_accessibility.py -v
pytest tests/functional/test_video_integration.py -v

# E2E Tests
pytest tests/integration/scenarios/test_e2e_scenarios.py -v
```

## Run Specific Tests

```bash
# Single test
pytest tests/unit/api/test_auth_route.py::test_kayit_endpoint_accessible -v

# Test pattern
pytest tests/unit/api/ -k "auth" -v
pytest tests/functional/ -k "accessibility" -v
```

## With Coverage

```bash
# API coverage
pytest tests/unit/api/ --cov=backend/api --cov-report=term-missing

# Full coverage
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

## Debugging Failed Tests

```bash
# Stop on first failure
pytest tests/unit/api/ -x

# Show full output
pytest tests/unit/api/test_auth_route.py -v -s

# Show local variables on failure
pytest tests/unit/api/test_auth_route.py -l
```

## Verification Loop (Boris Cherny Standard)

After ANY code change:

```bash
# 1. Linting
ruff check . --select=E,F,W --ignore=E501

# 2. Type checking
mypy --ignore-missing-imports main.py

# 3. Tests
pytest tests/unit/api/ -x --tb=short
```

## Common Issues

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Ensure you're in backend directory
cd backend

# Check Python path
python -c "import sys; print(sys.path)"

# Run with PYTHONPATH
PYTHONPATH=. pytest tests/unit/api/ -v
```

### Database Connection Errors

```bash
# Check PostgreSQL is running on port 5434
psql -h localhost -p 5434 -U postgres

# Check DATABASE_URL
echo $DATABASE_URL
# Should be: postgresql+asyncpg://user:pass@localhost:5434/kiro2
```

### Async Test Errors

Make sure pytest-asyncio is installed:

```bash
pip install pytest-asyncio

# Check it's working
pytest tests/unit/api/test_health_route.py::test_health_endpoint_200 -v
```

## Test Statistics

| Category | Files | Tests | Time (est.) |
|----------|-------|-------|-------------|
| API Routes | 5 | 31 | ~5s |
| Database | 3 | 17 | ~2s |
| DevOps | 3 | 14 | ~3s |
| Functional | 6 | 38 | ~10s |
| Integration | 1 | 10 | ~8s |
| **TOTAL** | **18** | **110** | **~28s** |

## Expected Output

### Successful Run
```
tests/unit/api/test_auth_route.py::test_kayit_endpoint_accessible PASSED
tests/unit/api/test_giris_endpoint_accessible PASSED
...
==================== 110 passed in 28.45s ====================
```

### With Failures
```
tests/unit/api/test_auth_route.py::test_kayit_endpoint_accessible FAILED
...
FAILED tests/unit/api/test_auth_route.py::test_kayit_endpoint_accessible - AssertionError: ...
==================== 1 failed, 109 passed in 30.12s ====================
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run KIRO2 Tests
  run: |
    cd backend
    pytest tests/unit/api/ -v
    pytest tests/db/ -v
    pytest tests/devops/ -v
    pytest tests/functional/ -v
    pytest tests/integration/scenarios/ -v
```

### Pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

cd backend
ruff check . --select=E,F,W || exit 1
pytest tests/unit/api/ -x || exit 1
```

## Next Steps

1. ✅ Run verification: `python tests/run_new_tests.py`
2. ✅ Check coverage: `pytest --cov=backend --cov-report=html`
3. ✅ Fix any failures
4. ✅ Add to CI/CD pipeline
5. ✅ Document any skipped tests

## Support

- Check `TEST_CREATION_SUMMARY.md` for detailed test documentation
- Review individual test files for implementation details
- See `.claude/rules/testing.md` for testing standards
- See `.claude/rules/verification.md` for verification rules

---

**Created:** 2026-01-28
**KIRO2 Version:** 1.0
**Standards:** Boris Cherny Verification Loops
