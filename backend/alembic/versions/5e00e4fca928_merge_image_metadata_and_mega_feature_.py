"""merge image_metadata and mega_feature heads

Revision ID: 5e00e4fca928
Revises: b3c4d5e6f7a8, mega_feature_001
Create Date: 2026-03-14 16:18:06.180064

"""
from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = '5e00e4fca928'
down_revision: Union[str, None] = ('b3c4d5e6f7a8', 'mega_feature_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
