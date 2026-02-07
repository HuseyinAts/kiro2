# Quality Gates - Development Guide

KIRO2 Quality Gates sistemine yeni gate ekleme ve gelistirme rehberi.

## Adding a New Gate

### 1. Gate Class Olusturma

```python
# backend/core/quality_gates/gates/my_new_gate.py

from __future__ import annotations

import time
from pathlib import Path

from ..models import (
    GateConfig,
    GateIssue,
    GateMetrics,
    GateResult,
    GateSeverity,
    GateStatus,
)
from .base import BaseGate, GateContext


class MyNewGate(BaseGate):
    """Yeni gate tanimi."""

    def get_name(self) -> str:
        return "my_new_gate"

    def get_default_config(self) -> GateConfig:
        return GateConfig(
            name="my_new_gate",
            enabled=True,
            blocking=True,  # Pipeline'i bloklayacak mi?
            threshold=7.0,
            warning_threshold=8.5,
            timeout_seconds=120,
            max_retries=2,
            depends_on=["code_quality"],  # Bagimliliklar
            tool_config={
                "custom_option": "value",
            },
        )

    async def execute(self, context: GateContext) -> GateResult:
        """Gate mantigi buraya."""
        start_time = time.time()
        issues: list[GateIssue] = []

        # 1. Kontrolleri calistir
        check_result = await self._run_checks(context.working_dir)

        # 2. Issue'lari topla
        for problem in check_result.get("problems", []):
            issues.append(
                self.create_issue(
                    file=problem["file"],
                    line=problem.get("line"),
                    rule="MY_RULE",
                    message=problem["message"],
                    severity=GateSeverity.MEDIUM,
                    suggestion=problem.get("fix"),
                )
            )

        # 3. Score hesapla
        score = self._calculate_score(check_result)

        # 4. Result dondur
        execution_time_ms = (time.time() - start_time) * 1000
        status = self.determine_status(score)

        return GateResult(
            gate_name=self.get_name(),
            status=status,
            score=score,
            threshold=self.config.threshold,
            message=f"Found {len(issues)} issues",
            issues=issues,
            execution_time_ms=execution_time_ms,
            blocking=self.config.blocking,
        )

    async def _run_checks(self, working_dir: Path) -> dict:
        """Custom kontroller."""
        result = await self.run_command(
            ["my-tool", "--check", "."],
            working_dir,
        )

        # Parse output
        return {"problems": [], "score": 10.0}

    def _calculate_score(self, result: dict) -> float:
        """Score hesaplama."""
        base_score = 10.0
        penalty = len(result.get("problems", [])) * 0.5
        return max(0, base_score - penalty)
```

### 2. Gate'i Register Et

```python
# backend/core/quality_gates/gates/__init__.py

from .my_new_gate import MyNewGate

__all__ = [
    # ... existing gates
    "MyNewGate",
]
```

### 3. Orchestrator'a Ekle

```python
# backend/core/quality_gates/orchestrator.py

def _setup_gates(self) -> None:
    from .gates import (
        # ... existing
        MyNewGate,
    )

    gate_classes = {
        # ... existing
        "my_new_gate": MyNewGate,
    }
```

### 4. Dependency Graph Guncelle

```python
# backend/core/quality_gates/dependency_graph.py

DEFAULT_GATE_DEPENDENCIES = {
    # ... existing
    "my_new_gate": ["code_quality"],  # Bagimliliklar
}
```

## Testing Gates

### Unit Test

```python
# backend/tests/unit/test_my_new_gate.py

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from backend.core.quality_gates.gates.my_new_gate import MyNewGate
from backend.core.quality_gates.gates.base import GateContext


@pytest.fixture
def gate():
    return MyNewGate()


@pytest.fixture
def context(tmp_path):
    return GateContext(
        working_dir=tmp_path,
        config=MyNewGate().get_default_config(),
    )


class TestMyNewGate:
    @pytest.mark.asyncio
    async def test_execute_success(self, gate, context):
        """Basarili durumda score >= threshold olmali."""
        result = await gate.execute(context)

        assert result.gate_name == "my_new_gate"
        assert result.score >= 0
        assert result.score <= 10

    @pytest.mark.asyncio
    async def test_execute_with_issues(self, gate, context):
        """Issue varsa score dusmeli."""
        # Setup mock
        with patch.object(gate, '_run_checks') as mock:
            mock.return_value = {
                "problems": [
                    {"file": "test.py", "message": "Issue 1"},
                    {"file": "test.py", "message": "Issue 2"},
                ]
            }

            result = await gate.execute(context)

            assert len(result.issues) == 2
            assert result.score < 10

    def test_get_name(self, gate):
        """Gate ismi dogru olmali."""
        assert gate.get_name() == "my_new_gate"

    def test_get_default_config(self, gate):
        """Default config gecerli olmali."""
        config = gate.get_default_config()

        assert config.name == "my_new_gate"
        assert config.threshold > 0
        assert config.timeout_seconds > 0
```

