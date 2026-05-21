# Algorithm Pipeline Integration — Deep Audit (2026-05-21)

**Scope:** BKT → IRT → FSRS → ZPD record_answer pipeline + DAG read-path
**Method:** Read-only static trace + cross-file integration analysis
**Effort:** ~75 minutes
**Files reviewed:**
- `backend/services/bkt_service.py` (474 lines, prod entry)
- `backend/services/fsrs_v6_service.py` (167 lines, prod)
- `backend/services/irt_service_3pl.py` (167 lines, prod)
- `backend/services/learning_event_service.py` (553 lines, quiz/exam/assessment dispatcher)
- `backend/api/sinav.py:619-784, 1045-1055` (exam answer path)
- `backend/api/learning_path_v2.py:1224-1465` (quiz submit path)
- `backend/api/placement_assessment_api.py:230-273` (assessment path)
- `backend/app/services/learning_path_orchestrator.py` (727 lines, read path)
- `backend/app/services/dag_service.py` (322 lines)
- `backend/app/services/dag_engine.py` (cycle detect + traversal)
- `backend/models/{gamification,fsrs_models,enums_db}.py`

---

## Pipeline Entry Points

| Caller | File:Line | Input shape | Path through pipeline |
|---|---|---|---|
| OSYM exam answer | `backend/api/sinav.py:753` | `(user, qid, selected_answer)` w/ real IRT params from question_bank | Direct `BKTService.record_answer(...)` per answer, then `db.commit()` |
| Quiz submit (learning path) | `backend/api/learning_path_v2.py:1374` | List of answers + `q_meta {topic_id, subject}` (no irt params) | `LearningEventService.on_quiz_completed` → loop `record_answer` per question |
| Placement assessment finish | `backend/api/placement_assessment_api.py:260` | `subjects: {subj_name: {theta, se}}` | `LearningEventService.on_assessment_completed` → only upserts StudentAbility + BKTState, **skips** record_answer entirely |
| Exam completion (post-exam summary) | `backend/api/sinav.py:1048` | aggregate counts only | `LearningEventService.on_exam_completed` → XP/streak only, **does not** call record_answer (assumes per-answer calls already happened during exam) |
| (None) | — | — | No quiz-answer-level fire-and-forget pipeline trigger from any other surface (Soru Meydanı, Çözüm Düellosu, daily learning path study block, review-queue submit) |

**Coverage gap:** Soru Meydanı (`backend/api/soru_meydani_*.py`) and any study-block question-answer surface do NOT route through `record_answer`. BKT/IRT/FSRS state only updates from OSYM exam (sinav.py) or quiz submit (learning_path_v2.py).

`backend/api/learning_path_v2.py:1975` `@router.post("/submit-review")` exists but does not call `record_answer`. Worth verifying separately.

---

## BKT → IRT Bridge

**Implementation:** `backend/services/bkt_service.py:282-292`

```python
# Branch A: With history (answered_questions non-empty)
if answered_questions and responses:
    theta_after, theta_se = IRTService3PL.eap_theta(answered_questions, responses)
# Branch B: No history — BKT-only bridge
else:
    clamped = max(0.05, min(0.95, new_p_L))
    raw_logit = math.log(clamped / (1.0 - clamped))
    theta_after = max(-4.0, min(4.0, raw_logit))
    theta_se = max(0.3, 1.0 - new_p_L)
```

**Formula:** `theta = ln(p_L / (1 - p_L))` (logit) — DM-05 changed from earlier linear `(p_L - 0.5) * 8.0`.

**Edge case handling:**
- p_L clamped to [0.05, 0.95] before logit → no div-by-zero
- raw_logit clamped to [-4.0, 4.0] → no infinite theta
- theta_se min 0.3 (post-clamp)

**Numerical correctness:** Logit at p=0.05 → -2.944; at p=0.95 → +2.944. Theta range is conservative compared to IRT [-4, 4] full range.

**P0 — Test/implementation drift (test currently broken or stale):**

