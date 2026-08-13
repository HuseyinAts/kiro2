"""split_god_table

Revision ID: 7f8ef189da5a
Revises: aadc4eb93551
Create Date: 2026-08-09 02:30:51.589744

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f8ef189da5a"
down_revision: Union[str, None] = "aadc4eb93551"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the massive question_bank table to force recreation of the 4 normalized tables
    # Since the DB is in testing/empty phase, we rely on SQLAlchemy Base.metadata.create_all
    # or a subsequent autogenerate to build the new normalized tables.
    op.execute("DROP TABLE IF EXISTS question_bank CASCADE")


def downgrade() -> None:
    pass
