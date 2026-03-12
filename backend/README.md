# KIRO2 Backend Tests

## Test Stratification Contract

This document defines the test stratification system for CI/CD pipeline.

### Routing Rules
- Unstratified tests in specific directories are routed to `integration` or `infra` markers.
- Existing markers (unit/property/integration/infra/serial) are NEVER overridden.
- Routing directories:
  - **Infra**: `/tests/db/`, `/tests/health/`
  - **Integration**: `/tests/services/`, `/tests/core/`, `/tests/test_pipeline/`, `/tests/accessibility/`, `/tests/slow/`, `/tests/smoke/`, `/tests/functional/`, `/tests/fast/`, `/tests/hooks/`, `/tests/performance/`, `/tests/agents/`, `/tests/guardrails/`, `/tests/mcp_servers/`

### Serial Marker
- `serial` is orthogonal - it can coexist with any marker (unit/integration/infra/property).
- Tests with serial marker cannot run in parallel.

### Parallel Execution
- `all_parallel` filter: `(unit or property) and not serial`
- Parallel is NOT the default; explicit marker required.

### Coverage Calculation
- Coverage = total collected - unstratified
- Stratified layer counts may overlap due to serial orthogonality.

### Canonical Execution
- Use `.agent/run_tests.py` with `tests.json` keys.
- CI Guardrail: Unstratified ratio must be ≤10% (exit code 2 if exceeded).

## Running Tests

```bash
# All stratified tests
pytest -m "unit or property or integration or infra or serial"

# Parallel-safe only
pytest -m "(unit or property) and not serial"

# Run specific marker
pytest -m "unit"
pytest -m "integration"
```

## CI Guardrail

To check unstratified ratio:

```bash
python .agent/guardrail_unstratified.py
```

Exit code 2 if ratio > 10%.

CI guardrail key: py.backend.ci_guardrail_unstratified (threshold 10%)
