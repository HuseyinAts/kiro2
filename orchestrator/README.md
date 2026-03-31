# Orchestrator v2.5.0

LangGraph-based orchestration layer for KIRO2. 24 core modules, 45 policies, 20 agents.

## Active (used in production flow)
- `core/graph.py` — LangGraph state machine
- `core/routing.py` — Request routing + policy dispatch
- `core/policy_engine.py` — 45 policy rules
- `core/state.py` — Shared state management
- `core/agents.py` — Agent definitions
- `core/calibration_pipeline.py` — IRT calibration orchestration
- `core/adaptive_recommender.py` — Learning path recommendations
- `algorithms.py` — Algorithm dispatch (BKT/IRT/FSRS/ZPD)

## Experimental (not yet wired to production)
Everything else in `core/` is experimental — built for future phases.
Do not delete (import chains may reference them), but do not optimize or test.

## Tests
```bash
cd orchestrator && pytest tests/ -v  # 71 tests
```