`backend/tests/unit/test_bkt_record_answer_batch1b.py:343` asserts the OLD linear formula:

```python
expected_theta = (clamped - 0.5) * 8.0  # OLD linear, removed in DM-05
assert abs(result["theta_after"] - expected_theta) < 0.01
```

For any p_L outside ~[0.45, 0.55], `linear ≠ logit`. E.g. `p_L=0.1` → linear=-3.2, logit=-2.197. Diff > 1.0. Either this test is failing in CI (and ignored), or the test scenario keeps p_L pegged near 0.5 by coincidence, **or** test runs entirely in error-swallowed branch (line 293 `except Exception` covers ZeroDivision for p_L→0/1 only — not for an active assertion mismatch).

**Action:** Run test in isolation to confirm fail/pass status, then either update test or revert to linear.

---

## IRT → FSRS Bridge

**Implementation:** `backend/services/bkt_service.py:345-415` (FSRS section)

**Reality:** There is no IRT-derived parameter handoff into FSRS.

FSRS update uses only:
- `rating` (1-4, computed externally from correctness)
- previous FSRS state (stability, difficulty, due_date, reps) from `fsrs_cards` row

`theta_after` is computed but **never passed into FSRS**. FSRS difficulty (kart-level) is independent of IRT difficulty (item-level). This is by FSRS design — but the audit description's "IRT difficulty → FSRS interval seed" premise does not hold.

**Rating derivation:**
- `sinav.py:695`: `rating = request.rating or (3 if correct else 1)`
- `learning_event_service.py:63`: `rating=3 if qr["is_correct"] else 1`

Only **2 ratings used** in practice: 1 (Again, wrong) and 3 (Good, correct). Hard (2) and Easy (4) are never reached. This means FSRS difficulty parameter (which adjusts based on rating distribution) plateaus quickly.

**FSRSCard.subject_area writes:**

`bkt_service.py:382-386`:
```python
subject_area=_SUBJECT_AREA_MAP.get(subject_slug.lower(), subject_slug.lower())
if subject_slug else "matematik"
```

Resolves to a string in `SubjectArea` enum's `.value` set (lowercase: "matematik", "turkce", "sosyal", etc.). The Enum column `_missing_` handler (`enums_db.py:101-108`) casefolds for lookup, so write succeeds.

**P1 — No unique constraint on `(student_id, topic)` in `fsrs_cards`:** Concurrent requests for same student+topic could create duplicate rows. `bkt_service.py:354-359` SELECT picks one via `scalar_one_or_none()` — silently picks first / raises if multiple. Then UPDATE writes only one row → other becomes orphaned but still queried for FSRS due-count. Recommendation: add unique index `(student_id, topic)`.

---

## FSRS → ZPD Interaction

**There is none.** Pipeline is BKT → ZPD (parallel to IRT/FSRS):

`bkt_service.py:418`: `zpd_zone = ZPDManager.zone(new_p_L)` — uses BKT-derived `new_p_L` only, not FSRS interval or IRT theta.

Two-system divergence:
- **Write path (bkt_service):** ZPD zone from BKT `p_L` (lines 75-81): `<0.40 FRUSTRATION, <0.80 ZPD_ACTIVE, >=0.80 MASTERED`
- **Read path (orchestrator):** ZPD zone from IRT mastery_pct (lines 246-251): `<40 FRUSTRATION, <80 ZPD_ACTIVE, >=80 MASTERED`

`mastery_pct = normal_cdf(theta/SE) * 100` (orchestrator line 670-674). So read-path ZPD is a different number from write-path ZPD — they will disagree even if BKT and IRT were perfectly bridged, because BKT p_L is bounded to [0.001, 0.999] from logit clamping, while IRT mastery_pct uses CDF.

**P1 — Zone-string-format drift:** `bkt_service.py:426` writes `zone=zpd_zone.lower()` → values stored as `"mastered"`, `"zpd_active"`, `"frustration"`. But `gamification.py:324` comment for ZPDHistory.zone says `# frustration / zpd / mastery`. The schema-versus-code-versus-comment discrepancy:

