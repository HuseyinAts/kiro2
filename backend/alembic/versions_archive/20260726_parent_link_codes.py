"""parent_link_codes — kod-tabanli veli-ogrenci baglama (6-hane, 10dk TTL)

Yeni tablo: ogrenci 6-hane kisa-omurlu kod uretir, veli kodu girerek
ParentChild(approved=False) iliskisi baslatir. Email-tabanli akisa ek yol.

RLS: parent_child ile ayni tenant_isolation policy (permissive-when-unset)
+ FORCE. FORCE ROW LEVEL SECURITY altinda policy'siz tablo, GUC set iken
INSERT'i reddeder → parity policy ZORUNLU (defense-in-depth + izolasyon).

GRANT: kiro2_app non-superuser rolu (RLS-aktif ortam) icin explicit GRANT —
rol yoksa (test/CI) sessizce atlanir (idempotent DO blok). ALTER DEFAULT
PRIVILEGES zaten gelecek tablolari kapsar; bu explicit GRANT belt-and-suspenders.

users.id VARCHAR → student_id sa.String. tz-aware UTC (DateTime(timezone=True)).

Revision ID: parent_link_codes_20260726
Revises: offline_sync_restore_20260725
Create Date: 2026-07-26
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "parent_link_codes_20260726"
down_revision: Union[str, None] = "offline_sync_restore_20260725"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# parent_child (faz1_rls2) ile birebir ayni tenant_isolation predikati.
_PRED = (
    "current_setting('app.current_org_id', true) IS NULL "
    "OR current_setting('app.current_org_id', true) = '' "
    "OR organization_id = current_setting('app.current_org_id', true)"
)


def upgrade() -> None:
    op.create_table(
        "parent_link_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "organization_id",
            sa.String(),
            sa.ForeignKey("organizations.id", ondelete="RESTRICT"),
            nullable=False,
            server_default="org_legacy_default",
        ),
        sa.Column("code", sa.String(length=6), nullable=False),
        sa.Column(
            "student_id",
            sa.String(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "consumed",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_parent_link_codes_code", "parent_link_codes", ["code"])
    op.create_index(
        "ix_parent_link_codes_organization_id",
        "parent_link_codes",
        ["organization_id"],
    )
    op.create_index(
        "ix_parent_link_codes_student_id",
        "parent_link_codes",
        ["student_id"],
    )

    # RLS — parent_child ile ayni desen (permissive-when-unset + FORCE).
    op.execute("ALTER TABLE parent_link_codes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE parent_link_codes FORCE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY tenant_isolation ON parent_link_codes FOR ALL "
        f"USING ({_PRED}) WITH CHECK ({_PRED})"
    )

    # GRANT — kiro2_app varsa (RLS-aktif ortam); yoksa (test/CI) sessizce atla.
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'kiro2_app') THEN
            GRANT SELECT, INSERT, UPDATE, DELETE
              ON parent_link_codes TO kiro2_app;
            GRANT USAGE, SELECT, UPDATE
              ON SEQUENCE parent_link_codes_id_seq TO kiro2_app;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON parent_link_codes")
    op.execute("ALTER TABLE parent_link_codes NO FORCE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE parent_link_codes DISABLE ROW LEVEL SECURITY")
    op.drop_index("ix_parent_link_codes_student_id", table_name="parent_link_codes")
    op.drop_index(
        "ix_parent_link_codes_organization_id", table_name="parent_link_codes"
    )
    op.drop_index("ix_parent_link_codes_code", table_name="parent_link_codes")
    op.drop_table("parent_link_codes")
