"""Add KVKK compliance tables

Revision ID: kvkk_compliance_001
Revises: 
Create Date: 2025-10-04 12:00:00.000000

KVKK (Kişisel Verilerin Korunması Kanunu) compliance tables:
- kvkk_consents: Rıza kayıtları
- kvkk_data_processing_logs: Veri işleme kayıtları
- kvkk_data_subject_requests: Veri sahibi talepleri
- kvkk_data_breaches: Veri ihlali kayıtları
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "kvkk_compliance_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create KVKK compliance tables"""

    # kvkk_consents table
    op.create_table(
        "kvkk_consents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("consent_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("consent_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column("consent_version", sa.String(length=20), nullable=False),
        sa.Column("granted_at", sa.DateTime(), nullable=True),
        sa.Column("withdrawn_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("consent_method", sa.String(length=50), nullable=True),
        sa.Column("additional_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kvkk_consents_consent_id", "kvkk_consents", ["consent_id"], unique=True
    )
    op.create_index("ix_kvkk_consents_user_id", "kvkk_consents", ["user_id"])

    # kvkk_data_processing_logs table
    op.create_table(
        "kvkk_data_processing_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("log_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("data_category", sa.String(length=50), nullable=False),
        sa.Column("purpose", sa.String(length=50), nullable=False),
        sa.Column("operation", sa.String(length=50), nullable=False),
        sa.Column("data_fields", sa.JSON(), nullable=False),
        sa.Column("legal_basis", sa.String(length=100), nullable=False),
        sa.Column("consent_id", sa.String(length=36), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=500), nullable=True),
        sa.Column("service_name", sa.String(length=100), nullable=True),
        sa.Column("additional_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kvkk_data_processing_logs_log_id",
        "kvkk_data_processing_logs",
        ["log_id"],
        unique=True,
    )
    op.create_index(
        "ix_kvkk_data_processing_logs_user_id", "kvkk_data_processing_logs", ["user_id"]
    )
    op.create_index(
        "ix_kvkk_data_processing_logs_processed_at",
        "kvkk_data_processing_logs",
        ["processed_at"],
    )

    # kvkk_data_subject_requests table
    op.create_table(
        "kvkk_data_subject_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("request_type", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("response_date", sa.DateTime(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("deadline", sa.DateTime(), nullable=False),
        sa.Column("additional_data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kvkk_data_subject_requests_request_id",
        "kvkk_data_subject_requests",
        ["request_id"],
        unique=True,
    )
    op.create_index(
        "ix_kvkk_data_subject_requests_user_id",
        "kvkk_data_subject_requests",
        ["user_id"],
    )
    op.create_index(
        "ix_kvkk_data_subject_requests_requested_at",
        "kvkk_data_subject_requests",
        ["requested_at"],
    )

    # kvkk_data_breaches table
    op.create_table(
        "kvkk_data_breaches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("breach_id", sa.String(length=36), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("affected_users_count", sa.Integer(), nullable=False),
        sa.Column("data_categories", sa.JSON(), nullable=False),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("reported_to_kvkk", sa.Boolean(), nullable=False),
        sa.Column("reported_to_kvkk_at", sa.DateTime(), nullable=True),
        sa.Column("users_notified", sa.Boolean(), nullable=False),
        sa.Column("users_notified_at", sa.DateTime(), nullable=True),
        sa.Column("mitigation_actions", sa.JSON(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("additional_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_kvkk_data_breaches_breach_id",
        "kvkk_data_breaches",
        ["breach_id"],
        unique=True,
    )


def downgrade():
    """Drop KVKK compliance tables"""

    op.drop_index("ix_kvkk_data_breaches_breach_id", table_name="kvkk_data_breaches")
    op.drop_table("kvkk_data_breaches")

    op.drop_index(
        "ix_kvkk_data_subject_requests_requested_at",
        table_name="kvkk_data_subject_requests",
    )
    op.drop_index(
        "ix_kvkk_data_subject_requests_user_id", table_name="kvkk_data_subject_requests"
    )
    op.drop_index(
        "ix_kvkk_data_subject_requests_request_id",
        table_name="kvkk_data_subject_requests",
    )
    op.drop_table("kvkk_data_subject_requests")

    op.drop_index(
        "ix_kvkk_data_processing_logs_processed_at",
        table_name="kvkk_data_processing_logs",
    )
    op.drop_index(
        "ix_kvkk_data_processing_logs_user_id", table_name="kvkk_data_processing_logs"
    )
    op.drop_index(
        "ix_kvkk_data_processing_logs_log_id", table_name="kvkk_data_processing_logs"
    )
    op.drop_table("kvkk_data_processing_logs")

    op.drop_index("ix_kvkk_consents_user_id", table_name="kvkk_consents")
    op.drop_index("ix_kvkk_consents_consent_id", table_name="kvkk_consents")
    op.drop_table("kvkk_consents")
