# `.github/scripts/`

CI helper scripts invoked by `.github/workflows/quality-gate.yml`.

## `check_new_endpoints.py`

Static analysis of newly added `@router.{get,post,put,delete,patch}(...)`
decorators in the PR diff (vs `origin/$BASE_REF`, default `master`). Each
new endpoint is validated against a 7-item checklist:

| Code | Severity | Check |
|------|----------|-------|
| C1   | **HARD** | Decorator route uses `/api/v1/` prefix |
| C2   | SOFT     | Path segments English (Turkish only via `TR_ALLOWLIST`) |
| C3   | **HARD** | Auth dependency present (`current_user`, `require_admin`, etc.) — public endpoint allowlist hardcoded |
| C4   | **HARD** | No `user_id: ... = Query(...)` (IDOR — must come from `current_user`) |
| C5   | SOFT     | `response_model=` set in decorator |
| C6   | SOFT     | New `app/api/` or `api/` modules registered in `backend/routers/loader.py` |
| C7   | SOFT     | Tests added under `tests/` referencing the endpoint |

HARD violations exit `1` (CI fails). SOFT violations emit advisory warnings
but exit `0`.

### Background — which incidents this catches

- **C3** — Session 84 (`/api/v1/gamification/*` 13-endpoint IDOR sweep,
  user_id query param accepted from anyone).
- **C4** — Session 113 (31 endpoints missing auth across 5 files).
- **C6** — Session 112 (5 routers existed but never made it into
  `loader.py` ROUTER_MAPPING; silent 404 for 2+ weeks).
- **C1 / C2** — `.claude/rules/path-naming.md` Turkish/English duplicate
  ban and `/api/v1` canonical prefix.

### Override

To demote a HARD check, edit the top of `check_new_endpoints.py`:

```python
HARD_CHECKS: set[str] = {"C1", "C3", "C4"}  # remove or add codes
SOFT_CHECKS: set[str] = {"C2", "C5", "C6", "C7"}
```

To extend the public-endpoint allowlist for C3, edit `PUBLIC_ENDPOINTS`.
To extend the Turkish allowlist for C2, edit `TR_ALLOWLIST` (mirrors
`backend/scripts/audit_path_drift.py`).

### Related KIRO2 rules

- `.claude/rules/path-naming.md` — TR/EN duplicate ban, `/api/v1` prefix.
- `.claude/rules/golden-flows.md` — write-path GFs that exercise these endpoints.
- `.claude/rules/debugging-first.md` — root-cause table required before bug fix.

### Run locally

```bash
# Diff against master (defaults to BASE_REF=master)
python .github/scripts/check_new_endpoints.py

# Diff against a different base
BASE_REF=clean-main python .github/scripts/check_new_endpoints.py
```

Windows + Linux compatible — uses `pathlib.Path`, no `shell=True`.
