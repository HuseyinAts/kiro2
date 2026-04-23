"""Add CASCADE DELETE to missing foreign keys

Revision ID: 20260123_cascade
Revises: 20260118_quality_gates
Create Date: 2026-01-23

This migration adds CASCADE DELETE to foreign keys that were missing it,
ensuring referential integrity and preventing orphan records when parent
records are deleted.

Affected tables:
- manipulative_activities (user_id)
- manipulative_progress (user_id)
- notifications (user_id)
- point_transactions (user_id)
- student_goals (user_id)
- student_learning_profiles (student_id)
- user_achievements (user_id)
- user_badges (user_id)
- weekly_progress (user_id)

"""
from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260123_cascade"
down_revision: Union[str, None] = "20260118_quality_gates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Foreign keys to update with CASCADE DELETE
FK_UPDATES = [
    # (table_name, constraint_name, column_name, referenced_table, referenced_column)
    ("manipulative_activities", "manipulative_activities_user_id_fkey", "user_id", "users", "id"),
    ("manipulative_progress", "manipulative_progress_user_id_fkey", "user_id", "users", "id"),
    ("notifications", "notifications_user_id_fkey", "user_id", "users", "id"),
    ("point_transactions", "point_transactions_user_id_fkey", "user_id", "users", "id"),
    ("student_goals", "student_goals_user_id_fkey", "user_id", "users", "id"),
    ("student_learning_profiles", "student_learning_profiles_student_id_fkey", "student_id", "users", "id"),
    ("user_achievements", "user_achievements_user_id_fkey", "user_id", "users", "id"),
    ("user_badges", "user_badges_user_id_fkey", "user_id", "users", "id"),
    ("weekly_progress", "weekly_progress_user_id_fkey", "user_id", "users", "id"),
]


def upgrade() -> None:
    """Add CASCADE DELETE to foreign keys that were missing it."""
    for table_name, constraint_name, column_name, ref_table, ref_column in FK_UPDATES:
        # Drop existing foreign key constraint
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")

        # Recreate with CASCADE DELETE
        op.create_foreign_key(
            constraint_name,
            table_name,
            ref_table,
            [column_name],
            [ref_column],
            ondelete="CASCADE"
        )


def downgrade() -> None:
    """Remove CASCADE DELETE from foreign keys (restore original behavior)."""
    for table_name, constraint_name, column_name, ref_table, ref_column in FK_UPDATES:
        # Drop CASCADE foreign key
        op.drop_constraint(constraint_name, table_name, type_="foreignkey")

        # Recreate without CASCADE (original behavior)
        op.create_foreign_key(
            constraint_name,
            table_name,
            ref_table,
            [column_name],
            [ref_column]
        )