| Source | Values used/expected |
|---|---|
| ZPDManager.zone (write) | MASTERED, ZPD_ACTIVE, FRUSTRATION (lowercased to store) |
| ZPDHistory.zone (model comment) | frustration / zpd / mastery |
| Orchestrator.zpd_zone (read field) | MASTERED, ZPD_ACTIVE, FRUSTRATION |

Anyone querying `ZPDHistory WHERE zone='zpd'` finds 0 rows. Anyone reading old comments expects `mastery` but stored value is `mastered`.

**P2 — ZPD bilge_mode boundary inconsistency:** scaffold_level / hints / bilge_mode / recommended_difficulty all use different thresholds, often without alignment to ZPD zone boundaries (0.40 / 0.80). Example: `p_L = 0.35` → zone=FRUSTRATION but bilge_mode=guiding (not scaffolding) and recommended_difficulty=orta. User in frustration is offered medium-difficulty problems — opposite of pedagogical intent.

---

## DAG Traversal

**Case convention:** `topic_hierarchy.subject_area` is UPPERCASE. Defensive `.upper()` exists at `dag_service.py:243` for `get_next_recommended_topic`. Orchestrator passes `YKS_SUBJECTS` UPPERCASE strings directly — consistent.

**Cycle detection:** `dag_engine.py:166-181` uses Kahn's algorithm. If topo length != node count → cycle detected → returns `False, [error_msg]`. `dag_service._load_from_db()` raises `RuntimeError` on cycle (line 141). Cache load path (`_deserialize_dag` line 312-314) logs warning but does NOT raise — **silent corrupted cache** can leak through if a cycle was committed before cache invalidation. P2.

**Mastery cutoff thresholds (dag_engine.py):**

Hard cutoff (HARD prereq): default `MASTERY_CUTOFF_HARD` (need to read constants). Soft cutoff for SOFT prereq. Per-prereq weighted by `strength` (line 241-247). Strength=1.0 default — if calibration goes wrong (strength=0.0) prereq is silently never blocking. No range validation on strength field.

**P1 — Inefficient `_collect_prerequisites`:** `dag_engine.py:325` `self._collect_prerequisites(pid, collected, visiting.copy())`. The `visiting.copy()` is per-recursive-call, O(V^2) memory worst case. For YKS curriculum (~140 topics, ~300 edges) this is tolerable, but conceptually wrong — cycle detection should use a single union path or color marks (WHITE/GRAY/BLACK). The current logic protects against cycles but at significant overhead.

---

## Real Student Session Trace

### Read path: GET /api/v1/learning-path/today

```
1. Endpoint → orchestrator.get_student_subject_statuses(user_id, "TYT")
2. _fetch_thetas_with_se(user_id):
     SELECT subject_id, theta, theta_se FROM student_abilities WHERE student_id = :uid
     → theta_map keyed by _REVERSE_SUBJECT_MAP value (UPPERCASE: "MATEMATIK", "TURKCE", ...)
3. _fetch_fsrs_due_counts(user_id):
     SELECT subject_area::text, COUNT(*) FROM fsrs_cards
       WHERE student_id = :uid AND due_date <= NOW() AND state NOT IN ('new')
     → fsrs_map keyed by enum.value (lowercase: "matematik", "turkce", ...)
4. dag_service.get_user_mastery(user_id) — Redis cache check + DB fallback
     Query: kiro2_cat_sessions (CAT-completed sessions)
5. For each subject in YKS_SUBJECTS["TYT"] (UPPERCASE):
     theta = theta_map.get(subject, 0.0)    # UPPERCASE → UPPERCASE: HIT
     fsrs_due = fsrs_map.get(subject, 0)    # UPPERCASE → lowercase keys: ALWAYS MISS, returns 0
     next_tid = dag.get_next_recommended_topic(user_id, subject)  # .upper() defensive
     check = dag.check_can_study_topic(user_id, next_tid)
```

