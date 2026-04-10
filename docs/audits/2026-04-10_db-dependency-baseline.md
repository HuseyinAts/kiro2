# DB Dependency Baseline — Session 137

**Date:** 2026-04-10
**Tool:** `backend/scripts/audit_db_dependency.py`
**Scope:** `backend/{api,app/api,app/services,core,services,analytics}`
**Total findings:** 179

## Summary

| Pattern | Severity | Count | Meaning |
|---|---|---|---|
| A — `AsyncSession = Depends(get_db)` + `await db.*` | HIGH | **25** | Guaranteed `MissingGreenlet` 500 on first call — broken today |
| A — type lie (no await) | MEDIUM | **110** | Annotation says `AsyncSession`, runtime gets sync `Session`. Works today, undefined tomorrow |
| B — `current_user.id` on `TokenPayload` | HIGH | **44** | `AttributeError` 500 — `TokenPayload` has `.sub`, not `.id` |

## Root Cause

**`backend/core/database.py:395`** — `get_db()` is a SYNC compatibility shim that
yields a sync `sqlalchemy.orm.Session`. When a handler is declared as
`db: AsyncSession = Depends(get_db)`, FastAPI's DI resolver does NOT type-check
the annotation against what the dependency yields — it silently injects a sync
Session. The first `await db.execute(...)` raises `MissingGreenlet` → 500.

**`backend/core/jwt_auth.py`** — `get_current_user` returns a Pydantic
`TokenPayload` whose user_id field is `sub`. Any handler that imports
`get_current_user` from `core.jwt_auth` and does `current_user.id` will raise
`AttributeError` → 500.

**Aliasing escape hatch** — files that write
`from core.database import get_async_session as get_db` are safe (linter
correctly filters them out). The broken pattern is the bare
`from core.database import get_db`.

---

## HIGH — Pattern A Broken (25 handlers, 4 files)

Every handler below fails `status_code < 500` on first call because
`await db.execute(...)` receives a sync Session.

| File | Count | Notes |
|---|---|---|
| `api/khan_routes.py` | 9 | Pure Pattern A. No Pattern B. Ideal Aşama 2a target. |
| `api/two_factor_auth_api.py` | 7 | **Dual-trap** (A=7, B=19). 2FA endpoints completely unusable. |
| `api/kvkk_privacy_api.py` | 6 | **Dual-trap** (A=6, B=22). KVKK privacy endpoints completely unusable. |
| `api/eba_routes.py` | 3 | Also has 10 type-lie. EBA integration partially broken. |

## HIGH — Pattern B TokenPayload.id (44 uses, 3 files)

| File | Count | Notes |
|---|---|---|
| `api/kvkk_privacy_api.py` | 22 | Dual-trap — blocks all privacy flows |
| `api/two_factor_auth_api.py` | 19 | Dual-trap — blocks all 2FA flows |
| `api/rate_limit_api.py` | 3 | Pattern B only. Independent fix. |

## MEDIUM — Pattern A Type-Lie (110 handlers, 8 files)

These work today because the handler never actually awaits on `db`. The
annotation is a lie — it says `AsyncSession` but the runtime object is a sync
Session. Any future refactor that adds `await db.*` to these handlers will
silently convert them into 500 factories.

| File | Count |
|---|---|
| `api/diary_api.py` | 47 |
| `api/university_info_routes.py` | 19 |
| `api/department_info_routes.py` | 15 |
| `api/eba_routes.py` | 10 |
| `api/preference_simulation_routes.py` | 9 |
| `api/sequential_reasoning_api.py` | 8 |
| `api/khan_routes.py` | 1 |
| `api/rate_limit_api.py` | 1 |

---

## Dual-Trap Files (highest impact)

Files with BOTH Pattern A broken AND Pattern B:

| File | A broken | B | Impact |
|---|---|---|---|
| `api/kvkk_privacy_api.py` | 6 | 22 | 100% 500 on every call |
| `api/two_factor_auth_api.py` | 7 | 19 | 100% 500 on every call |

These files are fire-and-forget — every single endpoint will 500. Users cannot
enable 2FA and cannot exercise any KVKK privacy right (data export, deletion,
consent withdrawal). **These are the highest-impact fixes.**

---

## Correction — Earlier Audit False Positives

The earlier `2026-04-10_half-working-feature-deep-audit.md` report listed
these as broken; the AST linter proves they are NOT:

| File | Claim | Reality |
|---|---|---|
| `api/osym_questions_api.py` | 5 handlers broken | Uses `from core.database import get_async_session as get_db` — alias pattern, actually async, working. 0 findings. |
| `api/question_crud_api.py` | 1 handler broken | Same alias pattern. 0 findings. |
| `api/enhanced_auth_api.py` | Pattern B | 0 findings — uses `.sub` correctly or annotates `AuthenticatedUser`. |

The deep audit was text-based grep that matched on import lines without
resolving the alias. The linter is AST-based and handles `as` correctly.

---

## Fix Plan (4 stages)

**Aşama 1 — Detection (THIS COMMIT)**
- [x] AST linter written
- [x] Baseline captured
- [ ] CI gate wired (Aşama 4)

**Aşama 2 — High-severity Pattern A fixes (TDD, one file per commit)**
- [ ] 2a. `khan_routes.py` — 9 handlers, pure Pattern A, no dual trap. Start here.
- [ ] 2b. `eba_routes.py` — 3 broken + 10 type-lie, fix both together.
- [ ] 2c. `kvkk_privacy_api.py` — dual trap (6A + 22B). Two fix passes in one commit.
- [ ] 2d. `two_factor_auth_api.py` — dual trap (7A + 19B). Two fix passes.

**Aşama 3 — Pattern B only**
- [ ] 3a. `rate_limit_api.py` — 3 `.id` → `.sub` rewrites.

**Aşama 4 — Long-term hardening**
- [ ] Deprecate sync `get_db()` shim in `core/database.py:395` (rename to `get_db_sync` so no one imports it by accident).
- [ ] Wire linter into `.github/workflows/golden-flows.yml` — `--fail` on any HIGH severity finding in `api/`.
- [ ] Medium-term: address 110 type-lie findings (less urgent — works today).

Per-stage TDD loop:
1. Write `golden_flow` write-path test → run → FAIL
2. Fix imports: `from core.database import get_db` → `from core.database import get_async_session`
3. Fix params: `Depends(get_db)` → `Depends(get_async_session)`
4. Fix token: `current_user.id` → `current_user.sub` where applicable
5. Rebuild docker backend, run GF test → PASS
6. Re-run linter — target file's HIGH count must drop to 0
7. Commit with trace to this baseline doc

## How to Reproduce

```bash
cd backend
python scripts/audit_db_dependency.py                    # text report
python scripts/audit_db_dependency.py --json audit.json  # machine readable
python scripts/audit_db_dependency.py --fail             # exit 1 if any findings
```
