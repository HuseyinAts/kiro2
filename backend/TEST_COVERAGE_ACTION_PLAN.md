# Test Coverage Action Plan
## algorithms, analytics, agents Modules

**Date:** 2026-01-30
**Current Coverage:** 13.05%
**Target Coverage:** 60%
**Gap:** -46.95%
**Status:** 🔴 CRITICAL

---

## Top 10 Critical Files (0% Coverage)

| Priority | File | Statements | Impact |
|----------|------|------------|--------|
| **P0** | analytics/exam_results_reporting.py | 574 | YKS reporting & analytics |
| **P0** | analytics/student_performance_engine.py | 416 | Student performance tracking |
| **P0** | agents/study_buddy_agent.py | 412 | AI study assistant |
| **P0** | algorithms/multi_agent_blackboard.py | 352 | Agent coordination |
| **P0** | algorithms/cultural_adaptation_engine.py | 340 | Turkish cultural adaptation |
| **P0** | algorithms/recommendation.py | 327 | Question recommendation |
| **P0** | algorithms/irt_morfoloji_service.py | 320 | Turkish morphology IRT |
| **P0** | algorithms/adaptive_learning.py | 233 | Adaptive difficulty |
| **P1** | agents/coordination/blackboard.py | 200 | Multi-agent blackboard |
| **P1** | agents/domain_experts/matematik_agent.py | 169 | Math expert agent |

**Total Critical Statements:** 3,343 (22% of all code in these modules)

---

## Immediate Actions (This Week)

### Day 1: Setup & IRT Tests
```bash
# Create test structure
mkdir -p tests/unit/algorithms/bionic
mkdir -p tests/unit/analytics
mkdir -p tests/unit/agents/domain_experts
mkdir -p tests/unit/agents/coordination

# Write IRT tests (already 92% covered - use as template)
cp tests/unit/algorithms/test_irt_boundaries.py tests/unit/algorithms/test_irt_morfoloji.py
# Edit to test irt_morfoloji_service.py
```

**Target:** Write 50 tests for IRT morphology
**Expected Coverage Gain:** +2%

### Day 2: Adaptive Learning Tests
```bash
# Create adaptive learning test file
touch tests/unit/algorithms/test_adaptive_learning.py
```

**Test Cases Needed:**
- Difficulty adjustment within ZPD (15-85% success probability)
- Student ability progression tracking
- Performance-based adaptation
- Edge cases (very high/low ability students)

**Target:** Write 40 tests
**Expected Coverage Gain:** +1.5%

### Day 3: Recommendation Engine Tests
```bash
touch tests/unit/algorithms/test_recommendation.py
touch tests/unit/algorithms/test_personalized_recommender.py
```

**Test Cases Needed:**
- Similar question retrieval
- Difficulty matching
- Topic coverage
- Learning style adaptation

**Target:** Write 50 tests
**Expected Coverage Gain:** +2%

### Day 4-5: Analytics Module Tests
```bash
touch tests/unit/analytics/test_student_performance.py
touch tests/unit/analytics/test_exam_reporting.py
touch tests/unit/analytics/test_realtime_monitoring.py
```

**Test Cases Needed:**
- YKS score prediction
- Performance metrics calculation
- Report generation
- Real-time monitoring alerts

**Target:** Write 80 tests
**Expected Coverage Gain:** +3%

---

## Week 2: Agent Systems

### Day 6-7: Study Buddy Agent
```bash
touch tests/unit/agents/test_study_buddy.py
touch tests/unit/agents/test_enhanced_study_buddy.py
```

**Target:** 60 tests, +2.5% coverage

### Day 8-9: Domain Expert Agents
```bash
touch tests/unit/agents/domain_experts/test_matematik.py
touch tests/unit/agents/domain_experts/test_biyoloji.py
touch tests/unit/agents/domain_experts/test_fizik.py
touch tests/unit/agents/domain_experts/test_turkce.py
```

**Target:** 70 tests, +2% coverage

### Day 10: Coordination & Blackboard
```bash
touch tests/unit/agents/coordination/test_blackboard.py
touch tests/unit/agents/coordination/test_handoff.py
touch tests/unit/agents/coordination/test_coordinator.py
```

**Target:** 40 tests, +1.5% coverage

---

## Week 3: Turkish NLP & Cultural Features

### Day 11-12: Turkish Features
```bash
touch tests/unit/algorithms/test_turkish_morphology.py
touch tests/unit/algorithms/test_cultural_adaptation.py
touch tests/unit/algorithms/test_text_simplification.py
```

**Test Cases:**
- Turkish uppercase (istanbul → İSTANBUL)
- Morphological analysis
- Cultural context adaptation
- Text simplification levels

**Target:** 60 tests, +2% coverage

### Day 13-15: Bionic Reading
```bash
touch tests/unit/algorithms/bionic/test_fixation.py
touch tests/unit/algorithms/bionic/test_formatter.py
touch tests/unit/algorithms/bionic/test_accessibility.py
touch tests/unit/algorithms/bionic/test_comprehension.py
```

**Target:** 80 tests, +2.5% coverage

---

## Coverage Milestones

| End of Week | Target Coverage | Cumulative Tests | Status |
|-------------|-----------------|------------------|--------|
| Week 1 | 22% (+9%) | 220 | 🟡 In Progress |
| Week 2 | 35% (+13%) | 440 | 🟡 In Progress |
| Week 3 | 48% (+13%) | 660 | 🟡 In Progress |
| Week 4 | 60% (+12%) | 850 | 🟢 Target |

---

## Test Template Examples

