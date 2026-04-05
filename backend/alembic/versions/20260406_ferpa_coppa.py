"""create_ferpa_coppa_tables

Revision ID: 20260406_ferpa_coppa
Revises: 20260406_kvkk_recreate
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa

revision = "20260406_ferpa_coppa"
down_revision = "20260406_kvkk_recreate"
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types with safe pattern
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE parentalconsentstatus AS ENUM ('pending','verified','denied','expired','withdrawn');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE educationalrecordtype AS ENUM ('academic_performance','attendance','behavioral_records','health_records','special_education','disciplinary_records','standardized_test_scores');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.create_table("ferpa_consents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("consent_id", sa.String(36), unique=True),
        sa.Column("student_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_id", sa.String, sa.ForeignKey("users.id"), nullable=True),
        sa.Column("consent_status", sa.String(20)),
        sa.Column("record_types", sa.String(500)),
        sa.Column("allow_third_party_disclosure", sa.Boolean, default=False),
        sa.Column("third_party_institutions", sa.Text, nullable=True),
        sa.Column("parent_verification_method", sa.String(100)),
        sa.Column("verification_date", sa.DateTime, nullable=True),
        sa.Column("verification_ip", sa.String(50), nullable=True),
        sa.Column("consent_given_date", sa.DateTime, nullable=True),
        sa.Column("consent_expiry_date", sa.DateTime, nullable=True),
        sa.Column("last_modified", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("coppa_parental_consents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("consent_id", sa.String(36), unique=True),
        sa.Column("child_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("parent_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("child_date_of_birth", sa.Date, nullable=False),
        sa.Column("consent_status", sa.String(20)),
        sa.Column("verification_method", sa.String(100)),
        sa.Column("verification_date", sa.DateTime, nullable=True),
        sa.Column("verification_document_path", sa.String(500), nullable=True),
        sa.Column("allow_data_collection", sa.Boolean, default=False),
        sa.Column("allow_marketing_communication", sa.Boolean, default=False),
        sa.Column("allow_third_party_sharing", sa.Boolean, default=False),
        sa.Column("consent_given_date", sa.DateTime, nullable=True),
        sa.Column("consent_expiry_date", sa.DateTime, nullable=True),
        sa.Column("withdrawal_date", sa.DateTime, nullable=True),
        sa.Column("withdrawal_reason", sa.Text, nullable=True),
        sa.Column("parent_ip_address", sa.String(50)),
        sa.Column("parent_user_agent", sa.String(500)),
        sa.Column("consent_form_version", sa.String(20)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_modified", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table("educational_record_access_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("log_id", sa.String(36), unique=True),
        sa.Column("student_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("accessor_id", sa.String, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("accessor_role", sa.String(50)),
        sa.Column("record_type", sa.String(50)),
        sa.Column("access_purpose", sa.String(200)),
        sa.Column("access_timestamp", sa.DateTime, server_default=sa.func.now()),
        sa.Column("ip_address", sa.String(50)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("legitimate_educational_interest", sa.Boolean, default=True),
        sa.Column("consent_id", sa.String(36), nullable=True),
    )

    op.create_table("data_retention_policies",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("policy_id", sa.String(36), unique=True),
        sa.Column("policy_name", sa.String(200), nullable=False),
        sa.Column("data_category", sa.String(100)),
        sa.Column("retention_period_days", sa.Integer, nullable=False),
        sa.Column("compliance_framework", sa.String(50)),
        sa.Column("auto_delete_enabled", sa.Boolean, default=False),
        sa.Column("deletion_grace_period_days", sa.Integer, default=30),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_modified", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_by", sa.String, sa.ForeignKey("users.id")),
    )

    op.create_table("data_processing_agreements",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("agreement_id", sa.String(36), unique=True),
        sa.Column("third_party_name", sa.String(200), nullable=False),
        sa.Column("third_party_contact", sa.String(500)),
        sa.Column("agreement_type", sa.String(50)),
        sa.Column("ferpa_compliant", sa.Boolean, default=False),
        sa.Column("coppa_compliant", sa.Boolean, default=False),
        sa.Column("data_types_shared", sa.Text),
        sa.Column("data_usage_purpose", sa.Text),
        sa.Column("data_retention_period", sa.Integer),
        sa.Column("agreement_start_date", sa.Date, nullable=False),
        sa.Column("agreement_end_date", sa.Date, nullable=True),
        sa.Column("agreement_status", sa.String(50), default="active"),
        sa.Column("agreement_document_path", sa.String(500)),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_modified", sa.DateTime, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("data_processing_agreements")
    op.drop_table("data_retention_policies")
    op.drop_table("educational_record_access_logs")
    op.drop_table("coppa_parental_consents")
    op.drop_table("ferpa_consents")
    op.execute("DROP TYPE IF EXISTS educationalrecordtype")
    op.execute("DROP TYPE IF EXISTS parentalconsentstatus")