### Write path: POST /api/v1/sinav/{session_id}/auto-save

```
1. save_answer(session_id, qid, selected) — exam_engine in-memory state
2. If selected_answer:
     async with get_db_session_context() as db:   # auto-commit on __aexit__
       SELECT correct_answer, primary_topic_id, subject_area, irt_a/b/c FROM question_bank
       Compute correct = (selected_answer.strip().upper() == correct_answer.strip().upper())
       rating = 3 if correct else 1
       # Build IRT history
       SELECT question_id, is_correct FROM student_answers WHERE session_id = :sid AND is_correct IS NOT NULL
       SELECT id, irt_a, irt_b, irt_c FROM question_bank WHERE id IN (prev_qids)
       Append current Q's IRT params + response to lists
       await BKTService.record_answer(...)
         → SELECT BKTState WHERE student_id, topic_id
         → BKTService.update(p_learn, correct, p_T, p_G, p_S) — pure calc
         → INSERT or UPDATE BKTState (no row lock!)
         → IRTService3PL.eap_theta(answered_questions, responses)  [Branch A]
         → INSERT or UPDATE student_abilities via on_conflict_do_update
         → SELECT FSRSCard WHERE student_id, topic
         → FSRSService.review_card(...) — pure calc with fsrs lib
         → INSERT or UPDATE fsrs_cards
         → INSERT ZPDHistory (always new row, never updated)
         → BlackboardService.publish_learning_event(...) — fire-and-forget (line 445)
       await db.commit()
     # → end of `async with get_db_session_context` triggers second commit
```

**DB queries per single auto-save (worst case):** 8 separate executes:
1. SELECT question_bank by qid (with irt fields)
2. SELECT student_answers by session_id
3. SELECT question_bank IN(prev_qids)
4. SELECT BKTState
5. INSERT/UPDATE BKTState
6. INSERT...ON CONFLICT student_abilities
7. SELECT FSRSCard
8. INSERT/UPDATE FSRSCard
9. INSERT ZPDHistory

Plus 1 Blackboard pub. So 9 DB round-trips per auto-save. Auto-save fires on EVERY answer click — for a 40-question exam, that's 360 queries.

---

## Error Propagation Matrix

| Stage fail | Effect on subsequent | Source |
|---|---|---|
| BKT read fails | Falls back to `p_learn=0.10` (cold-start default), BKT update still computes, write attempted | `bkt_service.py:224-230` |
| BKT write fails | `errors["bkt"]` set, p_learn used in IRT/ZPD computation still | `bkt_service.py:265-270` |
| IRT EAP throws | `theta_after=0.0, theta_se=1.0` (initial defaults) | `bkt_service.py:293-296` |
| IRT logit-bridge throws | Same defaults — but logit only throws if clamped<=0 (impossible after `max(0.05,...)`) | safe |
| student_abilities upsert fails | Theta written nowhere, but p_L still went to BKTState | `bkt_service.py:339-343` |
| FSRS read fails | `prev_stability=None, prev_difficulty=None` → first_review path, but UPDATE branch never reached → no FSRS persistence | `bkt_service.py:407-415` |
| FSRS lib fails | Same → no persistence | same |
| ZPD persist fails | Returned ZPD zone still computed, just no history row | `bkt_service.py:432-439` |
| Blackboard publish fails | Logged at DEBUG, totally silent (line 457) | `bkt_service.py:456-457` |

**Pattern:** Each stage swallows its own exception, sets `errors[stage]`, returns to caller. **No early-exit when an earlier stage failed.** This is intentional but means the returned `errors` dict can have BOTH `bkt: error` AND `irt: error` with results computed from default fallbacks — caller must inspect `errors` to know if values are real.

**P2 — `errors["irt"]` overwriting:** Lines 294-296 and 340-343 both set `errors["irt"]`. Line 341 has a guard `if errors["irt"] is None` to not overwrite first error. But `_ALGO_ERRORS["irt"]` counter increments twice for a single logical failure. Minor metric pollution.

