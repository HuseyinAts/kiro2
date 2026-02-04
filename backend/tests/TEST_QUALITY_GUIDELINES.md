# Test Quality Guidelines

## ✅ DO: Write Real Tests

### Good Example: Real Database Test
```python
def test_user_creation(sync_db_session):
    """Test REAL database operation"""
    user = User(username="test", email="test@example.com")
    sync_db_session.add(user)
    sync_db_session.commit()

    # Verify in ACTUAL database
    found = sync_db_session.query(User).filter_by(username="test").first()
    assert found.email == "test@example.com"
```

**Why it's good:**
- ✅ Uses real database (via fixture)
- ✅ Tests actual code paths
- ✅ Catches real integration bugs
- ✅ Meaningful assertions

---

## ❌ DON'T: Mock What You're Testing

### Bad Example: Mock Test
```python
@patch('database.User')
def test_user_creation(mock_user):
    """This tests NOTHING!"""
    mock_user.return_value = Mock(email="test@example.com")
    user = mock_user()
    assert user.email == "test@example.com"  # Testing the mock!
```

**Why it's bad:**
- ❌ Mocks the entire thing being tested
- ❌ 0% coverage of real code
- ❌ Tests pass even if real code is broken
- ❌ False confidence

---

## Test Types & Rules

### 1. Unit Tests (70-80% of tests)
**Purpose:** Test single functions/methods in isolation

**DO:**
```python
def test_calculate_score():
    """Test pure logic without I/O"""
    score = calculate_exam_score(correct=40, wrong=10, empty=0)
    assert score == 350
```

**DON'T:**
```python
@patch('exam.calculate_exam_score')  # Why mock the function you're testing?!
def test_calculate_score(mock_calc):
    mock_calc.return_value = 350
    assert mock_calc() == 350  # Meaningless!
```

**Rules:**
- ✅ Test pure functions (no I/O)
- ✅ Mock external APIs/services only
- ✅ Fast (< 100ms per test)
- ❌ No database access
- ❌ No file I/O
- ❌ Don't mock the function being tested

---

### 2. Integration Tests (15-20% of tests)

**Purpose:** Test components working together with REAL dependencies

**DO:**
```python
def test_user_authentication_flow(sync_db_session, redis_client):
    """Test with REAL database and Redis"""
    # Create user in real DB
    user = User(username="test", hashed_password=hash_password("Pass123!"))
    sync_db_session.add(user)
    sync_db_session.commit()

    # Authenticate with real auth service
    auth_service = AuthService(db_session, redis_client)
    token = auth_service.login("test", "Pass123!")

    # Verify token in real Redis
    assert redis_client.get(f"token:{token}") is not None
```

**DON'T:**
```python
@patch('database.get_session')
@patch('redis.get_client')
def test_user_authentication(mock_db, mock_redis):
    """Mocking everything = testing nothing!"""
    mock_db.return_value = Mock()
    mock_redis.return_value = Mock()
    # This tests your mocks, not your code!
```

**Rules:**
- ✅ Use real database (PostgreSQL in Docker)
- ✅ Use real Redis
- ✅ Use real file system (temp directories)
- ❌ Don't mock database
- ❌ Don't mock Redis
- ❌ Don't mock the services being integrated

---

### 3. E2E Tests (5-10% of tests)

**Purpose:** Test entire system end-to-end

**DO:**
```python
@pytest.mark.e2e
async def test_complete_exam_flow(test_client, sync_db_session):
    """Test full user journey"""
    # Register user via API
    response = await test_client.post("/api/auth/register", json={
        "username": "student",
        "email": "student@test.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 201

    # Login via API
    login_response = await test_client.post("/api/auth/login", json={
        "username": "student",
        "password": "SecurePass123!"
    })
    token = login_response.json()["access_token"]

    # Take exam via API
    exam_response = await test_client.post(
        "/api/exams/tyt/submit",
        headers={"Authorization": f"Bearer {token}"},
        json={"answers": [...]}
    )
    assert exam_response.status_code == 200

    # Verify in database
    user = sync_db_session.query(User).filter_by(username="student").first()
    assert user.exam_count == 1
```

**Rules:**
- ✅ Test via HTTP API
- ✅ Multiple API calls in sequence
- ✅ Verify in database
- ✅ Slow is OK (< 5s per test)

---

## Common Anti-Patterns to AVOID

### 1. Testing Mocks
```python
# ❌ BAD
@patch('service.process_data')
def test_process(mock_process):
    mock_process.return_value = {"status": "ok"}
    result = service.process_data({})
    assert result == {"status": "ok"}  # You're testing the mock!
```

### 2. Meaningless Assertions
```python
# ❌ BAD
def test_function():
    result = some_function()
    assert result is not None  # So what? Could be anything!
    assert isinstance(result, dict)  # Still meaningless!
```

