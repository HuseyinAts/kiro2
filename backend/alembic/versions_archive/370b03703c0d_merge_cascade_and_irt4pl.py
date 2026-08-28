"""merge_cascade_and_irt4pl

Revision ID: 370b03703c0d
Revises: 20260123_cascade, 20260126_irt_4pl
Create Date: 2026-01-27 19:32:06.572237

"""

from collections.abc import Sequence
from typing import Union

# revision identifiers, used by Alembic.
revision: str = "370b03703c0d"
down_revision: Union[str, None] = ("20260123_cascade", "20260126_irt_4pl")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
