"""KVKK Faz 2: veli_consent tablosu (veli açık rıza akışı)

Reşit olmayan öğrenci için veli onay kaydı. Token plaintext sadece email
linkinde bulunur; DB'de yalnızca SHA-256 hash (token_hash) saklanır.
ORM modeli: models/veli_consent.py (VeliConsent).
"""

import sqlalchemy as sa

from alembic import op

revision = "kvkk2_veli_consent_20260529"
down_revision = "kvkk1_veli_email_20260528"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "veli_consent",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("child_user_id", sa.String(), nullable=False),
        sa.Column("veli_email", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "requested_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("consent_text", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "consent_version",
            sa.String(length=20),
            nullable=False,
            server_default="kvkk-veli-1.0",
        ),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_veli_consent_child_user_id", "veli_consent", ["child_user_id"])
    op.create_index("ix_veli_consent_token_hash", "veli_consent", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_veli_consent_token_hash", table_name="veli_consent")
    op.drop_index("ix_veli_consent_child_user_id", table_name="veli_consent")
    op.drop_table("veli_consent")
