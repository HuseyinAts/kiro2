"""merge_all_branches

Revision ID: 0df6ae499ee4
Revises: 002_performance_indexes, 20251117_044637, 20260102_fix_cols, 3ec73c2c6d97, kvkk_compliance_001
Create Date: 2026-01-13 08:13:03.258230

"""
from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = '0df6ae499ee4'
down_revision: Union[str, None] = ('002_performance_indexes', '20251117_044637', '20260102_fix_cols', '3ec73c2c6d97', 'kvkk_compliance_001')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
