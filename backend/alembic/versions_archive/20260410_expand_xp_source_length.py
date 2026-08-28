"""expand xp_transactions.source to VARCHAR(50)

Revision ID: xp_source_len_001
Revises: teacher_classroom_001
Create Date: 2026-04-10

GF2w fix — gamification points/award was returning 500 for any caller
passing a reason longer than 20 chars ("golden_flow_write_test" = 22).
Bumping to 50 gives API callers reasonable headroom without opening the
field up to unbounded input.
"""

import sqlalchemy as sa

from alembic import op

revision = "xp_source_len_001"
down_revision = "teacher_classroom_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "xp_transactions",
        "source",
        existing_type=sa.String(length=20),
        type_=sa.String(length=50),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "xp_transactions",
        "source",
        existing_type=sa.String(length=50),
        type_=sa.String(length=20),
        existing_nullable=False,
    )
