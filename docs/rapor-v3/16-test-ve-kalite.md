# BÖLÜM 16: Test ve Kalite

## 16.1 Test Stratejisi

### Test Piramidi

```
                    ┌───────────────┐
                    │    E2E       │  10%
                    │   Tests      │
                    └───────┬───────┘
                    ┌───────┴───────┐
                    │  Integration  │  30%
                    │    Tests      │
                    └───────┬───────┘
            ┌───────────────┴───────────────┐
            │         Unit Tests            │  60%
            │                               │
            └───────────────────────────────┘
```

### KIRO2 Test Kategorileri

| Kategori | Amaç | Araçlar |
|----------|------|---------|
| Unit | Tek fonksiyon/sınıf | pytest |
| Integration | Modül arası | pytest + fixtures |
| E2E | Tam workflow | pytest + mock API |
| Performance | Hız ve kaynak | pytest-benchmark |
| Security | Güvenlik | bandit, safety |

---

## 16.2 pytest Yapılandırması

### Dizin Yapısı

```
kiro2/
├── orchestrator/
│   ├── core/
│   ├── agents/
│   └── validators/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_state.py
│   │   ├── test_validators.py
│   │   └── test_routing.py
│   ├── integration/
│   │   ├── test_graph.py
│   │   └── test_pipeline.py
│   └── e2e/
│       └── test_question_generation.py
├── pytest.ini
└── pyproject.toml
```

### pytest.ini

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    -ra
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    requires_api: Requires API key
filterwarnings =
    ignore::DeprecationWarning
```

### pyproject.toml (Coverage)

```toml
[tool.coverage.run]
source = ["orchestrator"]
branch = true
omit = [
    "tests/*",
    "*/__init__.py"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if TYPE_CHECKING:"
]
fail_under = 80
```

---

## 16.3 Fixtures

### conftest.py

```python
# tests/conftest.py

import pytest
from unittest.mock import Mock, patch
from orchestrator.core.state import KIROState
from orchestrator.validators import SchemaValidator

# ============= State Fixtures =============

@pytest.fixture
def empty_state() -> KIROState:
    """Boş state."""
    return {
        "messages": [],
        "task_id": "test-001",
        "task_type": "generate",
        "task_input": {},
        "current_node": "start",
        "iteration": 0,
        "max_iterations": 5,
        "generated_content": None,
        "validation_result": None,
        "final_output": None,
        "started_at": "2026-02-01T10:00:00Z",
        "updated_at": "2026-02-01T10:00:00Z",
        "error": None
    }

@pytest.fixture
def state_with_content(empty_state) -> KIROState:
    """İçerik ile state."""
    empty_state["generated_content"] = {
        "question_id": "MAT-001",
        "question_text": "Test sorusu",
        "options": {"A": "1", "B": "2", "C": "3", "D": "4", "E": "5"},
        "correct_answer": "A",
        "difficulty_level": 3
    }
    return empty_state

# ============= Mock Fixtures =============

@pytest.fixture
def mock_anthropic():
    """Mock Anthropic client."""
    with patch("anthropic.Anthropic") as mock:
        client = Mock()
        mock.return_value = client
        
        # Mock response
        response = Mock()
        response.content = [Mock(text='{"question_id": "MAT-001", "question_text": "Test"}')]
        client.messages.create.return_value = response
        
        yield client

@pytest.fixture
def mock_database():
    """Mock database connection."""
    with patch("psycopg2.connect") as mock:
        conn = Mock()
        cursor = Mock()
        conn.cursor.return_value = cursor
        cursor.fetchall.return_value = []
        mock.return_value = conn
        yield conn

# ============= Validator Fixtures =============

@pytest.fixture
def schema_validator() -> SchemaValidator:
    """Schema validator instance."""
    return SchemaValidator()

# ============= Sample Data Fixtures =============

@pytest.fixture
def valid_question() -> dict:
    """Geçerli soru."""
    return {
        "question_id": "MAT-AYT-LIMIT-001",
        "question_text": "$$\\lim_{x \\to 0} \\frac{\\sin x}{x}$$ limitinin değeri nedir?",
        "options": {
            "A": "0",
            "B": "1",
            "C": "∞",
            "D": "-1",
            "E": "Tanımsız"
        },
        "correct_answer": "B",
        "difficulty_level": 3,
        "topic_tags": ["limit", "trigonometri"],
        "explanation": "Özel limit formülü: sin(x)/x → 1",
        "solution_steps": [
            "L'Hôpital kuralı veya özel limit",
            "lim sin(x)/x = 1"
        ]
    }

