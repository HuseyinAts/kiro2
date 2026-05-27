# ORM Schema Drift Baseline — Session 155

**Date:** 2026-04-12
**Tool:** `backend/scripts/audit_orm_schema_drift.py`
**Database:** kiro2 (port 5434, 235 live tables)
**ORM tables loaded:** 222 (0 not in live DB)

## Summary

| Severity | Count | Pattern |
|----------|------:|---------|
| HIGH     | 203   | Production-blocking ORM/DB type mismatches |
| MEDIUM   | 455   | Family-compatible drift (mostly nullability + tz) |
| LOW      | 206   | DB has columns ORM doesn't declare |

## Validation: Sessions 149/153/154 fixes are CLEAN

The audit was first run as a correctness check against the eight tables that
hand fixes had landed in over the prior six sessions. All eight return zero
HIGH findings, confirming the script catches what it should:

| Table                       | Session | Bug                            | Audit |
|-----------------------------|---------|--------------------------------|-------|
| `osb_settings`              | 153 GF115 | inverse rule-of-seven (id)   | CLEAN |
| `student_reviews`           | 154 GF106 | drop+recreate, 14+ cols      | CLEAN |
| `review_ratings`            | 154 GF106 | drop+recreate                | CLEAN |
| `review_votes`              | 154 GF106 | drop+recreate, schema redo   | CLEAN |
| `review_reports`            | 154 GF106 | drop+recreate                | CLEAN |
| `review_statistics`         | 154 GF106 | drop+recreate                | CLEAN |
| `moderation_queue`          | 154 GF106 | drop+recreate, priority type | CLEAN |
| `coppa_parental_consents`   | 149 GF113 | child_id type mismatch (503 shim) | CLEAN |

## HIGH findings by pattern

| Pattern                       | Count |
|-------------------------------|------:|
| `orm-declares-missing-db-col` |  158 |
| `inverse-rule-of-seven`       |   41 |
| `int-vs-string`               |    4 |

## HIGH findings by table (top 30)

| Table                          | Count |
|--------------------------------|------:|
| `dormitory_info`               |    32 |
| `scholarship_programs`         |    31 |
| `city_living_costs`            |    30 |
| `osym_questions`               |    19 |
| `university_statistics`        |     9 |
| `department_curricula`         |     8 |
| `department_statistics`        |     8 |
| `salary_expectations`          |     8 |
| `sector_analyses`              |     8 |
| `campus_info`                  |     7 |
| `study_sessions`               |     7 |
| `career_opportunities`         |     6 |
| `kiro2_learning_events`        |     3 |
| `knowledge_points`             |     3 |
| `reasoning_steps`              |     3 |
| `university_programs`          |     3 |
| `kiro2_cat_sessions`           |     2 |
| `program_score_history`        |     2 |
| `sub_problems`                 |     2 |
| `user_badges`                  |     2 |
| `badges`                       |     1 |
| `departments`                  |     1 |
| `performance_history`          |     1 |
| `question_knowledge_mappings`  |     1 |
| `reasoning_cache`              |     1 |
| `reasoning_sessions`           |     1 |
| `student_knowledge_states`     |     1 |
| `topic_prerequisites`          |     1 |
| `universities`                 |     1 |
| `user_university_preferences`  |     1 |

## Triage clusters

### Cluster 1 — University-info backlog (~140 findings, 8 tables)

`dormitory_info`, `scholarship_programs`, `city_living_costs`, `campus_info`,
`career_opportunities`, `department_curricula`, `salary_expectations`,
`sector_analyses` all have huge `orm-declares-missing-db-col` lists. These
look like a feature batch where the ORM models were written and committed
but the alembic migration was never run (or was reverted). All 8 tables
share the same shape: the live tables are minimal placeholders with `id`
+ `name` + a couple of FKs, while the ORM declares the full feature schema
with 20-40 columns each.

**Recommended action:** generate a single Alembic migration that adds the
missing columns to all 8 tables. None of these are on the user-facing path
yet (no Golden Flow probe has hit them), so the order matters less than
the volume — one batch migration closes 140 of the 203 findings.

### ~~Cluster 2 — Inverse rule-of-seven (41 findings, ~22 tables)~~ ✅ FIXED 2026-05-27

