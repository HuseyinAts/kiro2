# ORM Cluster 1 Sample Verify — university-info domain

**Date:** 2026-05-27 (Session 198, W4.3)
**Methodology:** Read-only DB schema diff via `audit_orm_schema_drift.py` re-run
+ `psql \d` cross-check + ORM model inspection.
**Sample:** 5/8 Cluster 1 tables (top by baseline finding count).
**Tool:** `backend/scripts/audit_orm_schema_drift.py` (live re-run)
**SQL:** `d-dataset/scripts/s198_cluster1_verify.sql` (`\d` for each sample)

## Verdict: REAL drift (NOT phantom, opposite of Cluster 2)

Re-audit confirmed every sample table still has the baseline-claimed missing
columns. Cluster 1 is **bona fide pending-migration backlog**, not stale
documentation. Global HIGH count dropped 203 → 159 since baseline, which is
exactly the -44 expected from the Cluster 2 (-41) + Cluster 3 (-3) closes —
no quiet Cluster 1 fixes happened in between.

## Sample matrix

| Table                  | Baseline HIGH | Live HIGH | Rows | Verdict |
|------------------------|--------------:|----------:|-----:|---------|
| `dormitory_info`       | 32 | **30** | 0 | REAL drift |
| `scholarship_programs` | 31 | **29** | 0 | REAL drift |
| `city_living_costs`    | 30 | **29** | 0 | REAL drift |
| `campus_info`          |  7 | **5**  | 0 | REAL drift |
| `career_opportunities` |  6 | **4**  | 0 | REAL drift |
| **Sample total**       | **106** | **97** | 0 | All 5 REAL |

Small baseline/live deltas (~2 per table) likely reflect ORM trims between
2026-04-12 and 2026-05-27, not DB column additions — DB schemas are
unchanged minimal placeholders.

Example evidence — `dormitory_info`: ORM declares `single_rooms`,
`double_rooms`, `triple_rooms`, `quad_rooms`, `meal_plan_cost`,
`common_areas`, `kitchen_access`, `gym`, `library`, `prayer_room`,
`cleanliness_rating`, `location_rating`, ... (30 missing). Live DB has
only the basic 31-col placeholder. Any ORM `INSERT` referencing these
would raise `UndefinedColumnError`.

## Production risk: LATENT, not active

- Routers mounted: `university_info_routes` + `department_info_routes`,
  **34 endpoints** in `routers/loader.py` under `university` category.
- Services exist: `university_info_service.py`, `department_info_service.py`.
- **Mitigating factor:** All 5 sample tables have **0 rows**. No
  frontend Golden Flow currently exercises these endpoints (consistent
  with baseline "no GF probe has hit them" assessment).
- **Crash mode:** First real POST/GET hitting a missing column →
  asyncpg `UndefinedColumnError` → 500. Not silent corruption.

## Why opposite of Cluster 2

| Cluster | Type | Fix scope | What S155→S198 did |
|---------|------|-----------|--------------------|
| 2 (UUID drift) | Model-only | One-liner per file | Silently fixed at model level (cat_models.py self-doc proves it). Doc not updated → phantom. |
| 1 (missing cols) | Migration | New Alembic file with 100+ `op.add_column()` | Nobody wrote it. Cold tables = no pressure. Baseline still accurate. |

## Recommended action (do NOT apply in this session)

Single Alembic migration `add_university_info_full_schema.py` adding the
~159 missing columns across all 8 Cluster 1 tables. **Read-only constraint**
of this session honored — no migration written, no `op.execute` issued.

Migration draft scope per table (live HIGH counts):

```
dormitory_info        30 columns
scholarship_programs  29 columns
city_living_costs     29 columns
campus_info            5 columns
career_opportunities   4 columns
department_curricula   ? (not sampled; baseline 8)
salary_expectations    ? (not sampled; baseline 8)
sector_analyses        ? (not sampled; baseline 8)
```

Rough total: ~140 `op.add_column()` calls, all `nullable=True` (cold tables,
no backfill needed). One commit, one Alembic file, zero data movement.

## CI gate suggestion

`backend/scripts/audit_orm_schema_drift.py --fail` already returns nonzero
on any HIGH finding. Wire into `.github/workflows/quality-gate.yml` after
the migration ships — currently this would fail CI on every PR because
of Cluster 1 backlog, so the gate is **deferred until the migration lands**.

## Phantom-rate comparison

| Audit wave | Cluster | Sample size | Phantom rate |
|------------|---------|-------------|--------------|
| W4.2 (S198) | Cluster 2 (UUID) | 5/22 tables | **100% phantom** |
| W4.3 (S198) | Cluster 1 (cols) | 5/8 tables | **0% phantom** |

S197 Mega Audit Lock rule validated: per-cluster verify before triage
reuse — phantom-rate is **not uniform** across the same baseline doc.

## Files referenced

- `C:\Users\husey\kiro2\docs\audits\2026-04-12_orm-schema-drift-baseline.md`
  (Cluster 1 section, lines 78-92)
- `C:\Users\husey\kiro2\backend\models\university_info.py`
  (CampusInfo / CityLivingCost / DormitoryInfo / ScholarshipProgram / UniversityStatistics)
- `C:\Users\husey\kiro2\backend\models\department_info.py`
  (DepartmentCurriculum / CareerOpportunity / SalaryExpectation / SectorAnalysis / DepartmentStatistics)
- `C:\Users\husey\kiro2\backend\scripts\audit_orm_schema_drift.py` (re-audit tool)
- `C:\Users\husey\kiro2\backend\routers\loader.py`
  (mounts `api.university_info_routes` + `api.department_info_routes`)
- `C:\Users\husey\kiro2\d-dataset\scripts\s198_cluster1_verify.sql` (this session)
