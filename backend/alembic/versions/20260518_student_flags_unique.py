"""Add UNIQUE constraint to student_question_flags

Revision ID: sqf_unique_20260518
Revises: student_flags_20260517
Create Date: 2026-05-18

S1.1 fix — Same (user_id, question_id, flag_type) combo should be rejected.
Existing duplicates are deduplicated (earliest created_at kept). UNIQUE index
is partial (WHERE resolved_at IS NULL) so admin-resolved flags don't block
re-flagging of the same question.
"""

import sqlalchemy as sa

from alembic import op

revision = "sqf_unique_20260518"
down_revision = "student_flags_20260517"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Deduplicate: keep earliest created_at per (user_id, question_id, flag_type)
    op.execute(
        """
        DELETE FROM student_question_flags
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY user_id, question_id, flag_type
                           ORDER BY created_at ASC, id ASC
                       ) AS rn
                FROM student_question_flags
            ) ranked
            WHERE rn > 1
        )
        """
    )

    # 2. Partial UNIQUE — only unresolved flags. Admin-resolved flags
    # (resolved_at IS NOT NULL) don't block users from re-flagging if the
    # underlying problem recurs.
    op.create_index(
        "uq_student_flags_user_question_type",
        "student_question_flags",
        ["user_id", "question_id", "flag_type"],
        unique=True,
        postgresql_where=sa.text("resolved_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_student_flags_user_question_type",
        table_name="student_question_flags",
    )
