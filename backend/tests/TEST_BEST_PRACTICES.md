# 🎯 Test Best Practices

**Comprehensive guide for writing high-quality, maintainable tests**

**Last Updated:** 2025-01-07

---

## 📖 Table of Contents

1. [Test Philosophy](#test-philosophy)
2. [Test Structure](#test-structure)
3. [Naming Conventions](#naming-conventions)
4. [Test Organization](#test-organization)
5. [Test Data Management](#test-data-management)
6. [Assertion Best Practices](#assertion-best-practices)
7. [Mocking Strategy](#mocking-strategy)
8. [Async Testing](#async-testing)
9. [Performance](#performance)
10. [Common Pitfalls](#common-pitfalls)
11. [Code Review Checklist](#code-review-checklist)

---

## 💡 Test Philosophy

### The Testing Pyramid

```
        /\
       /  \      E2E Tests (Few, Slow, High Confidence)
      /    \
     /------\
    /        \   Integration Tests (Some, Medium Speed)
   /          \
  /------------\
 /              \ Unit Tests (Many, Fast, Low-Level)
/________________\
```

**Target Distribution:**
- **70% Unit Tests** - Fast, isolated, test single functions
- **20% Integration Tests** - Test component interactions
- **10% E2E Tests** - Test full user workflows

### Test Qualities (F.I.R.S.T.)

- ✅ **Fast** - Tests should run quickly (< 1s for unit tests)
- ✅ **Independent** - No dependencies between tests
- ✅ **Repeatable** - Same result every time
- ✅ **Self-Validating** - Pass/fail, no manual verification
- ✅ **Timely** - Write tests before or with code (TDD)

---

## 🏗️ Test Structure

### AAA Pattern (Arrange-Act-Assert)

```python
async def test_user_creation():
    # Arrange - Setup test data and dependencies
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "secure123"
    }
    service = UserService(db=mock_db)

    # Act - Execute the functionality
    result = await service.create_user(user_data)

    # Assert - Verify the outcome
    assert result.success is True
    assert result.user.email == "test@example.com"
    assert result.user.is_verified is False
```

### Given-When-Then (BDD Style)

```python
async def test_student_can_enroll_in_course():
    # Given a verified student user
    student = await user_factory(role="STUDENT", is_verified=True)
    course = await course_factory(available_slots=10)

    # When the student enrolls in the course
    enrollment = await enroll_student(student.id, course.id)

    # Then the enrollment is successful
    assert enrollment.status == "ENROLLED"
    assert enrollment.student_id == student.id
    assert course.enrolled_count == 1
```

### One Assertion Per Test (Guideline)

```python
# ❌ Bad - multiple unrelated assertions
def test_user_service():
    assert service.create_user() is not None
    assert service.delete_user() is True
    assert service.update_user() is not None

# ✅ Good - focused tests
def test_create_user_returns_user_object():
    result = service.create_user(valid_data)
    assert result is not None
    assert isinstance(result, User)

def test_delete_user_returns_success():
    result = service.delete_user(user_id)
    assert result is True

def test_update_user_returns_updated_user():
    result = service.update_user(user_id, new_data)
    assert result is not None
    assert result.email == new_data["email"]
```

**Exception:** Related assertions for same concept are OK:
```python
def test_user_creation_sets_defaults():
    user = await user_factory()

    # These are all testing "default values" - OK together
    assert user.is_active is True
    assert user.is_verified is False
    assert user.role == "STUDENT"
    assert user.created_at is not None
```

---

## 🏷️ Naming Conventions

### Test File Names

```python
# ✅ Good
test_user_service.py
test_authentication.py
test_exam_generation.py

# ❌ Bad
user_tests.py       # Wrong prefix
test.py             # Too generic
user_service.py     # Missing test_ prefix
```

### Test Function Names

**Pattern:** `test_<what>_<condition>_<expected_result>`

```python
# ✅ Excellent - Clear intent
def test_create_user_with_valid_data_returns_success()
def test_create_user_with_duplicate_email_raises_error()
def test_login_with_invalid_password_returns_unauthorized()

# ✅ Good - Descriptive
def test_user_creation_success()
def test_duplicate_email_fails()
def test_invalid_password_denied()

# ❌ Bad - Too generic
def test_user()
def test_create()
def test_success()
```

### Turkish vs English

**Recommendation:** Use English for consistency with code.

```python
# ✅ Good
def test_exam_score_calculation_with_empty_answers()

# ⚠️ Acceptable but inconsistent
def test_sinav_puani_hesaplama()

# ❌ Bad - Mixing languages
def test_user_olusturma_success()
```

**Comment Exception:** Turkish comments for domain-specific logic is OK:
```python
def test_tyt_net_calculation():
    """Test TYT net calculation (doğru - yanlış/4)"""
    # TYT'de 4 yanlış 1 doğruyu götürür
    correct = 10
    wrong = 4
    net = calculate_tyt_net(correct, wrong)
    assert net == 9.0  # 10 - (4/4) = 9
```

---

## 📁 Test Organization

### Directory Structure

```
tests/
├── fast/                    # Unit tests (< 1s each)
│   ├── test_models.py
│   ├── test_validators.py
│   └── test_utils.py
├── integration/             # Integration tests (database, APIs)
│   ├── test_user_service.py
│   ├── test_exam_api.py
│   └── conftest.py
├── slow/                    # Slow tests (> 10s)
│   ├── test_ml_training.py
│   └── test_full_exam_simulation.py
├── fixtures/                # Reusable test fixtures
│   ├── database_fixtures.py
│   ├── mock_data.py
│   └── factories.py
├── accessibility/           # Accessibility tests
├── load/                    # Load/performance tests
├── conftest.py             # Common fixtures
├── FIXTURE_GUIDE.md        # Fixture documentation
├── FIXTURE_REFERENCE.md    # Complete fixture reference
└── TEST_BEST_PRACTICES.md  # This file
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.fast
def test_email_validation():
    """Fast unit test"""
    pass

@pytest.mark.integration
async def test_user_creation_flow(async_db_session):
    """Integration test requiring database"""
    pass

@pytest.mark.slow
async def test_full_exam_simulation():
    """Slow end-to-end test"""
    pass

@pytest.mark.smoke
def test_api_health():
    """Smoke test for quick validation"""
    pass
```

**Run specific markers:**
```bash
pytest -m fast              # Only fast tests
pytest -m "not slow"        # Exclude slow tests
pytest -m "fast or smoke"   # Fast or smoke tests
```

---

## 📊 Test Data Management

### Use Factories for Complex Data

```python
# ❌ Bad - Hard to maintain, not reusable
async def test_student_analytics(async_db_session):
    user = User(
        id=str(uuid.uuid4()),
        email="student@test.com",
        username="student123",
        password_hash="hashed",
        first_name="Test",
        last_name="Student",
        role="STUDENT",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    async_db_session.add(user)
    await async_db_session.commit()

    profile = StudentProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        grade_level=9,
        target_exam="TYT",
        created_at=datetime.utcnow()
    )
    async_db_session.add(profile)
    await async_db_session.commit()

# ✅ Good - Clean, reusable
async def test_student_analytics(student_profile_factory):
    student = await student_profile_factory(
        grade_level=9,
        target_exam="TYT"
    )
```

### Randomize Non-Critical Data

```python
import random
from faker import Faker

faker = Faker("tr_TR")  # Turkish locale

async def test_user_search(user_factory):
    # Use Faker for realistic but random data
    users = [
        await user_factory(
            first_name=faker.first_name(),
            last_name=faker.last_name(),
            email=faker.email()
        )
        for _ in range(10)
    ]

    # Critical test data should be specific
    target_user = await user_factory(
        email="specifically.this@example.com"
    )

    results = await search_users("specifically.this@example.com")
    assert target_user in results
```

### Avoid Magic Numbers

```python
# ❌ Bad - What do these numbers mean?
def test_exam_scoring():
    score = calculate_score(40, 10)
    assert score == 37.5

# ✅ Good - Clear intent
def test_exam_scoring():
    correct_answers = 40
    wrong_answers = 10
    expected_net = 37.5  # 40 - (10/4)

    score = calculate_score(correct_answers, wrong_answers)

    assert score == expected_net
```

### Fixture vs Inline Data

**Use fixtures for:**
- ✅ Data used across multiple tests
- ✅ Complex setup (database, API clients)
- ✅ Expensive operations (file I/O, network)

**Use inline for:**
- ✅ Simple, test-specific data
- ✅ One-time use values
- ✅ Test readability is improved

```python
# ✅ Fixture - Reused across tests
@pytest.fixture
def valid_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "SecurePass123!"
    }

def test_user_creation(valid_user_data):
    user = create_user(valid_user_data)
    assert user is not None

def test_user_validation(valid_user_data):
    result = validate_user_data(valid_user_data)
    assert result.is_valid

# ✅ Inline - Test-specific
def test_email_normalization():
    # This specific case only used here
    email = "Test.User@EXAMPLE.COM"
    normalized = normalize_email(email)
    assert normalized == "test.user@example.com"
```

---

## ✅ Assertion Best Practices

### Use Specific Assertions

```python
# ❌ Bad - Generic assertion
assert user is not None
assert len(results) > 0
assert email.find("@") != -1

# ✅ Good - Specific assertion
assert isinstance(user, User)
assert len(results) == 5
assert "@" in email
assert email.endswith("@example.com")
```

### Use pytest Helpers

```python
import pytest

# ✅ Testing exceptions
def test_invalid_email_raises_error():
    with pytest.raises(ValidationError) as exc_info:
        validate_email("not-an-email")

    assert "Invalid email format" in str(exc_info.value)

# ✅ Testing warnings
def test_deprecated_function_warns():
    with pytest.warns(DeprecationWarning):
        old_function()

# ✅ Approximate equality (floats)
def test_score_calculation():
    score = calculate_score(40, 10)
    assert score == pytest.approx(37.5, abs=0.01)
```

### Assert Messages

```python
# ❌ Bad - No context on failure
assert result == expected

# ✅ Good - Clear failure message
assert result == expected, f"Expected {expected}, got {result}"

# ✅ Better - Detailed context
assert result.status == "PASSED", (
    f"Exam scoring failed: "
    f"Expected status=PASSED, got status={result.status}. "
    f"Details: correct={result.correct}, wrong={result.wrong}, "
    f"net={result.net}"
)
```

### Multiple Assertions

```python
# ⚠️ Be careful - if first fails, others don't run
def test_user_creation():
    user = create_user(data)

    assert user.id is not None  # If this fails, rest skipped
    assert user.email == "test@example.com"
    assert user.is_active is True

# ✅ Better - Use pytest.assume (plugin) or separate tests
def test_user_creation_sets_id():
    user = create_user(data)
    assert user.id is not None

def test_user_creation_sets_email():
    user = create_user(data)
    assert user.email == "test@example.com"

def test_user_creation_sets_active_status():
    user = create_user(data)
    assert user.is_active is True
```

---

## 🎭 Mocking Strategy

### When to Mock

**Mock:**
- ✅ External APIs (LLM, YouTube API, payment gateways)
- ✅ File system operations
- ✅ Time-dependent functions (`datetime.now()`)
- ✅ Random number generation
- ✅ Expensive operations (ML inference, video processing)

**Don't Mock:**
- ❌ Your own business logic (test it!)
- ❌ Simple utility functions
- ❌ Database in integration tests
- ❌ Everything (over-mocking makes tests brittle)

### Mock Levels

```python
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Level 1: Mock return value
def test_user_service(mock_db):
    mock_db.execute.return_value = Mock(fetchone=lambda: {"id": "123"})
    service = UserService(db=mock_db)

    result = service.get_user("123")
    assert result["id"] == "123"

# Level 2: Mock with side effects
def test_retry_on_failure():
    mock_api = Mock()
    mock_api.call.side_effect = [
        Exception("Timeout"),  # First call fails
        Exception("Timeout"),  # Second call fails
        {"success": True}      # Third call succeeds
    ]

    result = call_with_retry(mock_api, max_retries=3)
    assert result["success"] is True
    assert mock_api.call.call_count == 3

# Level 3: Patch modules
@patch('services.user_service.datetime')
def test_user_creation_timestamp(mock_datetime):
    fixed_time = datetime(2025, 1, 1, 12, 0, 0)
    mock_datetime.utcnow.return_value = fixed_time

    user = create_user(data)

    assert user.created_at == fixed_time
```

### Mock Verification

```python
def test_email_sent_on_user_creation(mock_email_service):
    mock_email_service.send = Mock()

    create_user({"email": "test@example.com"})

    # ✅ Verify mock was called
    mock_email_service.send.assert_called_once()

    # ✅ Verify with specific arguments
    mock_email_service.send.assert_called_once_with(
        to="test@example.com",
        subject="Welcome!",
        template="welcome"
    )

    # ✅ Verify call order
    manager = Mock()
    manager.attach_mock(mock_db, 'db')
    manager.attach_mock(mock_cache, 'cache')

    service.create_user(data)

    expected_calls = [
        call.cache.get('user_123'),
        call.db.insert(ANY),
        call.cache.set('user_123', ANY)
    ]
    assert manager.mock_calls == expected_calls
```

### Async Mocks

```python
from unittest.mock import AsyncMock

async def test_llm_service():
    mock_client = AsyncMock()
    mock_client.post.return_value = Mock(
        status_code=200,
        json=lambda: {"response": "Test response"}
    )

    service = LLMService(client=mock_client)
    result = await service.generate("prompt")

    assert result == "Test response"
    mock_client.post.assert_called_once()
```

---

## ⚡ Async Testing

### Async Fixtures

```python
import pytest_asyncio

@pytest_asyncio.fixture
async def async_resource():
    # Setup
    resource = await create_async_resource()

    yield resource

    # Cleanup
    await resource.close()

async def test_with_async_fixture(async_resource):
    result = await async_resource.fetch_data()
    assert result is not None
```

### Testing Async Code

```python
# ✅ Async test function
async def test_async_operation(async_db_session):
    user = await create_user_async(async_db_session)
    assert user.id is not None

# ❌ Don't mix sync/async incorrectly
def test_async_operation(async_db_session):  # Missing 'async'
    user = await create_user_async(async_db_session)  # Will fail!
```

### Async Timeout

```python
import pytest

@pytest.mark.timeout(5)  # 5 seconds max
async def test_slow_operation():
    result = await potentially_slow_operation()
    assert result is not None

# Or inline
async def test_with_inline_timeout():
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            very_slow_operation(),
            timeout=1.0
        )
```

### Async Context Managers

```python
async def test_async_context_manager():
    async with get_async_session() as session:
        user = User(email="test@example.com")
        session.add(user)
        await session.commit()

        # Session auto-closes here

    # Verify user was created
    async with get_async_session() as session:
        result = await session.execute(
            select(User).where(User.email == "test@example.com")
        )
        user = result.scalar_one()
        assert user is not None
```

---

## 🚀 Performance

### Test Speed Targets

| Test Type | Target Time | Example |
|-----------|-------------|---------|
| Unit Test | < 100ms | Validation, calculations |
| Integration | < 1s | Database operations |
| E2E | < 10s | Full user workflows |
| Slow Test | < 60s | ML training, large data |

### Speed Optimization

```python
# ❌ Slow - Creates engine every test
@pytest.fixture
async def slow_db_session():
    engine = create_async_engine(DATABASE_URL)  # Expensive!
    async with engine.connect() as conn:
        yield conn
    await engine.dispose()

# ✅ Fast - Reuses session-scoped engine
@pytest.fixture(scope="session")
async def fast_engine():
    engine = create_async_engine(DATABASE_URL)
    yield engine
    await engine.dispose()

@pytest.fixture
async def fast_db_session(fast_engine):
    async with fast_engine.connect() as conn:
        yield conn
```

### Parallel Execution

```bash
# Run tests in parallel (4 workers)
pytest -n 4

# With coverage
pytest -n auto --cov=. --cov-report=html
```

**Ensure tests are parallel-safe:**
```python
# ✅ Parallel-safe - Isolated data
async def test_user_creation(user_factory, worker_id):
    # Each worker gets unique email
    user = await user_factory(
        email=f"test_{worker_id}_{uuid.uuid4()}@example.com"
    )

# ❌ Not parallel-safe - Shared state
global_counter = 0

def test_increment():
    global global_counter
    global_counter += 1
    assert global_counter == 1  # Fails in parallel!
```

### Use Fixtures Wisely

```python
# ❌ Slow - Re-creates data for each test
class TestUserAnalytics:
    async def test_daily_stats(self, user_factory):
        users = [await user_factory() for _ in range(1000)]
        stats = calculate_daily_stats(users)

    async def test_weekly_stats(self, user_factory):
        users = [await user_factory() for _ in range(1000)]
        stats = calculate_weekly_stats(users)

# ✅ Fast - Shares data across test class
class TestUserAnalytics:
    @pytest.fixture(scope="class")
    async def test_users(self, user_factory):
        return [await user_factory() for _ in range(1000)]

    async def test_daily_stats(self, test_users):
        stats = calculate_daily_stats(test_users)

    async def test_weekly_stats(self, test_users):
        stats = calculate_weekly_stats(test_users)
```

---

## ⚠️ Common Pitfalls

### 1. Test Interdependence

```python
# ❌ Bad - Tests depend on each other
def test_create_user():
    global created_user_id
    user = create_user(data)
    created_user_id = user.id

def test_update_user():
    # Depends on test_create_user running first!
    update_user(created_user_id, new_data)

# ✅ Good - Each test is independent
async def test_create_user(user_factory):
    user = await user_factory()
    assert user.id is not None

async def test_update_user(user_factory):
    user = await user_factory()
    result = update_user(user.id, new_data)
    assert result.success
```

### 2. Hardcoded IDs

```python
# ❌ Bad - Hardcoded IDs break in different environments
def test_get_user():
    user = get_user("123")  # What if this ID doesn't exist?
    assert user is not None

# ✅ Good - Create test data
async def test_get_user(user_factory):
    created_user = await user_factory()
    fetched_user = get_user(created_user.id)
    assert fetched_user.id == created_user.id
```

### 3. Testing Implementation, Not Behavior

```python
# ❌ Bad - Testing implementation details
def test_user_service_calls_repository():
    mock_repo = Mock()
    service = UserService(repo=mock_repo)

    service.create_user(data)

    # This breaks if we refactor internal implementation
    mock_repo.insert.assert_called_once()
    mock_repo.commit.assert_called_once()

# ✅ Good - Testing behavior
async def test_user_creation_persists_data(async_db_session):
    service = UserService(db=async_db_session)

    created_user = await service.create_user(data)

    # Verify the behavior (user is persisted)
    fetched_user = await service.get_user(created_user.id)
    assert fetched_user.email == data["email"]
```

### 4. Ignoring Test Failures

```python
# ❌ Bad - Ignoring intermittent failures
@pytest.mark.xfail  # "Expected to fail"
def test_flaky_feature():
    # This test fails sometimes, we'll fix it later...
    pass

# ❌ Bad - Skipping tests
@pytest.mark.skip(reason="TODO: Fix this")
def test_broken_feature():
    pass

# ✅ Good - Fix the test!
def test_fixed_feature():
    # Identified root cause: race condition
    # Solution: Use deterministic timing
    pass
```

### 5. Over-Mocking

```python
# ❌ Bad - Mocking everything (test is useless)
def test_user_creation():
    mock_validator = Mock(return_value=True)
    mock_hasher = Mock(return_value="hashed")
    mock_db = Mock()
    mock_db.insert.return_value = Mock(id="123")

    service = UserService(
        validator=mock_validator,
        hasher=mock_hasher,
        db=mock_db
    )

    result = service.create_user(data)

    # This doesn't test anything real!
    assert result.id == "123"

# ✅ Good - Mock only external dependencies
async def test_user_creation(async_db_session, mock_email_service):
    # Real validation, real hashing, real DB
    # Only email service is mocked (external)
    service = UserService(
        db=async_db_session,
        email_service=mock_email_service
    )

    result = await service.create_user(data)

    # This tests real behavior
    assert result.email == data["email"]
    assert result.password_hash != data["password"]  # Was hashed
```

### 6. Not Testing Edge Cases

```python
# ❌ Bad - Only happy path
def test_division():
    assert divide(10, 2) == 5

# ✅ Good - Test edge cases
def test_division_happy_path():
    assert divide(10, 2) == 5

def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)

def test_division_negative_numbers():
    assert divide(-10, 2) == -5
    assert divide(10, -2) == -5

def test_division_floats():
    assert divide(10, 3) == pytest.approx(3.333, abs=0.001)
```

---

## ✔️ Code Review Checklist

Use this checklist when reviewing test code:

### Test Quality
- [ ] Tests follow AAA (Arrange-Act-Assert) pattern
- [ ] Each test has a clear, descriptive name
- [ ] Tests are independent (no test depends on another)
- [ ] Tests are repeatable (same result every run)
- [ ] Tests use appropriate markers (`@pytest.mark.fast`, etc.)

### Test Coverage
- [ ] Happy path is tested
- [ ] Edge cases are tested (empty lists, zero, negative, etc.)
- [ ] Error cases are tested (exceptions, validation failures)
- [ ] Boundary conditions are tested

### Fixture Usage
- [ ] Uses appropriate fixtures (not creating resources manually)
- [ ] Fixtures have proper scope (session vs function)
- [ ] No fixture duplication
- [ ] Async fixtures use `@pytest_asyncio.fixture`

### Assertions
- [ ] Assertions are specific (not just `assert x`)
- [ ] Assertion messages provide context
- [ ] Uses pytest helpers (`pytest.raises`, `pytest.approx`)
- [ ] One logical assertion per test (guideline)

### Mocking
- [ ] Only external dependencies are mocked
- [ ] Business logic is not mocked
- [ ] Mocks are verified (`assert_called_once`, etc.)
- [ ] Async functions use `AsyncMock`

### Performance
- [ ] Unit tests run fast (< 100ms)
- [ ] Uses factories for test data
- [ ] No unnecessary database operations
- [ ] Parallel-safe (no shared state)

### Code Style
- [ ] Follows project naming conventions
- [ ] No hardcoded values (use constants)
- [ ] No commented-out code
- [ ] Proper error handling

---

## 📚 Additional Resources

### Internal Documentation
- [FIXTURE_GUIDE.md](FIXTURE_GUIDE.md) - How to use fixtures
- [FIXTURE_REFERENCE.md](FIXTURE_REFERENCE.md) - Complete fixture reference
- [TEST_CONFIG_SUMMARY.md](../TEST_CONFIG_SUMMARY.md) - Test configuration
- [pytest.ini](../pytest.ini) - Pytest configuration
- [.coveragerc](../.coveragerc) - Coverage configuration

### External Resources
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)

### Commands
```bash
# Run specific test
pytest tests/fast/test_user_service.py::test_create_user -v

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run only fast tests
pytest -m fast

# Run in parallel
pytest -n auto

# Show fixture setup
pytest --setup-show

# List all fixtures
pytest --fixtures

# Debug failing test
pytest tests/test_example.py -vv --pdb
```

---

## 🎓 Training Examples

### Example 1: Refactoring Bad Test to Good

**Before:**
```python
def test_user():
    user = User("test@example.com", "testuser", "password", "Test", "User", "STUDENT", True, False, datetime.now(), datetime.now())
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.role == "STUDENT"
    assert user.is_active == True
    assert user.is_verified == False
```

**After:**
```python
@pytest.mark.fast
async def test_user_factory_creates_student_with_defaults(user_factory):
    """Test that user factory creates a student with correct default values."""
    # Arrange & Act
    user = await user_factory(role="STUDENT")

    # Assert
    assert user.role == "STUDENT"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.email is not None
    assert "@" in user.email
```

### Example 2: Testing Error Cases

```python
@pytest.mark.fast
class TestEmailValidation:
    """Test suite for email validation edge cases."""

    def test_valid_email_passes(self):
        """Standard valid email should pass validation."""
        assert is_valid_email("user@example.com") is True

    def test_empty_email_fails(self):
        """Empty string should fail validation."""
        assert is_valid_email("") is False

    def test_no_at_symbol_fails(self):
        """Email without @ symbol should fail."""
        assert is_valid_email("userexample.com") is False

    def test_no_domain_fails(self):
        """Email without domain should fail."""
        assert is_valid_email("user@") is False

    def test_spaces_in_email_fails(self):
        """Email with spaces should fail."""
        assert is_valid_email("user name@example.com") is False

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.co.uk",
        "user123@sub.example.com"
    ])
    def test_various_valid_formats(self, email):
        """Test various valid email formats."""
        assert is_valid_email(email) is True
```

---

**Last Updated:** 2025-01-07
**Maintained By:** QA Team
**Questions?** Ask in #testing-help channel
