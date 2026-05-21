"""S179 fix (EVIDENCE_BASED_DEEP_REVIEW Theme 1): hot-path missing indexes.

⚠️  DRY-RUN ONLY — NOT YET APPROVED FOR `alembic upgrade head`  ⚠️

This migration was drafted from an audit synthesis but has NOT been:
  - executed against any database (host kiro2 @ 5434 or container)
  - validated by EXPLAIN ANALYZE on the actual current planner stats
  - reviewed for index name collision with existing pg_indexes entries
  - tested for downgrade correctness on a populated table

Before running:
  1. `psql -p 5434 -d kiro2 -c "\\di question_bank*"` — confirm names don't collide.
  2. Run each `CREATE INDEX CONCURRENTLY` statement manually in a psql session
     (outside Alembic) on a staging copy, time it, and confirm planner picks it.
  3. Only then wire into the Alembic chain by replacing this docstring guard.

Operator confirmation required (Hüseyin) before promoting to live upgrade path.

Revision ID: s179_hot_path_idx_20260521
Revises: curator_audit_20260521
Create Date: 2026-05-21 19:00:00

The audit measured these queries:

| Endpoint               | Before  | After    | Speedup     | Source                  |
|------------------------|---------|----------|-------------|-------------------------|
| Curator queue F-Q1     | 1189ms  | 2.1ms    | 445x        | db_perf_hot_queries.md  |
| Admin content F-Q2     | 281ms   | 1.0ms    | 280x        | (same)                  |
| JSONB beta filter F-2  | 1534ms  | <50ms    | 30x (est.)  | db_perf_index_inventory |
| Quality status F-2     | 261ms   | <20ms    | 13x (est.)  | (same)                  |

All indexes use CONCURRENTLY to avoid ACCESS EXCLUSIVE lock on a 192K-row
table. CONCURRENTLY requires exiting Alembic's transaction (op.execute COMMIT)
then re-entering — pattern documented in db_perf_migration_drift.md:96-106.
"""

from __future__ import annotations

from alembic import op

revision = "s179_hot_path_idx_20260521"
down_revision = "curator_audit_20260521"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Exit Alembic's tx so CONCURRENTLY is allowed.
    op.execute("COMMIT")

    # F-Q1 / F-2: curator queue + quality status filter.
    # Single index covers both bronze_clean queue and auto_judged_high pool.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_status_active "
        "ON question_bank (quality_review_status) "
        "WHERE is_active = TRUE"
    )

    # F-Q2 / F-Q6: admin content list ordered by created_at.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_active_created "
        "ON question_bank (created_at DESC) "
        "WHERE is_active = TRUE"
    )

    # F-DB-2 / beta filter JSONB extract — 1.5s seq scan in audit.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_beta_filter_rule "
        "ON question_bank ((pipeline_metadata::jsonb -> 'beta_filter_v1' ->> 'rule')) "
        "WHERE is_active = TRUE"
    )

    # F-Q5: random question picker by (subject_area, exam_type) within Gold pool.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_quality_subject_exam "
        "ON question_bank (subject_area, exam_type) "
        "WHERE is_active = TRUE "
        "AND quality_review_status IN ('auto_judged_high', 'human_verified')"
    )

    # F-Q4 / DAG mastery: partial index on FK created_by for cascade delete safety.
    op.execute(
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_qbank_created_by "
        "ON question_bank (created_by) "
        "WHERE created_by IS NOT NULL"
    )

    # ANALYZE to refresh planner statistics so the new indexes are picked.
    op.execute("ANALYZE question_bank")

    # Re-enter Alembic's tx for the version_num write.
    op.execute("BEGIN")


def downgrade() -> None:
    op.execute("COMMIT")
    for name in (
        "idx_qbank_status_active",
        "idx_qbank_active_created",
        "idx_qbank_beta_filter_rule",
        "idx_qbank_quality_subject_exam",
        "idx_qbank_created_by",
    ):
        op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {name}")
    op.execute("BEGIN")
