# Golden Flow CI Gate

The 8 Golden Flows are the user-validated set of critical journeys the
platform MUST deliver. Unit tests can all pass while a real user cannot log
in, list topics, or start an exam — Golden Flows catch that class of failure
before merge.

## The 8 Flows (user-approved, 10 Apr 2026)

| # | Flow | Surfaces |
|---|------|----------|
| GF1 | Login → `/me` | Auth stack end-to-end |
| GF2 | Daily learning path → DAG topics | Case convention endpoint gate |
| GF3 | TYT exam start → configs list | Exam engine read path |
| GF4 | Review queue (FSRS) | Review scheduler read path |
| GF5 | Teacher profile | Async ORM + AuthenticatedUser attrs |
| GF6 | Admin question bank | Production table wiring (`question_bank`) |
| GF7 | Video fallback (both cases) | Turkish locale I/ı trap |
| GF8 | Parent children view | Consent + parent auth |

Implementation: `backend/tests/e2e/test_golden_flows.py`
CI gate: `.github/workflows/golden-flows.yml`
Marker: `@pytest.mark.golden_flow`

## Rules

1. **Merge block.** If any Golden Flow test fails on a PR, the PR MUST NOT
   be merged. No exceptions — fix the regression first. Golden Flows are
   the last line of defense against silent feature rot.

2. **New top-level feature → new GF test.** Any new user-facing journey that
   is significant enough to be a "feature" (as opposed to a tweak) MUST be
   paired with a new `golden_flow` test before the feature ships. Use the
   same shape as the existing 8: one test, one journey, assert the endpoint
   responds with a *semantic* status (200/404) and never 500.

3. **No 500s allowed.** Every GF test asserts `status_code < 500` at minimum.
   A 500 means the auth → ORM → response pipeline is broken. The tests are
   deliberately lenient on 404 (the feature may be gated or unseeded) but
   a crash is always a regression.

4. **Case convention regression tests live here.** Any bug that was caused
   by Turkish case/locale mismatches (UPPERCASE DB vs lowercase query,
   `I → ı` locale trap, `subject_key()` / `subject_db()` misuse) should get
   a GF test added if it touched a user-facing surface. See GF2 and GF7.

5. **Path drift regression tests live here.** When `/api/v1/teacher/*` and
   `/api/v1/ogretmen/*` coexist and the frontend picks the wrong one, it is
   a GF-level bug. See GF5 and GF8.

## When adding a new GF test

```python
def test_gfN_short_description(client: httpx.Client):
    """One-line user-facing sentence describing the journey."""
    token = _login(client, STUDENT)  # or TEACHER/PARENT/ADMIN
    resp = client.get("/api/v1/your/endpoint", headers=_auth_headers(token))
    assert resp.status_code < 500, (
        f"GFN crashed: {resp.status_code} {resp.text[:300]}"
    )
    # Optional: assert semantic response shape
```

Then:

- Update the `GF list` comment at the top of
  `backend/tests/e2e/test_golden_flows.py`
- Update this file's table

## Running locally

```bash
# Full stack up first (docker compose or native)
cd backend
pytest tests/e2e/test_golden_flows.py -m golden_flow -v
```

If the backend is unreachable, the tests auto-skip with a clear message —
they will never fail-close against a missing environment.

## Related rules

- `.claude/rules/case-convention.md` — Endpoint Gate (subject identifier normalization)
- `.claude/rules/path-naming.md` — TR/EN duplicate implementation ban
- `.claude/rules/debugging-first.md` — Root cause analysis gate

---

*Oluşturulma: 2026-04-10 Session 135*
