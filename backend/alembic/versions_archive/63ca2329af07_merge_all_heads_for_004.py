"""merge_all_heads_for_004

Revision ID: 63ca2329af07
Revises: 004_adv_perf_idx, add_taxonomy_fields, b49a86e335e5
Create Date: 2026-02-07 15:37:26.479462

"""

from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "63ca2329af07"
down_revision: Union[str, None] = (
    "004_adv_perf_idx",
    "add_taxonomy_fields",
    "b49a86e335e5",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
