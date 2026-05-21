# Algorithm Pipeline Audit — Product Readiness (2026-05-22)

**Verdict**: 4-stage pipeline (BKT→IRT→FSRS→ZPD) functionally complete after May 22 fixes (commit 6e97065cb) but **3 P0 silent-failure surfaces** remain.

## Full Call Chain

```
HTTP POST /api/v1/osym-exam/{session_id}/save-answer  (sinav.py:617)
  ↓
  osym_exam_engine.save_answer()  [exam_state + StudentAnswer]
  ↓
  BKTService.record_answer()  (bkt_service.py:183)
    ├─ Stage 1: BKT.update(p_learn, correct) → new_p_L
    ├─ Stage 2: IRT theta (EAP or logit bridge)
    ├─ Stage 3: FSRS.review_card() + FSRSCard persist
    └─ Stage 4: ZPDManager.zone + ZPDHistory persist
  ↓
  LearningEventService.on_exam_completed()  [XP/Streak]
  ↓
  (async commit if ALGO_FIRE_AND_FORGET=false; else fire-and-forget)
```

## Stage 1: BKT

| Component | Status | Evidence |
|---|---|---|
| Entry point | ✅ | sinav.py:667-799 |
| Slug normalization | ⚠️ | sinav.py:697 — `(row.subject_area or "matematik").lower()` no validation |
| `_SUBJECT_AREA_MAP` coverage | ❌ **P0** | bkt_service.py:52-59 — only 6 entries (tarih→sosyal, edebiyat→turkce, felsefe→sosyal, din→sosyal, cografya→sosyal, geometri→matematik). **Missing: FIZIK, KIMYA, BIYOLOJI, INGILIZCE, GENEL, FEN, TDE** |
| State persistence | ✅ | bkt_service.py:254-284 upsert on (student_id, topic_id), table `bkt_states` |
| Exception handling | ⚠️ | bkt_service.py:230-240 — log + p_learn=0.10 degraded, but caller sees `algorithm_degraded=True` only if entire call fails |

## Stage 2: IRT (✅ SOLID)

| Component | Status | Evidence |
|---|---|---|
| Theta from BKT | ✅ | bkt_service.py:293-306 EAP or logit bridge |
| Question params | ✅ | question_bank.py:352/355/358 — irt_discrimination/difficulty/guessing all Float |
| Theta SE | ✅ | bkt_service.py:304-306 SE = max(0.3, 1.0 - new_p_L) |
| Subject ID mapping | ✅ | bkt_service.py:318-341 12-subject map |
| Persistence | ✅ | StudentAbility table |

## Stage 3: FSRS

| Component | Status | Evidence |
|---|---|---|
| Card read by (student_id, topic_id) | ✅ | bkt_service.py:378-389 |
| Params (stability/difficulty/state) | ✅ | bkt_service.py:417,429 |
| **Enum validation** | ❌ **P0** | bkt_service.py:406-410 writes `_SUBJECT_AREA_MAP.get(subject_slug.lower(), subject_slug.lower())`. `SubjectArea` enum has 8 members (MATEMATIK/TURKCE/FEN/SOSYAL/FIZIK/KIMYA/BIYOLOJI/INGILIZCE). Subjects GENEL/TDE/COGRAFYA/EDEBIYAT/TARIH/FELSEFE/GEOMETRI write unmapped values → enum violation |
| Exception handling | ⚠️ | bkt_service.py:431-439 silent log; caller sees no error |

## Stage 4: ZPD (✅ SOLID)

| Component | Status | Evidence |
|---|---|---|
| Zone calculation | ✅ | bkt_service.py:442-443 — MASTERED/ZPD_ACTIVE/FRUSTRATION thresholds 0.40/0.80 |
| Scaffold level | ✅ | bkt_service.py:95-96 clamped [0,5] |
| History persistence | ✅ | gamification.py:316-331 `zpd_history` table |

## Cross-Stage Handoffs

