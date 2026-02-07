# Test Suite Verification Checklist

Follow this checklist to verify the newly created test suite is working correctly.

---

## ✅ Pre-Flight Checks

### 1. Environment Setup

- [ ] Python 3.11+ installed
- [ ] Virtual environment activated
- [ ] In `backend/` directory

```bash
cd backend
python --version  # Should be 3.11+
```

### 2. Dependencies Installed

- [ ] pytest installed
- [ ] pytest-asyncio installed
- [ ] httpx installed

```bash
pip install pytest pytest-asyncio httpx
```

### 3. Database Running

- [ ] PostgreSQL running on port 5434
- [ ] Database `kiro2` exists
- [ ] User credentials configured

```bash
psql -h localhost -p 5434 -U postgres -d kiro2 -c "SELECT 1"
```

### 4. Environment Variables

- [ ] DATABASE_URL set
- [ ] REDIS_URL set (if needed)
- [ ] SECRET_KEY set (if needed)

```bash
echo $DATABASE_URL
# Should output: postgresql+asyncpg://user:pass@localhost:5434/kiro2
```

---

## ✅ File Structure Verification

### 1. Test Files Created

- [ ] `tests/unit/api/__init__.py`
- [ ] `tests/unit/api/test_auth_route.py`
- [ ] `tests/unit/api/test_health_route.py`
- [ ] `tests/unit/api/test_sinav_route.py`
- [ ] `tests/unit/api/test_learning_path_route.py`
- [ ] `tests/unit/api/test_gamification_route.py`
- [ ] `tests/db/test_seed_data.py`
- [ ] `tests/db/test_connection_pool.py`
- [ ] `tests/db/test_indexes.py`
- [ ] `tests/devops/__init__.py`
- [ ] `tests/devops/test_docker.py`
- [ ] `tests/devops/test_health_components.py`
- [ ] `tests/devops/test_graceful_shutdown.py`
- [ ] `tests/functional/test_video_integration.py`
- [ ] `tests/functional/test_accessibility.py`
- [ ] `tests/functional/test_gamification.py`
- [ ] `tests/functional/test_admin_panel.py`
- [ ] `tests/functional/test_cultural_adaptation.py`
- [ ] `tests/functional/test_question_bank_quality.py`
- [ ] `tests/integration/scenarios/__init__.py`
- [ ] `tests/integration/scenarios/test_e2e_scenarios.py`

```bash
# Quick check
ls -la tests/unit/api/
ls -la tests/db/
ls -la tests/devops/
ls -la tests/functional/
ls -la tests/integration/scenarios/
```

### 2. Documentation Files

- [ ] `tests/INDEX.md`
- [ ] `tests/QUICK_START.md`
- [ ] `tests/TEST_CREATION_SUMMARY.md`
- [ ] `tests/VERIFICATION_CHECKLIST.md` (this file)
- [ ] `tests/run_new_tests.py`

---

## ✅ Syntax Verification

### 1. Python Syntax Check

```bash
# Check all test files for syntax errors
python -m py_compile tests/unit/api/*.py
python -m py_compile tests/db/*.py
python -m py_compile tests/devops/*.py
python -m py_compile tests/functional/*.py
python -m py_compile tests/integration/scenarios/*.py
```

**Expected:** No output (success)

### 2. Import Check

```bash
# Verify imports work
python -c "import tests.unit.api.test_auth_route"
python -c "import tests.db.test_seed_data"
python -c "import tests.devops.test_docker"
```

**Expected:** No errors

---

## ✅ Linting Verification

### 1. Ruff Check

```bash
cd backend
ruff check tests/unit/api/ --select=E,F,W
ruff check tests/db/ --select=E,F,W
ruff check tests/devops/ --select=E,F,W
ruff check tests/functional/ --select=E,F,W
ruff check tests/integration/ --select=E,F,W
```

**Expected:** No critical errors (warnings OK)

### 2. Type Checking (Optional)

```bash
mypy tests/unit/api/test_auth_route.py --ignore-missing-imports
```

**Expected:** No type errors

---

## ✅ Test Execution

### 1. Dry Run (Collect Only)

```bash
# Verify tests are discoverable
pytest tests/unit/api/ --collect-only
pytest tests/db/ --collect-only
pytest tests/devops/ --collect-only
pytest tests/functional/ --collect-only
pytest tests/integration/scenarios/ --collect-only
```

**Expected Output:**
```
collected 31 items  # API tests
collected 17 items  # DB tests
collected 14 items  # DevOps tests
collected 38 items  # Functional tests
collected 10 items  # Integration tests
```

### 2. Run Individual Test Files

- [ ] API Route Tests

```bash
pytest tests/unit/api/test_auth_route.py -v
pytest tests/unit/api/test_health_route.py -v
pytest tests/unit/api/test_sinav_route.py -v
pytest tests/unit/api/test_learning_path_route.py -v
pytest tests/unit/api/test_gamification_route.py -v
```

- [ ] Database Tests

```bash
pytest tests/db/test_seed_data.py -v
pytest tests/db/test_connection_pool.py -v
pytest tests/db/test_indexes.py -v
```

- [ ] DevOps Tests