> **STATUS: %100 PHANTOM — Cluster 2 closed.** W4.2 (Session 198) audit:
> baseline 41 finding → live re-audit **0 finding**. All 23 tables aligned
> (ORM=UUID, DB=uuid). Sample verify: `kiro2_learning_events` (254 row),
> `kiro2_cat_sessions` (8), `topic_prerequisites` (106), `reasoning_cache` (0),
> `universities` (0) — hepsi temiz.
>
> Evidence: `backend/models/cat_models.py:8-12` self-doc says "Session 155
> Cluster 2 fix... no migration needed". S155 baseline yazıldıktan sonra
> model-level fix uygulanmış ama bu doc güncellenmemiş — klasik phantom
> pattern (S197 Mega Audit Lock kuralı bu yüzden var).
>
> Detay rapor: `docs/audits/2026-05-27_orm_cluster2_sample5.md`

~~The pattern Session 153/154 ground out at the model level for 7 tables is
still live in 22 more, **including these production-critical tables with
real row counts**:~~

| Table                  | Rows | Status |
|------------------------|-----:|--------|
| `kiro2_learning_events`|  254 | ✅ aligned |
| `topic_prerequisites`  |  106 | ✅ aligned |
| `kiro2_cat_sessions`   |    8 | ✅ aligned |
| `osym_questions`       |    ? | ✅ aligned (re-audit clean) |

~~Whatever currently writes to them must be using either raw SQL or a
caller-side `str(uuid)` shim — anything that goes through the ORM as
declared will trip `DatatypeMismatchError` on the next INSERT.~~

~~**Recommended action:** convert each model's `id` (and FK) declarations
from `Column(String, default=lambda: str(uuid4()))` to
`Column(UUID(as_uuid=True), default=uuid4)`. Each fix is one-line, no
migration needed (the DB is already correct). Repeat the Session 154
recipe.~~

**Updated HIGH total: 203 → 159** (Cluster 2 -41 + Cluster 3 -3 = -44).
Cluster 1 (university-info, 158 finding) ve Cluster 3 kalan 1 (`osym_questions.bloom_level`)
hâlâ açık — bu mega audit'in tek aktif backlog'u.

### Cluster 3 — int-vs-string (4 findings, 2 tables)

`badges.id`, `user_badges.id`, `user_badges.badge_id` — ORM Integer, DB
varchar. The badges feature is half-wired (5 badges seeded, 0 user_badges).
Either the ORM should drop `Integer` for `String`, or the DB should be
migrated to integer. The user_badges table is empty, so either direction
works.

## Tool usage

```bash
# Report-only (default — exit 0)
python backend/scripts/audit_orm_schema_drift.py

# Limit to one table (debugging)
python backend/scripts/audit_orm_schema_drift.py --table osb_settings

# CI gate — exit 1 if any HIGH finding
python backend/scripts/audit_orm_schema_drift.py --fail

# Save JSON for trend tracking
python backend/scripts/audit_orm_schema_drift.py --json out.json

# Show MEDIUM/LOW too (default is HIGH only)
python backend/scripts/audit_orm_schema_drift.py --severity LOW
```

## Why this audit exists

Two recurring asyncpg crash classes had been hand-fixed across Sessions
142-154 (forward + inverse rule-of-seven, schema drift). Each was caught
by a Golden Flow probe (GF22 → GF115) that surfaced the bug days or weeks
after the offending commit landed. The audit script grounds the entire
class out by walking every ORM table on every CI run, so future drift is
caught at merge time instead of at probe time.

## Out of scope (intentional)

- ORM table not present in DB (different audit — pending migration tracker)
- DB table not in any ORM (legacy tables / not yet adopted)
- ARRAY element-type granularity
- Numeric precision/scale, varchar length
- DEFAULT value semantics (`gen_random_uuid()` vs Python `default=uuid4`)
- MEDIUM and LOW findings (455 + 206) — see JSON for the full list

## Next steps

The 203 HIGH findings become Session 156+ backlog. They split into the
three clusters above; cluster 2 (inverse-rule-of-seven, 41 findings on
production tables) is the highest-priority fix because it touches live
data. Cluster 1 (university-info, 140 findings) is the largest by volume
but on cold tables — one batch migration closes it.
