# 📚 Fixture Reference Guide

**Complete reference for all test fixtures in the project**

**Last Updated:** 2025-01-07
**Total Fixtures:** 30+

---

## 📖 Table of Contents

1. [Database Fixtures](#database-fixtures)
2. [Mock Fixtures](#mock-fixtures)
3. [Factory Fixtures](#factory-fixtures)
4. [Agent Fixtures](#agent-fixtures)
5. [API Client Fixtures](#api-client-fixtures)
6. [Environment Fixtures](#environment-fixtures)
7. [Test Data Fixtures](#test-data-fixtures)
8. [Advanced Fixtures](#advanced-fixtures)

---

## 🗄️ Database Fixtures

### `test_async_engine`
**Source:** `backend/conftest.py:32-44`
**Scope:** Session
**Type:** Async

**Purpose:** Creates a session-scoped async database engine for all tests.

**Configuration:**
- Pool size: 5
- Max overflow: 10
- Pool pre-ping: True
- Echo: False (set to True for SQL debugging)

**Usage:**
```python
async def test_with_engine(test_async_engine):
    async with test_async_engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
```

**When to Use:**
- ✅ When you need direct engine access
- ✅ For custom connection handling
- ❌ Don't use for normal CRUD operations (use `async_db_session`)

---

### `async_db_session`
**Source:** `backend/conftest.py:46-60`
**Scope:** Function
**Type:** Async

**Purpose:** Provides an async database session with automatic rollback after each test.

**Features:**
- ✅ Transaction isolation (auto-rollback)
- ✅ expire_on_commit=False for better performance
- ✅ Uses session-scoped engine

**Usage:**
```python
async def test_create_user(async_db_session):
    user = User(email="test@example.com", username="testuser")
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)

    assert user.id is not None
```

**When to Use:**
- ✅ **Most common fixture** for database tests
- ✅ All CRUD operations
- ✅ Integration tests requiring database

**Best Practices:**
```python
# ✅ Good - test is isolated
async def test_user_creation(async_db_session):
    user = User(email="test@example.com")
    async_db_session.add(user)
    await async_db_session.commit()
    # Rollback happens automatically

# ❌ Bad - no isolation
def test_user_creation():
    # Direct database access without fixture
    # Changes persist across tests
```

---

### `sync_db_session`
**Source:** `backend/conftest.py:62-77`
**Scope:** Function
**Type:** Sync

**Purpose:** Synchronous database session for legacy code or sync-only libraries.

**Usage:**
```python
def test_sync_operation(sync_db_session):
    user = User(email="test@example.com")
    sync_db_session.add(user)
    sync_db_session.commit()
```

**When to Use:**
- ✅ Legacy synchronous code
- ✅ Libraries that don't support async
- ❌ Prefer `async_db_session` for new tests

---

### `db_session` (from tests/conftest.py)
**Source:** `backend/tests/conftest.py:347-410`
**Scope:** Function
**Type:** Async

**Purpose:** Alternative async session with nested transaction support.

**Features:**
- Transaction rollback after test
- Nested savepoint support
- Bound to test engine

**Usage:**
```python
async def test_with_rollback(db_session):
    user = User(email="test@example.com")
    db_session.add(user)
    await db_session.commit()
    # Auto-rollback on test end
```

**Note:** Use `async_db_session` from root conftest for consistency.

---

## 🎭 Mock Fixtures

### `mock_db`
**Source:** `backend/tests/conftest.py:253-256`
**Scope:** Function
**Type:** Sync

**Purpose:** Mock database dependency for unit tests that don't need real database.

**Usage:**
```python
def test_service_logic(mock_db):
    service = UserService(db=mock_db)
    mock_db.execute.return_value = MagicMock()

    result = service.get_user("123")
    mock_db.execute.assert_called_once()
```

**When to Use:**
- ✅ Unit tests (fast tests)
- ✅ Testing service logic without database
- ✅ When you want to control database behavior
- ❌ Don't use for integration tests

---

### `mock_db_session`
**Source:** `backend/tests/conftest.py:259-262`
**Scope:** Function
**Type:** Async Mock

**Purpose:** Mock async database session.

**Usage:**
```python
async def test_async_service(mock_db_session):
    service = AsyncUserService(session=mock_db_session)
    mock_db_session.execute = AsyncMock()

    await service.create_user({"email": "test@example.com"})
    mock_db_session.execute.assert_called()
```

---

### `mock_user`
**Source:** `backend/tests/conftest.py:622-633`
**Scope:** Function

**Purpose:** Mock user object for testing without database.

**Returns:**
```python
{
    "id": "test_user_123",
    "email": "mock@example.com",
    "username": "mockuser",
    "role": "STUDENT",
    "is_active": True,
    "is_verified": True
}
```

**Usage:**
```python
def test_authorization(mock_user):
    assert can_access_resource(mock_user, "/api/student/")
    assert not can_access_resource(mock_user, "/api/admin/")
```

---

### `mock_student_user`
**Source:** `backend/tests/conftest.py:266-274`
**Scope:** Function

**Purpose:** Pre-configured student user mock.

**Usage:**
```python
def test_student_access(mock_student_user):
    service = StudentService()
    result = service.get_dashboard(mock_student_user["user_id"])
```

---

### `mock_admin_user`
**Source:** `backend/tests/conftest.py:277-286`
**Scope:** Function

**Purpose:** Pre-configured admin user mock.

**Usage:**
```python
def test_admin_access(mock_admin_user):
    service = AdminService()
    result = service.delete_user(mock_admin_user["user_id"], "target_user_id")
```

---

### `mock_teacher_user`
**Source:** `backend/tests/conftest.py:288-296`
**Scope:** Function

**Purpose:** Pre-configured teacher user mock.

---

### `mock_httpx_client`
**Source:** `backend/tests/conftest.py:110-125`
**Scope:** Function

**Purpose:** Mock HTTP client for external API calls.

**Usage:**
```python
def test_llm_api(mock_httpx_client):
    mock_httpx_client.post.return_value = AsyncMock(
        status_code=200,
        json=lambda: {"response": "test"}
    )

    service = LLMService(client=mock_httpx_client)
    result = await service.generate("prompt")
```

---

### `mock_llm_response`
**Source:** `backend/tests/conftest.py:121-127`
**Scope:** Function

**Purpose:** Pre-configured successful LLM API response.

**Returns:**
```python
{
    'generated_text': 'This is a mock LLM response for testing purposes.'
}
```

---

## 🏭 Factory Fixtures

Factory fixtures are **functions that create test data**. They're more flexible than static fixtures.

### `user_factory`
**Source:** `backend/tests/conftest.py:437-523`
**Scope:** Function
**Type:** Async Factory

**Purpose:** Create test users with customizable attributes.

**Signature:**
```python
async def _create_user(
    email: str = None,
    username: str = None,
    password_hash: str = "hashed_password_123",
    first_name: str = "Test",
    last_name: str = "User",
    role: str = "STUDENT",
    is_active: bool = True,
    is_verified: bool = True,
    **kwargs
) -> User
```

**Usage:**
```python
async def test_multiple_users(user_factory):
    # Create with defaults
    user1 = await user_factory()

    # Create with custom attributes
    admin = await user_factory(
        email="admin@example.com",
        role="ADMIN",
        is_verified=True
    )

    # Create multiple users
    students = [await user_factory(role="STUDENT") for _ in range(5)]
```

**Features:**
- ✅ Auto-generates unique email and username
- ✅ Uses UUID for IDs
- ✅ Automatically commits to database
- ✅ Refreshes object after creation

**When to Use:**
- ✅ When you need multiple users in a test
- ✅ When you need users with specific attributes
- ✅ When you want realistic test data
- ❌ Don't use for simple mock scenarios (use `mock_user`)

---

### `student_profile_factory`
**Source:** `backend/tests/conftest.py:493-564`
**Scope:** Function
**Type:** Async Factory

**Purpose:** Create student profiles with associated users.

**Signature:**
```python
async def _create_student_profile(
    user=None,
    grade_level: int = 9,
    target_exam: str = "TYT",
    **kwargs
) -> StudentProfile
```

**Usage:**
```python
async def test_student_analytics(student_profile_factory):
    # Create student with default user
    student = await student_profile_factory()

    # Create student with custom user
    custom_user = await user_factory(email="student@test.com")
    student = await student_profile_factory(
        user=custom_user,
        grade_level=12,
        target_exam="AYT"
    )
```

**Features:**
- ✅ Auto-creates user if not provided
- ✅ Links student profile to user
- ✅ Configurable grade level and target exam

---

### `question_factory`
**Source:** `backend/tests/conftest.py:534-616`
**Scope:** Function
**Type:** Async Factory

**Purpose:** Create test questions with IRT parameters.

**Signature:**
```python
async def _create_question(
    question_text: str = "Test question?",
    subject_area: str = "MATEMATIK",
    difficulty: str = "MEDIUM",
    correct_answer: str = "A",
    **kwargs
) -> Question
```

**Usage:**
```python
async def test_exam_generation(question_factory):
    # Create questions with different difficulties
    easy_q = await question_factory(difficulty="EASY")
    medium_q = await question_factory(difficulty="MEDIUM")
    hard_q = await question_factory(difficulty="HARD")

    # Create math questions
    math_questions = [
        await question_factory(subject_area="MATEMATIK")
        for _ in range(10)
    ]
```

**Features:**
- ✅ IRT parameters included (difficulty, discrimination, guessing)
- ✅ Morphology complexity and readability scores
- ✅ Four answer options pre-configured
- ✅ Statistics fields (times_asked, times_correct)

---

## 🤖 Agent Fixtures

### `learning_agent`
**Source:** `backend/tests/conftest.py:149-164`
**Scope:** Function
**Type:** Async

**Purpose:** Create a LearningAgent instance for testing.

**Usage:**
```python
async def test_learning_plan(learning_agent):
    plan = await learning_agent.generate_study_plan(
        user_id="123",
        subjects=["MATEMATIK", "FEN"]
    )

    assert plan.success
    assert len(plan.recommendations) > 0
```

**Features:**
- ✅ Auto-cleanup (closes LLM client)
- ✅ Configured for testing environment
- ✅ Mock LLM responses enabled

**When to Use:**
- ✅ Testing learning plan generation
- ✅ Testing adaptive learning algorithms
- ✅ Integration tests with LLM

---

### `study_agent`
**Source:** `backend/tests/conftest.py:160-175`
**Scope:** Function
**Type:** Async

**Purpose:** Create a StudyAgent instance for testing.

**Usage:**
```python
async def test_study_recommendation(study_agent):
    recommendation = await study_agent.recommend_next_topic(
        user_id="123",
        current_topic="Trigonometry"
    )

    assert recommendation.next_topic
    assert recommendation.difficulty_level
```

---

### `exam_agent`
**Source:** `backend/tests/conftest.py:171-186`
**Scope:** Function
**Type:** Async

**Purpose:** Create an ExamAgent instance for testing.

**Usage:**
```python
async def test_exam_generation(exam_agent):
    exam = await exam_agent.generate_exam(
        user_id="123",
        exam_type="TYT",
        question_count=40
    )

    assert len(exam.questions) == 40
    assert exam.time_limit == 2400  # seconds
```

---

## 🌐 API Client Fixtures

### `test_client`
**Source:** `backend/tests/conftest.py:93-106`
**Scope:** Function

**Purpose:** Create a test client for FastAPI application.

**Usage:**
```python
def test_health_endpoint(test_client):
    response = test_client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

**Features:**
- ✅ Synchronous test client
- ✅ Auto-closes after test
- ✅ Full FastAPI app access

---

### `async_client`
**Source:** `backend/tests/conftest.py:102-114`
**Scope:** Function
**Type:** Async

**Purpose:** Async test client for FastAPI.

**Usage:**
```python
async def test_async_endpoint(async_client):
    response = await async_client.post(
        "/api/users",
        json={"email": "test@example.com"}
    )

    assert response.status_code == 201
```

**When to Use:**
- ✅ Testing async endpoints
- ✅ WebSocket connections
- ✅ Streaming responses

---

## 🔧 Environment Fixtures

### `setup_test_env_once`
**Source:** `backend/conftest.py:78-95`
**Scope:** Session
**Type:** Not autouse (explicit)

**Purpose:** Setup test environment variables once per session.

**Sets:**
- `TESTING=true`
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `SECRET_KEY`
- API keys (mocked)

**Usage:**
```python
def test_config(setup_test_env_once):
    # Environment is set up
    assert os.environ["TESTING"] == "true"
    assert os.environ.get("JWT_SECRET_KEY")
```

**Note:** Not autouse - tests must explicitly request this fixture.

---

### `mock_env_with_llm`
**Source:** `backend/tests/conftest.py:129-144`
**Scope:** Function

**Purpose:** Enable LLM for specific tests.

**Usage:**
```python
def test_real_llm(mock_env_with_llm):
    # LLM is enabled for this test
    service = LLMService()
    response = await service.generate("test prompt")
```

---

### `mock_env_without_llm`
**Source:** `backend/tests/conftest.py:140-153`
**Scope:** Function

**Purpose:** Disable LLM (use mocks).

**Usage:**
```python
def test_with_mock_llm(mock_env_without_llm):
    # LLM calls return mock responses
    service = LLMService()
    response = await service.generate("test")
    assert response == "mock response"
```

---

## 📊 Test Data Fixtures

### `sample_user`
**Source:** `backend/tests/conftest.py:589-628`
**Scope:** Function
**Type:** Async

**Purpose:** Pre-created sample user for quick tests.

**Usage:**
```python
async def test_with_sample_user(sample_user):
    # User is already in database
    assert sample_user.email == "sample@example.com"
    assert sample_user.username == "sampleuser"
```

---

### `sample_student`
**Source:** `backend/tests/conftest.py:631-634`
**Scope:** Function
**Type:** Async

**Purpose:** Pre-created sample student profile.

---

### `sample_questions`
**Source:** `backend/tests/conftest.py:637-649`
**Scope:** Function
**Type:** Async

**Purpose:** Pre-created set of 5 sample questions.

**Usage:**
```python
async def test_exam_creation(sample_questions):
    # 5 questions already in database
    assert len(sample_questions) == 5

    exam = Exam(questions=sample_questions)
    assert exam.total_questions == 5
```

---

### `sample_chat_request`
**Source:** `backend/tests/conftest.py:182-196`
**Scope:** Function

**Purpose:** Sample chat request data.

**Returns:**
```python
{
    "agent": "learning",
    "message": "Bana bir öğrenme planı oluştur",
    "session_id": "test_session_123"
}
```

---

### `sample_ws_message`
**Source:** `backend/tests/conftest.py:192-205`
**Scope:** Function

**Purpose:** Sample WebSocket message.

**Returns:**
```python
{
    "agent": "study",
    "message": "Python nedir?"
}
```

---

## 🚀 Advanced Fixtures

### `worker_id`
**Source:** `backend/tests/conftest.py:202-214`
**Scope:** Session
**Type:** Autouse

**Purpose:** Get worker ID for parallel test execution.

**Usage:**
```python
def test_parallel_safe(worker_id):
    # Use worker_id to create isolated resources
    cache_key = f"test_key_{worker_id}"
    db_name = f"test_db_{worker_id}"
```

**When to Use:**
- ✅ Parallel test execution (pytest-xdist)
- ✅ Avoiding resource conflicts
- ✅ Worker-specific test data

---

### `test_database_url`
**Source:** `backend/tests/conftest.py:210-226`
**Scope:** Session

**Purpose:** Create isolated database URL for each test worker.

**Features:**
- ✅ SQLite per worker
- ✅ No database conflicts
- ✅ Parallel test safety

---

### `isolated_cache_key`
**Source:** `backend/tests/conftest.py:244-256`
**Scope:** Function

**Purpose:** Generate worker-isolated cache keys.

**Usage:**
```python
def test_cache(isolated_cache_key):
    key = isolated_cache_key("user_data")
    # key = "user_data_worker1" for worker 1

    cache.set(key, "value")
```

---

## 📋 Fixture Decision Tree

```
Need database access?
├─ Yes
│  ├─ Need real database?
│  │  ├─ Yes → use `async_db_session` or `sync_db_session`
│  │  └─ No → use `mock_db` or `mock_db_session`
│  └─ Need multiple test data?
│     └─ Yes → use factories (`user_factory`, `question_factory`)
└─ No
   ├─ Need API testing?
   │  ├─ Sync → use `test_client`
   │  └─ Async → use `async_client`
   └─ Need mock users?
      ├─ Student → use `mock_student_user`
      ├─ Teacher → use `mock_teacher_user`
      ├─ Admin → use `mock_admin_user`
      └─ Generic → use `mock_user`
```

---

## 🎯 Best Practices

### 1. Choose the Right Fixture
```python
# ❌ Bad - using real database for unit test
async def test_validation_logic(async_db_session):
    service = UserService(db=async_db_session)
    result = service.validate_email("invalid")
    assert not result

# ✅ Good - using mock for unit test
def test_validation_logic():
    service = UserService()
    result = service.validate_email("invalid")
    assert not result
```

### 2. Use Factories for Multiple Objects
```python
# ❌ Bad - manual creation
async def test_class_roster(async_db_session):
    user1 = User(email="student1@test.com", username="student1", ...)
    async_db_session.add(user1)
    user2 = User(email="student2@test.com", username="student2", ...)
    async_db_session.add(user2)
    # ... repeat 20 times

# ✅ Good - factory
async def test_class_roster(user_factory):
    students = [await user_factory(role="STUDENT") for _ in range(20)]
```

### 3. Explicit Dependencies
```python
# ❌ Bad - implicit dependency
def test_feature():
    # Assumes env is set up
    api_key = os.environ["API_KEY"]

# ✅ Good - explicit dependency
def test_feature(setup_test_env_once):
    # Clear that test needs env
    api_key = os.environ["API_KEY"]
```

### 4. Async vs Sync
```python
# ❌ Bad - mixing async/sync incorrectly
async def test_something(sync_db_session):
    await some_async_operation()  # Won't work with sync session

# ✅ Good - correct fixture type
async def test_something(async_db_session):
    await some_async_operation()
```

---

## 🔍 Quick Reference Table

| Fixture | Type | Scope | Use Case |
|---------|------|-------|----------|
| `async_db_session` | Async | Function | **Most common** - DB operations |
| `user_factory` | Async Factory | Function | Create test users |
| `question_factory` | Async Factory | Function | Create test questions |
| `mock_db` | Mock | Function | Unit tests without DB |
| `mock_user` | Mock | Function | Quick user mock |
| `test_client` | Sync | Function | API testing |
| `async_client` | Async | Function | Async API testing |
| `learning_agent` | Async | Function | Agent testing |
| `setup_test_env_once` | Setup | Session | Environment setup |

---

## 📚 Related Documentation

- [FIXTURE_GUIDE.md](FIXTURE_GUIDE.md) - High-level fixture guide
- [TEST_CONFIG_SUMMARY.md](../TEST_CONFIG_SUMMARY.md) - Configuration changes
- [pytest.ini](../pytest.ini) - Test configuration
- [conftest.py](../conftest.py) - Root fixtures

---

**Questions?** Run `pytest --fixtures` to see all available fixtures with descriptions.

**Last Updated:** 2025-01-07