```bash
pytest tests/devops/test_docker.py -v
pytest tests/devops/test_health_components.py -v
pytest tests/devops/test_graceful_shutdown.py -v
```

- [ ] Functional Tests

```bash
pytest tests/functional/test_video_integration.py -v
pytest tests/functional/test_accessibility.py -v
pytest tests/functional/test_gamification.py -v
pytest tests/functional/test_admin_panel.py -v
pytest tests/functional/test_cultural_adaptation.py -v
pytest tests/functional/test_question_bank_quality.py -v
```

- [ ] Integration Tests

```bash
pytest tests/integration/scenarios/test_e2e_scenarios.py -v
```

### 3. Run All Tests

```bash
python tests/run_new_tests.py
```

**Expected:** All test suites pass (or documented failures)

---

## ✅ Coverage Check

### 1. Generate Coverage Report

```bash
pytest tests/unit/api/ --cov=backend/api --cov-report=term-missing
pytest tests/ --cov=backend --cov-report=html
```

- [ ] Coverage report generated
- [ ] HTML report viewable in `htmlcov/index.html`

### 2. Coverage Targets

- [ ] API routes: 75%+
- [ ] Services: 80%+
- [ ] Global: 60%+

---

## ✅ Anti-Pattern Check

### 1. Reward Hacking Detection

Search for forbidden patterns:

```bash
# Should return NO results
grep -r "assert True" tests/unit/api/
grep -r "assert 1 == 1" tests/db/
grep -r "pass  # placeholder" tests/devops/
grep -r "return None  # stub" tests/functional/
```

**Expected:** No matches found

### 2. Meaningful Assertions

Verify each test has real assertions:

```bash
# Count assertions in each file
grep -c "assert " tests/unit/api/test_auth_route.py
# Should be >= 8 (one per test minimum)
```

---

## ✅ Integration Verification

### 1. FastAPI App Import

```bash
python -c "from main import app; print(app)"
```

**Expected:** FastAPI app object printed

### 2. Database Connection

```bash
python -c "from backend.core.database import engine; print(engine)"
```

**Expected:** SQLAlchemy engine printed

### 3. Mock Verification

Run a test with verbose mocking:

```bash
pytest tests/unit/api/test_auth_route.py::test_kayit_endpoint_accessible -v -s
```

**Expected:** Test passes with mock output

---

## ✅ Documentation Verification

### 1. Docstrings Present

- [ ] All test files have module docstrings
- [ ] All test functions have docstrings
- [ ] Docstrings mention "NO REWARD HACKING"

```bash
# Check for docstrings
head -n 10 tests/unit/api/test_auth_route.py
```

### 2. README Accuracy

- [ ] QUICK_START.md has correct commands
- [ ] TEST_CREATION_SUMMARY.md lists all tests
- [ ] INDEX.md has complete directory structure

---

## ✅ Performance Check

### 1. Test Execution Time

```bash
time pytest tests/unit/api/ -v
```

**Expected:** < 10 seconds for API tests

### 2. Parallel Execution (Optional)

```bash
pytest tests/unit/api/ -n auto
```

**Expected:** Faster than sequential

---

## ✅ CI/CD Ready

### 1. GitHub Actions Compatible

- [ ] No absolute paths in tests
- [ ] No hardcoded credentials
- [ ] Environment variables documented

### 2. Docker Compatible

- [ ] Tests can run in container
- [ ] No host-specific dependencies

```bash
docker build -t kiro2-test -f Dockerfile.test .
docker run kiro2-test pytest tests/unit/api/
```

---

## 📊 Final Checklist Summary

### Critical (Must Pass)

- [ ] All test files created (18 files)
- [ ] All tests runnable (110 tests)
- [ ] No syntax errors
- [ ] No reward hacking patterns
- [ ] Documentation complete

### Important (Should Pass)

- [ ] Linting passes
- [ ] Coverage targets met
- [ ] Integration tests work
- [ ] Performance acceptable

### Nice to Have

- [ ] Type checking passes
- [ ] Parallel execution works
- [ ] CI/CD integration ready

---

## 🚨 Troubleshooting

### Common Issues

1. **Import Error: `ModuleNotFoundError`**
   ```bash
   # Solution: Add to PYTHONPATH
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

2. **Database Connection Error**
   ```bash
   # Solution: Check port and credentials
   psql -h localhost -p 5434 -U postgres -d kiro2
   ```

3. **Async Test Error**
   ```bash
   # Solution: Install pytest-asyncio
   pip install pytest-asyncio
   ```

4. **httpx Import Error**
   ```bash
   # Solution: Install httpx
   pip install httpx
   ```

---

## ✅ Sign-Off

### Developer Sign-Off

- [ ] All tests created
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code reviewed
- [ ] Ready for merge

### Reviewer Sign-Off

- [ ] Code follows standards
- [ ] Tests are meaningful
- [ ] No reward hacking
- [ ] Coverage acceptable
- [ ] Documentation accurate

---

**Verification Date:** _____________
**Verified By:** _____________
**Status:** ⬜ PASS / ⬜ FAIL
**Notes:** _____________

---

**Created:** 2026-01-28
**KIRO2 Version:** 1.0
**Standards:** Boris Cherny Verification Loops
