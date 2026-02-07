# Design Document - Python Code Quality Hooks Sistemi

## Overview

Python Code Quality Hooks Sistemi, PreToolUse ve PostToolUse hook'ları ile ruff, mypy, pytest, black, isort otomatik çalıştırır. Boris Cherny'nin verification feedback loops prensibi ile kod kalitesi %200-300 artırılır.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Developer Kod Yazıyor                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              PostToolUse Hook Trigger                        │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│Ruff Linting  │  │Mypy Type     │  │ Pytest       │
│+ Auto-fix    │  │ Checking     │  │ Auto-Run     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Black      │  │    isort     │  │  Docstring   │
│ Formatting   │  │Import Sorting│  │ Validation   │
└──────────────┘  └──────────────┘  └──────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
                  Exit Code 0/2
                         │
            ┌────────────┴────────────┐
            │                         │
         Exit 0                    Exit 2
            │                         │
            ▼                         ▼
    ┌──────────────┐          ┌──────────────┐
    │   Success    │          │Feedback to   │
    │      ✓       │          │   Claude     │
    └──────────────┘          └──────────────┘
```

## Components

```python
app/
├── hooks/
│   ├── __init__.py
│   ├── post_tool_use_hook.py       # Main hook
│   ├── ruff_hook.py                # Ruff linting
│   ├── mypy_hook.py                # Type checking
│   ├── pytest_hook.py              # Test runner
│   ├── black_hook.py               # Formatting
│   ├── isort_hook.py               # Import sorting
│   └── docstring_hook.py           # Docstring validation
└── utils/
    ├── __init__.py
    ├── file_watcher.py             # Changed files detection
    └── cache_manager.py            # .ruff_cache, .mypy_cache
```

## Key Interfaces

```python
class QualityCheckResult(BaseModel):
    tool: str
    passed: bool
    exit_code: int
    errors: List[str]
    warnings: List[str]
    execution_time: float

class PostToolUseHook:
    async def run_all_checks(self, changed_files: List[str]) -> Dict
    async def run_ruff(self, files: List[str]) -> QualityCheckResult
    async def run_mypy(self, files: List[str]) -> QualityCheckResult
    async def run_pytest(self, files: List[str]) -> QualityCheckResult
```

## Correctness Properties

### Property 1: Exit Code Consistency
*For any* quality check with errors, exit code must be 2.
**Validates: Requirements 1.5, 2.5, 3.5**

### Property 2: Parallel Execution Time
*For any* hook execution, total time must be less than sum of individual times (parallelization benefit).
**Validates: Requirements 8.3**

### Property 3: Cache Effectiveness
*For any* unchanged file, quality check must use cached result.
**Validates: Requirements 8.1, 8.2**

## Testing Strategy

- Unit tests for each hook
- Property tests for exit codes, timing, caching
- Integration tests for full hook flow

**Test Configuration**: Minimum 100 iterations per property test
