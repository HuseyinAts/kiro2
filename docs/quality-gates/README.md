# Quality Gates Pipeline

KIRO2 projesinin 8-gate kalite sistemi. Boris Cherny verification standards uygulanmaktadir.

## Overview

Quality Gates Pipeline, kod kalitesini otomatik olarak dogrulayan 8 bagimsiz kapidan olusur:

| Gate | Kontroller | Blocking |
|------|------------|----------|
| **Code Quality** | Lint, type check, complexity | Evet |
| **Test Coverage** | Line, branch, function coverage | Evet |
| **Security** | Bandit, safety, secrets | Evet |
| **Performance** | Locust, memory, N+1 | Evet |
| **Architecture** | Imports, coupling, layers | Evet |
| **Documentation** | README, API docs, docstrings | Hayir |
| **Compliance** | GDPR, KVKK, audit logs | Evet |

## Quick Start

### CLI Kullanimi

```bash
# Tum gate'leri calistir
cd backend && python -m core.quality_gates.cli run --all

# Belirli bir gate calistir
python -m core.quality_gates.cli run --gate code_quality

# HTML rapor olustur
python -m core.quality_gates.cli run --all --format html --output report.html

# JSON cikti
python -m core.quality_gates.cli run --all --format json
```

### Python API

```python
import asyncio
from pathlib import Path
from core.quality_gates import QualityGatesOrchestrator

async def run_gates():
    orchestrator = QualityGatesOrchestrator(Path.cwd())
    result = await orchestrator.run()

    print(f"Status: {result.status}")
    print(f"Score: {result.total_score}/10")

    for gate in result.gates:
        print(f"  {gate.gate_name}: {gate.score}/10 ({gate.status})")

asyncio.run(run_gates())
```

## Configuration

### Gate Thresholds

Her gate icin threshold ve warning_threshold ayarlanabilir:

```python
from core.quality_gates.models import GateConfig, PipelineConfig

config = PipelineConfig(
    gates={
        "code_quality": GateConfig(
            name="code_quality",
            threshold=7.0,        # FAIL if score < 7
            warning_threshold=8.5, # WARNING if score < 8.5
            timeout_seconds=120,
        ),
        "security": GateConfig(
            name="security",
            blocking=True,  # Pipeline fails if this gate fails
        ),
    }
)
```

### Gate Dependencies

Gate'ler arasindaki bagimliliklar:

```
code_quality (no deps)
├── test_coverage
├── security
├── architecture
└── documentation
    └── performance
        └── compliance
```

## Gate Details

### 1. Code Quality Gate

**Kontroller:**
- **Ruff Linting** (40% weight): Syntax ve style kontrolleri
- **Mypy Type Check** (30% weight): Static type analysis
- **Radon Complexity** (30% weight): Cyclomatic complexity

**Score Hesaplama:**
```
lint_score = max(0, 10 - error_count * 0.5)
type_score = max(0, 10 - type_error_count * 0.3)
complexity_score = f(avg_complexity)

final_score = lint_score * 0.4 + type_score * 0.3 + complexity_score * 0.3
```

### 2. Test Coverage Gate

**Thresholds:**
- Line coverage: >= 80%
- Branch coverage: >= 70%
- New code: >= 90% (stricter)
- Critical paths: 100%

**Coverage Regression:** Onceki run'dan 2% dususe izin verilir.

### 3. Security Gate

**Tools:**
- **Bandit**: Python security scanner
- **Safety**: Dependency vulnerability check
- **detect-secrets**: Secret exposure detection

**Blocking Conditions:**
- Critical vulnerability: Immediate FAIL
- Secret exposed: Immediate FAIL

### 4. Performance Gate

**Checks:**
- P50, P95, P99 response times
- Memory usage ve leak detection
- N+1 query patterns
- Performance regression (>10% fail)

**Default Thresholds:**
- P95 < 200ms
- P99 < 500ms
- Memory < 512MB

