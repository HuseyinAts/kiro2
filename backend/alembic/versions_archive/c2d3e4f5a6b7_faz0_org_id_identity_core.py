"""faz0 org_id retrofit — kimlik çekirdeği (users + 3 profil)

Faz 0 Step 2 (güvenli dilim): nullable organization_id FK + org_legacy_default
backfill. NOT NULL flip ve diğer ~76 tablo AYRI turlarda.

Reversible: downgrade kolonları + legacy org'u düşürür.

Revision ID: c2d3e4f5a6b7
Revises: b1a2c3d4e5f6
Create Date: 2026-07-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "c2d3e4f5a6b7"
down_revision: Union[str, None] = "b1a2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

IDENTITY_TABLES = ["users", "student_profiles", "teacher_profiles", "parent_profiles"]
LEGACY_ORG = "org_legacy_default"


def upgrade() -> None:
    # 1) legacy tenant kaydı (mevcut tek-kiracılı veri buraya bağlanır)
    op.execute(
        sa.text(
            "INSERT INTO organizations (id, name, org_type, status, kvkk_role, "
            "license_seats, created_at, updated_at) "
            "VALUES (:id, :name, 'kurumsal', 'active', 'controller', 0, now(), now()) "
            "ON CONFLICT (id) DO NOTHING"
        ).bindparams(id=LEGACY_ORG, name="Legacy (tek-kiracılı geçiş)")
    )

    # 2) nullable organization_id + FK (nullable => mevcut satırlar kırılmaz)
    for t in IDENTITY_TABLES:
        op.add_column(t, sa.Column("organization_id", sa.String(), nullable=True))
        op.create_foreign_key(
            f"fk_{t}_organization",
            t,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index(f"idx_{t}_organization_id", t, ["organization_id"])

    # 3) backfill: tüm mevcut satırlar legacy org'a
    for t in IDENTITY_TABLES:
        op.execute(
            sa.text(
                f"UPDATE {t} SET organization_id = :org WHERE organization_id IS NULL"
            ).bindparams(org=LEGACY_ORG)
        )


def downgrade() -> None:
    for t in IDENTITY_TABLES:
        op.drop_index(f"idx_{t}_organization_id", table_name=t)
        op.drop_constraint(f"fk_{t}_organization", t, type_="foreignkey")
        op.drop_column(t, "organization_id")
    op.execute(
        sa.text("DELETE FROM organizations WHERE id = :id").bindparams(id=LEGACY_ORG)
    )
