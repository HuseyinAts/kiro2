"""add_cascade_deletes_to_foreign_keys

Revision ID: 4aec28c6c9e0
Revises: None
Create Date: 2025-10-04 02:13:40.762639
Note: Orphan branch - original parent db66ce0bd16f was removed
      CASCADE DELETE logic moved to 20260123_cascade_deletes.py

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "4aec28c6c9e0"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CASCADE DELETE logic moved to 20260123_cascade_deletes.py
    pass


def downgrade() -> None:
    pass
