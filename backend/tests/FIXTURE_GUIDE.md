# Test Fixture Guide

## 📁 Fixture Organization

Test fixtures are organized in a **3-layer hierarchy**:

```
backend/
├── conftest.py                    # Root fixtures (database engines)
└── tests/
    ├── conftest.py                # Common test fixtures (mocks, users, agents)
    ├── integration/
    │   └── conftest.py            # Integration-specific fixtures
    └── fixtures/
        ├── database_fixtures.py   # Advanced DB fixtures
        ├── integration_fixtures.py # Integration test helpers
        ├── mock_data.py           # Mock data generators
        └── factories.py           # Factory fixtures
```

---

## 🎯 Which Fixture to Use?

### Database Fixtures

| Fixture Name | Source | Scope | Use Case |
|--------------|--------|-------|----------|
| `test_async_engine` | root conftest | session | Async database engine (PostgreSQL/SQLite) |
| `async_db_session` | root conftest | function | Async session with auto-rollback |
| `sync_db_session` | integration conftest | function | Sync session for integration tests |

**Example:**
```python
async def test_create_user(async_db_session):
    user = User(email="test@example.com")
    async_db_session.add(user)
    await async_db_session.commit()
```

---

### Mock Fixtures

| Fixture Name | Source | Use Case |
|--------------|--------|----------|
| `mock_db` | tests conftest | Mock database dependency |
| `mock_user` | tests conftest | Mock user object |
| `mock_admin_user` | tests conftest | Mock admin user |
| `mock_llm_response` | tests conftest | Mock LLM API response |

**Example:**
```python
def test_user_service(mock_db, mock_user):
    service = UserService(db=mock_db)
    result = service.get_user(mock_user.id)
```

---

### Factory Fixtures

| Fixture Name | Source | Returns | Use Case |
|--------------|--------|---------|----------|
| `user_factory` | tests conftest | async function | Create test users |
| `student_profile_factory` | tests conftest | async function | Create student profiles |
| `question_factory` | tests conftest | async function | Create test questions |

**Example:**
```python
async def test_student_exam(user_factory, question_factory):
    user = await user_factory(role="STUDENT")
    question = await question_factory(difficulty="EASY")
```

---

### Agent Fixtures

| Fixture Name | Source | Returns | Cleanup |
|--------------|--------|---------|---------|
| `learning_agent` | tests conftest | LearningAgent | Auto-cleanup |
| `study_agent` | tests conftest | StudyAgent | Auto-cleanup |
| `exam_agent` | tests conftest | ExamAgent | Auto-cleanup |

**Example:**
```python
async def test_learning_recommendation(learning_agent):
    result = await learning_agent.generate_study_plan(user_id="123")
    assert result.success
```

---

## 🔧 Environment Setup

### Automatic Setup (Session-scoped)
```python
# Root conftest sets up these automatically:
- TESTING=true
- DATABASE_URL
- REDIS_URL (disabled in tests)
- JWT_SECRET_KEY
```

### Manual Setup (when needed)
```python
@pytest.fixture
def custom_env(setup_test_env_once):
    # setup_test_env_once is NOT autouse anymore
    # Explicitly request it when you need full env setup
    pass
```

---

## 🚫 Removed Fixtures (Duplicates)

These fixtures were **removed** to avoid conflicts:

### ❌ `event_loop` (tests/conftest.py)
**Reason:** pytest-asyncio 0.21+ handles this automatically
**Migration:** No action needed, remove from test signatures

### ❌ `test_engine` (tests/conftest.py)
**Reason:** Duplicate of `test_async_engine` in root conftest
**Migration:** Use `test_async_engine` instead

### ❌ `pytest_configure` (tests/conftest.py)
**Reason:** Markers already defined in pytest.ini
**Migration:** No action needed

---

## 📊 Test Markers

Use these markers to categorize tests:

```python
@pytest.mark.fast          # Unit tests < 1s
@pytest.mark.integration   # Requires database
@pytest.mark.slow          # Tests > 10s
@pytest.mark.unit          # Unit tests with mocks
@pytest.mark.e2e           # End-to-end tests
@pytest.mark.smoke         # Quick validation tests
```

**Example:**
```python
@pytest.mark.integration
async def test_database_operation(async_db_session):
    pass

@pytest.mark.fast
def test_validation_logic():
    pass
```

---

## 🎯 Best Practices

### 1. **Use Specific Fixtures**
```python
# ❌ Bad - too general
async def test_something(db_session):
    pass

# ✅ Good - specific
async def test_create_user(async_db_session):
    pass
```

### 2. **Request Fixtures Explicitly**
```python
# ❌ Bad - relying on autouse
def test_something():
    # Assumes env is set up
    pass

# ✅ Good - explicit dependency
def test_something(setup_test_env_once):
    # Clear that test needs env setup
    pass
```

### 3. **Use Factories for Complex Data**
```python
# ❌ Bad - manual setup
async def test_exam(async_db_session):
    user = User(email="...", username="...", ...)
    async_db_session.add(user)
    await async_db_session.commit()
    # 10+ more lines...

# ✅ Good - factory
async def test_exam(user_factory):
    user = await user_factory()
    # Test logic here
```

### 4. **Clean Up Resources**
```python
# ❌ Bad - no cleanup
@pytest.fixture
def resource():
    r = create_resource()
    return r

# ✅ Good - with cleanup
@pytest.fixture
def resource():
    r = create_resource()
    yield r
    r.cleanup()
```

---

## 🔍 Debugging Fixtures

### List all available fixtures:
```bash
pytest --fixtures
```

### Show fixture setup order:
```bash
pytest --setup-show tests/fast/test_example.py
```

### Verbose fixture output:
```bash
pytest -vv --capture=no tests/
```

---

## 📝 Migration Checklist

If you're migrating old tests:

- [ ] Remove `event_loop` from test signatures
- [ ] Replace `test_engine` with `test_async_engine`
- [ ] Replace `db_session` with `async_db_session` or `sync_db_session`
- [ ] Add explicit `setup_test_env_once` if test needs full env
- [ ] Add appropriate test marker (`@pytest.mark.fast`, etc.)
- [ ] Use factories instead of manual object creation
- [ ] Ensure fixtures have proper cleanup (yield pattern)

---

## 🚀 Performance Tips

1. **Use session-scoped fixtures** for expensive resources (engines, connections)
2. **Use function-scoped fixtures** for test isolation (sessions, data)
3. **Mock external services** (LLM, YouTube API, etc.)
4. **Disable Redis/Elasticsearch** in unit tests
5. **Use SQLite in-memory** for fast tests, PostgreSQL for integration

---

## 📚 Related Documentation

- [pytest.ini](../pytest.ini) - Test configuration
- [.coveragerc](../.coveragerc) - Coverage settings
- [docker-compose.test.yml](../docker-compose.test.yml) - Test database setup
- [TEST_QUALITY_GUIDELINES.md](TEST_QUALITY_GUIDELINES.md) - Test quality standards

---

**Last Updated:** 2025-01-07
**Maintained By:** Platform Team
