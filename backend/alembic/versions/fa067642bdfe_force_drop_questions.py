"""force_drop_questions

Revision ID: fa067642bdfe
Revises: 7b00c895ec27
Create Date: 2026-08-04 18:43:46.759327

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fa067642bdfe"  # pragma: allowlist secret
down_revision: Union[str, None] = "7b00c895ec27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop questions if it exists
    op.execute("DROP TABLE IF EXISTS questions CASCADE")


def downgrade() -> None:
    pass
