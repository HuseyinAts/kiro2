# Session State — 2026-03-26 IRT/CAT Engine + Code Review Fixes

## Quick Resume
- **Branch:** master
- **Last commit:** 0b5f936 fix: 13 code review fixes — security, psychometrics, frontend
- **Previous commits this session:**
  - aa95a1e feat: IRT/CAT/FSRS/DAG/Placement engine + 202 tests
  - 980b9fe chore: cleanup — migrations, scripts, deprecated pages
  - b7a2fc7 fix: ruff lint cleanup — unused imports, type annotations, F841 vars
- **Push:** BASARILI (fbf2775..0b5f936, 4 commit)
- **Docker:** rebuild --no-cache OK, backend healthy, frontend 200
- **Production:** 77,336 questions
- **Tests:** 202 IRT/CAT/FSRS/DAG/Placement PASS, ruff 0, TSC 0

## Bu Session'da Yapilanlar

### 1. IRT/CAT/FSRS/DAG/Placement Engine (aa95a1e)
- **irt_engine.py**: 3PL model, Fisher info, EAP theta estimation
- **cat_session.py**: Redis-backed CAT, MFI question selection, warm-up phase
- **fsrs_engine.py**: FSRS v6 state machine, retrievability, urgency scoring
- **dag_engine.py**: Kahn topological sort, mastery prereq checks
- **placement_service.py**: Bisection + Bayesian estimation, school-type priors
- **yks_estimator.py**: theta-to-net, TYT/AYT scoring, OSYM formulas
- **irt_calibrator.py**: EM 3PL algorithm, CTT fallback, batch processing
- **202 tests**: test_cat, test_placement, test_estimator, test_dag, test_irt_calibration, test_fsrs

### 2. Code Review Fixes (0b5f936, 13 dosya)
- C1: hardcoded localhost → relative URL (2 hooks)
- C2: localStorage auth → httpOnly cookie (3 pages)
- C3: client-side is_correct removed → server-only answer check + is_active
- C4: CTT r_pbis always-1.0 bug → fixed constant proxy
- C5: ParentDashboard fetching own data instead of child's
- W1: auth added to DAG /topics endpoint
- W3: sys.path.insert hack → proper import (2 locations)
- W4: warm-up b_max floor at -0.5
- W5: datetime.utcnow() → datetime.now(UTC)
- W8: useEffect dependency arrays (PlacementWidget, CATWidget)
- W9: fetch r.ok checks
- W10: saveGoal error handling
- W11: MUI Button color 'default' → 'inherit'

## Dokunulan Dosyalar (toplam ~25 dosya)
- backend/app/api/placement.py, dag.py, calibration_api.py, cat.py
- backend/app/services/irt_engine.py, cat_session.py, fsrs_engine.py, dag_engine.py (NEW)
- backend/app/services/dag_service.py, placement_service.py, yks_estimator.py, irt_calibrator.py (NEW)
- backend/tests/test_cat.py, test_placement.py, test_estimator.py, test_dag.py, test_irt_calibration.py, test_fsrs.py (NEW)
- frontend/src/hooks/useCATSession.ts, usePlacementSession.ts
- frontend/src/components/CAT/QuestionCard.tsx, PlacementWidget.tsx, CATWidget.tsx
- frontend/src/pages/DailyPlanPage.tsx, LearningPathMapPage.tsx, ParentDashboardNew.tsx

## Bekleyen
1. W2: Admin role guard for calibration endpoint (no admin dependency exists yet)
2. Test coverage artirma (backend ~18% → hedef 80%)
3. MVP beta launch
4. Re-OCR recovery (+1,521-2,511 soru)
5. Docker frontend SW cache bump (stale 404 riski)