---

## Performance Findings

**Queries per submit:** 9 DB round-trips (counted above). No prepared statement reuse. No batch.

**Lock acquisition order:** None. All updates are last-writer-wins because:
- `select(BKTState)` has no `with_for_update`
- `select(FSRSCard)` has no `with_for_update`
- `INSERT...ON CONFLICT DO UPDATE` for `student_abilities` is atomic at row level but NOT atomic with the BKTState UPDATE that preceded it

**Transaction boundaries:** Single implicit transaction across the entire `record_answer`. Caller commits. `get_db_session_context` (`core/database.py:249-258`) auto-commits on exit. Result: **double commit in sinav.py** (explicit `db.commit()` at line 763, implicit auto-commit on `async with` exit). Harmless but smelly.

**P1 — No row-level lock on hot path:** Two concurrent quiz submits for the same `(student, topic)` will:
1. Both SELECT BKTState → same p_learn
2. Both compute new_p_L from stale p_learn
3. Both UPDATE → last writer wins, first BKT update lost
4. ZPDHistory rows BOTH inserted → audit log inconsistent with state
5. student_abilities ON CONFLICT picks one theta to keep → other lost

**Mitigation options:** `SELECT FOR UPDATE` on BKTState read; or version-stamped optimistic lock; or move to single SQL UPSERT with computed expression.

---

## ZPD Accuracy Risk

`ZPDManager.zone(p_L)`:
- `>= 0.80` MASTERED
- `>= 0.40` ZPD_ACTIVE
- else FRUSTRATION

Compared to BKT default p_L0=0.10 (initial), **brand new students are always FRUSTRATION** until p_L crosses 0.40. With p_T=0.10 (stem) and 5 correct in a row from prior=0.10:

Single update with correct=True, p_T=0.10, p_G=0.20, p_S=0.10:
```
denom = 0.10 * 0.90 + 0.90 * 0.20 = 0.27
posterior = 0.10 * 0.90 / 0.27 = 0.333
new_p_L = 0.333 + 0.667 * 0.10 = 0.40 (just barely ZPD_ACTIVE)
```

So a new student needs exactly 1 correct to leave FRUSTRATION (in theory). But because `prior=0.10` (DM-09 says "p_L0 not p_T" — line 232) and update returns `0.40 + transit`, the actual landing is `>= 0.40` → ZPD_ACTIVE. The FRUSTRATION zone is effectively "never seen correct". Reasonable.

**P2 — Mastery threshold (0.80) is the same as the BKT clamp upper bound (0.999) minus transit-adjustment.** With p_T=0.10 (stem subjects), once posterior >= 0.778, new_p_L = 0.778 + 0.222*0.10 = 0.800 — landing exactly on MASTERY. This means **the mastery transition is effectively a one-shot from p_L ~ 0.78**. There's no gradual mastery in BKT formula, just a sharp threshold.

---

## Cold Start

| Resource | Initial state | Source |
|---|---|---|
| BKTState row | not created until first answer | `bkt_service.py:245-258` |
| p_learn (in-memory if no row) | 0.10 | `bkt_service.py:233` |
| StudentAbility (per subject_id) | `theta=0.0, theta_se=1.0` (default) | initial computed by `update_theta` calls |
| FSRSCard | not created until first answer | `bkt_service.py:377-396` |
| FSRSCard.subject_area | from `_SUBJECT_AREA_MAP` mapping or fallback "matematik" | line 382-386 |
| First scaffold | `scaffold_level(0.10)` = `5 * (0.80-0.10)/0.40 = 8.75 → min(5,8) = 5` (MAX scaffold) | by formula |

