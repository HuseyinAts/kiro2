# Code Quality Guide

**Document Version**: 1.0
**Sprint**: Phase 3 Sprint 8 - Code Quality & Standardization
**Last Updated**: 2025-11-12
**Status**: ✅ Active

---

## Table of Contents

1. [Overview](#overview)
2. [Tools & Standards](#tools--standards)
3. [Code Formatting](#code-formatting)
4. [Linting](#linting)
5. [Type Checking](#type-checking)
6. [Security Scanning](#security-scanning)
7. [Pre-commit Hooks](#pre-commit-hooks)
8. [CI/CD Integration](#cicd-integration)
9. [Best Practices](#best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

This guide establishes **code quality standards** for the Kiro2 backend. All code must pass quality checks before merging to maintain:

- ✅ **Consistency**: Uniform code style across the team
- ✅ **Readability**: Clear, maintainable code
- ✅ **Reliability**: Fewer bugs through static analysis
- ✅ **Security**: Early detection of vulnerabilities

### Quality Gates

| Gate | Tool | Required | Auto-fix |
|------|------|----------|----------|
| Formatting | Black | ✅ Yes | ✅ Yes |
| Import Sorting | isort | ✅ Yes | ✅ Yes |
| Linting | Flake8 + Ruff | ⚠ Warning | Partial |
| Type Checking | MyPy | ⚠ Gradually | No |
| Security | Bandit + Safety | ⚠ Warning | No |

---

## Tools & Standards

### 1. Black - Code Formatter

**Purpose**: Automatic code formatting
**Configuration**: `pyproject.toml`
**Standard**: PEP 8 compliant

**Settings**:
```toml
[tool.black]
line-length = 88
target-version = ['py311']
```

**Why Black?**
- Zero configuration
- Deterministic formatting
- Fast (written in Python + Rust)
- Industry standard

---

### 2. isort - Import Sorter

**Purpose**: Organize imports consistently
**Configuration**: `pyproject.toml`
**Profile**: Black-compatible

**Settings**:
```toml
[tool.isort]
profile = "black"
line_length = 88
```

**Import Order**:
1. Future imports
2. Standard library
3. Third-party packages
4. First-party modules
5. Local imports

---

### 3. Flake8 - Linter

**Purpose**: Style guide enforcement
**Configuration**: `setup.cfg`
**Standard**: PEP 8 + additional rules

**Settings**:
```ini
[flake8]
max-line-length = 88
max-complexity = 10
ignore = E203,E501,W503
```

**Key Checks**:
- Syntax errors
- Undefined names
- Unused imports
- Code complexity
- Style violations

---

### 4. Ruff - Fast Linter

**Purpose**: Modern, extremely fast linter
**Configuration**: `pyproject.toml`
**Speed**: 10-100x faster than Flake8

**Settings**:
```toml
[tool.ruff]
target-version = "py311"
line-length = 88
```

**Rule Sets**:
- E/W: pycodestyle
- F: pyflakes
- I: isort
- N: pep8-naming
- S: bandit security
- B: bugbear
- ...and more

---

### 5. MyPy - Type Checker

**Purpose**: Static type checking
**Configuration**: `pyproject.toml`
**Mode**: Gradually enabled

**Settings**:
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = false  # Gradually enable
disallow_untyped_defs = false  # Gradually enable
check_untyped_defs = true
```

**Why Gradual?**
- Large codebase
- Incremental adoption
- Minimal disruption

---

### 6. Bandit - Security Scanner

**Purpose**: Find security issues
**Configuration**: `pyproject.toml`
**Focus**: OWASP Top 10

**Checks**:
- SQL injection
- Command injection
- Hardcoded secrets
- Weak cryptography
- Insecure functions

---

### 7. Safety - Dependency Scanner

**Purpose**: Check for vulnerable dependencies
**Source**: PyPI vulnerability database

**Checks**:
- Known CVEs
- Security advisories
- Outdated packages

---

## Code Formatting

### Using Black

**Auto-format all code**:
```bash
black .
```

**Check without modifying**:
```bash
black --check --diff .
```

**Format specific files**:
```bash
black core/advanced_rate_limiter.py
```

### Using isort

**Sort all imports**:
```bash
isort .
```

**Check without modifying**:
```bash
isort --check-only --diff .
```

**Combined (recommended)**:
```bash
make format
```

### Before/After Example

**Before** (inconsistent):
```python
import os
from typing import Optional
import redis
from fastapi import FastAPI,Request,HTTPException
from core.config import settings

def my_function(  x,y  ):
    return x+y
```

**After** (formatted):
```python
import os
from typing import Optional

import redis
from fastapi import FastAPI, HTTPException, Request

from core.config import settings


def my_function(x, y):
    return x + y
```

---

## Linting

### Using Flake8

**Run linter**:
```bash
flake8 .
```

**With statistics**:
```bash
flake8 . --count --statistics
```

**Check specific files**:
```bash
flake8 core/ api/
```

### Using Ruff

**Run linter**:
```bash
ruff check .
```

**Auto-fix issues**:
```bash
ruff check . --fix
```

**Watch mode**:
```bash
ruff check . --watch
```

### Common Issues

| Code | Issue | Fix |
|------|-------|-----|
| E501 | Line too long | Use Black |
| F401 | Unused import | Remove import |
| F841 | Unused variable | Use or remove |
| C901 | Too complex | Refactor function |
| E203 | Whitespace before ':' | Use Black |

---

## Type Checking

### Using MyPy

**Type check core modules**:
```bash
mypy core/ --ignore-missing-imports
```

**Strict mode (future)**:
```bash
mypy core/ --strict
```

**Check specific file**:
```bash
mypy core/advanced_rate_limiter.py
```

### Adding Type Hints

**Before**:
```python
def check_rate_limit(identifier, endpoint, tier, window):
    # ...
    return allowed, info
```

**After**:
```python
from typing import Tuple, Dict

def check_rate_limit(
    identifier: str,
    endpoint: str,
    tier: UserTier,
    window: int = 60
) -> Tuple[bool, Dict[str, int]]:
    # ...
    return allowed, info
```

### Type Checking Benefits

- ✅ Catch bugs before runtime
- ✅ Better IDE autocomplete
- ✅ Self-documenting code
- ✅ Refactoring confidence

---

## Security Scanning

### Using Bandit

**Scan for security issues**:
```bash
bandit -r . -x ./tests,./venv
```

**High severity only**:
```bash
bandit -r . -x ./tests,./venv -ll
```

**Generate report**:
```bash
bandit -r . -x ./tests,./venv -f json -o bandit-report.json
```

### Using Safety

**Check dependencies**:
```bash
safety check
```

**Check with JSON output**:
```bash
safety check --json
```

**Check requirements.txt**:
```bash
safety check -r requirements.txt
```

### Common Security Issues

| Issue | Example | Fix |
|-------|---------|-----|
| SQL Injection | `f"SELECT * FROM users WHERE id={user_id}"` | Use parameterized queries |
| Hardcoded Secret | `API_KEY = "sk-123456"` | Use environment variables |
| Command Injection | `os.system(f"ls {user_input}")` | Use subprocess with list |
| Weak Crypto | `hashlib.md5(password)` | Use bcrypt/argon2 |

---

## Pre-commit Hooks

### What are Pre-commit Hooks?

**Automatic code quality checks before each commit.**

### Setup

**Install pre-commit**:
```bash
pip install pre-commit
```

**Install hooks**:
```bash
pre-commit install
```

**Run manually**:
```bash
pre-commit run --all-files
```

### Configured Hooks

Our `.pre-commit-config.yaml` includes:

1. **Ruff** - Fast linting
2. **Black** - Code formatting
3. **isort** - Import sorting
4. **Basic checks** - Trailing whitespace, YAML syntax, etc.
5. **MyPy** - Type checking (optional)
6. **Bandit** - Security scanning

### Hook Workflow

```
git commit
    ↓
Pre-commit runs
    ↓
Black formats code
    ↓
isort sorts imports
    ↓
Ruff lints code
    ↓
Bandit scans security
    ↓
All pass? → Commit
    ↓
Fail? → Fix issues and retry
```

### Bypass Hooks (Emergency Only)

```bash
git commit --no-verify -m "Emergency fix"
```

⚠️ **Warning**: Only use in emergencies. CI will still run checks.

---

## CI/CD Integration

### GitHub Actions Workflow

Our CI pipeline runs all quality checks:

**File**: `.github/workflows/backend-tests.yml`

**Jobs**:
1. **Test & Coverage** - Run tests with coverage
2. **Lint & Format** - Check code style
3. **Security** - Scan for vulnerabilities

### Job 2: Lint & Format Check

```yaml
- name: Check code formatting with Black
  run: black --check --diff .

- name: Check import sorting with isort
  run: isort --check-only --diff .

- name: Lint with flake8
  run: flake8 . --count --statistics
```

### PR Workflow

```
Developer pushes code
    ↓
GitHub Actions triggered
    ↓
Run all quality checks
    ↓
Report status on PR
    ↓
Pass? → Merge allowed
    ↓
Fail? → Fix required
```

---

## Best Practices

### 1. Format Before Committing

**Always run before commit**:
```bash
make format
```

Or rely on pre-commit hooks.

### 2. Fix Linting Issues

**Don't ignore warnings**:
```bash
make lint
```

Address issues or add `# noqa` with justification:
```python
import something  # noqa: F401 - Used by plugin system
```

### 3. Add Type Hints Gradually

**Start with function signatures**:
```python
def my_function(x: int, y: str) -> bool:
    ...
```

**Use TypedDict for complex structures**:
```python
from typing import TypedDict

class RateLimitInfo(TypedDict):
    limit: int
    remaining: int
    reset: int
```

### 4. Write Secure Code

**Checklist**:
- [ ] No hardcoded secrets
- [ ] Use parameterized SQL queries
- [ ] Validate all user input
- [ ] Use secure random (secrets module)
- [ ] Hash passwords with bcrypt

### 5. Keep Dependencies Updated

**Check regularly**:
```bash
pip list --outdated
```

**Update with testing**:
```bash
pip install --upgrade package-name
make test
```

---

## Running Quality Checks

### Quick Commands

| Command | Description |
|---------|-------------|
| `make format` | Auto-format code |
| `make lint` | Run linters |
| `make type-check` | Type check code |
| `make security` | Security scan |
| `make quality` | All checks |
| `make pre-commit` | Run hooks |
| `make ci` | Full CI pipeline |

### Full Quality Check Script

**Run comprehensive check**:
```bash
python code_quality.py
```

**Output**:
```
================================================================================
                     KIRO2 CODE QUALITY CHECKER - SPRINT 8
================================================================================

================================================================================
                            PHASE 1: Code Formatting
================================================================================

► Running: Black Code Formatter Check
  Command: python -m black --check --diff .

✓ Black Code Formatter Check - PASSED

► Running: isort Import Sorting Check
  Command: python -m isort --check-only --diff .

✓ isort Import Sorting Check - PASSED

...

================================================================================
                            CODE QUALITY SUMMARY
================================================================================

Check Results:

  Black Formatting               ✓ PASSED
  isort Import Sorting           ✓ PASSED
  Flake8 Linting                 ✓ PASSED
  Ruff Linting                   ✓ PASSED
  MyPy Type Checking             ⚠ WARNINGS
  Bandit Security                ✓ PASSED
  Safety Dependencies            ✓ PASSED

✓ ALL CRITICAL CHECKS PASSED!
  Your code meets quality standards.
```

---

## Troubleshooting

### Issue 1: Black and Flake8 Conflict

**Problem**: Flake8 complains about Black's formatting

**Solution**: Ensure Flake8 config ignores Black-related rules:
```ini
[flake8]
ignore = E203,E501,W503
```

---

### Issue 2: isort and Black Conflict

**Problem**: isort changes break Black formatting

**Solution**: Use Black-compatible profile:
```toml
[tool.isort]
profile = "black"
```

---

### Issue 3: MyPy Too Strict

**Problem**: Too many type errors in legacy code

**Solution**: Enable gradually:
```toml
[tool.mypy]
disallow_untyped_defs = false  # Start here
check_untyped_defs = true      # Then this
# Later: disallow_untyped_defs = true
```

---

### Issue 4: Pre-commit Hooks Too Slow

**Problem**: Commits take too long

**Solution**: Skip slow hooks during development:
```yaml
# In .pre-commit-config.yaml
- id: mypy
  stages: [push]  # Only run on push, not commit
```

---

### Issue 5: CI Fails Locally Works

**Problem**: Code passes locally but fails CI

**Cause**: Different Python versions or dependencies

**Solution**: Match CI environment:
```bash
# Use same Python version as CI
pyenv install 3.11
pyenv local 3.11

# Update dependencies
pip install -r requirements-test.txt
```

---

## Code Quality Metrics

### Target Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Test Coverage | 40% | 80% | 🔄 In Progress |
| Type Coverage | 20% | 60% | 🔄 Gradual |
| Linting Score | 8/10 | 9/10 | ✅ Good |
| Security Score | 9/10 | 10/10 | ✅ Good |
| Code Complexity | Low | Low | ✅ Good |

### Measuring Progress

**Coverage over time**:
```bash
pytest --cov=core --cov-report=term
```

**Type coverage**:
```bash
mypy core/ --any-exprs-report=mypy-report
```

**Complexity**:
```bash
flake8 . --max-complexity=10
```

---

## IDE Integration

### VS Code

**Install extensions**:
- Python (Microsoft)
- Black Formatter
- isort
- Ruff
- MyPy Type Checker

**Settings** (`.vscode/settings.json`):
```json
{
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm

**Settings**:
1. **Black**: Preferences → Tools → Black
2. **isort**: Preferences → Tools → isort
3. **Flake8**: Preferences → Editor → Inspections → Python
4. **MyPy**: Preferences → Tools → External Tools

---

## Resources

### Official Documentation

- **Black**: https://black.readthedocs.io/
- **isort**: https://pycqa.github.io/isort/
- **Flake8**: https://flake8.pycqa.org/
- **Ruff**: https://docs.astral.sh/ruff/
- **MyPy**: https://mypy.readthedocs.io/
- **Bandit**: https://bandit.readthedocs.io/
- **Safety**: https://pyup.io/safety/

### Internal Documentation

- [ARCHITECTURE_REVIEW.md](../../ARCHITECTURE_REVIEW.md) - Overall architecture
- [SPRINT_7_COMPLETION_REPORT.md](../SPRINT_7_COMPLETION_REPORT.md) - Testing
- [SPRINT_8_COMPLETION_REPORT.md](../SPRINT_8_COMPLETION_REPORT.md) - This sprint

---

**Document Version**: 1.0
**Last Review**: 2025-11-12
**Next Review**: 2025-12-12
**Status**: ✅ Active
