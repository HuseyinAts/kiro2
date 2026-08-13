"""faz0 org_id NOT NULL — kimlik çekirdeği

Faz 0 Step 2b: organization_id NOT NULL flip (users + 3 profil).
Ön koşul: Step 2a backfill %100 (0 NULL doğrulandı).

Reversible: downgrade NULL'a izin verir.

Revision ID: d3e4f5a6b7c8
Revises: c2d3e4f5a6b7
Create Date: 2026-07-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz0_notnull_20260703"
down_revision: Union[str, None] = "c2d3e4f5a6b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]


def upgrade() -> None:
    # Güvenlik: hâlâ NULL varsa flip'i durdur (sessiz veri kaybı önle)
    conn = op.get_bind()
    for t in IDENTITY_TABLES:
        n = conn.execute(
            sa.text(f"SELECT count(*) FROM {t} WHERE organization_id IS NULL")
        ).scalar()
        if n:
            raise RuntimeError(
                f"{t}: {n} satır org_id NULL — NOT NULL flip iptal, önce backfill et"
            )
    for t in IDENTITY_TABLES:
        op.alter_column(t, "organization_id", existing_type=sa.String(), nullable=False)


def downgrade() -> None:
    for t in IDENTITY_TABLES:
        op.alter_column(t, "organization_id", existing_type=sa.String(), nullable=True)