**Placement assessment path** (placement_assessment_api.py:260):
- Calls `on_assessment_completed` which writes StudentAbility (real theta/se from CAT)
- AND BKTState seeded by `p_learn = (theta + 3) / 6` (lines 224 of learning_event_service.py)
  - theta=0 → p_learn=0.50 (ZPD_ACTIVE)
  - theta=-3 → p_learn=0.05
  - theta=+3 → p_learn=0.95
  - This formula is **subject-level seeding** but BKTState is **topic-level** — `topic_id=subj_name.lower()` (line 229). So `topic_id="matematik"` (a subject name, not a topic UUID). When a later quiz answers a real topic UUID like `"a3f...uuid"`, BKT lookup finds nothing, defaults to p_learn=0.10. **Placement BKT data is never read.**

**P1 — Placement → BKT seed pathway is broken.** Placement writes `BKTState(topic_id=subj_name.lower())` (e.g. "matematik" string), but `record_answer` queries `BKTState WHERE topic_id = primary_topic_id` (a UUID). The seed never gets used.

---

## Hot Path: get_user_mastery

`dag_service.py:147-202`

**Implementation:**
1. Redis cache key `mastery:{user_id}`, TTL=300s
2. If cached: deserialize JSON, return
3. Else SQL:
```sql
SELECT DISTINCT ON (q.primary_topic_id)
    q.primary_topic_id AS topic_id, cs.theta_final, cs.se_final
FROM kiro2_cat_sessions cs
JOIN question_bank q ON q.subject_area = cs.subject_id
WHERE cs.user_id = :uid AND cs.state = 'completed' AND q.primary_topic_id IS NOT NULL
  AND q.is_active = TRUE
ORDER BY q.primary_topic_id, cs.completed_at DESC
```
4. Compute `compute_mastery_from_theta(theta, se)` per topic
5. Cache to Redis

**P0 — SQL design flaw:**

`JOIN question_bank q ON q.subject_area = cs.subject_id` — `kiro2_cat_sessions.subject_id` is the **CAT subject** (likely string like "MATEMATIK"). `question_bank.subject_area` is UPPERCASE string. Join condition pairs every CAT session with EVERY question matching that subject. For matematik with 30K+ active questions, this generates a 30K-row intermediate before `DISTINCT ON (primary_topic_id)` collapses. There are likely ~140 distinct topics, so 99.5% of intermediate rows discarded.

Cost: O(CAT_sessions × questions_in_subject) → for 100 sessions × 30K questions = 3M rows scanned per uncached call. With 300s TTL, on cold cache this dominates.

**P1 — Per-topic mastery has weak data source:** Mastery is derived from `cs.theta_final` (CAT session-final theta), assigned to every primary_topic_id from question_bank matching that subject. So if a student takes one matematik CAT session, all ~30 matematik topics get the SAME theta-derived mastery. No actual per-topic resolution. Topic-level DAG check_mastery then collapses to subject-level check.

**P1 — Cache key includes only user_id, not subject_id:** Cached mastery is global per user. If a user studies matematik, then turkce, the cache may still be matematik-only until 300s expiry.

---

## Integration Test Coverage

```bash
grep -rn "test_.*record_answer\|test_.*bkt_irt_fsrs" backend/tests/
```

Hit files:
- `tests/unit/test_bkt_record_answer_batch1b.py` — 6 happy-path tests (per-stage)
- `tests/unit/test_bkt_record_answer_batch1b_errors.py` — error-swallow tests
- `tests/unit/test_fsrs_card_persistence.py` — FSRS write block tests
- `tests/unit/test_learning_event_service.py` — mocked BKT calls

**Coverage gaps:**

1. **No end-to-end test** that calls `record_answer` 10 times in sequence and verifies BKT state convergence + FSRS interval scheduling + ZPDHistory progression.
2. **No concurrency test** for two `record_answer` calls on same (student, topic).
3. **No placement → quiz seed continuity test**: assessment writes seed → quiz answer should read seed, not default 0.10.
4. **No DAG read-path test** with FSRS due-count case-mismatch (`fsrs_map` lowercase vs `theta_map` UPPERCASE).
5. **No test for stale `q_meta` IRT params** producing degenerate EAP (all default 1.0/0.0/0.2) when quiz path doesn't fetch real IRT.
6. **No test on `irt_method=="bridge"` formula** — the existing test asserts the OLD linear formula (likely failing or skipped — see P0 above).