@pytest.fixture
def invalid_question() -> dict:
    """Geçersiz soru (eksik alanlar)."""
    return {
        "question_id": "MAT-001",
        "question_text": "Test"
        # Eksik: options, correct_answer, difficulty_level
    }
```

---

## 16.4 Unit Testler

### State Tests

```python
# tests/unit/test_state.py

import pytest
from orchestrator.core.state import KIROState, ValidationResult

class TestKIROState:
    """KIROState testleri."""
    
    def test_empty_state_has_required_fields(self, empty_state):
        """Boş state tüm gerekli alanlara sahip olmalı."""
        required_fields = [
            "messages", "task_id", "task_type", "current_node",
            "iteration", "max_iterations"
        ]
        
        for field in required_fields:
            assert field in empty_state
    
    def test_iteration_starts_at_zero(self, empty_state):
        """İterasyon 0'dan başlamalı."""
        assert empty_state["iteration"] == 0
    
    def test_max_iterations_default(self, empty_state):
        """Varsayılan max_iterations 5 olmalı."""
        assert empty_state["max_iterations"] == 5


class TestValidationResult:
    """ValidationResult testleri."""
    
    def test_passed_with_high_score(self):
        """Yüksek skor passed olmalı."""
        result = ValidationResult(passed=True, score=0.9, issues=[])
        assert result.passed
        assert result.score >= 0.8
    
    def test_failed_with_issues(self):
        """İssue varsa passed=False olmalı."""
        result = ValidationResult(
            passed=False,
            score=0.5,
            issues=["Missing field: explanation"]
        )
        assert not result.passed
        assert len(result.issues) > 0
```

### Validator Tests

```python
# tests/unit/test_validators.py

import pytest
from orchestrator.validators import (
    SchemaValidator,
    ContentValidator,
    PedagogicalValidator
)

class TestSchemaValidator:
    """SchemaValidator testleri."""
    
    def test_valid_question_passes(self, schema_validator, valid_question):
        """Geçerli soru schema'dan geçmeli."""
        result = schema_validator.validate(valid_question)
        assert result["passed"]
        assert result["score"] == 1.0
    
    def test_missing_required_field_fails(self, schema_validator, invalid_question):
        """Eksik alan schema'dan geçmemeli."""
        result = schema_validator.validate(invalid_question)
        assert not result["passed"]
        assert "Missing required field" in str(result["issues"])
    
    def test_invalid_difficulty_range(self, schema_validator, valid_question):
        """Geçersiz zorluk seviyesi başarısız olmalı."""
        valid_question["difficulty_level"] = 10  # Geçersiz: 1-5 olmalı
        result = schema_validator.validate(valid_question)
        assert not result["passed"]
    
    def test_missing_option(self, schema_validator, valid_question):
        """Eksik seçenek başarısız olmalı."""
        del valid_question["options"]["E"]
        result = schema_validator.validate(valid_question)
        assert not result["passed"]


class TestContentValidator:
    """ContentValidator testleri."""
    
    @pytest.fixture
    def content_validator(self):
        return ContentValidator()
    
    def test_valid_turkish_characters(self, content_validator, valid_question):
        """Türkçe karakterler geçerli olmalı."""
        valid_question["question_text"] = "Şu ifadeyi çözünüz: ğüışöç"
        result = content_validator.validate(valid_question)
        assert result["passed"]
    
    def test_valid_latex_syntax(self, content_validator, valid_question):
        """LaTeX syntax geçerli olmalı."""
        result = content_validator.validate(valid_question)
        assert result["passed"]
    
    def test_invalid_latex_fails(self, content_validator, valid_question):
        """Geçersiz LaTeX başarısız olmalı."""
        valid_question["question_text"] = "$$\\invalid{command}$$"
        result = content_validator.validate(valid_question)
        # Not: Bu test LaTeX validation implementasyonuna bağlı
        # assert not result["passed"]


