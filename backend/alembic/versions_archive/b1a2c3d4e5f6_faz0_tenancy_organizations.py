"""faz0 tenancy — organizations + org_memberships

Faz 0 Step 1: multi-tenancy kök tabloları (additive, mevcut tablolara dokunmaz).
Model: models/organization.py. Reversible: downgrade tabloları düşürür.

Revision ID: b1a2c3d4e5f6
Revises: 3dfb6239addd
Create Date: 2026-07-03

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "b1a2c3d4e5f6"
down_revision: Union[str, None] = "3dfb6239addd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column(
            "org_type", sa.String(length=30), nullable=False, server_default="ozel_okul"
        ),
        sa.Column(
            "status", sa.String(length=20), nullable=False, server_default="trial"
        ),
        sa.Column(
            "kvkk_role",
            sa.String(length=20),
            nullable=False,
            server_default="controller",
        ),
        sa.Column("kvkk_verbis_no", sa.String(length=50), nullable=True),
        sa.Column("license_seats", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("license_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dpa_signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contact_email", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_org_status", "organizations", ["status"])
    op.create_index("idx_org_type", "organizations", ["org_type"])

    op.create_table(
        "org_memberships",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column(
            "org_role", sa.String(length=20), nullable=False, server_default="STUDENT"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("organization_id", "user_id", name="uq_org_membership"),
    )
    op.create_index("idx_org_membership_org", "org_memberships", ["organization_id"])
    op.create_index("idx_org_membership_user", "org_memberships", ["user_id"])
    op.create_index(
        "idx_org_membership_role", "org_memberships", ["organization_id", "org_role"]
    )


def downgrade() -> None:
    op.drop_table("org_memberships")
    op.drop_table("organizations")
