# Quick Test Reference Card

## Current Status
- **Coverage:** 13.05% (Target: 60%)
- **Gap:** -46.95%
- **Critical Files:** 36 with 0% coverage
- **Total Missing Tests:** ~850

---

## Quick Commands

```bash
# Run specific module tests
pytest tests/unit/algorithms/ -v --cov=algorithms
pytest tests/unit/analytics/ -v --cov=analytics
pytest tests/unit/agents/ -v --cov=agents

# Run with coverage report
pytest tests/unit/algorithms/ --cov=algorithms --cov-report=html
# View: backend/htmlcov/index.html

# Quick validation (Boris Cherny standards)
ruff check tests/ --fix && mypy tests/ --ignore-missing-imports && pytest -x

# Check for reward hacking
grep -r "assert True\|assert 1 == 1" tests/unit/
```

---

## Test Pattern Quick Reference

### ✅ Good Test
```python
async def test_zpd_optimal_range():
    """Test ZPD keeps success probability in 15-85% range."""
    ability = 0.0
    difficulty = 0.0
    prob = calculate_probability(ability, difficulty)
    assert 0.15 <= prob <= 0.85
```

### ❌ Bad Test (Reward Hacking)
```python
async def test_something():
    assert True  # NEVER!

async def test_feature():
    pass  # NEVER!
```

---

## KIRO2 Specific Tests

### IRT Parameters
```python
@pytest.mark.parametrize("difficulty", [-5.0, 4.1, 10.0])
def test_invalid_difficulty(difficulty):
    with pytest.raises(ValueError):
        create_question(difficulty=difficulty)
```

### Turkish Characters
```python
def test_turkish_upper():
    assert turkish_upper("istanbul") == "İSTANBUL"
    assert turkish_upper("çığır") == "ÇIĞIR"
```

### ZPD Boundaries
```python
def test_zpd_selection():
    prob = calculate_probability(ability=0.0, difficulty=0.0)
    assert 0.15 <= prob <= 0.85, "Question outside ZPD"
```

---

## Priority Files (Start Here)

1. `algorithms/adaptive_learning.py` (233 stmts, 0%)
2. `algorithms/irt_morfoloji_service.py` (320 stmts, 0%)
3. `analytics/student_performance_engine.py` (416 stmts, 0%)
4. `agents/study_buddy_agent.py` (412 stmts, 0%)

---

## Fixture Templates

### Mock Database
```python
@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.execute.return_value = None
    db.fetch_one.return_value = {'id': 1}
    return db
```

### Mock LLM
```python
@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = "Test response"
    return llm
```

### Test Engine
```python
@pytest.fixture
def engine(mock_db, mock_llm):
    return SomeEngine(db=mock_db, llm=mock_llm)
```

---

## Coverage Targets

| Module | Minimum |
|--------|---------|
| algorithms | 65% |
| analytics | 60% |
| agents | 60% |
| **Global** | **60%** |

---

## Verification Loop (MANDATORY)

After EVERY test file:

```bash
# 1. Lint
ruff check tests/unit/path/to/test.py --fix

# 2. Type check
mypy tests/unit/path/to/test.py --ignore-missing-imports

# 3. Run tests
pytest tests/unit/path/to/test.py -v

# 4. Check coverage
pytest tests/unit/path/to/test.py --cov=module --cov-report=term-missing
```

---

## References

- Full plan: `TEST_COVERAGE_ACTION_PLAN.md`
- Coverage report: `COVERAGE_REPORT_ALGORITHMS_ANALYTICS_AGENTS.md`
- Testing rules: `.claude/rules/testing.md`
- Verification rules: `.claude/rules/verification.md`
