"""faz1 Katman A — organization_id retrofit (yüksek-PII tablolar)

Faz 1 Step A: tenant-owned yüksek-PII tablolara org_id (nullable→backfill→NOT NULL
→server_default). Backfill: kullanıcının org'u (users/student_profiles join),
orphan/eksik → org_legacy_default (COALESCE, NULL kalması engellenir).

Tüm mevcut veri tek-kiracılı → hepsi org_legacy_default. server_default eski kod
INSERT'lerini kırılmaktan korur (Faz 0 register 500 dersi). ORM kolonu + repo
scoping AYRI tur (Step 3-eşdeğeri wiring).

Kapsam: FK→users grubu + exam_sessions (→student_profiles).
Reversible: downgrade kolonları düşürür.

Revision ID: faz1_katmanA_20260704
Revises: faz0_memberships_20260703
Create Date: 2026-07-04

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz1_katmanA_20260704"
down_revision: Union[str, None] = "faz0_memberships_20260703"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

LEGACY = "org_legacy_default"

# (tablo, user-ref kolon, backfill kaynak tablosu, kaynak-eşleşme kolonu)
# via_col = kaynak tabloda user-ref'in eşleştiği kolon
GROUP = [
    ("fsrs_cards", "student_id", "users", "id"),
    ("fsrs_reviews", "student_id", "users", "id"),
    ("fsrs_schedules", "student_id", "users", "id"),
    ("student_abilities", "student_id", "users", "id"),
    ("bkt_states", "student_id", "users", "id"),
    ("student_knowledge_states", "student_id", "users", "id"),
    ("performance_history", "user_id", "users", "id"),
    ("kvkk_consents", "user_id", "users", "id"),
    ("exam_sessions", "student_id", "student_profiles", "id"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for tbl, ucol, src, scol in GROUP:
        # 1) nullable org_id + FK + index
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
        # 2) backfill: kullanıcının org'u, orphan → legacy (NULL kalmaz)
        op.execute(
            sa.text(
                f"UPDATE {tbl} t SET organization_id = COALESCE("
                f"  (SELECT s.organization_id FROM {src} s WHERE s.{scol} = t.{ucol}), "
                f"  :legacy) "
                f"WHERE t.organization_id IS NULL"
            ).bindparams(legacy=LEGACY)
        )
        # 3) NULL guard (sessiz veri kaybı önle)
        n = conn.execute(
            sa.text(f"SELECT count(*) FROM {tbl} WHERE organization_id IS NULL")
        ).scalar()
        if n:
            raise RuntimeError(f"{tbl}: {n} NULL org_id — flip iptal")
        # 4) NOT NULL + server_default (geçiş güvenliği)
        op.alter_column(
            tbl,
            "organization_id",
            existing_type=sa.String(),
            nullable=False,
            server_default=LEGACY,
        )


def downgrade() -> None:
    for tbl, *_ in GROUP:
        op.drop_index(f"idx_{tbl}_organization_id", table_name=tbl)
        op.drop_constraint(f"fk_{tbl}_organization", tbl, type_="foreignkey")
        op.drop_column(tbl, "organization_id")
