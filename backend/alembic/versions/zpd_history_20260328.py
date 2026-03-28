"""Add zpd_history table

Revision ID: zpd_history_001
Revises: f822e22c28c6
Create Date: 2026-03-28

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "zpd_history_001"
down_revision: Union[str, None] = "f822e22c28c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "zpd_history",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column("topic_id", sa.String(), nullable=False),
        sa.Column("zone", sa.String(20), nullable=False),
        sa.Column("p_learn", sa.Float(), server_default="0.0"),
        sa.Column("theta", sa.Float(), server_default="0.0"),
        sa.Column("scaffold_level", sa.Integer(), server_default="0"),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zpd_history_student_id", "zpd_history", ["student_id"])
    op.create_index("ix_zpd_history_topic_id", "zpd_history", ["topic_id"])


def downgrade() -> None:
    op.drop_index("ix_zpd_history_topic_id", table_name="zpd_history")
    op.drop_index("ix_zpd_history_student_id", table_name="zpd_history")
    op.drop_table("zpd_history")