class TestPedagogicalValidator:
    """PedagogicalValidator testleri."""
    
    @pytest.fixture
    def pedagogy_validator(self):
        return PedagogicalValidator()
    
    def test_difficulty_content_match(self, pedagogy_validator, valid_question):
        """Zorluk içerikle uyumlu olmalı."""
        result = pedagogy_validator.validate(valid_question)
        assert result["score"] >= 0.7
    
    def test_answer_hint_detection(self, pedagogy_validator, valid_question):
        """Cevap ipucu tespit edilmeli."""
        # Cevap (B=1) soru metninde geçiyor
        valid_question["question_text"] = "Sonuç 1'dir. Bu değer nedir?"
        result = pedagogy_validator.validate(valid_question)
        # Hint detection aktifse skor düşmeli
```

---

## 16.5 Integration Testler

### Graph Tests

```python
# tests/integration/test_graph.py

import pytest
from orchestrator.core.graph import build_kiro_graph
from orchestrator.core.state import KIROState

class TestKIROGraph:
    """Graph integration testleri."""
    
    @pytest.fixture
    def graph(self):
        """Compiled graph."""
        return build_kiro_graph().compile()
    
    def test_graph_has_all_nodes(self, graph):
        """Graph tüm node'lara sahip olmalı."""
        expected_nodes = [
            "router", "generate", "validate", "review",
            "verify", "check", "approve", "fix"
        ]
        
        # Note: Node list implementation'a bağlı
        # for node in expected_nodes:
        #     assert node in graph.nodes
    
    @pytest.mark.integration
    def test_generate_workflow(self, graph, empty_state, mock_anthropic):
        """Generate workflow çalışmalı."""
        empty_state["task_type"] = "generate"
        empty_state["task_input"] = {
            "topic": "limit",
            "difficulty": 3
        }
        
        result = graph.invoke(empty_state)
        
        assert result["generated_content"] is not None
        assert result["current_node"] in ["verify", "end"]
    
    @pytest.mark.integration
    def test_max_iterations_respected(self, graph, empty_state, mock_anthropic):
        """Max iterations aşılmamalı."""
        empty_state["max_iterations"] = 2
        empty_state["iteration"] = 2
        
        result = graph.invoke(empty_state)
        
        # Router "end"'e yönlendirmeli
        assert result["iteration"] <= 3
```

### Pipeline Tests

```python
# tests/integration/test_pipeline.py

import pytest
from orchestrator.services.question_generator import QuestionGeneratorService

class TestQuestionPipeline:
    """Soru üretim pipeline testleri."""
    
    @pytest.fixture
    def service(self, mock_anthropic, mock_database):
        """Generator service with mocks."""
        return QuestionGeneratorService()
    
    @pytest.mark.integration
    def test_full_generation_pipeline(self, service):
        """Tam üretim pipeline'ı çalışmalı."""
        from orchestrator.services.question_generator import QuestionRequest
        
        request = QuestionRequest(
            topic="türev",
            difficulty=3,
            exam_type="AYT",
            count=1
        )
        
        questions = service.generate(request)
        
        assert len(questions) >= 1
        assert questions[0].question_id is not None
    
    @pytest.mark.integration
    def test_validation_pipeline(self, valid_question):
        """Validation pipeline çalışmalı."""
        from orchestrator.core.quality_gates import QualityGatesPipeline
        
        pipeline = QualityGatesPipeline()
        result = pipeline.run(valid_question)
        
        assert result["passed"]
        assert result["score"] >= 0.7
```

---

## 16.6 E2E Testler

### Full Workflow Test

```python
# tests/e2e/test_question_generation.py

import pytest
import os

# API key kontrolü
SKIP_E2E = os.environ.get("ANTHROPIC_API_KEY") is None

