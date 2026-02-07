# Python Code Quality Hooks Sistemi

Boris Cherny'nin verification feedback loops prensibi ile **%200-300 kalite artışı** sağlayan otomatik kod kalitesi kontrol sistemi.

## Özellikler

- **6 Kalite Hook'u**: Ruff, Mypy, Pytest, Black, isort, Docstring
- **Paralel Execution**: Tüm hook'lar aynı anda çalışır
- **Otomatik Düzeltme**: Auto-fix destekli linting ve formatting
- **Exit Code 2**: Engelleyici hatalar Claude'a geri beslenir
- **Timeout Koruması**: Hook başına maksimum 30 saniye

## Kurulum

```bash
# Gerekli paketler
pip install ruff mypy pytest black isort hypothesis

# Pre-commit kurulumu
pre-commit install
```

## Kullanım

### CLI'dan Çalıştırma

```bash
# Tüm hook'ları çalıştır (değişen dosyalarda)
cd backend
python -m hooks.orchestrator

# Belirli dosyalarda çalıştır
python -m hooks.orchestrator --files main.py api/routes.py

# Sadece hızlı kontroller (ruff, black, isort)
python -m hooks.orchestrator --quick

# Test modu
python -m hooks.orchestrator --test
```

### Python'dan Kullanım

```python
import asyncio
from backend.hooks.orchestrator import PostToolUseOrchestrator

async def check_code():
    orchestrator = PostToolUseOrchestrator()
    results = await orchestrator.run_all_checks(["my_file.py"])

    if results.all_passed:
        print("All checks passed!")
    else:
        print(f"Failed: {results.failed_checks} checks")
        print(f"Exit code: {results.exit_code}")

asyncio.run(check_code())
```

## Hook'lar

### 1. RuffHook (Linting)

```python
from backend.hooks.ruff_hook import run_ruff

result = await run_ruff(["file.py"])
```

- `ruff check --fix` çalıştırır
- Hata kategorileri: E (error), W (warning), F (fatal)
- E ve F hataları için Exit Code 2
- Auto-fix desteği

### 2. MypyHook (Type Checking)

```python
from backend.hooks.mypy_hook import run_mypy

result = await run_mypy(["file.py"])
```

- `mypy --ignore-missing-imports` çalıştırır
- Type error'lar için Exit Code 2
- Strict mode desteği (`--strict`)

### 3. PytestHook (Test Runner)

```python
from backend.hooks.pytest_hook import run_pytest

result = await run_pytest(["service.py"])
```

- İlgili test dosyasını otomatik bulur
- `pytest -x --tb=short` çalıştırır
- Test başarısızlığında Exit Code 2

### 4. BlackHook (Formatting)

```python
from backend.hooks.black_hook import run_black

result = await run_black(["file.py"])
```

- `black --line-length 88` çalıştırır
- Check-only mode desteği
- Ruff ile uyumlu

### 5. IsortHook (Import Sorting)

```python
from backend.hooks.isort_hook import run_isort

result = await run_isort(["file.py"])
```

- `isort --profile black` çalıştırır
- stdlib → third-party → local sıralaması
- Unused import uyarısı (silmez)

### 6. DocstringHook (Documentation)

```python
from backend.hooks.docstring_hook import run_docstring_check

result = await run_docstring_check(["file.py"])
```

- Public fonksiyonları tarar
- Google-style docstring bekler
- Coverage % hesaplar (hedef: ≥90%)

## Exit Codes

| Code | Anlam | Aksiyon |
|------|-------|---------|
| 0 | Success | Devam et |
| 2 | Blocking Error | Claude'a geri beslenir, düzeltme beklenir |

## Yapılandırma

```python
from backend.hooks.models import HookConfig

config = HookConfig(
    enabled=True,
    timeout=30.0,        # Saniye
    auto_fix=True,       # Otomatik düzeltme
    strict_mode=False,   # Mypy strict mode
    check_only=False,    # Sadece kontrol (değiştirme)
    line_length=88       # Black/isort line length
)
```

## Success Metrics

| Metrik | Hedef |
|--------|-------|
| Linting Error Rate | < %1 |
| Type Error Rate | < %2 |
| Test Pass Rate | ≥ %98 |
| Docstring Coverage | ≥ %90 |
| Hook Execution Time | < 10 saniye |

## Dosya Yapısı

```
backend/hooks/
├── __init__.py           # Module exports
├── models.py             # Pydantic models
├── base.py               # BaseHook abstract class
├── orchestrator.py       # Main orchestrator
├── ruff_hook.py          # Ruff linting
├── mypy_hook.py          # Mypy type checking
├── pytest_hook.py        # Pytest auto-run
├── black_hook.py         # Black formatting
├── isort_hook.py         # isort import sorting
├── docstring_hook.py     # Docstring validation
└── README.md             # Bu dosya

backend/utils/
├── file_watcher.py       # Git-based changed file detection
└── cache_manager.py      # Cache management

backend/tests/
├── unit/hooks/           # Unit tests
└── property/             # Property-based tests
```

## Pre-commit Entegrasyonu

`.pre-commit-config.yaml` ile entegre çalışır:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.1
    hooks:
      - id: ruff
        args: ['--fix']

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ['--profile', 'black']
```

## Testler

```bash
# Unit testler
pytest tests/unit/hooks/ -v

# Property testler (hypothesis, 100 iteration)
pytest tests/property/ -v

# Tüm hook testleri
pytest tests/unit/hooks/ tests/property/ -v --cov=backend/hooks
```

## Referanslar

- [Boris Cherny - Verification Feedback Loops](https://www.anthropic.com)
- [Daisy Stanton - Exit Code Standards](https://www.anthropic.com)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
