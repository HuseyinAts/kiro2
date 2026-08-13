"""secure_plaintext_sessions

Revision ID: 040b91d243a0
Revises: level4_kc_taxonomy_20260808
Create Date: 2026-08-09 02:29:13.937678

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "040b91d243a0"
down_revision: Union[str, None] = "level4_kc_taxonomy_20260808"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename 'token' to 'hashed_token' to enforce hashing at application layer
    op.alter_column("sessions", "token", new_column_name="hashed_token")


def downgrade() -> None:
    op.alter_column("sessions", "hashed_token", new_column_name="token")
