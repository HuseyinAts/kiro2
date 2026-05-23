# Test Collection — Known Issues (Post-S197)

**Updated**: 23 May 2026 (S197 — Cat B+E pollution fix)
**Status**: ✅ **0 collection errors** (was 12 pre-S197, then 5 post-Cat A/C/D, now 0)
**Total tests collected**: 16,259 (was 14,733 — **+1,526 newly accessible**)

## Fixed in S197 (Commit `392c00459`)

| Category | Files | Root Cause | Fix |
|----------|-------|------------|-----|
| C — typing bug | 3 | `callable \| None` invalid (callable is builtin) | `Callable[..., Any] \| None` from `collections.abc` |
| A — auth middleware imports | 2 | Wrong order (sec_mod before patch) + `backend.` prefix | `import tests.conftest_security` at top (isort:skip), no prefix |
| D — locust/Py3.13 SSL recursion | 2 | urllib3 minimum_version setter infinite loop on Py3.13 | Module-level `pytest.skip` guarded by `sys.version_info >= (3, 13)` |

## Cat B+E Pollution — RESOLVED ✅

Identified 2 polluter files via alphabetical bisect (~30 min):

### Polluter 1: `tests/unit/test_coverage_final_50.py` (line 79)
```python
# BEFORE (poisoned 4 quality tests):
sys.modules.setdefault("services.quality", types.ModuleType("services.quality"))
sys.modules.setdefault("services.quality.metrics", metrics_mod)

# AFTER (removed — real package exists at backend/services/quality/):
# S197: services.quality stub removed — real package exists.
```
- Root cause: `types.ModuleType("services.quality")` turns the real package
  into a non-package, breaking `from services.quality.* import ...`
- Real path: `backend/services/quality/__init__.py` exists

### Polluter 2: `tests/unit/test_core_security_content.py` (line 127-129)
```python
# BEFORE (poisoned test_exam_curriculum_models):
sys.modules["models.curriculum"] = _curriculum_mod  # _SubjectType has only 2 values

# AFTER (conditional guard, same pattern they used for 'models'):
if "models.curriculum" not in sys.modules:
    sys.modules["models.curriculum"] = _curriculum_mod
```
- Root cause: partial `_SubjectType` stub (only MATEMATIK + FEN) replaced
  the real 12-value enum (TURKCE, FEN_BILIMLERI, ...)
- Fix: respect the same conditional pattern used for parent `models` package

## Bisect Method (for future similar issues)

1. Identify failing files in sweep but pass in isolation
2. Run `tests/[half-of-alphabet]/test_*.py + failing.py --co`
3. Narrow by halves until single polluter range
4. Run each candidate × failing target to confirm

Time: ~30 minutes for 2 polluters across 14k+ tests.

## Key Lesson — Coverage-Hack Anti-Pattern

Files like `test_coverage_final_50.py` and `test_core_security_content.py`
mock heavy dependencies via `sys.modules` injection to hit coverage targets.
When the mock is PARTIAL (missing enum values, missing attributes), it
poisons OTHER tests that load AFTER them in the alphabetical sweep.

**Rule of thumb**: When mocking modules via `sys.modules[...]`, ALWAYS use
the conditional guard pattern:
```python
if "models.X" not in sys.modules:  # only stub if real not yet loaded
    sys.modules["models.X"] = stub_mod
```

This was already done for top-level `models` in test_core_security_content.py
but missed for the subpackage `models.curriculum`. Same fix applies.

## Outcome

- **12 → 0** collection errors
- **14,733 → 16,259** tests collected (+1,526)
- **2 surgical fixes** (line removal + conditional guard)
- Coverage measurement now unblocked for all auth+quality modules
