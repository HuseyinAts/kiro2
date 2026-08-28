"""faz1 Katman A grup-2 — org_id retrofit (karışık-FK PII tabloları)

learning_paths, topic_progress (→lp_student_profiles), user_theta (→users),
kiro2_learning_events (user_id UUID, tip uyumsuz).

Backfill = DOĞRUDAN org_legacy_default: tüm mevcut veri tek-kiracılı → hepsi
legacy'ye maplenir; join (grup-1'deki gibi) ile aynı sonuç ama tip/2-hop
sorunlarından kaçınır. Gelecek çok-kiracılı veride app org_id'yi insert'te set eder.

Reversible.

Revision ID: faz1_katmanA2_20260704
Revises: faz1_katmanA_20260704
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz1_katmanA2_20260704"
down_revision: Union[str, None] = "faz1_katmanA_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY = "org_legacy_default"
TABLES = ["learning_paths", "topic_progress", "user_theta", "kiro2_learning_events"]


def upgrade() -> None:
    conn = op.get_bind()
    for tbl in TABLES:
        op.add_column(tbl, sa.Column("organization_id", sa.String(), nullable=True))
        op.create_foreign_key(
            f"fk_{tbl}_organization",
            tbl,
            "organizations",
            ["organization_id"],
            ["id"],
            ondelete="RESTRICT",
        )
        op.create_index(f"idx_{tbl}_organization_id", tbl, ["organization_id"])
        op.execute(
            sa.text(
                f"UPDATE {tbl} SET organization_id = :legacy "
                f"WHERE organization_id IS NULL"
            ).bindparams(legacy=LEGACY)
        )
        n = conn.execute(
            sa.text(f"SELECT count(*) FROM {tbl} WHERE organization_id IS NULL")
        ).scalar()
        if n:
            raise RuntimeError(f"{tbl}: {n} NULL org_id")
        op.alter_column(
            tbl,
            "organization_id",
            existing_type=sa.String(),
            nullable=False,
            server_default=LEGACY,
        )


def downgrade() -> None:
    for tbl in TABLES:
        op.drop_index(f"idx_{tbl}_organization_id", table_name=tbl)
        op.drop_constraint(f"fk_{tbl}_organization", tbl, type_="foreignkey")
        op.drop_column(tbl, "organization_id")