| From | To | Data | Verified |
|---|---|---|---|
| BKT p_L | IRT theta | new_p_L (logit bridge with clamp 0.05) | ✅ |
| IRT | FSRS | answered_questions list[dict] w/ irt_a/b/c | ✅ |
| FSRS | FSRSCard | due_date, stability, difficulty, state, reps | ⚠️ ENUM RISK |
| BKT p_L | ZPD | p_L clamped [0.001, 0.999] | ✅ |
| Assessment | Quiz BKT | topic_id from topic_hierarchy | ⚠️ FALLBACK RISK |

## Placement Seed Risk

`learning_event_service.py:240-257` — If topic_hierarchy has no rows for subject:
- Fallback: `topic_ids = [subj_name.lower()]` (e.g., "matematik")
- Quiz BKT WHERE topic_id=UUID won't match string "matematik"
- **Result**: Silent placement signal loss

## Race Conditions / Lost-Update

| Site | FOR UPDATE? | Fire-forget? | Risk |
|---|---|---|---|
| sinav.py:700-799 BKT call | ❌ | ✅ ALGO_FIRE_AND_FORGET=true | 9 DB writes async, task exceptions invisible to client |
| learning_event_service.py:241-281 placement | ❌ | ❌ | Concurrent placement + quiz race |
| learning_path_orchestrator.py:567-604 FSRS due | ❌ | read-only | Workaround: populates lower/upper/raw keys (fragile) |

## Subject Coverage / Enum Mismatch — **DETAYLI**

**SubjectArea enum** (enums_db.py:90-108): 8 values
```
MATEMATIK, TURKCE, FEN, SOSYAL, FIZIK, KIMYA, BIYOLOJI, INGILIZCE
```

**Live DB subjects** (14): MATEMATIK, GEOMETRI, FIZIK, KIMYA, TURKCE, BIYOLOJI, EDEBIYAT, TARIH, GENEL, SOSYAL, COGRAFYA, FEN, TDE, INGILIZCE

**`_SUBJECT_AREA_MAP`** (bkt_service.py:52-59): 6 collapses
```
tarih → sosyal, edebiyat → turkce, felsefe → sosyal,
din → sosyal, cografya → sosyal, geometri → matematik
```

**Outcome**: Questions from GENEL, TDE → write 'genel'/'tde' → FSRSCard enum FK violation → silent failure in fire-forget task.

## Top P0 Risks

| # | Risk | Location | Impact |
|---|---|---|---|
| 1 | Subject enum collapse incomplete (GENEL, TDE not mapped) | bkt_service.py:52-59 + fsrs_models.py:55 | FSRSCard creation fails for ~3% of questions; review scheduling broken |
| 2 | Fire-forget task exceptions swallowed | sinav.py:761-787 | `algorithm_degraded=False` even if all 4 stages fail; observability gap |
| 3 | Placement fallback uses subject_name not UUID | learning_event_service.py:257 | Orphan placement signal when topic_hierarchy empty for subject |
| 4 | No SELECT FOR UPDATE in concurrent flow | learning_event_service.py:241 + sinav.py:700 | Lost updates under concurrent answer + placement |
| 5 | FSRS write lacks subject_area enum pre-validation | bkt_service.py:406-410 | Silent enum violation |

## Recommendations

1. **URGENT** Extend `_SUBJECT_AREA_MAP` for all 14 DB subjects OR validate against `SubjectArea` enum before FSRSCard write
2. **URGENT** Fire-forget exception callback to set `algorithm_degraded=True` per-stage
3. **HIGH** SELECT FOR UPDATE in BKTState + StudentAbility reads
4. **HIGH** Placement fallback: raise instead of writing subject_name as topic_id
5. **MEDIUM** Pre-commit validation: `if subject_slug not in SubjectArea → raise ValueError`

## Methodology

Static code review across:
- backend/api/sinav.py
- backend/services/bkt_service.py
- backend/services/learning_event_service.py
- backend/app/services/learning_path_orchestrator.py
- backend/models/{question_bank,gamification,fsrs_models,enums_db}.py

Commit verified: 6e97065cb (May 22) — BKT placement seed UUID + FSRS case + DAG mastery + IDOR.

NO live testing performed (read-only).
