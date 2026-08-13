"""dismantle_dual_table

Revision ID: aadc4eb93551
Revises: 040b91d243a0
Create Date: 2026-08-09 02:29:14.836895

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aadc4eb93551"
down_revision: Union[str, None] = "040b91d243a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Completely drop the dead questions table to fix the Dual Table trap
    op.execute("DROP TABLE IF EXISTS questions CASCADE")


def downgrade() -> None:
    # We do not fully recreate the dead table.
    pass
