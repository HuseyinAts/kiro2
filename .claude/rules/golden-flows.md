# Golden Flow CI Gate

The 8 Golden Flows are the user-validated set of critical journeys the
platform MUST deliver. Unit tests can all pass while a real user cannot log
in, list topics, or start an exam — Golden Flows catch that class of failure
before merge.

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

**Write-path (Session 136 — 13 write tests across two waves):**

Wave 1 — planned probe-fix pairs (K1–K4):

| # | Flow | Surfaces | Status |
|---|------|----------|--------|
| GF1w | save-answer must update mastery (`response_count` / `algorithm`) | BKT/IRT/FSRS/ZPD fire-and-forget pipeline (`sinav.py:737-738`) | ✅ PASS |
| GF3w | save-answer rejects empty `question_id` | Payload validation boundary (`SaveAnswerRequest` `min_length=1`) | ✅ PASS (fix: Session 136) |
| GF4w.1 | register-wrong-answers accepts valid ID | FSRS write path (`learning_path_v2.py:2020`) | ✅ PASS |
| GF4w.2 | submit-review returns non-null `next_due` | FSRS grading pipeline (`learning_path_v2.py:1971`) | ⏭️ SKIP (no due cards) |
| GF6w | admin question create returns 200 success | Dual-trap: QuestionBankItem legacy kwargs + NOT NULL `primary_topic_id` (`soru_bankasi_service.py:183` + `admin.py` bypasses buggy `admin_servisi.soru_ekle` decorator) | ✅ PASS (fix: Session 136) |

Wave 2 — domain write-path probes (Option B, 8 new tests, discovered 5 additional half-working features):

| # | Flow | Surfaces | Status |
|---|------|----------|--------|
| GF1wB | auth refresh token actually persisted in DB | `auth.py:329` fire-and-forget refresh token persist | ⏭️ SKIP (state-dependent) |
| GF2w | gamification points award advances balance | Query-param vs JSON body contract drift, `points/award` 500 (`xp_transactions.source` VARCHAR(20) overflow) | ✅ PASS (fix: Session 136) |
| GF2wB | placement returns session + first question | CAT placement write path | ✅ PASS |
| GF3wA | chat session create returns 200 | `ai_chat_routes.py` wrong `get_db` (sync), `ai_chat.py` UUID-vs-VARCHAR + native enum collision with `live_sessions.sessionstatus` | ✅ PASS (fix: Session 136) |
| GF5w | teacher class create accepts canonical schema | TR field names (`sinif_adi`, `seviye`) vs English body — `path-naming.md` violation | ✅ PASS (fix: Session 136) |
| GF5wB | daily quest progress advances counter | Gamification write path | ✅ PASS |
| GF7wA | video-solutions list not 500 | `video_solution.py` used sync `get_db` for `AsyncSession` handlers → `MissingGreenlet` 500 | ✅ PASS (fix: Session 136) |
| GF8wA | kvkk consent list not 500 | `kvkk_consent_api.py` used sync `get_db` for `AsyncSession` handlers + `current_user.id` on Pydantic `TokenPayload` (should be `.sub`) | ✅ PASS (fix: Session 136) |

Wave 3 — feature-inventory sweep probes (Session 138, 10 new tests, discovered 2 additional half-working features):

Context: `docs/audits/2026-04-11_feature-inventory.md` flagged 510 write-path
endpoints without GF coverage. Top 10 were probed; 2 real bugs fell out.

| # | Flow | Surfaces | Status |
|---|------|----------|--------|
| GF10 | learning-path create-profile accepts canonical schema | Student profile write path (`learning_path_v2.py:190`) | ✅ PASS |
| GF11 | learning-path quiz submit not 500 | Quiz write path (`learning_path_v2.py`) | ✅ PASS |
| GF12 | FSRS review write not 500 | FSRS grading pipeline (`api/fsrs.py`) | ✅ PASS |
| GF13 | CAT session start not 500 | CAT placement write path (`api/cat.py`) | ✅ PASS |
| GF14 | auth change-password rejects wrong current | **HTTP 200 anti-pattern**: `auth.py:1156-1187` returned `{"success": false}` with HTTP 200 on all 4 error branches (user not found, wrong password, weak new password, generic exception). Broke `response.ok` in clients, hid regressions from monitoring. | ✅ PASS (fix: Session 138 — each branch now `raise HTTPException` with the correct 4xx/5xx) |
| GF15 | auth 2FA setup not 500 | TOTP secret generation write path | ✅ PASS |
| GF16 | kvkk consent give not 500 | **PG enum name + value mismatch**: ORM `SQLEnum(DataProcessingPurpose)` used SQLAlchemy default (type name `dataprocessingpurpose`, values = enum `.name` UPPERCASE), but live DB has `data_processing_purpose` with lowercase `.value` members. Query `$2::dataprocessingpurpose` crashed with `UndefinedObjectError`. Also affected 4 other KVKK enums (ConsentStatus, ExportRequestStatus, DeletionRequestStatus, audit purpose). | ✅ PASS (fix: Session 138 — `_pg_enum(py_enum, "snake_case_name")` helper binds Python enum to existing DB type with `values_callable=lambda m: [x.value for x in m]` + `create_type=False`) |
| GF17 | cozum-duellosu create not 500 | Duel write path (`cozum_duellosu_api.py`) | ✅ PASS |
| GF18 | daily-quests claim-bonus not 500 | Gamification daily bonus write path | ✅ PASS |
| GF19 | parent notifications create not 500 | Parent notification write path | ✅ PASS |

**Current distribution (Session 138):** 36 tests → **34 PASS, 0 FAIL, 2 SKIP**.

All new Wave 3 probes PASS after the 2 Session 138 fixes (GF14 HTTP 200
anti-pattern, GF16 PG enum binding). The 2 remaining SKIPs are unchanged and
state-dependent (GF1wB refresh-token persist has no deterministic probe;
GF4w.2 needs a due FSRS card which only exists after the 24h schedule window)
— acceptable skips, not regressions.

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
