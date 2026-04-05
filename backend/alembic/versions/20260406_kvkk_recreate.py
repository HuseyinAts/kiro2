"""recreate_kvkk_tables

Revision ID: 20260406_kvkk_recreate
Revises: 20260401_fix_fsrs_reviews_fk
Create Date: 2026-04-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision: str = '20260406_kvkk_recreate'
down_revision: Union[str, None] = '20260401_fix_fsrs_reviews_fk'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("""
    DO $$ BEGIN
        CREATE TYPE consent_status AS ENUM ('given', 'withdrawn', 'expired');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """))

    conn.execute(sa.text("""
    DO $$ BEGIN
        CREATE TYPE data_processing_purpose AS ENUM (
            'service_provision', 'account_management', 'authentication',
            'communication', 'notifications', 'support',
            'analytics', 'performance_monitoring', 'product_improvement',
            'marketing', 'personalization',
            'legal_compliance', 'fraud_prevention',
            'exam_evaluation', 'progress_tracking', 'content_recommendation');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """))

    conn.execute(sa.text("""
    DO $$ BEGIN
        CREATE TYPE export_request_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'expired');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """))

    conn.execute(sa.text("""
    DO $$ BEGIN
        CREATE TYPE deletion_request_status AS ENUM ('pending', 'approved', 'processing', 'completed', 'rejected');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """))

    conn.execute(sa.text("""
    CREATE TABLE IF NOT EXISTS kvkk_consents (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        purpose data_processing_purpose NOT NULL,
        status consent_status NOT NULL,
        consent_text TEXT NOT NULL,
        privacy_policy_version VARCHAR(20) NOT NULL,
        given_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        withdrawn_at TIMESTAMPTZ,
        expires_at TIMESTAMPTZ,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        additional_data JSON
    )"""))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_user_id ON kvkk_consents(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_purpose ON kvkk_consents(purpose)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_consents_status ON kvkk_consents(status)"))

    conn.execute(sa.text("""
    CREATE TABLE IF NOT EXISTS kvkk_data_deletion_requests (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status deletion_request_status NOT NULL,
        request_reason TEXT NOT NULL,
        deletion_type VARCHAR(50) NOT NULL DEFAULT 'full',
        data_categories JSON,
        reviewed_by VARCHAR REFERENCES users(id),
        review_notes TEXT,
        rejection_reason TEXT,
        requested_at TIMESTAMPTZ DEFAULT NOW(),
        reviewed_at TIMESTAMPTZ,
        processed_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ
    )"""))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_deletion_user_id ON kvkk_data_deletion_requests(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_deletion_status ON kvkk_data_deletion_requests(status)"))

    conn.execute(sa.text("""
    CREATE TABLE IF NOT EXISTS kvkk_privacy_policy_versions (
        id VARCHAR PRIMARY KEY,
        version VARCHAR(20) NOT NULL UNIQUE,
        title VARCHAR(200) NOT NULL,
        content TEXT NOT NULL,
        is_active BOOLEAN DEFAULT FALSE,
        effective_date TIMESTAMPTZ NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        created_by VARCHAR REFERENCES users(id)
    )"""))

    conn.execute(sa.text("""
    CREATE TABLE IF NOT EXISTS kvkk_data_export_requests (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        status export_request_status NOT NULL,
        request_reason TEXT,
        export_format VARCHAR(20) NOT NULL DEFAULT 'json',
        data_categories JSON,
        file_path VARCHAR(500),
        file_size_bytes INTEGER,
        download_url VARCHAR(500),
        download_expires_at TIMESTAMPTZ,
        requested_at TIMESTAMPTZ DEFAULT NOW(),
        processed_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        error_message TEXT
    )"""))

    conn.execute(sa.text("""
    CREATE TABLE IF NOT EXISTS kvkk_audit_logs (
        id VARCHAR PRIMARY KEY,
        user_id VARCHAR REFERENCES users(id),
        accessed_by VARCHAR REFERENCES users(id),
        action VARCHAR(100) NOT NULL,
        resource_type VARCHAR(100),
        resource_id VARCHAR,
        purpose data_processing_purpose,
        ip_address VARCHAR(45),
        user_agent VARCHAR(500),
        request_method VARCHAR(10),
        request_path VARCHAR(500),
        details JSON,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )"""))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_user_id ON kvkk_audit_logs(user_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_action ON kvkk_audit_logs(action)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_kvkk_audit_created_at ON kvkk_audit_logs(created_at)"))


def downgrade() -> None:
    op.drop_table('kvkk_audit_logs')
    op.drop_table('kvkk_data_export_requests')
    op.drop_table('kvkk_privacy_policy_versions')
    op.drop_table('kvkk_data_deletion_requests')
    op.drop_table('kvkk_consents')
    op.execute("DROP TYPE IF EXISTS deletion_request_status")
    op.execute("DROP TYPE IF EXISTS export_request_status")
    op.execute("DROP TYPE IF EXISTS data_processing_purpose")
    op.execute("DROP TYPE IF EXISTS consent_status")