---

## Findings

### P0 — Block immediately

**P0-1. Test/implementation drift in BKT→IRT bridge formula.**
- File: `backend/tests/unit/test_bkt_record_answer_batch1b.py:343`
- Test asserts `expected_theta = (clamped - 0.5) * 8.0` (linear).
- Implementation (`bkt_service.py:288`) uses `log(clamped/(1-clamped))` (logit) since DM-05.
- Either the test is failing silently in CI or coverage is not hitting that line. Verify and reconcile.

**P0-2. Placement assessment seeds BKTState with subject_name as topic_id, never read by quiz path.**
- File: `backend/services/learning_event_service.py:229` writes `topic_id=subj_name.lower()` ("matematik", "fizik", etc.).
- File: `backend/services/bkt_service.py:218-221` reads `WHERE topic_id == topic_id` where caller passes `primary_topic_id` (UUID).
- Effect: Placement → BKT seed is dead data. New users always start with p_learn=0.10.
- Fix: Either remove BKTState seeding from placement, OR populate BKTState for each topic_id under the assessed subject, OR change `record_answer` lookup to also try subject-name fallback.

**P0-3. `dag_service.get_user_mastery` SQL fan-out.**
- File: `backend/app/services/dag_service.py:167-180`.
- JOIN question_bank on subject_area creates O(sessions × subject_questions) intermediate.
- For active subjects ~30K questions, single user query scans millions of rows per cold cache miss.
- Fix: Source theta from `student_abilities` table directly (already populated by `record_answer`), apply per-topic via mastery model lookup, or denormalize topic_mastery to a per-topic table.

**P0-4. Quiz path sends stub IRT params to EAP, degenerating theta estimation.**
- File: `backend/api/learning_path_v2.py:1271-1274, 1297-1300` — `q_meta` only contains `topic_id` and `subject`, no `irt_a/b/c`.
- File: `backend/services/learning_event_service.py:50-53` — `meta.get("irt_a", 1.0)` always returns 1.0 default.
- Effect: EAP estimation runs with identical item parameters → posterior collapses to a function of count(correct) - count(wrong), not weighted by item discriminability.
- Compare: `sinav.py:717-735` correctly fetches real IRT params for exam path.
- Fix: Update `q_meta` construction in `learning_path_v2.py` quiz submit handler to include `irt_a`, `irt_b`, `irt_c` from question_bank.

### P1 — Fix before next release

**P1-1. `_fetch_fsrs_due_counts` case-convention bug.**
- File: `backend/app/services/learning_path_orchestrator.py:567-588` returns lowercase keys ("matematik").
- File: same file:188 `fsrs_due = fsrs_map.get(subject, 0)` where subject is UPPERCASE from `YKS_SUBJECTS`.
- Effect: `fsrs_due_count` always 0 in subject status response → no FSRS-due review blocks ever scheduled in daily plan.
- Fix: Either normalize key (`subject.lower()` in get) or return UPPERCASE keys to match.

**P1-2. Subject collapse in `record_answer`'s `_SUBJECT_AREA_MAP`.**
- File: `backend/services/bkt_service.py:46-53, 317-318`.
- Slug `"tarih"` → `_SUBJECT_AREA_MAP` → `"sosyal"` → `_SUBJECT_ID_MAP["sosyal"]` = 12.
- Same for `cografya`, `felsefe`, `din` → all collapse to subject_id=12.
- `edebiyat` → 6 (overlaps turkce). `geometri` → 1 (overlaps matematik).
- Effect: per-subject IRT theta tracking is destroyed for sosyal-area and tied subjects. Placement writes subject_id=7-11 directly; quiz writes overwrite with subject_id=12.
- Fix: Decide: enrich SubjectArea enum, or stop collapsing in `_SUBJECT_AREA_MAP` (keep tarih/cografya/etc separate when writing StudentAbility).

