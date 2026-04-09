"""Create dungeon_progress table

Revision ID: dungeon_progress_001
Revises: user_item_fsrs_001
Create Date: 2026-04-10
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "dungeon_progress_001"
down_revision: Union[str, None] = "user_item_fsrs_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dungeon_progress",
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("topic_id", sa.String(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("best_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "first_attempt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_attempt",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["topic_id"], ["topic_hierarchy.id"]),
        sa.PrimaryKeyConstraint("user_id", "topic_id"),
    )
    op.create_index("idx_dungeon_progress_user", "dungeon_progress", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_dungeon_progress_user", table_name="dungeon_progress")
    op.drop_table("dungeon_progress")