### Algorithm Test Template
```python
"""Tests for adaptive_learning module."""
import pytest
from algorithms.adaptive_learning import AdaptiveLearningEngine

@pytest.fixture
def engine():
    return AdaptiveLearningEngine()

class TestAdaptiveLearning:
    async def test_zpd_optimal_range(self, engine):
        """Test that difficulty adjustments stay within ZPD optimal zone."""
        ability = 0.0
        performance = [0.7, 0.8, 0.75]

        difficulty = await engine.adjust_difficulty(ability, performance)
        prob = calculate_probability(ability, difficulty)

        assert 0.15 <= prob <= 0.85, f"Outside ZPD: {prob:.2f}"

    @pytest.mark.parametrize("ability,expected_min,expected_max", [
        (-2.0, -3.5, -0.5),
        (0.0, -1.5, 1.5),
        (2.0, 0.5, 3.5),
    ])
    async def test_ability_ranges(self, engine, ability, expected_min, expected_max):
        """Test difficulty ranges for different ability levels."""
        difficulty = await engine.adjust_difficulty(ability, [0.5] * 5)
        assert expected_min <= difficulty <= expected_max
```

### Analytics Test Template
```python
"""Tests for student_performance_engine."""
import pytest
from unittest.mock import AsyncMock
from analytics.student_performance_engine import PerformanceEngine

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.fetch_student_data.return_value = {
        'exam_scores': [450, 460, 470],
        'topic_scores': {'mat': 85, 'fiz': 90},
    }
    return db

@pytest.fixture
def engine(mock_db):
    return PerformanceEngine(db=mock_db)

class TestPerformanceEngine:
    async def test_yks_prediction_range(self, engine):
        """Test YKS prediction is within valid range."""
        prediction = await engine.predict_yks(student_id=123)

        assert 0 <= prediction <= 560, "Invalid YKS score range"
        assert prediction > 0, "Prediction should be positive"
```

### Agent Test Template
```python
"""Tests for matematik_agent."""
import pytest
from unittest.mock import AsyncMock, patch
from agents.domain_experts.matematik_agent import MatematikAgent

@pytest.fixture
def mock_llm():
    llm = AsyncMock()
    llm.generate.return_value = {
        'steps': ['Step 1', 'Step 2'],
        'answer': 'x = 2'
    }
    return llm

@pytest.fixture
def agent(mock_llm):
    return MatematikAgent(llm=mock_llm)

class TestMatematikAgent:
    async def test_solve_equation(self, agent, mock_llm):
        """Test solving mathematical equations."""
        question = "x² + x - 6 = 0"
        result = await agent.solve(question)

        assert 'steps' in result
        assert len(result['steps']) >= 1
        assert 'answer' in result
        mock_llm.generate.assert_called_once()
```

---

## Verification Checklist (Boris Cherny Standards)

After writing each test file, run:

```bash
# 1. Linting
cd backend && ruff check tests/unit/algorithms/test_adaptive_learning.py --fix

# 2. Type checking
cd backend && mypy tests/unit/algorithms/test_adaptive_learning.py --ignore-missing-imports

# 3. Run tests
cd backend && pytest tests/unit/algorithms/test_adaptive_learning.py -v

# 4. Check coverage
cd backend && pytest tests/unit/algorithms/test_adaptive_learning.py --cov=algorithms.adaptive_learning --cov-report=term-missing

# 5. Verify no reward hacking
cd backend && grep -r "assert True\|assert 1 == 1\|pass  #" tests/unit/algorithms/test_adaptive_learning.py
# Should return NOTHING
```

---

## Forbidden Patterns

### NEVER DO THIS ❌
```python
def test_something():
    assert True  # REWARD HACKING!

def test_another():
    pass  # EMPTY TEST!

def test_feature():
    assert 1 == 1  # MEANINGLESS!
```

### ALWAYS DO THIS ✅
```python
async def test_zpd_validation():
    """Test ZPD boundary validation."""
    with pytest.raises(ValueError):
        create_question(difficulty=10.0)  # Out of [-4, 4] range

async def test_turkish_upper():
    """Test Turkish uppercase conversion."""
    assert turkish_upper("istanbul") == "İSTANBUL"
    assert turkish_upper("diyarbakır") == "DİYARBAKIR"
```

---

## Progress Tracking

Create `backend/test_progress.json`:
```json
{
  "date": "2026-01-30",
  "baseline_coverage": 13.05,
  "target_coverage": 60.0,
  "current_coverage": 13.05,
  "tests_written": 0,
  "tests_target": 850,
  "modules": {
    "algorithms": {"current": 13.0, "target": 65.0},
    "analytics": {"current": 0.0, "target": 60.0},
    "agents": {"current": 36.8, "target": 60.0}
  }
}
```

Update daily after test runs.

---

## Resources

- Testing standards: `.claude/rules/testing.md`
- Verification rules: `.claude/rules/verification.md`
- Coverage report: `COVERAGE_REPORT_ALGORITHMS_ANALYTICS_AGENTS.md`
- IRT parameters: `CLAUDE.md` (difficulty: [-4, 4], discrimination: [0.2, 4.0])

---

## Success Criteria

- ✅ Global coverage ≥ 60%
- ✅ No files with 0% coverage in P0 category
- ✅ All P0 files ≥ 70% coverage
- ✅ Zero reward hacking patterns
- ✅ All tests pass CI/CD pipeline
- ✅ Type checking passes (mypy)
- ✅ Linting passes (ruff)

---

**Next Step:** Start with Day 1 - IRT Morphology Tests