**P1-3. Read-path / write-path ZPD zone string mismatch.**
- File: `bkt_service.py:426` writes lowercased "mastered", "zpd_active", "frustration".
- File: `models/gamification.py:324` comment expects "frustration / zpd / mastery".
- File: `learning_path_orchestrator.py:247-251` reads/returns "MASTERED", "ZPD_ACTIVE", "FRUSTRATION" (UPPERCASE).
- Effect: ZPDHistory queries with old-style zone strings return empty. UI receives different case than DB stores.
- Fix: pick one canonical, update model field type to enum, drop the manual `.lower()`.

**P1-4. No row-level lock on BKTState / FSRSCard updates.**
- File: `bkt_service.py:218, 354` SELECT without `with_for_update`.
- Effect: concurrent submits on same (student, topic) race → lost updates.
- Fix: `SELECT ... FOR UPDATE` on BKTState read, or migrate to single UPSERT with computed expression.

**P1-5. No unique constraint on `fsrs_cards (student_id, topic)`.**
- File: `models/fsrs_models.py:34-43` — only indices, no unique.
- Effect: duplicates possible under concurrency; `scalar_one_or_none()` raises if duplicates exist post-race.
- Fix: Add `UniqueConstraint("student_id", "topic", name="uq_fsrs_student_topic")`.

**P1-6. Inefficient `_collect_prerequisites` DFS (visiting.copy()).**
- File: `dag_engine.py:325`.
- Effect: O(V^2) memory in pathological cases.
- Fix: Use single `visiting` set with proper backtracking (add on enter, remove on exit).

### P2 — Track for cleanup

**P2-1. ZPDManager threshold misalignment** (scaffold/bilge_mode/recommended_difficulty don't agree with zone boundaries 0.40/0.80).

**P2-2. `_ALGO_ERRORS["irt"]` increments twice for a single IRT logical failure** (`bkt_service.py:294, 340`).

**P2-3. Dead code: `algorithms/turkish_optimized_fsrs.py` (680 lines) and `services/irt_service.py` (771 lines, 4PL) are imported only by tests and a `_deprecated/` service. Production uses `fsrs_v6_service.py` and `irt_service_3pl.py`.**

**P2-4. Cached DAG cycle warning is silent.**
- File: `dag_service.py:312-314` — `_deserialize_dag` logs warning on cycle but doesn't invalidate cache.
- Effect: corrupted cache persists.

**P2-5. Mastery cache key in `dag_service.get_user_mastery` is per-user only, not per-subject.**

**P2-6. Quiz path `q_meta` doesn't carry `irt_a/b/c`** — covered in P0-4 but a sister concern: same gap exists for `bloom_level`, `difficulty_level` if the pipeline ever wants to weight by item difficulty.

**P2-7. Double commit on `sinav.py:763` + `get_db_session_context` auto-commit** — harmless but should be one or the other.

**P2-8. Two-parallel implementations of IRT** (`IRTService3PL` vs `IRTService` 4PL) — production uses 3PL, the 4PL+morfoloji is research-grade and only imported as `IRTMorfolojiService`.

---

## Suggested next steps (out of scope of this audit)

1. Write an end-to-end integration test: seed user via placement (theta=+1.0 matematik), submit a matematik quiz with 5 questions, assert BKTState exists for each topic_id, assert StudentAbility theta moved toward +1.0, assert FSRSCard rows exist with due_date in future.
2. Add a concurrency stress test: spawn 10 coroutines each calling `record_answer(student=X, topic=Y)` — verify final p_learn matches single-threaded equivalent.
3. Migrate `bkt_service.record_answer` BKTState section to use `INSERT ... ON CONFLICT DO UPDATE` with computed expression to eliminate the read-modify-write race entirely.
4. Run the failing/stale `test_record_answer_without_answered_questions_uses_bridge` in CI to confirm pass/fail status.

---

*Audit complete — 2026-05-21. Read-only static trace. All findings have file:line refs above; no code was modified.*
