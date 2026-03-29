"""Create kiro2_cat_sessions table (merge heads)

Revision ID: cat_sessions_001
Revises: zpd_history_001, d3e4f5a6b7c8
Create Date: 2026-03-29

"""

from collections.abc import Sequence
from typing import Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "cat_sessions_001"
down_revision: Union[str, Sequence[str], None] = ("zpd_history_001", "d3e4f5a6b7c8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS kiro2_cat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            subject_id TEXT NOT NULL,
            theta_final NUMERIC,
            se_final NUMERIC,
            n_questions SMALLINT DEFAULT 0,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            termination_reason TEXT,
            state TEXT DEFAULT 'active',
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kiro2_cat_sessions_user_state
        ON kiro2_cat_sessions(user_id, state, completed_at DESC)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_kiro2_cat_sessions_user_subject
        ON kiro2_cat_sessions(user_id, subject_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_kiro2_cat_sessions_user_subject")
    op.execute("DROP INDEX IF EXISTS idx_kiro2_cat_sessions_user_state")
    op.execute("DROP TABLE IF EXISTS kiro2_cat_sessions")
