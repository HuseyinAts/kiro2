"""Add curator audit columns to question_bank

Revision ID: curator_audit_20260521
Revises: sqf_unique_20260518
Create Date: 2026-05-21

Session 179 — Curator UI gap-closing migration.

Adds `reviewed_at TIMESTAMPTZ` column for Faz 3.6 audit trail and ensures the
three JSON metadata columns the Phase 5 metadata pipeline populates have
proper schema-level presence (`misconception_tags`, `solution_steps`,
`similar_question_ids`).

The three JSON columns already exist in production DB (audited via
information_schema 2026-05-21), but a defensive `add_column` with a guard is
used so this migration is idempotent on fresh environments.

`reviewed_at` is indexed (partial, where IS NOT NULL) for the
`avg_velocity_sec` stats query and the future curator dashboard time-range
filter.
"""

import sqlalchemy as sa

from alembic import op

revision = "curator_audit_20260521"
down_revision = "sqf_unique_20260518"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return bool(
        conn.execute(
            sa.text(
                """
                SELECT 1
                FROM information_schema.columns
                WHERE table_name = :table
                  AND column_name = :column
                """
            ),
            {"table": table, "column": column},
        ).first()
    )


def upgrade() -> None:
    conn = op.get_bind()

    # 1. reviewed_at — Faz 3.6 audit trail timestamp
    if not _has_column(conn, "question_bank", "reviewed_at"):
        op.add_column(
            "question_bank",
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        )

    # 2-4. Defensive JSON columns (already in prod, idempotent for fresh envs)
    if not _has_column(conn, "question_bank", "misconception_tags"):
        op.add_column(
            "question_bank",
            sa.Column("misconception_tags", sa.JSON(), nullable=True),
        )

    if not _has_column(conn, "question_bank", "solution_steps"):
        op.add_column(
            "question_bank",
            sa.Column("solution_steps", sa.JSON(), nullable=True),
        )

    if not _has_column(conn, "question_bank", "similar_question_ids"):
        op.add_column(
            "question_bank",
            sa.Column("similar_question_ids", sa.JSON(), nullable=True),
        )

    # 5. Index for reviewed_at — partial, only non-null rows.
    # Skip creation if index already exists (idempotent).
    existing_index = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND tablename = 'question_bank'
              AND indexname = 'idx_question_bank_reviewed_at'
            """
        )
    ).first()
    if not existing_index:
        op.create_index(
            "idx_question_bank_reviewed_at",
            "question_bank",
            ["reviewed_at"],
            postgresql_where=sa.text("reviewed_at IS NOT NULL"),
        )


def downgrade() -> None:
    # Drop index first
    op.execute("DROP INDEX IF EXISTS idx_question_bank_reviewed_at")
    # Then drop reviewed_at. Do NOT drop the JSON columns — they were
    # populated by Phase 5 metadata pipeline (DB-only addition) and are
    # owned by that pipeline, not this migration.
    with op.batch_alter_table("question_bank") as batch_op:
        batch_op.drop_column("reviewed_at")
