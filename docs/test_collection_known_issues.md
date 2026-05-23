# Test Collection — Known Issues (Post-S197)

**Updated**: 23 May 2026 (S197)
**Status**: 5 collection errors remain (was 12 pre-S197)

## Fixed in S197 (Commit `392c00459`)

| Category | Files | Root Cause | Fix |
|----------|-------|------------|-----|
| C — typing bug | 3 | `callable \| None` invalid (callable is builtin) | `Callable[..., Any] \| None` from `collections.abc` |
| A — auth middleware imports | 2 | Wrong order (sec_mod before patch) + `backend.` prefix | `import tests.conftest_security` at top (isort:skip), no prefix |
| D — locust/Py3.13 SSL recursion | 2 | urllib3 minimum_version setter infinite loop on Py3.13 | Module-level `pytest.skip` guarded by `sys.version_info >= (3, 13)` |

## Remaining (Pollution — Collect Pass Individually)

These 5 files collect successfully in **isolation** but fail in the **full sweep**.
Root cause: shared sys.modules state pollution by some earlier test.

| File | Individual collect | Sweep error |
|------|---------------------|-------------|
| tests/unit/test_exam_curriculum_models.py | 1,250 tests | AttributeError |
| tests/unit/test_quality_ab_testing.py | 35 tests | ModuleNotFoundError |
| tests/unit/test_quality_expert_review.py | ? | ModuleNotFoundError |
| tests/unit/test_quality_nlp_metrics.py | ? | ModuleNotFoundError |
| tests/unit/test_quality_question_scorer.py | 39 tests | "services.quality is not a package" |

## Investigation Done (S197)

- ❌ `backend/quality.py` shadow hypothesis (top-level script): refuted — direct import test passed
- ❌ `services/youtube/quality.py` conflict: same dir tree, no shadow
- ❌ Direct sys.modules manipulation: only `test_social_content_filter.py` does `sys.modules["services.social_content_filter"] = _mod`, not related
- ❌ Pairing with test_social_content_filter: both collect fine together

## Next Investigation (Deferred)

Bisect the full sweep:
1. `pytest tests/ --co --collect-only` and find files alphabetically BEFORE first failure
2. Binary search by progressively narrowing the prefix
3. Look for `MagicMock` / `unittest.mock.patch` on `services` or `services.quality`
4. Check for `from services import quality` patterns (importing as attribute, not subpackage)

## Workaround (Until Pollution Fixed)

```bash
# These tests still work — just run them individually or in their own subset
pytest tests/unit/test_quality_ab_testing.py tests/unit/test_quality_expert_review.py \
       tests/unit/test_quality_nlp_metrics.py tests/unit/test_quality_question_scorer.py \
       tests/unit/test_exam_curriculum_models.py -v

# Full sweep skipping these (CI workaround):
pytest tests/ --ignore=tests/unit/test_quality_ab_testing.py \
              --ignore=tests/unit/test_quality_expert_review.py \
              --ignore=tests/unit/test_quality_nlp_metrics.py \
              --ignore=tests/unit/test_quality_question_scorer.py \
              --ignore=tests/unit/test_exam_curriculum_models.py
```

## Impact

- 1,250 + 35 + 39 + ~unknown = **~1,400 tests** affected
- Tests themselves work — only collection fails in sweep
- Real coverage measurement requires fix OR running them in separate process
