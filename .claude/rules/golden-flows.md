# Golden Flow CI Gate

The Golden Flows are the user-validated set of critical journeys the platform
MUST deliver. Unit tests can all pass while a real user cannot log in, list
topics, or start an exam — Golden Flows catch that class of failure before
merge.

## The Flows (user-approved, 10 Apr 2026)

**Read-path (GF1-GF8):**

| # | Flow | Surfaces |
|---|------|----------|
| GF1 | Login → `/me` | Auth stack end-to-end |
| GF2 | Daily learning path → DAG topics | Case convention endpoint gate |
| GF3 | TYT exam configs list | Exam engine read path (router prefix `/api/v1/osym-exam`) |
| GF4 | Review queue (FSRS) | Review scheduler read path |
| GF5 | Teacher profile | Async ORM + AuthenticatedUser attrs |
| GF6 | Admin question bank | Production table wiring (`question_bank`) |
| GF7 | Video fallback (both cases) | Turkish locale I/ı trap |
| GF8 | Parent children view | Consent + parent auth |

**Write-path (GF1w-GF149 across 16 waves, Sessions 136-152):**

Detailed per-wave probe tables, root-cause analyses, and hit-rate trailing
indicator are archived in `docs/audits/golden-flows-history.md`. Current
distribution as of Session 152: ~~**166 tests → 164 PASS / 0 FAIL / 2 SKIP**~~.

> ⚠️ **BAYAT — 31 Tem 2026 ölçümü (`docs/audits/2026-07-31_eksiklik_durum_dogrulamasi.md`, D6):**
> Gerçek **178 test** (`grep -c 'def test_' backend/tests/e2e/test_golden_flows.py`).
> Canlı koşum **30 PASS / 148 SKIP / 0 FAIL** — 147 skip rate-limit, 1 seed.
> **Aşağıdaki "Merge block" kuralı bu yüzden fiilen çalışmıyor:** `_login()`
> (`test_golden_flows.py:88-97`) 429'u `pytest.skip`'e çeviriyor ve skip ASLA FAIL
> üretmez; ayrıca `golden-flows.yml`'in `on:` bloğu `[main,master,develop]` iken aktif
> dal 318 commit önde, yani kapı hiç tetiklenmiyor. Görev **#462**.

## Suite saturation (Session 152)

Two consecutive 0% hit-rate waves on disjoint target strategies (Wave 15
frontend-traffic mapping, Wave 16 low-traffic breadth) declared the suite
**saturated for single-handler bug discovery**. The systemic anti-pattern
classes have been eradicated or guarded by linters:

- rule-of-eight bare-`except Exception` swallowing 4xx/5xx (Session 146 sweep)
- rule-of-seven VARCHAR + `default=uuid4` caller-coerce (Session 142 sweep)
- rule-of-five Pydantic `user_id: int` (Session 148 prophylactic sweep)
- rule-of-four `list[dict]` vs `Response(**dict)` contract drift (GF65 + GF125)
- three-part async traps (`sync def` handler + `Depends(get_db)` + async engine)
- wrapped-HTTPException propagation (GF117 — inspect `.detail` before reraise)

```
Hit rate trailing indicator:
Wave 10: 80%  (rule-of-eight harvest)
Wave 11: 50%  (three-part async traps + schema drift)
Wave 12: 20%  (idiosyncratic ORM drift)
Wave 13: 50%  (infra/admin bias bounce-back)
Wave 14: 10%  (breadth sweep, GF125 stacked exception)
Wave 15:  0%  (frontend-traffic bias)
Wave 16:  0%  (low-traffic breadth bias)
```

## Next development phase (Session 153+)

Shift from "probe + fix" to **migration backlog + sync-service async port
backlog**:

1. **Schema drift migration backlog** (P1):
   - GF106 StudentReview — ~18 missing columns. **DONE** in Session 154 (drop+recreate).
   - GF113 COPPA — `coppa_parental_consents.child_id` VARCHAR vs Integer. 503 shim in place.
   - GF115 OSB — `osb_settings.id` UUID drift + missing `reduced_motion`/`no_animations`/`no_shadows`. **DONE** in Sessions 152+153.
   - Remaining: see `docs/audits/2026-04-12_orm-schema-drift-baseline.md` (HIGH=203, MEDIUM=455, LOW=206 from Session 155 audit).

2. **Sync service async port backlog** (P1, refactor-heavy):
   - GF112 DifficultyClassificationService (~700 sync lines) — port to async or carve out thin async wrapper. 503 shim in place.
   - GF117 core/api_key_manager — **DONE** in Session 153 (full async port).
   - GF151b DINA EM calibration pipeline — wire load/persist or delete endpoint. 503 shim in place.

3. **Optional continued Wave work** (P2, low ROI):
   - A Wave 17 sweep is permitted but expected to stay at ≤10% hit rate.
     Reserve for surfaces that explicitly land in production incident
     reports, not prophylactic coverage expansion.

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
- Append a row to the wave history table in `docs/audits/golden-flows-history.md`

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
- `.claude/rules/middleware.md` — HTTPException propagation from middleware
- `docs/audits/golden-flows-history.md` — Per-wave probe tables (Waves 1-16)

---

*Oluşturulma: 2026-04-10 Session 135. Sıkıştırma: 2026-05-14 Session 156 (Wave 1-16 detayları `docs/audits/golden-flows-history.md`'a taşındı).*