### Property Test

```python
# backend/tests/property/test_my_new_gate.py

from hypothesis import given, strategies as st

from backend.core.quality_gates.gates.my_new_gate import MyNewGate


class TestMyNewGateProperties:
    @given(st.floats(min_value=0, max_value=10))
    def test_score_determines_status(self, score):
        """Score her zaman gecerli status uretmeli."""
        gate = MyNewGate()

        status = gate.determine_status(score)

        if score >= gate.config.warning_threshold:
            assert status.value == "pass"
        elif score >= gate.config.threshold:
            assert status.value == "warning"
        else:
            assert status.value == "fail"
```

## Base Class API

### BaseGate Methods

```python
class BaseGate(ABC):
    # Required - implement these
    def get_name(self) -> str: ...
    def get_default_config(self) -> GateConfig: ...
    async def execute(self, context: GateContext) -> GateResult: ...

    # Optional - override if needed
    def get_dependencies(self) -> list[str]: ...
    def is_blocking(self) -> bool: ...

    # Utilities - use these
    async def run_command(self, cmd, working_dir, timeout=None) -> CommandResult
    def run_command_sync(self, cmd, working_dir, timeout=None) -> CommandResult
    def calculate_score(self, metrics, weights) -> float
    def determine_status(self, score) -> GateStatus
    def create_issue(...) -> GateIssue
```

### GateContext

```python
@dataclass
class GateContext:
    working_dir: Path          # Proje dizini
    config: GateConfig         # Gate konfigurasyonu
    commit_hash: str | None    # Git commit
    branch: str | None         # Git branch
    changed_files: list[str]   # Degisen dosyalar
    previous_result: GateResult | None  # Onceki sonuc
    extra: dict                # Ek veriler
```

### GateResult

```python
class GateResult(BaseModel):
    gate_name: str             # Gate adi
    status: GateStatus         # PASS, WARNING, FAIL, SKIPPED, TIMEOUT, ERROR
    score: float               # 0-10 arasi skor
    threshold: float           # Gecis esigi
    message: str               # Ozet mesaj
    issues: list[GateIssue]    # Bulunan sorunlar
    metrics: GateMetrics | None  # Toplanan metrikler
    details: dict              # Ek detaylar
    execution_time_ms: float   # Calisma suresi
    blocking: bool             # Pipeline'i bloklayacak mi
    retries: int               # Retry sayisi
    auto_fixed: bool           # Auto-fix uygulandi mi
```

## Reporter Development

### Custom Reporter

```python
# backend/core/quality_gates/reporters/my_reporter.py

from ..models import PipelineResult


class MyReporter:
    def __init__(self, **options):
        self.options = options

    def report(self, result: PipelineResult) -> str:
        """Generate report string."""
        output = []

        output.append(f"Pipeline: {result.status}")
        output.append(f"Score: {result.total_score}/10")

        for gate in result.gates:
            output.append(f"  {gate.gate_name}: {gate.score}")

        return "\n".join(output)
```

## Debugging

### Verbose Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("quality_gates")
```

### Single Gate Test

```bash
# Tek gate calistir
python -m core.quality_gates.cli run --gate my_new_gate --verbose
```

### Mock External Tools

```python
@pytest.fixture
def mock_tool():
    with patch('subprocess.run') as mock:
        mock.return_value.returncode = 0
        mock.return_value.stdout = "OK"
        yield mock
```

## Best Practices

### 1. Idempotent Gates
Gate'ler ayni input ile ayni output uretmeli.

### 2. Timeout Handling
Her zaman timeout kullan, sonsuz loop'u onle.

### 3. Error Recovery
Exception'lari yakala ve anlamli error result dondur.

### 4. Metric Collection
Mumkun oldugunca metrik topla (debugging icin).

### 5. Clear Messages
Kullanici-dostu mesajlar yaz.

```python
# Iyi
message = "Found 5 type errors in api/routes.py"

# Kotu
message = "FAIL"
```

### 6. Suggest Fixes
Issue'larda cozum onerisi sun.

```python
self.create_issue(
    file="api/routes.py",
    rule="TYPE_ERROR",
    message="Function 'get_user' missing return type",
    suggestion="Add '-> User' return type annotation",
)
```

## Release Checklist

Yeni gate release oncesi:

- [ ] Unit testler yazildi
- [ ] Property testler yazildi
- [ ] Integration test eklendi
- [ ] Documentation guncellendi
- [ ] GitHub Actions workflow'a eklendi
- [ ] CHANGELOG guncellendi
- [ ] Code review yapildi
