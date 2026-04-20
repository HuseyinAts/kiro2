"""Create offline_sync_packages table

Revision ID: offline_sync_pkg_20260420 (<=32 chars for alembic_version)
Revises: student_review_drift_001
Create Date: 2026-04-20
"""

from alembic import op

revision = "offline_sync_pkg_20260420"
down_revision = "student_review_drift_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offline_sync_packages (
            package_id   VARCHAR PRIMARY KEY,
            student_id   VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            consumed_at  TIMESTAMPTZ NULL,
            question_ids JSONB NULL
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_offline_sync_packages_student "
        "ON offline_sync_packages (student_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_offline_sync_packages_consumed "
        "ON offline_sync_packages (consumed_at)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_offline_sync_packages_consumed")
    op.execute("DROP INDEX IF EXISTS idx_offline_sync_packages_student")
    op.execute("DROP TABLE IF EXISTS offline_sync_packages")
