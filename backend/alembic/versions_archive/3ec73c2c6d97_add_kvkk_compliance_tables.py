"""add_kvkk_compliance_tables

Revision ID: 3ec73c2c6d97
Revises: d7a10d07b648
Create Date: 2025-11-11 19:17:00.551893

Sprint 5: KVKK Compliance
Creates tables for Turkish GDPR compliance:
- kvkk_consents - User consent management
- kvkk_privacy_policy_versions - Privacy policy tracking
- kvkk_data_export_requests - Data portability
- kvkk_data_deletion_requests - Right to erasure
- kvkk_audit_logs - Data access audit trail
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3ec73c2c6d97"
down_revision: Union[str, None] = "d7a10d07b648"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create KVKK compliance tables"""

    # Create enum types
    op.execute("""
        CREATE TYPE consent_status AS ENUM ('given', 'withdrawn', 'expired');
    """)

    op.execute("""
        CREATE TYPE data_processing_purpose AS ENUM (
            'service_provision', 'account_management', 'authentication',
            'communication', 'notifications', 'support',
            'analytics', 'performance_monitoring', 'product_improvement',
            'marketing', 'personalization',
            'legal_compliance', 'fraud_prevention',
            'exam_evaluation', 'progress_tracking', 'content_recommendation'
        );
    """)

    op.execute("""
        CREATE TYPE export_request_status AS ENUM (
            'pending', 'processing', 'completed', 'failed', 'expired'
        );
    """)

    op.execute("""
        CREATE TYPE deletion_request_status AS ENUM (
            'pending', 'approved', 'processing', 'completed', 'rejected'
        );
    """)

    # 1. KVKK Consents table
    op.create_table(
        "kvkk_consents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("purpose", sa.Enum(name="data_processing_purpose"), nullable=False),
        sa.Column("status", sa.Enum(name="consent_status"), nullable=False),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column("privacy_policy_version", sa.String(20), nullable=False),
        sa.Column(
            "given_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("additional_data", JSON, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_kvkk_consents_user_id", "kvkk_consents", ["user_id"])
    op.create_index("idx_kvkk_consents_purpose", "kvkk_consents", ["purpose"])
    op.create_index("idx_kvkk_consents_status", "kvkk_consents", ["status"])

    # 2. Privacy Policy Versions table
    op.create_table(
        "kvkk_privacy_policy_versions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index(
        "idx_kvkk_policy_version", "kvkk_privacy_policy_versions", ["version"]
    )
    op.create_index(
        "idx_kvkk_policy_active", "kvkk_privacy_policy_versions", ["is_active"]
    )

    # 3. Data Export Requests table
    op.create_table(
        "kvkk_data_export_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("status", sa.Enum(name="export_request_status"), nullable=False),
        sa.Column("request_reason", sa.Text(), nullable=True),
        sa.Column(
            "export_format", sa.String(20), nullable=False, server_default="json"
        ),
        sa.Column("data_categories", JSON, nullable=True),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("download_url", sa.String(500), nullable=True),
        sa.Column("download_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_kvkk_export_user_id", "kvkk_data_export_requests", ["user_id"])
    op.create_index("idx_kvkk_export_status", "kvkk_data_export_requests", ["status"])

    # 4. Data Deletion Requests table
    op.create_table(
        "kvkk_data_deletion_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("status", sa.Enum(name="deletion_request_status"), nullable=False),
        sa.Column("request_reason", sa.Text(), nullable=False),
        sa.Column(
            "deletion_type", sa.String(50), nullable=False, server_default="full"
        ),
        sa.Column("data_categories", JSON, nullable=True),
        sa.Column("reviewed_by", sa.String(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column(
            "requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
    )
    op.create_index(
        "idx_kvkk_deletion_user_id", "kvkk_data_deletion_requests", ["user_id"]
    )
    op.create_index(
        "idx_kvkk_deletion_status", "kvkk_data_deletion_requests", ["status"]
    )

    # 5. Audit Logs table
    op.create_table(
        "kvkk_audit_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("accessed_by", sa.String(), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("purpose", sa.Enum(name="data_processing_purpose"), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("request_path", sa.String(500), nullable=True),
        sa.Column("details", JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["accessed_by"], ["users.id"]),
    )
    op.create_index("idx_kvkk_audit_user_id", "kvkk_audit_logs", ["user_id"])
    op.create_index("idx_kvkk_audit_accessed_by", "kvkk_audit_logs", ["accessed_by"])
    op.create_index("idx_kvkk_audit_action", "kvkk_audit_logs", ["action"])
    op.create_index("idx_kvkk_audit_created_at", "kvkk_audit_logs", ["created_at"])

    print("SUCCESS: KVKK compliance tables created")


def downgrade() -> None:
    """Drop KVKK compliance tables"""

    # Drop tables
    op.drop_table("kvkk_audit_logs")
    op.drop_table("kvkk_data_deletion_requests")
    op.drop_table("kvkk_data_export_requests")
    op.drop_table("kvkk_privacy_policy_versions")
    op.drop_table("kvkk_consents")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS deletion_request_status")
    op.execute("DROP TYPE IF EXISTS export_request_status")
    op.execute("DROP TYPE IF EXISTS data_processing_purpose")
    op.execute("DROP TYPE IF EXISTS consent_status")

    print("SUCCESS: KVKK compliance tables dropped")