### 5. Architecture Gate

**Checks:**
- Import direction validation
- Circular dependency detection
- Layer separation
- Coupling/cohesion metrics

### 6. Documentation Gate

**Checks:**
- README completeness (length, sections)
- API documentation coverage
- Docstring coverage (>= 70%)
- Example code presence

**Non-blocking:** Bu gate sadece warning verir.

### 7. Compliance Gate

**GDPR/KVKK Checks:**
- PII encryption
- Audit logging
- Consent management
- Data retention policy
- Right to erasure
- Data portability

## Override Workflow

Gate failure durumunda override talep edilebilir:

```python
from core.quality_gates.override import OverrideManager

manager = OverrideManager()

# Override talep et
manager.submit_request(
    gate_name="security",
    reason="False positive - third-party lib pattern",
    requestor="dev@kiro2.com",
    ticket_id="KIRO-1234",
    expires_in_days=7,
)

# Admin approval
manager.approve(
    gate_name="security",
    approver="admin@kiro2.com",
    comments="Verified as false positive",
)
```

## CI/CD Integration

GitHub Actions workflow otomatik olarak PR ve push'larda calisir:

```yaml
# .github/workflows/quality-gates.yml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

**Gate Execution Order:**
1. Code Quality (parallel start)
2. Test Coverage, Security, Architecture, Documentation (parallel)
3. Performance, Compliance (after deps)
4. Final Gate Summary

## Session Summary Automation

Her oturum sonunda ayni formatta summary dosyasi olusturmak icin:

```bash
python3 docs/quality-gates/create_session_summary.py --slug screenshots-gate
```

Bu komut su dosyalari kullanir:
- Template: `docs/quality-gates/session-summary-template.md`
- Output: `docs/quality-gates/<slug>-session-summary-YYYY-MM-DD.md`

## Reports

### Console Report
```
Quality Gates Pipeline: PASS
========================================
[PASS] code_quality      Score: 8.5/10  Time: 2500ms
[PASS] test_coverage     Score: 7.8/10  Time: 45000ms
[WARN] security          Score: 7.2/10  Time: 8000ms
...
Summary:
  Total Score: 7.9/10
  Passed: 6 | Failed: 0 | Skipped: 1
```

### JSON Report
```json
{
  "pipeline": {
    "status": "pass",
    "total_score": 7.9
  },
  "gates": [...]
}
```

### HTML Report
Visual dashboard with charts - see `report.html` output.

## Troubleshooting

### Gate Timeout
Gate 120 saniyeden uzun surerse TIMEOUT olur. Timeout artirmak icin:

```python
GateConfig(timeout_seconds=300)
```

### False Positives
Security gate false positive verirse:
1. Override workflow kullan
2. Tool config ayarla (bandit exclude)
3. `.bandit` config dosyasi olustur

### CI Failures
1. `quality-gates.yml` workflow loglarini kontrol et
2. Local'de ayni gate'i calistir
3. Gate-specific debug flags kullan

## Success Metrics

| Metrik | Hedef |
|--------|-------|
| Gate Pass Rate | >= 85% |
| Pipeline Duration | < 10 dakika |
| False Positive Rate | < 5% |
| Production Bug Rate | 95% azalma |

## Architecture

```
core/quality_gates/
├── __init__.py          # Public API
├── models.py            # Pydantic models
├── dependency_graph.py  # Topological sort
├── orchestrator.py      # Pipeline coordinator
├── override.py          # Override workflow
├── cli.py               # Command-line interface
├── gates/
│   ├── base.py          # Abstract base class
│   ├── code_quality.py
│   ├── test_coverage.py
│   ├── security.py
│   ├── performance.py
│   ├── architecture.py
│   ├── documentation.py
│   └── compliance.py
└── reporters/
    ├── console.py
    ├── json_reporter.py
    └── html_reporter.py
```
