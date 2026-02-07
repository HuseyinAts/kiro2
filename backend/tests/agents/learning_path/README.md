# Learning Path Agent Tests

Test suite for Learning Path Agent - Teknofest 2025 Eğitim Eylemci Projesi

## Test Structure

```
tests/agents/learning_path/
├── __init__.py                      # Package marker
├── conftest.py                      # Test fixtures (THIS FILE IS KEY!)
├── test_fixtures_validation.py      # Fixture validation tests
├── core/                            # Core component tests
├── strategies/                      # Strategy tests
├── integrations/                    # Integration tests
└── README.md                        # This file
```

## Available Fixtures

### Student Profile Fixtures

- `mock_student_profile` - Standard 12th grade YKS-AYT student
- `mock_student_profile_beginner` - 9th grade beginner student
- `mock_student_profile_advanced` - 12th grade advanced student
- `student_profile_obj` - StudentProfile dataclass instance
- `create_student_profile(**overrides)` - Factory function

### Learning Resource Fixtures

- `mock_youtube_resource` - YouTube video resource
- `mock_khan_resource` - Khan Academy resource
- `mock_oer_resource` - Wikipedia/OER resource
- `mock_eba_resource` - EBA (MEB) resource
- `learning_resource_obj` - LearningResource dataclass instance
- `create_learning_resource(platform, **overrides)` - Factory function

### Learning Path Fixtures

- `mock_learning_path` - Complete learning path with phases
- `create_learning_path(num_phases, resources_per_phase, **overrides)` - Factory

### Assessment Fixtures

- `mock_assessment` - Mock assessment with questions
- `create_assessment(num_questions, **overrides)` - Factory

### Mock External Services

- `mock_db_session` - AsyncSession mock for database
- `mock_redis_client` - Redis client mock
- `mock_llm_service` - LLM service mock
- `mock_youtube_api` - YouTube API mock
- `mock_khan_api` - Khan Academy API mock

### Turkish Test Data

- `turkish_subjects` - List of Turkish education subjects
- `yks_topics` - Dict of YKS topics by subject
- `turkish_names` - List of Turkish student names

### Composite Scenarios

- `complete_learning_scenario` - Full workflow with student, path, assessment

## Usage Examples

### Example 1: Using Mock Student Profile

```python
def test_create_learning_path(mock_student_profile):
    """Test learning path creation"""
    student_id = mock_student_profile["student_id"]
    # ... use in test
```

### Example 2: Using Factory Function

```python
def test_different_grades():
    """Test with different grade levels"""
    from tests.agents.learning_path.conftest import create_student_profile

    grade_9 = create_student_profile(grade="9")
    grade_10 = create_student_profile(grade="10")
    grade_11 = create_student_profile(grade="11")
    grade_12 = create_student_profile(grade="12")
```

### Example 3: Using Mock Services

```python
async def test_with_database(mock_db_session):
    """Test with database mock"""
    service = SomeService(db=mock_db_session)
    await service.create_something()
    mock_db_session.add.assert_called_once()
```

### Example 4: Turkish Character Testing

```python
def test_turkish_characters(turkish_names):
    """Test Turkish character handling"""
    for name in turkish_names:
        # Test with İ, ı, ş, ğ, ü, ö, ç
        result = process_name(name)
        assert result is not None
```

## Running Tests

```bash
# Run all learning path tests
cd backend && pytest tests/agents/learning_path/ -v

# Run specific test file
pytest tests/agents/learning_path/test_fixtures_validation.py -v

# Run with coverage
pytest tests/agents/learning_path/ --cov=agents.learning_path --cov-report=term-missing

# Run single test
pytest tests/agents/learning_path/test_fixtures_validation.py::test_mock_student_profile_fixture -v
```

## Fixture Validation

To verify all fixtures work correctly:

```bash
cd backend && pytest tests/agents/learning_path/test_fixtures_validation.py -v
```

This will run 17 validation tests covering:
- All fixture types
- Factory functions
- Mock services
- Turkish data collections
- Dataclass instances

## Key Features

### 1. Turkish Character Support

All fixtures contain proper Turkish characters (İ, ı, ş, ğ, ü, ö, ç) to ensure:
- Encoding issues are caught early
- Case conversion works correctly
- Text processing handles Turkish properly

### 2. IRT/ZPD Parameters

Mock questions include realistic IRT parameters:
- `irt_difficulty`: -4.0 to 4.0
- `irt_discrimination`: 0.2 to 4.0
- `irt_guessing`: 0.0 to 0.35

### 3. YKS/TYT/AYT Topics

Fixtures use real YKS exam topics:
- Matematik (Türev, İntegral, Fonksiyonlar, etc.)
- Fizik (Hareket, Kuvvet, Elektrik, etc.)
- Kimya (Atom, Bağlar, Asit-Baz, etc.)
- Biyoloji (Hücre, Genetik, Evrim, etc.)

### 4. Cache Reset

The `reset_caches` fixture (auto-use) ensures:
- LRU caches are cleared between tests
- No test pollution
- Isolated test execution

## Adding New Fixtures

When adding new fixtures:

1. Add to `conftest.py`
2. Add to `__all__` export list
3. Add validation test to `test_fixtures_validation.py`
4. Update this README

Example:

```python
# In conftest.py
@pytest.fixture
def mock_new_thing() -> Dict[str, Any]:
    """Mock new thing fixture"""
    return {
        "id": "new-001",
        "name": "Yeni Test Öğesi",
        # ... with Turkish characters
    }

# In test_fixtures_validation.py
def test_mock_new_thing_fixture(mock_new_thing):
    """Test that new thing fixture works"""
    assert mock_new_thing is not None
    assert mock_new_thing["id"] == "new-001"
```

## Troubleshooting

### Import Errors

If you get import errors:

```python
# Use relative imports from tests
from tests.agents.learning_path.conftest import create_student_profile

# Not absolute imports
# from backend.tests.agents.learning_path.conftest import ...  # WRONG
```

### Fixture Not Found

Make sure fixture is:
1. Decorated with `@pytest.fixture`
2. Listed in `__all__` export
3. In the correct `conftest.py` scope

### Mock Not Working

Check that:
1. Mock is AsyncMock for async functions
2. Return values are set correctly
3. Mock is passed to function under test

## Coverage Goals

Target coverage for test fixtures:
- Fixture usage: 100% (all fixtures used in at least one test)
- Factory functions: 100% (all parameters tested)
- Mock services: 90% (all critical methods tested)

## Related Files

- `backend/agents/learning_path/models.py` - Data models used by fixtures
- `backend/agents/learning_path/config.py` - Configuration (cache reset)
- `.claude/rules/testing.md` - Project testing standards

## Questions?

See:
- Project testing rules: `.claude/rules/testing.md`
- KIRO2 project docs: `CLAUDE.md`
- Worker tester spec: `.claude/agents/kfc/spec-test.md`
