"""faz1 B2B — DPA + lisanslama/faturalama MVP tabloları

plans (global katalog) + organization_licenses + data_processing_agreements +
invoices. Model: models/billing.py. Additive (yeni tablolar).
3 varsayılan plan seed'lenir (free / okul_basic / okul_pro).
Reversible.

Revision ID: faz1_billing_20260704
Revises: faz1_rls2_20260704
Create Date: 2026-07-04
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op

revision: str = "faz1_billing_20260704"
down_revision: Union[str, None] = "faz1_rls2_20260704"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("price_try", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column(
            "billing_period", sa.String(12), nullable=False, server_default="yearly"
        ),
        sa.Column("seat_limit", sa.Integer(), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_table(
        "organization_licenses",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("plan_id", sa.String(), nullable=False),
        sa.Column("seat_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(20), nullable=False, server_default="trial"),
        sa.Column("term_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("term_end", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="RESTRICT"),
    )
    op.create_index("idx_org_license_org", "organization_licenses", ["organization_id"])
    op.create_index("idx_org_license_status", "organization_licenses", ["status"])

    op.create_table(
        "data_processing_agreements",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("version", sa.String(20), nullable=False, server_default="v1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("signer_name", sa.String(200), nullable=True),
        sa.Column("signer_email", sa.String(255), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("idx_dpa_org", "data_processing_agreements", ["organization_id"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("license_id", sa.String(), nullable=True),
        sa.Column("invoice_no", sa.String(40), nullable=False, unique=True),
        sa.Column("amount_try", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="TRY"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("method", sa.String(20), nullable=False, server_default="havale"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"], ["organizations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["license_id"], ["organization_licenses.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("idx_invoice_org", "invoices", ["organization_id"])
    op.create_index("idx_invoice_status", "invoices", ["status"])

    # 3 varsayılan plan seed. json_build_object kullan — JSON literal'ındeki :true
    # SQLAlchemy text() tarafından bind-param (:true) sanılıyordu.
    op.execute(
        """
        INSERT INTO plans (id,code,name,price_try,billing_period,seat_limit,features,is_active,created_at) VALUES
        (gen_random_uuid()::text,'free','Ucretsiz Deneme',0,'yearly',25,
          json_build_object('beta',true),true,now()),
        (gen_random_uuid()::text,'okul_basic','Okul Basic',15000,'yearly',150,
          json_build_object('analytics',true,'sso',false),true,now()),
        (gen_random_uuid()::text,'okul_pro','Okul Pro',40000,'yearly',500,
          json_build_object('analytics',true,'sso',true,'priority_support',true),true,now())
        """
    )


def downgrade() -> None:
    op.drop_table("invoices")
    op.drop_table("data_processing_agreements")
    op.drop_table("organization_licenses")
    op.drop_table("plans")
