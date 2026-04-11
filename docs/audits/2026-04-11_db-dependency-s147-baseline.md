# DB Dependency Baseline — Session 147 (Refresh)

**Date:** 2026-04-11
**Tool:** `backend/scripts/audit_db_dependency.py`
**Scope:** `backend/{api,app/api,app/services,core,services,analytics}`
**Total findings:** **0**

## Headline

Pattern A and Pattern B are now **fully eradicated** from the audit scope.
The `audit_db_dependency.py --fail-on-high` CI gate (Session 137 Aşama 4)
remains green at **zero** HIGH-severity findings.

## Summary

| Pattern | Severity | Session 137 | Session 147 | Δ |
|---|---|---:|---:|---:|
| A — `AsyncSession = Depends(get_db)` + `await db.*` | HIGH | 25 | **0** | **−25** |
| A — type lie (no await) | MEDIUM | 110 | **0** | **−110** |
| B — `current_user.id` on `TokenPayload` | HIGH | 44 | **0** | **−44** |
| **Total** | — | **179** | **0** | **−179** |

> Session 137 published a "post-fix" baseline of 98 MEDIUM remaining after
> Aşama 4 (Pattern A broken + Pattern B both at 0, type-lies left as tech
> debt). Session 147 confirms all three categories are now zero.

## What changed since Session 137

The run-down was incremental, not a single sweep:

1. **Session 137 — Aşama 1-4**: 25 Pattern A broken + 44 Pattern B fixes
   (khan/eba/kvkk/2fa) + 44 Pattern B fixes; CI gate added (`--fail-on-high`).
   Closed 69 HIGH findings.
2. **Wave 10 (Session 145, GF86/GF87)**: `instant_feedback_api.py` rewritten
   sync → async, dep swapped from `get_db` → `get_async_session` (the bug
   class that surfaced this exact gate).
3. **Session 146 — rule-of-eight bonus cleanup**: smoke test surfaced 6
   pre-existing broken imports, 4 of which were missing `get_async_session`
   imports (`khan_routes.py`, `eba_routes.py`, `instant_feedback_api.py`,
   `sequential_reasoning_api.py`). Fixed in the same commit as the
   rule-of-eight sweep.
4. **Incremental MEDIUM type-lie cleanups across Sessions 138-146** —
   handler-by-handler, every time a Wave probe touched a file with a type
   lie, the dep was upgraded to `get_async_session`.

## Verification

```bash
cd backend
python scripts/audit_db_dependency.py --fail-on-high
# fail-on-high exit: 0

python scripts/audit_db_dependency.py
# **Total findings:** 0
#   - Pattern A (broken, await db.*): 0
#   - Pattern A (type lie, no await): 0
#   - Pattern B (TokenPayload.id): 0
# _Clean — no Pattern A/B mismatches detected._
```

## Implications

- The `get_db` sync shim in `backend/core/database.py:395-449` is no longer
  referenced by any handler in the audit scope. The shim's
  `DeprecationWarning` (Session 137 Aşama 4) is now informational only — it
  can be removed safely after one more grep sweep across the
  `_deprecated/` and tests directories that the audit excludes.
- The `--fail-on-high` CI gate continues to merge-block any future
  regression. Combined with the new Session 147 rule-of-eight gate, the
  KIRO2 backend now has six AST linters enforcing handler invariants:
  1. `audit_db_dependency.py --fail-on-high` (Pattern A/B)
  2. `audit_missing_auth.py --fail-on-high`
  3. `audit_dual_table_trap.py --fail-on-high`
  4. `audit_missing_is_active.py --fail-on-high`
  5. `audit_missing_rate_limit.py --fail-on-high`
  6. `audit_httpexception_guard.py --fail` (rule-of-eight, Session 147)

## Caveats

- **Parse error**: `services/nlp_training/berturk_finetuning_pipeline.py`
  fails to decode as UTF-8 (binary content in a `.py` file). Audit skips it
  with a warning; this has been the case since Session 137 and is not a
  regression. File should be deleted or moved out of `services/` if it is
  not actually a Python module.
- The audit excludes `_deprecated/`, `tests/`, `scripts/`, `alembic/`. Any
  legacy `get_db` usage in those trees is intentional and out of scope.

---

*Session 147 — 2026-04-11*