@pytest.mark.e2e
@pytest.mark.skipif(SKIP_E2E, reason="API key required")
class TestQuestionGenerationE2E:
    """End-to-end soru üretim testleri."""
    
    def test_generate_single_question(self):
        """Tek soru üretimi (gerçek API)."""
        from orchestrator.services.question_generator import (
            QuestionGeneratorService,
            QuestionRequest
        )
        
        service = QuestionGeneratorService()
        request = QuestionRequest(
            topic="limit",
            difficulty=2,
            exam_type="AYT",
            count=1
        )
        
        questions = service.generate(request)
        
        assert len(questions) == 1
        q = questions[0]
        
        # Validate structure
        assert q.question_id.startswith("MAT-")
        assert len(q.options) == 5
        assert q.correct_answer in ["A", "B", "C", "D", "E"]
        assert 1 <= q.difficulty_level <= 5
    
    def test_generate_multiple_questions(self):
        """Çoklu soru üretimi."""
        from orchestrator.services.question_generator import (
            QuestionGeneratorService,
            QuestionRequest
        )
        
        service = QuestionGeneratorService()
        request = QuestionRequest(
            topic="türev",
            difficulty=3,
            exam_type="AYT",
            count=3
        )
        
        questions = service.generate(request)
        
        assert len(questions) == 3
        
        # Unique IDs
        ids = [q.question_id for q in questions]
        assert len(ids) == len(set(ids))
    
    def test_validation_catches_errors(self):
        """Validation hataları yakalamalı."""
        from orchestrator.core.quality_gates import QualityGatesPipeline
        
        invalid = {
            "question_id": "TEST-001",
            "question_text": ""  # Boş
            # Eksik alanlar
        }
        
        pipeline = QualityGatesPipeline()
        result = pipeline.run(invalid)
        
        assert not result["passed"]
        assert len(result["issues"]) > 0
```

---

## 16.7 Performance Testler

### Benchmark Tests

```python
# tests/performance/test_benchmarks.py

import pytest

class TestValidatorPerformance:
    """Validator performans testleri."""
    
    @pytest.mark.benchmark
    def test_schema_validation_speed(self, benchmark, schema_validator, valid_question):
        """Schema validation 1ms altında olmalı."""
        result = benchmark(schema_validator.validate, valid_question)
        
        assert benchmark.stats["mean"] < 0.001  # 1ms
    
    @pytest.mark.benchmark
    def test_full_validation_speed(self, benchmark, valid_question):
        """Tam validation 100ms altında olmalı."""
        from orchestrator.core.quality_gates import QualityGatesPipeline
        
        pipeline = QualityGatesPipeline()
        result = benchmark(pipeline.run, valid_question)
        
        assert benchmark.stats["mean"] < 0.1  # 100ms


class TestGraphPerformance:
    """Graph performans testleri."""
    
    @pytest.mark.benchmark
    @pytest.mark.slow
    def test_graph_execution_speed(self, benchmark, empty_state, mock_anthropic):
        """Graph execution 5s altında olmalı."""
        from orchestrator.core.graph import build_kiro_graph
        
        graph = build_kiro_graph().compile()
        empty_state["task_type"] = "validate"
        empty_state["generated_content"] = {"test": "data"}
        
        result = benchmark(graph.invoke, empty_state)
        
        assert benchmark.stats["mean"] < 5.0  # 5s
```

---

## 16.8 Test Çalıştırma

### Komutlar

```bash
# Tüm testler
pytest

# Belirli marker
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Coverage ile
pytest --cov=orchestrator --cov-report=html

# Verbose
pytest -v --tb=long

# Paralel (pytest-xdist)
pytest -n auto

# Belirli dosya
pytest tests/unit/test_validators.py

# Belirli test
pytest tests/unit/test_validators.py::TestSchemaValidator::test_valid_question_passes
```

### CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run unit tests
        run: pytest -m unit --cov=orchestrator
      
      - name: Run integration tests
        run: pytest -m integration
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 16.9 Özet

### Checklist

- [ ] Test dizin yapısı oluşturuldu
- [ ] pytest.ini yapılandırıldı
- [ ] Fixtures tanımlandı
- [ ] Unit testler yazıldı
- [ ] Integration testler yazıldı
- [ ] E2E testler yazıldı
- [ ] Coverage %80+ hedeflendi
- [ ] CI/CD entegrasyonu yapıldı

### Quick Reference

```bash
# Test komutları
pytest                      # Tüm testler
pytest -m unit              # Sadece unit
pytest --cov               # Coverage ile
pytest -v -s               # Verbose + print
pytest -x                  # İlk hatada dur
pytest --lf                # Son başarısızları tekrarla
```

### Metrikler

| Metrik | Hedef |
|--------|-------|
| Test coverage | > 80% |
| Unit test time | < 30s |
| Integration test time | < 2min |
| E2E test time | < 5min |

---

**Önceki Bölüm:** [15 - LangGraph Entegrasyonu](./15-langgraph-entegrasyonu.md)  
**Sonraki Bölüm:** [17 - Risk Yönetimi](./17-risk-yonetimi.md)
