"""phase2_indexes

Revision ID: 3dfb6239addd
Revises: c555a10f4b93
Create Date: 2026-06-18 03:27:48.436869

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3dfb6239addd"
down_revision: Union[str, None] = "c555a10f4b93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_user_email_phase2", "users", ["email"], unique=False, if_not_exists=True
    )
    op.create_index(
        "idx_user_username_phase2",
        "users",
        ["username"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("idx_user_email_phase2", table_name="users", if_exists=True)
    op.drop_index("idx_user_username_phase2", table_name="users", if_exists=True)