### 3. Try/Except All
```python
# ❌ BAD
def test_function():
    try:
        result = some_function()
        assert result is not None
    except Exception as e:
        assert isinstance(e, Exception)  # Always true!
```

### 4. Mock Overuse
```python
# ❌ BAD - Integration test with all mocks!
@patch('db.session')
@patch('redis.client')
@patch('s3.client')
@patch('email.sender')
def test_user_registration(mock_db, mock_redis, mock_s3, mock_email):
    # If everything is mocked, what are you testing?
```

---

## Coverage Requirements

### By Test Type
- **Unit tests:** 90%+ coverage of business logic
- **Integration tests:** 70%+ coverage of service layer
- **E2E tests:** 50%+ coverage of API routes

### By Module Type
- **Security modules:** 90%+ required
- **Data models:** 80%+ required
- **Business logic:** 80%+ required
- **API routes:** 70%+ required
- **Utilities:** 60%+ required

### Quality Gates
- ❌ Reject PR if coverage drops by > 1%
- ❌ Reject PR if new code < 70% coverage
- ❌ Reject PR if security code < 90% coverage

---

## Test Naming Convention

### Pattern: `test_<what>_<condition>_<expected>`

**Good Examples:**
```python
def test_user_login_valid_credentials_returns_token()
def test_exam_submit_missing_answers_raises_validation_error()
def test_password_hash_same_input_produces_different_hashes()
```

**Bad Examples:**
```python
def test_user()  # Too vague
def test_login()  # What about login?
def test_1()  # Completely useless
```

---

## Fixtures Best Practices

### DO: Use Fixtures for Real Dependencies
```python
@pytest.fixture
def sync_db_session():
    """Provide REAL database session"""
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()  # Clean up
    session.close()
```

### DON'T: Use Fixtures for Mocks
```python
# ❌ BAD
@pytest.fixture
def mock_db():
    """Why make a fixture for a mock?"""
    return Mock()
```

---

## When to Mock (Rare Cases)

### ✅ Mock External APIs You Don't Control
```python
@patch('requests.post')  # OK: External payment gateway
def test_payment_processing(mock_request):
    mock_request.return_value.status_code = 200
    result = process_payment(100, "USD")
    assert result.success is True
```

### ✅ Mock Slow/Expensive Operations
```python
@patch('ai_model.generate')  # OK: Expensive AI inference
def test_content_generation(mock_ai):
    mock_ai.return_value = "Generated content"
    result = generate_quiz_question("math")
    assert "Generated content" in result
```

### ❌ Don't Mock Your Own Services
```python
# ❌ BAD
@patch('services.user_service.create_user')  # Your own code!
def test_registration(mock_create):
    # You should test the real user_service!
```

---

## Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_calculations.py
│   ├── test_validators.py
│   └── test_utils.py
│
├── integration/             # Real dependencies
│   ├── test_database_real.py
│   ├── test_auth_real.py
│   ├── test_redis_real.py
│   └── test_services_real.py
│
├── e2e/                     # Full system tests
│   ├── test_user_journey.py
│   ├── test_exam_flow.py
│   └── test_admin_workflows.py
│
├── fixtures/                # Shared fixtures
│   ├── database.py
│   ├── redis.py
│   └── test_data.py
│
└── conftest.py             # Pytest configuration
```

---

## Code Review Checklist

Before approving tests, verify:

- [ ] No mocking of the function/class being tested
- [ ] Integration tests use real database/Redis
- [ ] Assertions are specific and meaningful
- [ ] No `assert result is not None` without context
- [ ] No `try/except` that catches everything
- [ ] Test name describes what/condition/expected
- [ ] Coverage increases or stays the same
- [ ] New code has > 70% coverage
- [ ] Security code has > 90% coverage

---

## Migration Plan

### Week 1: Clean Up
- [x] Delete 146 auto-generated mock tests
- [ ] Identify top 10 critical modules with low coverage

### Week 2: Infrastructure
- [ ] Set up Docker Compose for test dependencies
- [ ] Configure real PostgreSQL for tests
- [ ] Configure real Redis for tests
- [ ] Update conftest.py with real fixtures

### Week 3: Critical Modules
- [ ] Write real tests for auth modules (3% → 80%)
- [ ] Write real tests for security modules (3% → 90%)
- [ ] Write real tests for encryption (0% → 80%)

### Week 4: Coverage Goals
- [ ] Achieve 40% overall coverage
- [ ] Achieve 80% coverage on core modules
- [ ] Set up CI/CD coverage gates

---

## Examples of Good Tests

See these files for examples:
- `tests/integration/test_database_real.py` - Real database operations
- `tests/integration/test_auth_real.py` - Real authentication flow
- `tests/integration/test_message_queue_real.py` - Real data structures

---

## Remember

> "100 mock tests = 0% coverage. 1 real test = meaningful coverage."

**Test quality > Test quantity**
